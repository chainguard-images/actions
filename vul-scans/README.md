# Vulnerability Scanning

This action will scan the provided image with [Snyk](https://docs.snyk.io/snyk-cli), 
[Anchore/Grype](https://github.com/anchore/grype) and [Aquasecurity/Trivy](https://github.com/aquasecurity/trivy) 
vulnerability scanners

It will attach the results as a cosign attestation with the results and report the Count of Vulnerabilities found. 


## Usage

```yaml
  - uses: distroless/actions/vul-scans@main
    id: scans
    with:
      # OCI registry where the image is located
      registry: ghcr.io
      # Username for access to the above registry
      username: ${{ github.actor }}
      # Password for access to the above registry
      password: ${{ secrets.GITHUB_TOKEN }}
      # OCI image ref; example  ghcr.io/chainguard-dev/go-demo@sha256:663af4dfa41bb72fc308faf67580aa3af41c5a6ea244250e02fd5f42b8cfbeaa
      image: ${{ env.IMAGE }}
      # API Token for the Snyk CLI
      SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
      #Should the GitHub action upload the results to GitHub Advance Security portal
      UPLOAD_GITHUB_CODE: true
```

## Scenarios

```yaml
  - uses: distroless/actions/vul-scans@main
    id: scans
    with:
      registry: ghcr.io
      username: ${{ github.actor }}
      password: ${{ secrets.GITHUB_TOKEN }}
      image: ${{ env.IMAGE }}
      SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
      UPLOAD_GITHUB_CODE: true
```

Example Usage at https://github.com/chainguard-dev/go-demo

### Verify Attestations

Cosign Verify
```bash
COSIGN_EXPERIMENTAL=true cosign verify-attestation ghcr.io/chainguard-dev/go-demo@sha256:663af4dfa41bb72fc308faf67580aa3af41c5a6ea244250e02fd5f42b8cfbeaa -o json 2>/dev/null
```

Cosign has attached all three attestations in `ghcr.io/chainguard-dev/go-demo:sha256-663af4dfa41bb72fc308faf67580aa3af41c5a6ea244250e02fd5f42b8cfbeaa.att`

```json
{"payloadType":"application/vnd.in-toto+json","payload":"eyJfdHlwZSI6Imh0dHBzOi8vaW4tdG90by5pby9TdGF0ZW1lbnQvdjAuMSIsInByZWRpY2F0ZVR5cGUiOiJjb3NpZ24uc2lnc3RvcmUuZGV2L2F0dGVzdGF0aW9uL3Z1bG4vdjEiLCJzdWJqZWN0IjpbeyJuYW1lIjoiZ2hjci5pby9jaGFpbmd1YXJkLWRldi9nby1kZW1vIiwiZGlnZXN0Ijp7InNoYTI1NiI6IjY2M2FmNGRmYTQxYmI3MmZjMzA4ZmFmNjc1ODBhYTNhZjQxYzVhNmVhMjQ0MjUwZTAyZmQ1ZjQyYjhjZmJlYWEifX1dLCJwcmVkaWNhdGUiOnsiaW52b2NhdGlvbiI6eyJwYXJhbWV0ZXJzIjpudWxsLCJ1cmkiOiJodHRwczovL2dpdGh1Yi5jb20vY2hhaW5ndWFyZC1kZXYvZ28tZGVtby9hY3Rpb25zL3J1bnMvMjY3MDU2Njk1NiIsImV2ZW50X2lkIjoiMjY3MDU2Njk1NiIsImJ1aWxkZXIuaWQiOiJSZWxlYXNlIExhdGVzdCBDaGFuZ2VzIn0sInNjYW5uZXIiOnsidXJpIjoiaHR0cHM6Ly9zdGF0aWMuc255ay5pby9jbGkvdjEuOTY2LjAvc255ay1saW51eCIsInZlcnNpb24iOiJ2MS45NjYuMCIsImRiIjp7InVyaSI6IiIsInZlcnNpb24iOiIifSwicmVzdWx0Ijp7ImRlcGVuZGVuY3lDb3VudCI6MywiZG9ja2VyIjp7fSwiZmlsZXN5c3RlbVBvbGljeSI6ZmFsc2UsImlnbm9yZVNldHRpbmdzIjp7ImFkbWluT25seSI6ZmFsc2UsImRpc3JlZ2FyZEZpbGVzeXN0ZW1JZ25vcmVzIjpmYWxzZSwicmVhc29uUmVxdWlyZWQiOmZhbHNlfSwiaXNQcml2YXRlIjp0cnVlLCJsaWNlbnNlc1BvbGljeSI6eyJvcmdMaWNlbnNlUnVsZXMiOnsiQUdQTC0xLjAiOnsiaW5zdHJ1Y3Rpb25zIjoiIiwibGljZW5zZVR5cGUiOiJBR1BMLTEuMCIsInNldmVyaXR5IjoiaGlnaCJ9LCJBR1BMLTMuMCI6eyJpbnN0cnVjdGlvbnMiOiIiLCJsaWNlbnNlVHlwZSI6IkFHUEwtMy4wIiwic2V2ZXJpdHkiOiJoaWdoIn0sIkFydGlzdGljLTEuMCI6eyJpbnN0cnVjdGlvbnMiOiIiLCJsaWNlbnNlVHlwZSI6IkFydGlzdGljLTEuMCIsInNldmVyaXR5IjoibWVkaXVtIn0sIkFydGlzdGljLTIuMCI6eyJpbnN0cnVjdGlvbnMiOiIiLCJsaWNlbnNlVHlwZSI6IkFydGlzdGljLTIuMCIsInNldmVyaXR5IjoibWVkaXVtIn0sIkNEREwtMS4wIjp7Imluc3RydWN0aW9ucyI6IiIsImxpY2Vuc2VUeXBlIjoiQ0RETC0xLjAiLCJzZXZlcml0eSI6Im1lZGl1bSJ9LCJDUE9MLTEuMDIiOnsiaW5zdHJ1Y3Rpb25zIjoiIiwibGljZW5zZVR5cGUiOiJDUE9MLTEuMDIiLCJzZXZlcml0eSI6ImhpZ2gifSwiRVBMLTEuMCI6eyJpbnN0cnVjdGlvbnMiOiIiLCJsaWNlbnNlVHlwZSI6IkVQTC0xLjAiLCJzZXZlcml0eSI6Im1lZGl1bSJ9LCJHUEwtMi4wIjp7Imluc3RydWN0aW9ucyI6IiIsImxpY2Vuc2VUeXBlIjoiR1BMLTIuMCIsInNldmVyaXR5IjoiaGlnaCJ9LCJHUEwtMy4wIjp7Imluc3RydWN0aW9ucyI6IiIsImxpY2Vuc2VUeXBlIjoiR1BMLTMuMCIsInNldmVyaXR5IjoiaGlnaCJ9LCJMR1BMLTIuMCI6eyJpbnN0cnVjdGlvbnMiOiIiLCJsaWNlbnNlVHlwZSI6IkxHUEwtMi4wIiwic2V2ZXJpdHkiOiJtZWRpdW0ifSwiTEdQTC0yLjEiOnsiaW5zdHJ1Y3Rpb25zIjoiIiwibGljZW5zZVR5cGUiOiJMR1BMLTIuMSIsInNldmVyaXR5IjoibWVkaXVtIn0sIkxHUEwtMy4wIjp7Imluc3RydWN0aW9ucyI6IiIsImxpY2Vuc2VUeXBlIjoiTEdQTC0zLjAiLCJzZXZlcml0eSI6Im1lZGl1bSJ9LCJNUEwtMS4xIjp7Imluc3RydWN0aW9ucyI6IiIsImxpY2Vuc2VUeXBlIjoiTVBMLTEuMSIsInNldmVyaXR5IjoibWVkaXVtIn0sIk1QTC0yLjAiOnsiaW5zdHJ1Y3Rpb25zIjoiIiwibGljZW5zZVR5cGUiOiJNUEwtMi4wIiwic2V2ZXJpdHkiOiJtZWRpdW0ifSwiTVMtUkwiOnsiaW5zdHJ1Y3Rpb25zIjoiIiwibGljZW5zZVR5cGUiOiJNUy1STCIsInNldmVyaXR5IjoibWVkaXVtIn0sIlNpbVBMLTIuMCI6eyJpbnN0cnVjdGlvbnMiOiIiLCJsaWNlbnNlVHlwZSI6IlNpbVBMLTIuMCIsInNldmVyaXR5IjoiaGlnaCJ9fSwic2V2ZXJpdGllcyI6e319LCJvayI6dHJ1ZSwib3JnIjoic3Ryb25nanotNm8wIiwicGFja2FnZU1hbmFnZXIiOiJkZWIiLCJwYXRoIjoiZ2hjci5pby9jaGFpbmd1YXJkLWRldi9nby1kZW1vQHNoYTI1Njo2NjNhZjRkZmE0MWJiNzJmYzMwOGZhZjY3NTgwYWEzYWY0MWM1YTZlYTI0NDI1MGUwMmZkNWY0MmI4Y2ZiZWFhL2NoYWluZ3VhcmQtZGV2L2dvLWRlbW8iLCJwbGF0Zm9ybSI6ImxpbnV4L2FtZDY0IiwicG9saWN5IjoiIyBTbnlrIChodHRwczovL3NueWsuaW8pIHBvbGljeSBmaWxlLCBwYXRjaGVzIG9yIGlnbm9yZXMga25vd24gdnVsbmVyYWJpbGl0aWVzLlxudmVyc2lvbjogdjEuMjUuMFxuaWdub3JlOiB7fVxucGF0Y2g6IHt9XG4iLCJwcm9qZWN0TmFtZSI6ImRvY2tlci1pbWFnZXxnaGNyLmlvL2NoYWluZ3VhcmQtZGV2L2dvLWRlbW8iLCJzdW1tYXJ5IjoiTm8ga25vd24gdnVsbmVyYWJpbGl0aWVzIiwidW5pcXVlQ291bnQiOjAsInZ1bG5lcmFiaWxpdGllcyI6W119fSwibWV0YWRhdGEiOnsic2NhblN0YXJ0ZWRPbiI6IjIwMjItMDctMTRUMTM6MTY6NTRaIiwic2NhbkZpbmlzaGVkT24iOiIyMDIyLTA3LTE0VDEzOjE3OjAyWiJ9fX0=","signatures":[{"keyid":"","sig":"MEUCIBOeMT2JN6mWQhRsvAGYRwdBISDh4YI7VQBnDemwCu2pAiEA7C9LWiZ1BjXdIMy+pWt1jn/Sthp9Yi/QGLQAjtSQT6g="}]}
{"payloadType":"application/vnd.in-toto+json","payload":"eyJfdHlwZSI6Imh0dHBzOi8vaW4tdG90by5pby9TdGF0ZW1lbnQvdjAuMSIsInByZWRpY2F0ZVR5cGUiOiJjb3NpZ24uc2lnc3RvcmUuZGV2L2F0dGVzdGF0aW9uL3Z1bG4vdjEiLCJzdWJqZWN0IjpbeyJuYW1lIjoiZ2hjci5pby9jaGFpbmd1YXJkLWRldi9nby1kZW1vIiwiZGlnZXN0Ijp7InNoYTI1NiI6IjY2M2FmNGRmYTQxYmI3MmZjMzA4ZmFmNjc1ODBhYTNhZjQxYzVhNmVhMjQ0MjUwZTAyZmQ1ZjQyYjhjZmJlYWEifX1dLCJwcmVkaWNhdGUiOnsiaW52b2NhdGlvbiI6eyJwYXJhbWV0ZXJzIjpudWxsLCJ1cmkiOiJodHRwczovL2dpdGh1Yi5jb20vY2hhaW5ndWFyZC1kZXYvZ28tZGVtby9hY3Rpb25zL3J1bnMvMjY3MDU2Njk1NiIsImV2ZW50X2lkIjoiMjY3MDU2Njk1NiIsImJ1aWxkZXIuaWQiOiJSZWxlYXNlIExhdGVzdCBDaGFuZ2VzIn0sInNjYW5uZXIiOnsidXJpIjoiaHR0cHM6Ly9naXRodWIuY29tL2FxdWFzZWN1cml0eS90cml2eSIsInZlcnNpb24iOiIwLjI5LjIiLCJkYiI6eyJ1cmkiOiIiLCJ2ZXJzaW9uIjoiIn0sInJlc3VsdCI6eyIkc2NoZW1hIjoiaHR0cHM6Ly9qc29uLnNjaGVtYXN0b3JlLm9yZy9zYXJpZi0yLjEuMC1ydG0uNS5qc29uIiwicnVucyI6W3siY29sdW1uS2luZCI6InV0ZjE2Q29kZVVuaXRzIiwib3JpZ2luYWxVcmlCYXNlSWRzIjp7IlJPT1RQQVRIIjp7InVyaSI6ImZpbGU6Ly8vIn19LCJyZXN1bHRzIjpbXSwidG9vbCI6eyJkcml2ZXIiOnsiZnVsbE5hbWUiOiJUcml2eSBWdWxuZXJhYmlsaXR5IFNjYW5uZXIiLCJpbmZvcm1hdGlvblVyaSI6Imh0dHBzOi8vZ2l0aHViLmNvbS9hcXVhc2VjdXJpdHkvdHJpdnkiLCJuYW1lIjoiVHJpdnkiLCJydWxlcyI6W10sInZlcnNpb24iOiIwLjI5LjIifX19XSwidmVyc2lvbiI6IjIuMS4wIn19LCJtZXRhZGF0YSI6eyJzY2FuU3RhcnRlZE9uIjoiMjAyMi0wNy0xNFQxMzoxNjo1NFoiLCJzY2FuRmluaXNoZWRPbiI6IjIwMjItMDctMTRUMTM6MTc6MTBaIn19fQ==","signatures":[{"keyid":"","sig":"MEUCIE8iLyAVQzajFI0GgJFl36Jc0X509X6vKLS/47dyg02aAiEAmxmxKp5eEe7k4U44YbDWiAezDlCcrIAhEk2jWCUTYJc="}]}
{"payloadType":"application/vnd.in-toto+json","payload":"eyJfdHlwZSI6Imh0dHBzOi8vaW4tdG90by5pby9TdGF0ZW1lbnQvdjAuMSIsInByZWRpY2F0ZVR5cGUiOiJjb3NpZ24uc2lnc3RvcmUuZGV2L2F0dGVzdGF0aW9uL3Z1bG4vdjEiLCJzdWJqZWN0IjpbeyJuYW1lIjoiZ2hjci5pby9jaGFpbmd1YXJkLWRldi9nby1kZW1vIiwiZGlnZXN0Ijp7InNoYTI1NiI6IjY2M2FmNGRmYTQxYmI3MmZjMzA4ZmFmNjc1ODBhYTNhZjQxYzVhNmVhMjQ0MjUwZTAyZmQ1ZjQyYjhjZmJlYWEifX1dLCJwcmVkaWNhdGUiOnsiaW52b2NhdGlvbiI6eyJwYXJhbWV0ZXJzIjpudWxsLCJ1cmkiOiJodHRwczovL2dpdGh1Yi5jb20vY2hhaW5ndWFyZC1kZXYvZ28tZGVtby9hY3Rpb25zL3J1bnMvMjY3MDU2Njk1NiIsImV2ZW50X2lkIjoiMjY3MDU2Njk1NiIsImJ1aWxkZXIuaWQiOiJSZWxlYXNlIExhdGVzdCBDaGFuZ2VzIn0sInNjYW5uZXIiOnsidXJpIjoiaHR0cHM6Ly9naXRodWIuY29tL2FuY2hvcmUvZ3J5cGUiLCJ2ZXJzaW9uIjoiMC4zOC4wIiwiZGIiOnsidXJpIjoiIiwidmVyc2lvbiI6IiJ9LCJyZXN1bHQiOnsiJHNjaGVtYSI6Imh0dHBzOi8vanNvbi5zY2hlbWFzdG9yZS5vcmcvc2FyaWYtMi4xLjAtcnRtLjUuanNvbiIsInJ1bnMiOlt7InJlc3VsdHMiOltdLCJ0b29sIjp7ImRyaXZlciI6eyJpbmZvcm1hdGlvblVyaSI6Imh0dHBzOi8vZ2l0aHViLmNvbS9hbmNob3JlL2dyeXBlIiwibmFtZSI6IkdyeXBlIiwidmVyc2lvbiI6IjAuMzguMCJ9fX1dLCJ2ZXJzaW9uIjoiMi4xLjAifX0sIm1ldGFkYXRhIjp7InNjYW5TdGFydGVkT24iOiIyMDIyLTA3LTE0VDEzOjE2OjU0WiIsInNjYW5GaW5pc2hlZE9uIjoiMjAyMi0wNy0xNFQxMzoxNzoyNVoifX19","signatures":[{"keyid":"","sig":"MEUCIQDy1UVSgCGrHPZ5mAnixGQGUI/5RjuakdXk2PbR+taePwIgJgI4VqzSvi787LN5KE9VwBAJ8J/nm7/49bY6Tt0W0tE="}]}
```

Inspect each Attestation

```bash
echo '{"payloadType":"application/vnd.in-toto+json","payload":"eyJfdHlwZSI6Imh0dHBzOi8vaW4tdG90by5pby9TdGF0ZW1lbnQvdjAuMSIsInByZWRpY2F0ZVR5cGUiOiJjb3NpZ24uc2lnc3RvcmUuZGV2L2F0dGVzdGF0aW9uL3Z1bG4vdjEiLCJzdWJqZWN0IjpbeyJuYW1lIjoiZ2hjci5pby9jaGFpbmd1YXJkLWRldi9nby1kZW1vIiwiZGlnZXN0Ijp7InNoYTI1NiI6IjY2M2FmNGRmYTQxYmI3MmZjMzA4ZmFmNjc1ODBhYTNhZjQxYzVhNmVhMjQ0MjUwZTAyZmQ1ZjQyYjhjZmJlYWEifX1dLCJwcmVkaWNhdGUiOnsiaW52b2NhdGlvbiI6eyJwYXJhbWV0ZXJzIjpudWxsLCJ1cmkiOiJodHRwczovL2dpdGh1Yi5jb20vY2hhaW5ndWFyZC1kZXYvZ28tZGVtby9hY3Rpb25zL3J1bnMvMjY3MDU2Njk1NiIsImV2ZW50X2lkIjoiMjY3MDU2Njk1NiIsImJ1aWxkZXIuaWQiOiJSZWxlYXNlIExhdGVzdCBDaGFuZ2VzIn0sInNjYW5uZXIiOnsidXJpIjoiaHR0cHM6Ly9naXRodWIuY29tL2FxdWFzZWN1cml0eS90cml2eSIsInZlcnNpb24iOiIwLjI5LjIiLCJkYiI6eyJ1cmkiOiIiLCJ2ZXJzaW9uIjoiIn0sInJlc3VsdCI6eyIkc2NoZW1hIjoiaHR0cHM6Ly9qc29uLnNjaGVtYXN0b3JlLm9yZy9zYXJpZi0yLjEuMC1ydG0uNS5qc29uIiwicnVucyI6W3siY29sdW1uS2luZCI6InV0ZjE2Q29kZVVuaXRzIiwib3JpZ2luYWxVcmlCYXNlSWRzIjp7IlJPT1RQQVRIIjp7InVyaSI6ImZpbGU6Ly8vIn19LCJyZXN1bHRzIjpbXSwidG9vbCI6eyJkcml2ZXIiOnsiZnVsbE5hbWUiOiJUcml2eSBWdWxuZXJhYmlsaXR5IFNjYW5uZXIiLCJpbmZvcm1hdGlvblVyaSI6Imh0dHBzOi8vZ2l0aHViLmNvbS9hcXVhc2VjdXJpdHkvdHJpdnkiLCJuYW1lIjoiVHJpdnkiLCJydWxlcyI6W10sInZlcnNpb24iOiIwLjI5LjIifX19XSwidmVyc2lvbiI6IjIuMS4wIn19LCJtZXRhZGF0YSI6eyJzY2FuU3RhcnRlZE9uIjoiMjAyMi0wNy0xNFQxMzoxNjo1NFoiLCJzY2FuRmluaXNoZWRPbiI6IjIwMjItMDctMTRUMTM6MTc6MTBaIn19fQ==","signatures":[{"keyid":"","sig":"MEUCIE8iLyAVQzajFI0GgJFl36Jc0X509X6vKLS/47dyg02aAiEAmxmxKp5eEe7k4U44YbDWiAezDlCcrIAhEk2jWCUTYJc="}]}' | jq -r .payload | base64 -d  | jq -r .
```

Attestation Output 

<details>

```json
{
  "_type": "https://in-toto.io/Statement/v0.1",
  "predicateType": "cosign.sigstore.dev/attestation/vuln/v1",
  "subject": [
    {
      "name": "ghcr.io/chainguard-dev/go-demo",
      "digest": {
        "sha256": "663af4dfa41bb72fc308faf67580aa3af41c5a6ea244250e02fd5f42b8cfbeaa"
      }
    }
  ],
  "predicate": {
    "invocation": {
      "parameters": null,
      "uri": "https://github.com/chainguard-dev/go-demo/actions/runs/2670566956",
      "event_id": "2670566956",
      "builder.id": "Release Latest Changes"
    },
    "scanner": {
      "uri": "https://github.com/aquasecurity/trivy",
      "version": "0.29.2",
      "db": {
        "uri": "",
        "version": ""
      },
      "result": {
        "$schema": "https://json.schemastore.org/sarif-2.1.0-rtm.5.json",
        "runs": [
          {
            "columnKind": "utf16CodeUnits",
            "originalUriBaseIds": {
              "ROOTPATH": {
                "uri": "file:///"
              }
            },
            "results": [],
            "tool": {
              "driver": {
                "fullName": "Trivy Vulnerability Scanner",
                "informationUri": "https://github.com/aquasecurity/trivy",
                "name": "Trivy",
                "rules": [],
                "version": "0.29.2"
              }
            }
          }
        ],
        "version": "2.1.0"
      }
    },
    "metadata": {
      "scanStartedOn": "2022-07-14T13:16:54Z",
      "scanFinishedOn": "2022-07-14T13:17:10Z"
    }
  }
}
```

</details>

To get the Rekor Log index, we can get that from the GitHub Action Log which is stored in `.predicate.invocation.uri`. 

```bash
echo '{"payloadType":"application/vnd.in-toto+json","payload":"eyJfdHlwZSI6Imh0dHBzOi8vaW4tdG90by5pby9TdGF0ZW1lbnQvdjAuMSIsInByZWRpY2F0ZVR5cGUiOiJjb3NpZ24uc2lnc3RvcmUuZGV2L2F0dGVzdGF0aW9uL3Z1bG4vdjEiLCJzdWJqZWN0IjpbeyJuYW1lIjoiZ2hjci5pby9jaGFpbmd1YXJkLWRldi9nby1kZW1vIiwiZGlnZXN0Ijp7InNoYTI1NiI6IjY2M2FmNGRmYTQxYmI3MmZjMzA4ZmFmNjc1ODBhYTNhZjQxYzVhNmVhMjQ0MjUwZTAyZmQ1ZjQyYjhjZmJlYWEifX1dLCJwcmVkaWNhdGUiOnsiaW52b2NhdGlvbiI6eyJwYXJhbWV0ZXJzIjpudWxsLCJ1cmkiOiJodHRwczovL2dpdGh1Yi5jb20vY2hhaW5ndWFyZC1kZXYvZ28tZGVtby9hY3Rpb25zL3J1bnMvMjY3MDU2Njk1NiIsImV2ZW50X2lkIjoiMjY3MDU2Njk1NiIsImJ1aWxkZXIuaWQiOiJSZWxlYXNlIExhdGVzdCBDaGFuZ2VzIn0sInNjYW5uZXIiOnsidXJpIjoiaHR0cHM6Ly9naXRodWIuY29tL2FxdWFzZWN1cml0eS90cml2eSIsInZlcnNpb24iOiIwLjI5LjIiLCJkYiI6eyJ1cmkiOiIiLCJ2ZXJzaW9uIjoiIn0sInJlc3VsdCI6eyIkc2NoZW1hIjoiaHR0cHM6Ly9qc29uLnNjaGVtYXN0b3JlLm9yZy9zYXJpZi0yLjEuMC1ydG0uNS5qc29uIiwicnVucyI6W3siY29sdW1uS2luZCI6InV0ZjE2Q29kZVVuaXRzIiwib3JpZ2luYWxVcmlCYXNlSWRzIjp7IlJPT1RQQVRIIjp7InVyaSI6ImZpbGU6Ly8vIn19LCJyZXN1bHRzIjpbXSwidG9vbCI6eyJkcml2ZXIiOnsiZnVsbE5hbWUiOiJUcml2eSBWdWxuZXJhYmlsaXR5IFNjYW5uZXIiLCJpbmZvcm1hdGlvblVyaSI6Imh0dHBzOi8vZ2l0aHViLmNvbS9hcXVhc2VjdXJpdHkvdHJpdnkiLCJuYW1lIjoiVHJpdnkiLCJydWxlcyI6W10sInZlcnNpb24iOiIwLjI5LjIifX19XSwidmVyc2lvbiI6IjIuMS4wIn19LCJtZXRhZGF0YSI6eyJzY2FuU3RhcnRlZE9uIjoiMjAyMi0wNy0xNFQxMzoxNjo1NFoiLCJzY2FuRmluaXNoZWRPbiI6IjIwMjItMDctMTRUMTM6MTc6MTBaIn19fQ==","signatures":[{"keyid":"","sig":"MEUCIE8iLyAVQzajFI0GgJFl36Jc0X509X6vKLS/47dyg02aAiEAmxmxKp5eEe7k4U44YbDWiAezDlCcrIAhEk2jWCUTYJc="}]}' | jq -r .payload | base64 -d  | jq -r .predicate.invocation.uri
```

GitHub Log Output 

```bash
https://github.com/chainguard-dev/go-demo/actions/runs/2670566956
```

The GitHub Log entry is at https://github.com/chainguard-dev/go-demo/runs/7340623086?check_suite_focus=true#step:11:507

```bash
tlog entry created with index: 2943993
```

Using the Rekor CLI, we can see the attestation is in rekor as well. 

```bash
rekor-cli get --log-index 2943993 --format json | jq -r .Attestation | jq -r .
```

<details>

```json
{
  "_type": "https://in-toto.io/Statement/v0.1",
  "predicateType": "cosign.sigstore.dev/attestation/vuln/v1",
  "subject": [
    {
      "name": "ghcr.io/chainguard-dev/go-demo",
      "digest": {
        "sha256": "663af4dfa41bb72fc308faf67580aa3af41c5a6ea244250e02fd5f42b8cfbeaa"
      }
    }
  ],
  "predicate": {
    "invocation": {
      "parameters": null,
      "uri": "https://github.com/chainguard-dev/go-demo/actions/runs/2670566956",
      "event_id": "2670566956",
      "builder.id": "Release Latest Changes"
    },
    "scanner": {
      "uri": "https://github.com/aquasecurity/trivy",
      "version": "0.29.2",
      "db": {
        "uri": "",
        "version": ""
      },
      "result": {
        "$schema": "https://json.schemastore.org/sarif-2.1.0-rtm.5.json",
        "runs": [
          {
            "columnKind": "utf16CodeUnits",
            "originalUriBaseIds": {
              "ROOTPATH": {
                "uri": "file:///"
              }
            },
            "results": [],
            "tool": {
              "driver": {
                "fullName": "Trivy Vulnerability Scanner",
                "informationUri": "https://github.com/aquasecurity/trivy",
                "name": "Trivy",
                "rules": [],
                "version": "0.29.2"
              }
            }
          }
        ],
        "version": "2.1.0"
      }
    },
    "metadata": {
      "scanStartedOn": "2022-07-14T13:16:54Z",
      "scanFinishedOn": "2022-07-14T13:17:10Z"
    }
  }
}
```

</details>
