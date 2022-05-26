# APKO Build

This action builds a snapshot with [APKO](https://github.com/chainguard-dev/apko)
given a config file and base tag to use and output that to a tar file, this does not push to a registry.

## Usage

```yaml
- uses: distroless/actions/apko-build@main
  with:
    # Configuration is the configuration file to use, default is .apko.yaml.
    # Optional.
    config: foo.yaml
    # tag is the base tag to use, required.
    tag: ghcr.io/distroless/foo
    # use-docker-mediatypes is whether or not to use Docker mediatypes.
    # Optional.
    use-docker-mediatypes: false
```

## Scenarios

```yaml
steps:
- uses: distroless/actions/apko-snapshot@main
  with:
    tag: ghcr.io/distroless/foo
```
