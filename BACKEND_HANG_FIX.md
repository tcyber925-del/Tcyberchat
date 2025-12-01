# Backend Not Responding - Diagnosis & Fix

## Problem
The backend server is not responding to requests (models endpoint hangs).

## Root Cause
When code files (`deep_research_graph.py`, `groq_client.py`) were modified, uvicorn's `--reload` feature detected the changes and attempted to reload the application. During this reload, the initialization got stuck, likely when trying to:
- Connect to Ollama (if configured)
- Connect to Llama.cpp server (if configured)
- Initialize AI clients with long timeouts

## Symptoms
- `/api/v1/models` endpoint hangs indefinitely
- `curl http://localhost:8000/api/v1/models` never returns
- `import main` in Python hangs

## Solution

### Quick Fix: Restart Backend

1. **Stop the current backend**:
   - Go to the terminal running `uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000`
   - Press `Ctrl+C` to stop the server

2. **Restart the backend**:
   ```bash
   cd backend
   uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Verify it's working**:
   ```bash
   curl http://localhost:8000/api/v1/models
   ```
   Should return JSON within 2-3 seconds (or use the 15s timeout).

### Long-term Fix: Prevent Hangs

The `/api/v1/models` endpoint already has a timeout (added in previous fixes):
```python
async def get_models():
    try:
        ai_service = await asyncio.wait_for(get_ai_service(), timeout=10.0)
        models = await asyncio.wait_for(ai_service.get_available_models(), timeout=5.0)
        return models
    except asyncio.TimeoutError:
        # Returns fallback models
        ...
```

However, if the **import/initialization** itself hangs (before the endpoint code runs), the timeout won't help.

**Recommendation**: 
- Ensure Ollama/Llama.cpp are either running OR properly configured to be optional.
- Consider lazy initialization of local model clients (only when requested).

## Files Modified (Recent Changes)
- `backend/src/agents/deep_research_graph.py` - Fixed indentation
- `backend/src/clients/groq_client.py` - Added base_url logging
- `backend/src/services/prompts/deep_research_synthesis.txt` - New prompt template

These changes are all safe, but triggered a reload that exposed the underlying initialization hang issue.
