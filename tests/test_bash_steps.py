"""Tests for the bash run: steps in apko-snapshot and vul-scans that call cosign,
crane and snyk with input values.

Each case runs one step's script the way GitHub runs it
(bash --noprofile --norc -eo pipefail), with stand-in tools that record argv.

Usage: python3 -I test_bash_steps.py <repo-root> [unittest args]
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

import yaml

REPO = os.environ.get("ACTIONS_REPO") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STUB = r"""#!/bin/sh
{ printf '%s\0' "$(basename "$0")"; for a in "$@"; do printf '%s\0' "$a"; done; printf '\n'; } >> "$ARGV_LOG"
case "$(basename "$0") $1" in
  "crane manifest")
    if [ -n "$CRANE_MANIFEST_FILE" ]; then cat "$CRANE_MANIFEST_FILE"
    else echo '{"mediaType":"application/vnd.oci.image.manifest.v1+json"}'; fi ;;
esac
exit 0
"""

GITHUB_CONTEXT = {"github.sha": "SHA", "github.run_id": "RUNID", "github.run_attempt": "1",
                  "github.repository": "example/repo"}


def find_step_script(action, key=None, contains=None):
    """Return the run: script of the step matching id/name key, or the single
    step whose script contains the given text."""
    with open(os.path.join(REPO, action, "action.yaml")) as f:
        doc = yaml.safe_load(f)
    steps = [s for s in doc["runs"]["steps"] if "run" in s]
    if key is not None:
        matches = [s for s in steps if key in (s.get("id"), s.get("name"))]
    else:
        matches = [s for s in steps if contains in s["run"]]
    assert len(matches) == 1, f"{len(matches)} steps in {action} match key={key!r} contains={contains!r}"
    script = matches[0]["run"]
    for k, v in GITHUB_CONTEXT.items():
        script = re.sub(r"\$\{\{\s*" + re.escape(k) + r"\s*\}\}", v, script)
    assert "${{" not in script, f"unexpected expression left in {action} step {key or contains!r}"
    return script


def run_step(action, key=None, env_vars=None, files=None, contains=None, want_output=False):
    """Run a step; return (returncode, output, recorded calls[, GITHUB_OUTPUT text])."""
    script = find_step_script(action, key=key, contains=contains)
    tmp = tempfile.mkdtemp(prefix="steptest-")
    try:
        bindir = os.path.join(tmp, "bin")
        os.mkdir(bindir)
        for tool in ("cosign", "crane", "snyk"):
            p = os.path.join(bindir, tool)
            with open(p, "w") as f:
                f.write(STUB)
            os.chmod(p, 0o755)
        # snyk is run as ./snyk from the workspace.
        shutil.copy(os.path.join(bindir, "snyk"), os.path.join(tmp, "snyk"))
        open(os.path.join(tmp, "GLOB_WOULD_MATCH_THIS"), "w").close()
        for name, content in (files or {}).items():
            with open(os.path.join(tmp, name), "w") as f:
                f.write(content)
        log = os.path.join(tmp, "argv.log")
        env = {"PATH": bindir + ":/usr/bin:/bin", "ARGV_LOG": log, "HOME": tmp,
               "GITHUB_OUTPUT": os.path.join(tmp, "out"), "GITHUB_ENV": os.path.join(tmp, "envf")}
        env.update(env_vars or {})
        proc = subprocess.run(
            ["bash", "--noprofile", "--norc", "-eo", "pipefail", "-c", script],
            env=env, cwd=tmp, capture_output=True, text=True, check=False)
        calls = []
        if os.path.exists(log):
            with open(log, "rb") as f:
                for line in f.read().split(b"\n"):
                    if line:
                        calls.append([a.decode() for a in line.split(b"\0")[:-1]])
        if want_output:
            out_path = os.path.join(tmp, "out")
            text = ""
            if os.path.exists(out_path):
                with open(out_path) as f:
                    text = f.read()
            return proc.returncode, proc.stdout + proc.stderr, calls, text
        return proc.returncode, proc.stdout + proc.stderr, calls
    finally:
        shutil.rmtree(tmp)


INJECT = "--rekor-url https://evil.example"
DIGEST = "ghcr.io/example/img@sha256:" + "a" * 64


class SnapshotSteps(unittest.TestCase):
    def test_cosign_sign(self):
        # The signing step has no id or name; find it by its "cosign sign" call.
        cases = [
            ("refs file with two references signs both, after --",
             "ref1@sha256:1\nref2@sha256:2\n", ["ref1@sha256:1", "ref2@sha256:2"]),
            ("a reference containing spaces stays one argument",
             "ref1 " + INJECT + "\n", ["ref1 " + INJECT]),
            ("a reference starting with - is still positional",
             "--output-signature=/tmp/x\n", ["--output-signature=/tmp/x"]),
        ]
        for name, refs, want_pos in cases:
            with self.subTest(name):
                rc, out, calls = run_step(
                    "apko-snapshot", contains="cosign sign", env_vars={"INPUTS_IMAGE_REFS": "refs.txt", "INPUTS_FULCIO_URL": "https://fulcio.example",
                     "INPUTS_REKOR_URL": "https://rekor.example", "COSIGN_EXPERIMENTAL": "true"},
                    files={"refs.txt": refs})
                self.assertEqual(rc, 0, out)
                want = ["cosign", "sign", "--yes", "--fulcio-url", "https://fulcio.example",
                        "--rekor-url", "https://rekor.example", "-a", "sha=SHA", "-a", "run_id=RUNID",
                        "-a", "run_attempt=1", "--"] + want_pos
                self.assertEqual(calls, [want], f"refs={refs!r}\nout={out}")

    def test_crane_tagging(self):
        cases = [
            ("target tag and comma-separated additional tags",
             {"INPUTS_TARGET_TAG": "latest", "INPUTS_ADDITIONAL_TAGS": "1.2, 1.2.3"},
             ["latest", "1.2", "1.2.3"]),
            ("no additional tags",
             {"INPUTS_TARGET_TAG": "latest", "INPUTS_ADDITIONAL_TAGS": ""}, ["latest"]),
            ("* in additional tags stays literal",
             {"INPUTS_TARGET_TAG": "latest", "INPUTS_ADDITIONAL_TAGS": "*"}, ["latest", "*"]),
        ]
        for name, env_vars, want_tags in cases:
            with self.subTest(name):
                env = {"STEPS_APKO_OUTPUTS_DIGEST": DIGEST, "INPUTS_BASE_TAG": "ghcr.io/example/img"}
                env.update(env_vars)
                rc, out, calls = run_step("apko-snapshot", contains="crane cp", env_vars=env)
                self.assertEqual(rc, 0, out)
                want = [["crane", "cp", "--", DIGEST, f"ghcr.io/example/img:{t}"] for t in want_tags]
                self.assertEqual(calls, want, f"env={env}\nout={out}")

    def test_extract_manifest(self):
        with self.subTest("crane manifest gets the digest after --"):
            rc, out, calls = run_step("apko-snapshot", "extract", env_vars={"STEPS_APKO_OUTPUTS_DIGEST": DIGEST,
                                       "INPUTS_BASE_TAG": "ghcr.io/example/img"})
            self.assertEqual(rc, 0, out)
            self.assertEqual(calls[0], ["crane", "manifest", "--", DIGEST], out)


def index_manifest(entries):
    """An OCI image index with (architecture, variant, digest) entries."""
    import json
    return json.dumps({
        "mediaType": "application/vnd.oci.image.index.v1+json",
        "manifests": [{"digest": d, "platform": dict({"architecture": a}, **({"variant": v} if v else {}))}
                      for a, v, d in entries],
    })


def read_outputs(text):
    """Parse GITHUB_OUTPUT name=value lines into a list of (name, value)."""
    return [tuple(line.split("=", 1)) for line in text.splitlines() if line]


class SnapshotValidation(unittest.TestCase):
    def test_validate_tag_inputs(self):
        ok = {"INPUTS_BASE_TAG": "ghcr.io/example/img", "INPUTS_TARGET_TAG": "latest",
              "INPUTS_ADDITIONAL_TAGS": ""}
        cases = [
            ("accepts the defaults' shape", {}, 0),
            ("accepts an uppercase owner from the default base-tag", {"INPUTS_BASE_TAG": "ghcr.io/Example/Img"}, 0),
            ("accepts a registry with a port", {"INPUTS_BASE_TAG": "localhost:5000/img"}, 0),
            ("accepts comma-separated additional tags", {"INPUTS_ADDITIONAL_TAGS": "1.2, 1.2.3,v1"}, 0),
            ("rejects a base-tag with a newline",
             {"INPUTS_BASE_TAG": "ghcr.io/example/img\ndigest-index=evil.example/x"}, 1),
            ("rejects a base-tag with a space", {"INPUTS_BASE_TAG": "ghcr.io/example/img --x"}, 1),
            ("rejects a base-tag starting with -", {"INPUTS_BASE_TAG": "-ghcr.io/x"}, 1),
            ("rejects a base-tag containing @", {"INPUTS_BASE_TAG": "ghcr.io/x@sha256:1"}, 1),
            ("rejects an empty target-tag", {"INPUTS_TARGET_TAG": ""}, 1),
            ("rejects a target-tag with a newline", {"INPUTS_TARGET_TAG": "latest\nx=y"}, 1),
            ("rejects a target-tag starting with -", {"INPUTS_TARGET_TAG": "-latest"}, 1),
            ("rejects a target-tag longer than 128 characters", {"INPUTS_TARGET_TAG": "a" * 129}, 1),
            ("rejects an additional tag with a newline", {"INPUTS_ADDITIONAL_TAGS": "1.2\nx=y"}, 1),
            ("rejects an additional tag that is *", {"INPUTS_ADDITIONAL_TAGS": "*"}, 1),
        ]
        for name, overrides, want_rc in cases:
            with self.subTest(name):
                env = dict(ok, **overrides)
                rc, out, _ = run_step("apko-snapshot", "Validate tag inputs", env_vars=env)
                self.assertEqual(rc, want_rc, f"env={env}\nout={out}")

    def test_extract_outputs(self):
        d1, d2 = "sha256:" + "1" * 64, "sha256:" + "2" * 64
        cases = [
            ("index writes one digest and shortdigest per platform",
             DIGEST, [("amd64", None, d1), ("arm", "v7", d2)], 0,
             [("digest-index", DIGEST), ("shortdigest-index", DIGEST.split("@")[1]),
              ("digest-amd64", "ghcr.io/example/img@" + d1), ("shortdigest-amd64", d1),
              ("digest-armv7", "ghcr.io/example/img@" + d2), ("shortdigest-armv7", d2)]),
            ("rejects an architecture containing =",
             DIGEST, [("amd64=x", None, d1)], 1, None),
            ("rejects a platform digest that isn't sha256",
             DIGEST, [("amd64", None, "sha256:zz")], 1, None),
            ("rejects an apko digest with a newline",
             DIGEST + "\ndigest-index=evil.example/x@" + d1, [], 1, None),
        ]
        for name, apko_digest, entries, want_rc, want_outputs in cases:
            with self.subTest(name):
                tmpd = tempfile.mkdtemp(prefix="manifest-")
                try:
                    mf = os.path.join(tmpd, "m.json")
                    with open(mf, "w") as f:
                        f.write(index_manifest(entries))
                    env = {"STEPS_APKO_OUTPUTS_DIGEST": apko_digest, "INPUTS_BASE_TAG": "ghcr.io/example/img",
                           "CRANE_MANIFEST_FILE": mf}
                    rc, out, _, outputs = run_step("apko-snapshot", "extract", env_vars=env, want_output=True)
                finally:
                    shutil.rmtree(tmpd)
                self.assertEqual(rc, want_rc, f"digest={apko_digest!r} entries={entries}\nout={out}")
                if want_outputs is not None:
                    self.assertEqual(read_outputs(outputs), want_outputs, out)


class VulScansSteps(unittest.TestCase):
    def test_validate_image(self):
        cases = [
            ("accepts a digest reference", DIGEST, 0),
            ("accepts a tag reference", "cgr.dev/chainguard/static:latest", 0),
            ("rejects an empty image", "", 1),
            ("rejects an image starting with -", "--output=/tmp/x", 1),
            ("rejects an image containing a space", "img:latest " + INJECT, 1),
            ("rejects an image containing a newline", "img:latest\nFOO=bar", 1),
            ("rejects an image containing a tab", "img:latest\t-x", 1),
        ]
        for name, image, want_rc in cases:
            with self.subTest(name):
                rc, out, _ = run_step("vul-scans", "Validate image input", env_vars={"INPUTS_IMAGE": image})
                self.assertEqual(rc, want_rc, f"image={image!r}\nout={out}")

    def test_cosign_attest_and_verify(self):
        env = {"INPUTS_IMAGE": DIGEST, "INPUTS_FULCIO_URL": "https://fulcio.example",
               "INPUTS_REKOR_URL": "https://rekor.example", "STEPS_SCAN_START_OUTPUTS_DATE": "D",
               "STEPS_GRYPE_SCAN_OUTPUTS_SARIF": "grype results.sarif", "SNYK_URL": "u", "SNYK_VERSION": "v",
               "COSIGN_EXPERIMENTAL": "true", "GITHUB_WORKFLOW": "wf", "SCANNER_URI": "u", "SCANNER_VERSION": "v"}
        sarif = '{"runs":[{"tool":{"driver":{"informationUri":"u","version":"v"}},"results":[]}]}'
        files = {"snyk.json": "{}", "trivy-results.sarif": sarif, "grype results.sarif": sarif}
        for step in ("snyk-attest", "trivy-attest", "grype-attest", "cue-verify"):
            with self.subTest(f"{step}: image is the last argument, after --"):
                rc, out, calls = run_step("vul-scans", step, env_vars=env, files=files)
                self.assertEqual(rc, 0, out)
                cosign = [c for c in calls if c[0] == "cosign"]
                self.assertEqual(len(cosign), 1, f"calls={calls}")
                self.assertEqual(cosign[0][-2:], ["--", DIGEST], f"argv={cosign[0]}")


if __name__ == "__main__":
    # Optional: ACTIONS_REPO env var or first arg overrides the repo root.
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        REPO = os.path.abspath(sys.argv.pop(1))
    unittest.main(verbosity=2)
