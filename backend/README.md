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
