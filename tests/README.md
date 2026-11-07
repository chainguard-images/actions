# Action argument tests

Regression tests for how the composite actions compose the command lines they
pass to `apko`, `cosign`, `crane` and `snyk`. They guard against
argument-injection (CWE-88): an input value expanded unquoted can split into
extra arguments, and these tools parse flags that follow positional arguments.

- `test_container_args.py` renders the `docker run ... -c` script of `apko-build`
  and `apko-publish` under busybox `sh`, with a stub `apko` that logs its argv,
  and checks that each input is a single argument and that `config`/tags land
  after `--`.
- `test_bash_steps.py` runs the `cosign`/`crane`/`snyk` steps of `apko-snapshot`
  and `vul-scans` under bash, with stubs that log argv, and checks the image and
  URL inputs stay single arguments and the `$GITHUB_OUTPUT`/image validations
  reject malformed values.

Run them against the checkout:

    python3 -m unittest discover -s tests -p 'test_*.py'

Set `ACTIONS_REPO=/path/to/checkout` (or pass the path as the first argument to a
single file) to test a different tree. They need `busybox`, `bash` and `PyYAML`.
