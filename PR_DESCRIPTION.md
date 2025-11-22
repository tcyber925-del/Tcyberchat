Title: Fix fakeredis shim and document test shims

Description:
- Fixes an issue where the in-repo `fakeredis.py` shim could self-import and return `None` when tests imported `fakeredis`.
- Adds a short note to `backend/README.md` documenting the test shims (`fakeredis.py` and `prometheus_client.py`) and recommending that CI install the real packages when available.

Files changed:
- `fakeredis.py` — avoid self-import and prefer the real `fakeredis` package when present; otherwise fall back to a minimal in-repo `FakeRedisShim`.
- `backend/README.md` — add "Test shims" section describing the test-only shims and CI recommendation.

Testing:
- Ran the full backend test suite locally with `PYTHONPATH` set: `198 passed, 9 skipped`.
- Focused admin/index-retry tests also passed (11/11).

Notes for the PR:
- The shims remain in the repo intentionally to make tests runnable without installing optional packages in lightweight dev setups.
- Recommended CI update: install `fakeredis` and `prometheus_client` in CI to prefer the real packages. Optionally move shims into `tests/_shims/` to make them explicitly test-only.

Commands to open PR locally using `gh` (if you prefer):

```pwsh
# create a branch locally that matches the remote branch (if needed)
git fetch origin feat/mcp-integration
git checkout -b feat/fix-fakeredis-shim origin/feat/mcp-integration

# create PR using GitHub CLI
gh pr create --title "Fix fakeredis shim and document test shims" --body-file PR_DESCRIPTION.md --base main --head feat/fix-fakeredis-shim
```

Or create PR via curl (requires `GITHUB_TOKEN` set):

```pwsh
$body = Get-Content PR_DESCRIPTION.md -Raw
$payload = @{ title = 'Fix fakeredis shim and document test shims'; head = 'feat/mcp-integration'; base = 'main'; body = $body } | ConvertTo-Json -Depth 5
curl -s -X POST -H "Authorization: token $env:GITHUB_TOKEN" -H "Accept: application/vnd.github+json" https://api.github.com/repos/Codcyber101/TcyberLocalChat/pulls -d $payload | ConvertFrom-Json
```

If you'd like, I can try creating the PR via the API now (requires a token). Let me know and I will proceed.
