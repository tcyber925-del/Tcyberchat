# LangChain Stack Upgrade Plan

This document describes a conservative, CI-first plan to upgrade the LangChain-related stack used by the backend.

Goal
------
- Upgrade LangChain-related packages (langchain, langchain-huggingface, langchain-core, sentence-transformers, chromadb, transformers, torch) while keeping the app stable and preserving current RAG behavior.

Principles
----------
- Make minimal code changes: centralize all LangChain/embeddings/vectorstore usage behind `backend/src/services/rag_adapter.py`.
- Perform heavy dependency installs in CI only. Avoid changing developer venvs unless the developer opts in.
- Provide in-repo fallback adapters/mocks to allow unit tests to run without heavy deps and to provide deterministic integration tests (DEV_MOCK_AI override).
- Validate with unit tests first, then run deterministic (mocked) integration tests locally, then run full heavy integration tests in CI.

High-level steps
----------------
1. Prepare branch (done): `upgrade/langchain-stack` with adapter/fallback changes and deterministic integration tests.
2. Run unit tests locally (fast) and address failures.
3. Create an upgrade candidate manifest `backend/requirements.langchain-upgrade.txt` (already present) with *non-pinning* recommendations for CI-based testing.
4. In CI: create a separate job `integration-upgrade` which installs heavy deps from the upgrade manifest, seeds chroma, starts the backend, and runs the full integration test suite against real or mocked model providers as appropriate.
5. Iterate on test failures in CI until green. Keep changes small and limited to the adapter for compatibility.
6. When CI succeeds for the candidate versions, prepare a pinned `requirements.txt` or `pyproject.toml` update and open a follow-up PR to apply pins and final changes.

CI plan
-------
- Keep unit tests job unchanged (fast). This job runs on every push.
- Add a gated integration job (already added) that only runs when a reviewer or maintainer triggers it (workflow input `run_integration`), and which:
  - Installs heavy deps from `backend/requirements.langchain-upgrade.txt` in an isolated environment.
  - Seeds chroma with `backend/scripts/seed_chroma.py`.
  - Starts the backend on port 8000 and waits with a retry/backoff strategy.
  - Runs full integration tests (`pytest tests/integration`) with `RUN_INTEGRATION_TESTS=1`.

Rollback criteria
---------------
- If integration tests fail due to a package incompatibility, revert the branch and continue iterating in an isolated upgrade branch.
- If runtime errors affect production behavior after merge, revert the PR immediately and open a follow-up issue to pin the last-known-good versions.

Testing & Validation
--------------------
- Unit tests: must pass on developer machines without heavy installs (fallbacks should cover missing deps).
- Deterministic integration tests: run locally with `DEV_MOCK_AI=1` to exercise the RAG pipeline end-to-end without external model dependency.
- Full integration tests: run in CI job that installs heavy deps and seeds Chroma. Only run this in CI or in a disposable environment.

Recommended follow-ups
----------------------
- Add retry/backoff logic to the CI job waiting for the backend to be ready (3-5 attempts with increasing delays).
- Document how to opt into the upgrade locally (a short developer guide to create an isolated venv and install `backend/requirements.langchain-upgrade.txt`).
- After a successful upgrade, add pinned dependency manifest and update `AGENTS.md` and README with the new minimum required versions.

Files of interest
-----------------
- `backend/src/services/rag_adapter.py` — central adapter and fallback implementations.
- `backend/requirements.langchain-upgrade.txt` — candidate upgrade manifest for CI testing.
- `.github/workflows/ci.yml` — CI config; integration job should be gated and updated to use the upgrade manifest.
- `backend/scripts/seed_chroma.py` — CI helper that seeds Chroma before running tests.

Contact
-------
If anything here is unclear or you want me to proceed to run the gated CI job or open the PR, tell me and I'll proceed.
