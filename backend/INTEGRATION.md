# Integration tests and optional heavy dependencies

This document explains how to run the repository's integration tests locally and in CI, and lists the optional heavy dependencies used for full LangChain + Chroma integration.

Important notes
- Integration tests may require large downloads (models, embeddings) and extra CPU/RAM (especially `transformers`/`torch`). Run them only when necessary.
- Unit tests are fast and are run by default in CI. Integration tests are gated and opt-in.

Optional dependencies (common)
- langchain / langchain-core
- chromadb
- sentence-transformers
- transformers
- torch
- sse-starlette (for SSE endpoints during integration)
- pypdf / PyPDF2, python-docx, pytesseract, pillow, numpy, opencv-python (for richer document processing)

Install (recommended inside project venv)

PowerShell (Windows):

```powershell
cd backend
# activate venv per project setup (uv or .venv/scripts/activate)
python -m pip install --upgrade pip
pip install -r requirements.txt
# optional heavy deps (only when running integration)
pip install chromadb langchain sentence-transformers transformers torch sse-starlette
```

Linux / macOS (bash):

```bash
cd backend
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install chromadb langchain sentence-transformers transformers torch sse-starlette
```

Running the backend for integration tests

The tests expect the backend to be running on `127.0.0.1:8000` by default. Use the project's `uv` helper (if available) or run uvicorn directly.

PowerShell example (start in background):

```powershell
cd backend
# using uv wrapper (recommended if set up):
uv run uvicorn main:app --host 127.0.0.1 --port 8000
# or run in background (PowerShell):
Start-Process -NoNewWindow -FilePath uv -ArgumentList 'run uvicorn main:app --host 127.0.0.1 --port 8000'
Start-Sleep -Seconds 5
```

Run integration tests

- Locally (PowerShell):

```powershell
cd backend
# mark tests as integration-run when appropriate
$env:RUN_INTEGRATION_TESTS = "1"
uv run pytest tests/test_sse_client.py tests/unit/test_chat_rag_db_fallback.py -q
```

- In CI (GitHub Actions): the included workflow `.github/workflows/ci.yml` supports an input `run_integration=1` to run integration tests. You can trigger the workflow manually or set the env var `RUN_INTEGRATION_TESTS=1` in the runner environment.

CI recommendations
- Gate integration tests to avoid long-running or flaky CI by default (we already do this in the workflow).
- Add caching for pip wheels to speed up repeated runs (actions/cache). If you'd like, we can add caching to the CI workflow.
- If you rely on a persistent Chroma instance or other services, consider using a service container or dedicated test environment rather than installing chromadb in the runner.

Troubleshooting
- If you see `ModuleNotFoundError` for optional libraries, either install them or run the tests with integration gated off. Many imports in the backend are now lazy/optional so unit tests should not need heavy dependencies.
- If Chroma complains about missing embedding functions, ensure the test forces the fallback vectorstore or that real embeddings are provided (embedding models must be installed/available).

If you want, I can:
- Add pip cache steps to the CI workflow.
- Add an example `scripts/run_integration.ps1` to automate starting the server and running integration tests on Windows.
- Help run the integration tests here (I can prepare exact commands or run them if you want me to proceed).
