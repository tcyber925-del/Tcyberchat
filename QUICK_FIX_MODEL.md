# Quick Fix: Model Configuration

## 🚨 ISSUE FOUND

Your `.env` and `gemini_client.py` reference **`gemini-2.5-flash`** which doesn't exist!

**Google's actual models**:
- Gemini 1.5 Flash (`gemini-1.5-flash`)
- Gemini 2.0 Flash Exp (`gemini-2.0-flash-exp`)
- Gemini 1.5 Pro (`gemini-1.5-pro`)

---

## ✅ QUICK FIX (2 minutes)

### Option A: Use Gemini 2.0 with Native Google Search (BEST) ⭐

**Edit `backend/.env`**:
```bash
GEMINI_MODEL=gemini-2.0-flash-exp
```

**Restart backend**:
```bash
cd C:\Users\Tcyber\Documents\PROJECTS\TcyberChatbot\backend
python main.py
```

**Benefits**:
- ✅ Native Google Search capability
- ✅ Free tier (1500 requests/day)
- ✅ Latest model with best features

---

### Option B: Use Gemini 1.5 Flash (Current Architecture)

**Edit `backend/.env`**:
```bash
GEMINI_MODEL=gemini-1.5-flash-latest
```

**Restart backend**:
```bash
cd C:\Users\Tcyber\Documents\PROJECTS\TcyberChatbot\backend
python main.py
```

**Benefits**:
- ✅ Stable, production-ready
- ✅ Works with your current web search setup (Tavily/SerpAPI)
- ✅ Free tier (1500 requests/day)

---

## 🔥 RECOMMENDED UPGRADE (30 minutes)

To enable Gemini 2.0's **native Google Search**, update the code:

### Step 1: Update `.env`
```bash
GEMINI_MODEL=gemini-2.0-flash-exp
```

### Step 2: Update `backend/src/clients/gemini_client.py`

Replace the `generate()` method (lines 36-51) with:

```python
def generate(self, prompt: str, enable_grounding: bool = False, **kwargs) -> str:
    """Generate text for the given prompt with optional Google Search grounding.
    
    Args:
        prompt: The text prompt to generate from
        enable_grounding: If True and using Gemini 2.0, enables Google Search grounding
        **kwargs: Additional parameters passed to generate_content
    
    Returns:
        The generated text response
    """
    if self.model_client is None:
        raise RuntimeError("google-genai is not installed or client not configured (set GEMINI_API_KEY)")
    
    try:
        # Enable Google Search grounding for Gemini 2.0 models
        if enable_grounding and 'gemini-2.0' in self.model_name:
            logger.info(f"Enabling Google Search grounding for {self.model_name}")
            kwargs['tools'] = 'google_search_retrieval'
        
        response = self.model_client.generate_content(contents=prompt, **kwargs)
        if hasattr(response, "text"):
            return response.text
        return str(response)
    except Exception as e:
        logger.error(f"Gemini generate failed: {e}", exc_info=True)
        raise
```

### Step 3: Update `backend/src/services/ai_service.py`

Find the `generate()` method (around line 200) and add grounding parameter:

```python
# In AIService.generate() method
if self.provider == "google" and hasattr(self.gemini_client, 'generate'):
    # Enable grounding for time-sensitive queries with Gemini 2.0
    enable_grounding = (
        use_web_search and 
        'gemini-2.0' in os.getenv('GEMINI_MODEL', '')
    )
    
    response = self.gemini_client.generate(
        prompt=final_prompt,
        enable_grounding=enable_grounding,
        **generation_params
    )
```

### Step 4: Test

```bash
cd backend
python main.py
```

Ask: "What is the latest AI news?"

You should see in logs:
```
INFO: Enabling Google Search grounding for models/gemini-2.0-flash-exp
```

---

## 🆚 COMPARISON: Native vs External Search

### Gemini 2.0 Native Google Search

**Pros**:
- ✅ Built directly into the model
- ✅ No external API calls needed
- ✅ Saves Tavily/SerpAPI quota
- ✅ More coherent responses (model sees raw search data)
- ✅ Free within Gemini quota

**Cons**:
- ⚠️ Less control over search parameters
- ⚠️ Experimental (may change)
- ⚠️ Limited to Gemini 2.0 models

**How it works**:
```
User Query → Gemini 2.0 → Google Search (internal) → Response with citations
```

---

### Your Current Setup (Tavily/SerpAPI + RAG)

**Pros**:
- ✅ Full control over search results
- ✅ Multiple providers (fallback)
- ✅ Works with any AI model
- ✅ Can customize result filtering

**Cons**:
- ⚠️ Uses external API quotas
- ⚠️ Extra latency (separate API call)
- ⚠️ More complex architecture

**How it works**:
```
User Query → Web Search API → RAG Context → AI Model → Response
```

---

## 🎯 RECOMMENDED HYBRID APPROACH

Use **BOTH** for maximum reliability:

1. **For Gemini 2.0 with time-sensitive queries**: Use native grounding
2. **For other models or as fallback**: Use Tavily/SerpAPI
3. **For non-time-sensitive queries**: Use RAG without web search

### Implementation Logic

```python
# Pseudo-code for hybrid approach
if query_is_time_sensitive:
    if model == "gemini-2.0" and has_native_search:
        use_native_grounding()
    else:
        use_external_search_api()  # Tavily/SerpAPI
else:
    use_rag_only()  # No web search
```

---

## 📊 Model Comparison (Free Tier)

| Feature | Gemini 2.0 Flash Exp | Gemini 1.5 Flash | OpenRouter (gpt-oss-20b) |
|---------|---------------------|------------------|--------------------------|
| Native Web Search | ✅ Yes | ❌ No | ❌ No |
| Speed | ⚡⚡⚡ Fast | ⚡⚡⚡ Fast | ⚡⚡ Medium |
| Quality | ⭐⭐⭐⭐ High | ⭐⭐⭐ Good | ⭐⭐ Basic |
| Context Window | 1M tokens | 1M tokens | 32K tokens |
| Free Limit | 1500/day | 1500/day | Limited |
| Best For | **Web search queries** | General chat | Basic tasks |

---

## 🧪 TESTING

### Test 1: Verify Model Name

```bash
cd backend
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('Current model:', os.getenv('GEMINI_MODEL'))"
```

Expected output:
```
Current model: gemini-2.0-flash-exp
```

### Test 2: Test Model Connection

```bash
cd backend
python -c "from src.clients.gemini_client import GeminiClient; client = GeminiClient(); print(client.generate('Say hello'))"
```

Expected output:
```
Hello! How can I help you today?
```

### Test 3: Test Native Google Search (if using Gemini 2.0)

```bash
cd backend
python -c "from src.clients.gemini_client import GeminiClient; client = GeminiClient(); print(client.generate('What is the latest AI news?', enable_grounding=True))"
```

Expected: Should return recent news with URLs/citations

### Test 4: Test Web Search Service

```bash
cd backend
python -c "from src.services.web_search_service import get_web_search_service; import asyncio; ws = get_web_search_service(); results = asyncio.run(ws.search('latest AI news', max_results=3)); print(f'Found {len(results)} results'); print(results[0])"
```

Expected: Should show 3 search results

---

## ⚠️ CURRENT STATUS BEFORE FIX

**`.env`**: `GEMINI_MODEL=gemini-2.5-flash` ❌ (doesn't exist)
**`gemini_client.py`**: Hardcoded `models/gemini-2.5-flash` ❌

**What's probably happening**:
- Model initialization fails silently
- Falls back to default behavior
- Web search works but model may not be optimal

---

## ✅ AFTER FIX

**Option A (Best)**: `GEMINI_MODEL=gemini-2.0-flash-exp` ✅
**Option B (Stable)**: `GEMINI_MODEL=gemini-1.5-flash-latest` ✅

**Expected behavior**:
- Model initializes correctly
- Responses are faster and more accurate
- Web search integration works perfectly

---

## 📝 SUMMARY

**Immediate Action** (Choose one):

1. **Quick Fix**: Change `.env` line 5 from `gemini-2.5-flash` to `gemini-2.0-flash-exp`
2. **Alternative**: Change to `gemini-1.5-flash-latest` (more stable)

**Optional Upgrade**:
- Modify `gemini_client.py` to support native Google Search grounding
- Update `ai_service.py` to enable grounding for time-sensitive queries

**Result**:
- ✅ Model works correctly
- ✅ Web search integration functional
- ✅ Better responses for "latest" queries
- ✅ Free tier with 1500 requests/day

---

## 🔗 NEXT STEPS

After fixing the model name:

1. Test web search auto-detection (frontend in dev mode)
2. Monitor API quotas
3. Consider implementing hybrid approach (native + external search)
4. Fix frontend TypeScript errors (optional, use dev mode instead)

See `GOOGLE_MODELS_WEB_SEARCH.md` for full details!
