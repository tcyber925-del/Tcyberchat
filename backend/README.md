````markdown
# Backend

This folder contains the backend FastAPI application and tests for the Local First Chatbot.

Key notes
- Migrations: Alembic is used and a baseline migration is included. To run migrations locally use the project's Python environment and `alembic` from the `backend` folder.
- PDF extraction: We prefer PyMuPDF (`pymupdf`) for robust and fast PDF text extraction; the code falls back to `pypdf`/`PyPDF2` if PyMuPDF is not available.
- Tests: There are unit tests (`tests/unit`) and contract/integration tests (`tests/contract`, `tests/integration`).

Run tests locally

1. Activate the project's virtualenv (see project root README for `uv` steps) or:

```pwsh
cd backend
.venv\Scripts\activate
pip install -r requirements.txt
pytest tests/unit
pytest tests/contract
pytest tests/integration
```

CI
- A GitHub Actions workflow has been added at `.github/workflows/ci.yml` to run the backend tests on push / PR.

Test shims
- For CI/test stability the repository contains lightweight in-repo shims used when optional test dependencies
	are not installed: `fakeredis.py` (a minimal FakeRedis shim) and `prometheus_client.py` (a tiny metrics
	rendering shim). These are only intended for tests and local development; prefer installing the real
	`fakeredis` and `prometheus_client` packages in CI and production environments.

Recommended CI change:
- Install `fakeredis` and `prometheus_client` in the CI job when available so the shims are replaced by
	the real packages. The shims will continue to act as fallbacks for quick local runs where installing
	optional deps is not desirable.

<<<<<<< HEAD
**Open PR & Labels**

- A pre-filled Pull Request page for the `feat/move-shims` branch is available; open it in your browser and click "Create pull request" to submit the branch for review. Example:

  `https://github.com/Codcyber101/TcyberLocalChat/pull/new/feat/move-shims`

- If you prefer to create the PR from the command line, either use the `gh` CLI or the included PowerShell helper script `scripts/create_pr.ps1` (created alongside this README update). The helper script reads `PR_BODY.md` from the repo root and requires `GITHUB_TOKEN` in the environment (repo scope).

- Recommended labels to add: `tests`, `ci`, `bugfix`.

Using the PowerShell helper (local):

1. Export a GitHub Personal Access Token with `repo` scope as `GITHUB_TOKEN` in your session.

```powershell
$env:GITHUB_TOKEN = Read-Host -Prompt 'Paste your GitHub PAT (repo scope)'
```

2. Run the helper script:

```powershell
.\scripts\create_pr.ps1
```

Or use `gh` locally:

```powershell
gh pr create --base main --head feat/move-shims --title "Move test shims into backend/tests/_shims" --body-file PR_BODY.md
gh pr edit <pr-number> --add-label tests --add-label ci --add-label bugfix
gh pr comment <pr-number> --body "Local test results: 198 passed, 9 skipped. Ready for CI verification."
```

=======
````
>>>>>>> 98ae03f7b46feafbba0808aa71e6aa203051f0e5
