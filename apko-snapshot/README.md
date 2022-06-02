# APKO Snapshot

This action builds a snapshot with [APKO](https://github.com/chainguard-dev/apko)
given a config file and base tag to use.

The resulting image is signed with `cosign` keyless signing.

## Usage

```yaml
- uses: distroless/actions/apko-snapshot@main
  with:
    # Configuration is the configuration file to use, default is .apko.yaml.
    # Optional.
    config: foo.yaml
    # Base-tag is the base tag to use, required.
    base-tag: ghcr.io/distroless/foo
    # use-docker-mediatypes is whether or not to use Docker mediatypes.
    # Optional.
    use-docker-mediatypes: false
```

## Scenarios

```yaml
steps:
- uses: distroless/actions/apko-snapshot@main
  id: apko-snapshot
  with:
    base-tag: ghcr.io/distroless/foo

# Pass the digest output to a trivy scan.
- name: Run Trivy vulnerability scanner
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: ${{ steps.apko-snapshot.outputs.digest }}
    format: 'table'
    exit-code: '1'
    vuln-type: 'os,library'
    severity: 'CRITICAL,HIGH'
```
