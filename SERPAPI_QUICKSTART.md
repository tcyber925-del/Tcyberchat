# SerpAPI Quick Start

## ✅ What Changed

SerpAPI is now integrated as the **preferred** web search provider (replacing/supplementing Tavily).

## 🚀 Quick Setup (3 Steps)

### 1. Install Package
```bash
pip install google-search-results
```

### 2. Get API Key
- Sign up: [serpapi.com/users/sign_up](https://serpapi.com/users/sign_up)
- Get key: [serpapi.com/manage-api-key](https://serpapi.com/manage-api-key)
- Free: 100 searches/month

### 3. Configure
```bash
# Add to .env
SERPAPI_API_KEY=your_api_key_here
```

**That's it!** No code changes needed. 🎉

## 🎯 Provider Priority

The system auto-detects and uses providers in this order:

1. **SerpAPI** (if `SERPAPI_API_KEY` set) ← Preferred
2. **Tavily** (if `TAVILY_API_KEY` set)
3. **DuckDuckGo** (always available, free)

## 📊 Provider Comparison

| | DuckDuckGo | SerpAPI | Tavily |
|---|---|---|---|
| **Cost** | Free ∞ | 100/month free | Limited |
| **Quality** | Good | ★★★ Excellent | ★★ Very Good |
| **Source** | DuckDuckGo | 🔥 Real Google | AI-optimized |
| **Best For** | Dev/Testing | Production | AI Apps |

## 🔧 Configuration Options

```bash
# Primary provider (auto-detected by default)
WEB_SEARCH_PROVIDER=serpapi

# SerpAPI key
SERPAPI_API_KEY=your_key

# Optional: Keep Tavily as fallback
TAVILY_API_KEY=your_tavily_key

# Cache & rate limiting (unchanged)
WEB_SEARCH_CACHE_TTL=3600
WEB_SEARCH_RATE_LIMIT=10
WEB_SEARCH_ENABLE_CACHE=true
```

## 💡 Usage Examples

### Automatic (Recommended)
```python
from backend.src.services.web_search_service import get_web_search_service

# Uses SerpAPI automatically if key is configured
service = get_web_search_service()
results = await service.search("Python programming", max_results=5)
```

### Force Specific Provider
```python
from backend.src.services.web_search_service import WebSearchService

# Explicitly use SerpAPI
service = WebSearchService(provider="serpapi")
results = await service.search("machine learning", max_results=5)

# Or use DuckDuckGo
service = WebSearchService(provider="duckduckgo")
results = await service.search("latest news", max_results=10)
```

## 🧪 Testing

```bash
# Test SerpAPI provider
pytest tests/unit/test_serpapi_provider.py -v

# Test web search service
pytest tests/unit/test_web_search_service.py -v

# All web-related tests
pytest tests/unit/test_web*.py -v
```

## ❓ Troubleshooting

### "SerpAPI provider not available"
```bash
pip install google-search-results
# Add SERPAPI_API_KEY to .env
```

### "Authentication failed"
- Verify key at [serpapi.com/manage-api-key](https://serpapi.com/manage-api-key)
- Make sure key is in `.env` file

### "Rate limit exceeded"
- Check usage: [serpapi.com/dashboard](https://serpapi.com/dashboard)
- Enable caching: `WEB_SEARCH_ENABLE_CACHE=true`
- Consider upgrading plan

### Want to use DuckDuckGo only?
```bash
# Just don't set any API keys, or:
WEB_SEARCH_PROVIDER=duckduckgo
```

## 🔄 Reverting to Tavily

```bash
# Option 1: Remove SerpAPI key
# SERPAPI_API_KEY=...

# Option 2: Force Tavily
WEB_SEARCH_PROVIDER=tavily
TAVILY_API_KEY=your_tavily_key
```

## 📚 Documentation

- **Migration Guide**: `backend/docs/SERPAPI_MIGRATION.md`
- **Full Summary**: `backend/docs/SERPAPI_SUMMARY.md`
- **SerpAPI Docs**: [serpapi.com/docs](https://serpapi.com/docs)

## ✨ Benefits

- ✅ **Real Google Results** - Most comprehensive
- ✅ **Better Quality** - Google's ranking algorithm
- ✅ **100 Free Searches/Month** - Good for development
- ✅ **No Code Changes** - Drop-in replacement
- ✅ **Automatic Fallback** - Falls back to DuckDuckGo if needed
- ✅ **Backward Compatible** - Everything still works

## 💰 Cost

- **Free Tier**: 100 searches/month (perfect for development)
- **Paid Plans**: Starting at $50/month (production)
- **DuckDuckGo**: Always free (unlimited)

## 📈 Monitoring

Track your usage at: [serpapi.com/dashboard](https://serpapi.com/dashboard)

---

**Questions?** See full documentation in `backend/docs/SERPAPI_MIGRATION.md`
