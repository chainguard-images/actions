# Tag

This action takes a distroless image and adds additional tags that are relevant to the image.

It discovers these tags by comparing against the complementary image in DockerHub.

For example if `nginx:1.20.2` is the same imge as `nginx:stable`, then we want the same for the nginx distroless image.

## Usage

```yaml
- uses: distroless/actions/tag@main
  with:
    distroless_image: "ghcr.io/distroless/nginx"
    distroless_tag: "1.20.2"
    docker_image: "nginx"
```
