# Web Search Provider Switch & Log Fixes

## Actions Taken

### 1. Switched to SerpAPI
- **Action**: Updated `.env` to set `WEB_SEARCH_PROVIDER=serpapi`.
- **Reason**: Tavily was returning `403 Forbidden` (likely invalid/expired key).

### 2. Fixed Import Error
- **Action**: Installed `google-search-results` package.
- **Reason**: The logs showed `ImportError: cannot import name 'GoogleSearch' from 'serpapi'`. This package is required for SerpAPI to work.

### 3. Fixed Deprecation Warning
- **Action**: Verified `backend/src/services/rag_service.py` uses `langchain_huggingface`.
- **Reason**: To resolve `LangChainDeprecationWarning` for `HuggingFaceEmbeddings`.

---

## ⚠️ Action Required: Restart Backend

To apply the changes, you **MUST** restart the backend server:

1.  **Stop the current server**: Press `Ctrl+C` in the backend terminal.
2.  **Start it again**:
    ```bash
    cd backend
    uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
    ```

## Verification

After restarting:
1.  **Web Search**: Should now initialize with `provider=serpapi`.
2.  **Deep Research**: Should work using SerpAPI results.
3.  **Logs**: The `ImportError` and `ForbiddenError` should be gone.
