# Scan an APK for Vulnerabilities

This action uses apko to build an ephemeral image and scan it with
[Anchore/Grype](https://github.com/anchore/grype) to identify any
vulnerabilities.


## Usage

```yaml
  - uses: chainguard-images/actions/scan-apk@main
    with:
      package: foo # or foo=1.2.3-r4
```
