# Free Google Models with Web Search Capability

## Current Status in Your Project

### Configured Models ✅

From your `.env`:
```bash
GEMINI_API_KEY="AIzaSy..." ✅
GEMINI_MODEL=gemini-2.5-flash ✅

OPENROUTER_API_KEY="sk-or-v1-..." ✅
OPENROUTER_MODEL=openai/gpt-oss-20b:free ✅
```

### Your Web Search Setup ✅

```bash
WEB_SEARCH_PROVIDER=tavily ✅
TAVILY_API_KEY="tvly-dev-..." ✅
SERPAPI_API_KEY="4d74bbac..." ✅
```

---

## Google Models with Native Grounding/Web Search

### 1. ⭐ **Gemini 2.0 Flash (Experimental)** - BEST FOR WEB SEARCH

**Model Name**: `gemini-2.0-flash-exp`

**Features**:
- ✅ **Native Google Search Grounding** (built-in web search)
- ✅ **Free tier available**
- ✅ Fast response (Flash variant)
- ✅ Multimodal (text, images, audio)
- ✅ Extended context (1M tokens)

**Grounding Modes**:
- Google Search Grounding
- Code Execution
- Real-time information access

**How to Enable**:
```python
# Automatic grounding (includes Google Search)
model = genai.GenerativeModel('gemini-2.0-flash-exp')
response = model.generate_content(
    "What is the latest AI news?",
    tools='google_search_retrieval'  # ← Enables Google Search
)
```

**Cost**: **FREE** (within quota limits)
- 15 RPM (requests per minute)
- 1 million TPM (tokens per minute)
- 1500 RPD (requests per day)

---

### 2. **Gemini 1.5 Flash** - CURRENTLY USING

**Model Name**: `gemini-1.5-flash` or `gemini-1.5-flash-latest`

**Features**:
- ✅ Fast and efficient
- ✅ 1M token context window
- ✅ Free tier available
- ⚠️ **No native Google Search** (but can use external search)

**Your Current Setup**:
```bash
GEMINI_MODEL=gemini-2.5-flash  # ← You have this
```

**Note**: Your `.env` says `gemini-2.5-flash` but it should be either `gemini-1.5-flash` or `gemini-2.0-flash-exp`

**Cost**: **FREE**
- 15 RPM
- 1 million TPM
- 1500 RPD

---

### 3. **Gemini 1.5 Pro** - HIGH QUALITY

**Model Name**: `gemini-1.5-pro` or `gemini-1.5-pro-latest`

**Features**:
- ✅ Highest quality responses
- ✅ 2M token context window
- ✅ Free tier available
- ⚠️ **No native Google Search** (but can use external search)
- ⚠️ Slower than Flash

**Cost**: **FREE** (limited)
- 2 RPM (very low!)
- 32,000 TPM
- 50 RPD

---

### 4. **Gemini 1.5 Flash-8B** - FASTEST

**Model Name**: `gemini-1.5-flash-8b`

**Features**:
- ✅ Ultra-fast
- ✅ Good for simple tasks
- ✅ Free tier available
- ❌ Lower quality than Flash/Pro
- ⚠️ **No native Google Search**

**Cost**: **FREE**
- 15 RPM
- 4 million TPM
- 1500 RPD

---

## Recommended Configuration

### Option 1: Use Gemini 2.0 with Native Google Search ⭐ BEST

Update your configuration to use Gemini 2.0's built-in search:

**`.env`**:
```bash
GEMINI_API_KEY="AIzaSyAzxyrTis09q3mHKEznBbzvWz_uAb6DWfo"
GEMINI_MODEL=gemini-2.0-flash-exp  # ← Changed from gemini-2.5-flash

# Keep your external search as backup
WEB_SEARCH_PROVIDER=tavily
TAVILY_API_KEY="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"
SERPAPI_API_KEY="4d74bbac20c28c571041a827a278ca350a5547ffc5fe32a790bd84f4f369f4b1"
```

**Modify `backend/src/clients/gemini_client.py`** to enable grounding:

```python
def generate(self, prompt: str, enable_grounding: bool = False, **kwargs) -> str:
    """Generate text with optional Google Search grounding."""
    if self.model_client is None:
        raise RuntimeError("google-genai not configured")
    
    try:
        # Enable Google Search if requested
        if enable_grounding and 'gemini-2.0' in self.model_name:
            kwargs['tools'] = 'google_search_retrieval'
        
        response = self.model_client.generate_content(contents=prompt, **kwargs)
        if hasattr(response, "text"):
            return response.text
        return str(response)
    except Exception as e:
        logger.error(f"Gemini generate failed: {e}", exc_info=True)
        raise
```

**Benefits**:
- ✅ Built-in Google Search (no external API needed)
- ✅ More accurate (direct from Google)
- ✅ Saves Tavily/SerpAPI quota
- ✅ Simpler architecture

---

### Option 2: Use Gemini 1.5 Flash + Your Current Web Search Setup ✓ CURRENT

Keep your current setup but fix the model name:

**`.env`**:
```bash
GEMINI_MODEL=gemini-1.5-flash-latest  # ← Fixed from gemini-2.5-flash

# External web search (what you're using now)
WEB_SEARCH_PROVIDER=tavily
TAVILY_API_KEY="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"
SERPAPI_API_KEY="4d74bbac20c28c571041a827a278ca350a5547ffc5fe32a790bd84f4f369f4b1"
```

**Benefits**:
- ✅ Your current implementation already works
- ✅ Multiple search providers (Tavily, SerpAPI, DuckDuckGo)
- ✅ More control over search results
- ⚠️ Uses external API quotas

---

### Option 3: Hybrid Approach ⭐ RECOMMENDED

Use Gemini 2.0 with BOTH native search AND your external search as fallback:

**Logic**:
1. For time-sensitive queries → Use Gemini 2.0's native Google Search
2. If native search unavailable → Fall back to Tavily/SerpAPI
3. For non-time-sensitive queries → Use RAG without web search

**Benefits**:
- ✅ Best of both worlds
- ✅ Saves external API quota
- ✅ Fallback protection
- ✅ Maximum flexibility

---

## Available Free Google Models (via OpenRouter)

Your `OPENROUTER_API_KEY` gives you access to:

### Via OpenRouter (Free Tier)

```bash
google/gemini-flash-1.5        # Free
google/gemini-flash-1.5-exp    # Free (experimental)
google/gemini-pro-1.5          # Free (limited)
google/gemini-2.0-flash-exp    # Free (if available)
```

**Your Current**:
```bash
OPENROUTER_MODEL=openai/gpt-oss-20b:free
```

**Recommendation**: Switch to Google models via OpenRouter:
```bash
OPENROUTER_MODEL=google/gemini-flash-1.5  # ← Better than gpt-oss-20b
```

---

## Model Comparison Table

| Model | Speed | Quality | Context | Web Search | Free Limit | Best For |
|-------|-------|---------|---------|------------|------------|----------|
| **Gemini 2.0 Flash Exp** | ⚡⚡⚡ Fast | ⭐⭐⭐⭐ High | 1M | ✅ Native | 1500/day | **Web search queries** |
| **Gemini 1.5 Flash** | ⚡⚡⚡ Fast | ⭐⭐⭐ Good | 1M | ❌ External | 1500/day | General chat |
| **Gemini 1.5 Pro** | ⚡⚡ Medium | ⭐⭐⭐⭐⭐ Best | 2M | ❌ External | 50/day | Complex tasks |
| **Gemini 1.5 Flash-8B** | ⚡⚡⚡⚡ Fastest | ⭐⭐ Basic | 1M | ❌ External | 1500/day | Simple tasks |

---

## Implementation Steps

### Immediate Fix (5 minutes)

1. **Fix model name in `.env`**:
```bash
cd C:\Users\Tcyber\Documents\PROJECTS\TcyberChatbot\backend
```

Edit `.env`:
```bash
# Change from:
GEMINI_MODEL=gemini-2.5-flash

# To (choose one):
GEMINI_MODEL=gemini-2.0-flash-exp     # ← For native Google Search
# OR
GEMINI_MODEL=gemini-1.5-flash-latest  # ← For current setup
```

2. **Restart backend**:
```bash
python main.py
```

3. **Test**!

---

### Full Upgrade to Native Google Search (30 minutes)

1. **Update `.env`**:
```bash
GEMINI_MODEL=gemini-2.0-flash-exp
```

2. **Modify `gemini_client.py`** to support grounding (see Option 1 above)

3. **Update `ai_service.py`** to detect Gemini 2.0 and enable grounding for web queries

4. **Test with queries like**: "What is the latest AI news?"

---

## Testing

### Test Native Google Search (if using Gemini 2.0)

```python
import google.generativeai as genai

genai.configure(api_key="YOUR_KEY")
model = genai.GenerativeModel('gemini-2.0-flash-exp')

response = model.generate_content(
    "What is the latest AI news?",
    tools='google_search_retrieval'
)

print(response.text)
```

### Test Your Current Setup

```bash
cd backend
python -c "from src.services.web_search_service import get_web_search_service; import asyncio; ws = get_web_search_service(); results = asyncio.run(ws.search('latest AI news', max_results=3)); print(f'Found {len(results)} results')"
```

---

## Cost Comparison

### Gemini 2.0 Native Search (Free)
- ✅ **Free** Google Search grounding
- ✅ 1500 requests/day
- ✅ No external API needed

### Your Current Setup (External APIs)
- Tavily: Limited free tier
- SerpAPI: 100 searches/month free
- DuckDuckGo: Unlimited but rate-limited

### Recommendation

Use **Gemini 2.0 Flash Exp with native Google Search** for:
- Latest news queries
- Current events
- Real-time information

Keep **external search as backup** for:
- More results needed
- Specific search customization
- When Gemini quota exhausted

---

## Quick Action Items

1. ✅ Fix model name: `gemini-2.5-flash` → `gemini-2.0-flash-exp` or `gemini-1.5-flash-latest`
2. ⚠️ Consider upgrading to Gemini 2.0 for native search
3. ✅ Test current web search setup (it should work now!)
4. ✅ Monitor API quotas

---

## Resources

- **Gemini API Docs**: https://ai.google.dev/docs
- **Gemini 2.0 Grounding**: https://ai.google.dev/gemini-api/docs/grounding
- **Free Tier Limits**: https://ai.google.dev/pricing
- **OpenRouter Models**: https://openrouter.ai/models

---

**Bottom Line**: Your current setup is good, just fix the model name! For best results, upgrade to Gemini 2.0 Flash Exp with native Google Search grounding.
