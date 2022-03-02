# APKO Snapshot

This action builds a snapshot with APKO given a config file and base tag to use.

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
