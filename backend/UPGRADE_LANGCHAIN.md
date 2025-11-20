# LangChain Stack Upgrade Plan

This document outlines a safe, repeatable plan to upgrade the LangChain-related
stack in this repository. Upgrading these packages can be risky because they
frequently change public APIs and package split/renames (for example,
`HuggingFaceEmbeddings` moved to `langchain-huggingface`). Follow these steps in
a separate branch and CI-run before merging.

Recommended high-level steps

1. Create a branch: `git checkout -b upgrade/langchain-stack`.
2. Create a new virtual environment (or use `uv` helper) for the upgrade work.
3. Install candidate packages in the venv (do NOT change the primary
   `requirements.txt` yet). Example:

   ```powershell
   # from backend/ folder
   uv run pip install --upgrade "langchain" "langchain-core" "langchain-huggingface" "langchain-text-splitters" "langchain-community"
   uv run pip install --upgrade chromadb sentence-transformers transformers torch
   ```

4. Run the full test suite (unit + integration). Fix any API breakages.
5. When green, pin the working versions into `backend/requirements.txt` or
   `pyproject.toml` and open a PR.

Notes and safety precautions

- Prefer performing the upgrade in CI first (create a job that installs the
  candidate packages and runs tests). This avoids contaminating local dev venvs.
- If the repo uses `uv` for venv management, use `uv run pip` to ensure the
  project venv is used.
- If tests reveal deep incompatibilities, consider upgrading incrementally
  (e.g., only move to `langchain-huggingface` first and keep other packages
  pinned).
- Back up the current `requirements.txt` before making changes.

Troubleshooting

- If pip reports conflicts, collect the dependency tree:

  ```powershell
  uv run pipdeptree --freeze
  ```

- If a package is removed/renamed (e.g., `langchain` split into `langchain-core`),
  inspect the import sites and update the code to prefer the new package with
  guarded imports (the adapter pattern in `src/services/rag_adapter.py` already
  helps with this).

When to ask for help

- If the upgrade touches more than a few import sites or changes public class
  names used across the repo, pause and request a coordinated PR review; I can
  prepare the PR and run CI for you.
