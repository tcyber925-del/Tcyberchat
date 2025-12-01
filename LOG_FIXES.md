# Log Analysis and Fixes

## Issues Identified & Fixed

### 1. Web Search Provider Failure (CRITICAL)
**Log Error**:
```
WARNING:src.services.web_search_service:Primary provider (serpapi) failed: Could not import serpapi python package.
INFO:src.services.web_search_service:LangChain providers failed; attempting CUSTOM fallback provider: duckduckgo
```
**Cause**: `WEB_SEARCH_PROVIDER` was set to `serpapi` in `.env`, but the package wasn't installed.
**Fix Applied**: Updated `.env` to set `WEB_SEARCH_PROVIDER=tavily`. This will use your configured Tavily API key and fix the fallback behavior.

### 2. LangChain Deprecation Warning
**Log Warning**:
```
LangChainDeprecationWarning: The class `HuggingFaceEmbeddings` was deprecated in LangChain 0.2.2...
```
**Cause**: Old import path for embeddings.
**Fix Applied**: Updated `backend/src/services/rag_service.py` to use `langchain_huggingface` package, which is already installed.

### 3. Llama.cpp Connection Error (Expected)
**Log Warning**:
```
WARNING:src.services.ai_service:Could not retrieve Llama.cpp models: Client error '404 Not Found' for url 'http://localhost:8080/v1/models'
```
**Cause**: The backend attempts to connect to a local Llama.cpp server at startup.
**Action**: **Ignore this** if you are not running a local Llama.cpp server. It does not affect other AI services (Gemini, Groq, OpenRouter).

---

## ⚠️ Action Required: Restart Backend

To apply the `.env` changes (switching to Tavily), you **MUST** restart the backend server:

1.  **Stop the current server**: Press `Ctrl+C` in the backend terminal.
2.  **Start it again**:
    ```bash
    cd backend
    uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
    ```

After restarting, the logs should show:
`INFO:src.services.web_search_service:WebSearchService initialized: provider=tavily`
