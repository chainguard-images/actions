# Release Monitoring

This action fetches a project listed on 
[release-monitoring.org](https://release-monitoring.org)
and returns the most recent list of release versions.

## Usage

```yaml
- uses: distroless/actions/release-monitoring@main
  with:
    # Project ID for project listed on release-monitoring.org, required.
    project-id: 1234
    # API token for release-monitoring.org.
    # Optional, appears some access is allowed anonymously.
    api-token: '*****'
```

## Scenarios

```yaml
env:
  project-name: nginx
  project-id: 5413

steps:

# Fetch the latest version list
- uses: distroless/actions/release-monitoring@main
  id: release-monitoring
  with:
    project-id: ${{ env.project-id }}

# Print out all of the versions
- run: |
    echo "Latest versions of ${{ env.project-name }} listed on release-monitoring.org"
    echo
    echo "Latest version: ${{ steps.release-monitoring.outputs.latest-version }}"
    echo
    echo "Stable versions:"
    echo "- ${{ steps.release-monitoring.outputs.stable-versions }}" | sed 's/,/\n- /g'
    echo
    echo "All versions:"
    echo "- ${{ steps.release-monitoring.outputs.all-versions }}" | sed 's/,/\n- /g'
```
