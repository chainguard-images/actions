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
```

## Scenarios

```yaml
steps:
- uses: distroless/actions/apko-snapshot@main
  with:
    base-tag: ghcr.io/distroless/foo
```
