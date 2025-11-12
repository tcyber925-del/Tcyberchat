# Migration Guide: Tavily to SerpAPI

This guide explains how to switch from Tavily to SerpAPI for web search in the TcyberChatbot application.

## Why SerpAPI?

SerpAPI provides:
- **Google Search Results**: Direct access to Google's search results (most comprehensive)
- **Multiple Search Engines**: Support for Google, Bing, Yahoo, Baidu, Yandex, etc.
- **Rich Data**: Structured data including featured snippets, knowledge graphs, related searches
- **Reliable API**: Battle-tested infrastructure with excellent uptime
- **Flexible Plans**: Free tier with 100 searches/month, scalable paid plans

## Installation

### 1. Install SerpAPI Python Client

```bash
pip install google-search-results
```

This installs the official SerpAPI Python client library.

### 2. Get Your API Key

1. Sign up at [https://serpapi.com/users/sign_up](https://serpapi.com/users/sign_up)
2. Get your API key from [https://serpapi.com/manage-api-key](https://serpapi.com/manage-api-key)
3. Free tier includes 100 searches/month

### 3. Configure Environment

Add your SerpAPI key to your `.env` file:

```bash
# Replace Tavily with SerpAPI
SERPAPI_API_KEY=your_serpapi_key_here

# Optional: Explicitly set provider (auto-detected by default)
WEB_SEARCH_PROVIDER=serpapi
```

## Configuration

### Provider Priority

The system automatically detects and prioritizes providers in this order:

1. **SerpAPI** (if `SERPAPI_API_KEY` is set) ← **Preferred**
2. **Tavily** (if `TAVILY_API_KEY` is set)
3. **DuckDuckGo** (free, no API key needed)

### Environment Variables

```bash
# Primary provider (auto-detected, or explicitly set)
WEB_SEARCH_PROVIDER=serpapi  # Options: serpapi, tavily, duckduckgo

# API Keys
SERPAPI_API_KEY=your_key_here
# TAVILY_API_KEY=your_key_here  # Can keep as fallback

# Cache and rate limiting (same for all providers)
WEB_SEARCH_CACHE_TTL=3600      # Cache results for 1 hour
WEB_SEARCH_RATE_LIMIT=10       # Max 10 requests per minute
WEB_SEARCH_ENABLE_CACHE=true   # Enable result caching
```

## Usage

### Automatic Usage

No code changes needed! The web search service automatically uses SerpAPI when the API key is configured:

```python
from backend.src.services.web_search_service import get_web_search_service

# Automatically uses SerpAPI if SERPAPI_API_KEY is set
service = get_web_search_service()
results = await service.search("Python programming", max_results=5)
```

### Explicit Provider Selection

Force a specific provider:

```python
from backend.src.services.web_search_service import WebSearchService

# Use SerpAPI explicitly
service = WebSearchService(provider="serpapi")
results = await service.search("machine learning", max_results=5)
```

### Provider Fallback

The system automatically falls back to DuckDuckGo if SerpAPI fails:

```python
# Primary: SerpAPI
# Fallback: DuckDuckGo
service = get_web_search_service()

# If SerpAPI fails, automatically tries DuckDuckGo
results = await service.search("latest AI news", max_results=5)
```

## API Response Format

SerpAPI returns rich Google search results. The provider extracts:

```python
SearchResult(
    title="Page Title",
    url="https://example.com",
    snippet="Brief description from Google...",
    source="web_search",
    relevance_score=1.0,  # 1.0 for first result, decreases
    timestamp=datetime.now()
)
```

### Additional Data Available

SerpAPI provides more data than we currently extract. You can extend `SerpAPIProvider.search()` to include:

- `position`: Result position in search
- `displayed_link`: Formatted URL shown in Google
- `date`: Publication date (if available)
- `cached_page_link`: Google's cached version
- `related_results`: Related searches
- `sitelinks`: Page sitelinks

## Migration Checklist

- [ ] Install `google-search-results` package
- [ ] Sign up for SerpAPI account
- [ ] Get API key from [serpapi.com/manage-api-key](https://serpapi.com/manage-api-key)
- [ ] Add `SERPAPI_API_KEY` to `.env`
- [ ] Remove or comment out `TAVILY_API_KEY` (optional - can keep as fallback)
- [ ] Test search functionality
- [ ] Monitor API usage at [serpapi.com/dashboard](https://serpapi.com/dashboard)

## Testing

Run the SerpAPI provider tests:

```bash
# Test SerpAPI provider
pytest tests/unit/test_serpapi_provider.py -v

# Test web search service with SerpAPI
pytest tests/unit/test_web_search_service.py -v -k serpapi
```

## Comparison: Tavily vs SerpAPI

| Feature | Tavily | SerpAPI |
|---------|--------|---------|
| **Free Tier** | Limited | 100 searches/month |
| **Search Engine** | Optimized for AI | Real Google results |
| **Data Quality** | Good for AI summaries | Comprehensive, structured |
| **Speed** | Fast | Fast |
| **Rate Limits** | Strict on free tier | 100/month on free tier |
| **Cost** | $0-$499+/month | $50-$250+/month |
| **Best For** | AI-optimized search | Production apps, SEO tools |

## Cost Considerations

### Free Tier Limits

- **SerpAPI**: 100 searches/month free, then pay-as-you-go
- **Tavily**: Limited free tier, requires paid plan for production
- **DuckDuckGo**: Unlimited (free, no API key)

### Recommendations

- **Development**: Use DuckDuckGo (free, unlimited)
- **Production (low volume)**: SerpAPI free tier (100/month)
- **Production (high volume)**: SerpAPI paid plan ($50+/month)
- **Keep Tavily**: As fallback if you already have credits

## Advanced Configuration

### Custom Search Parameters

Extend `SerpAPIProvider` to use more SerpAPI features:

```python
# In backend/src/services/web_search_service.py
# Modify SerpAPIProvider.search() params:

params = {
    "q": query,
    "api_key": self.api_key,
    "num": max_results,
    "engine": "google",
    
    # Add custom parameters
    "location": "United States",      # Geo-location
    "hl": "en",                       # Language
    "gl": "us",                       # Country
    "safe": "active",                 # Safe search
    "tbs": "qdr:m",                   # Time range (past month)
}
```

### Multiple Providers with Priority

Keep both Tavily and SerpAPI:

```bash
# .env
SERPAPI_API_KEY=your_serpapi_key
TAVILY_API_KEY=your_tavily_key

# Primary provider
WEB_SEARCH_PROVIDER=serpapi
```

The system will use SerpAPI first, fall back to Tavily, then DuckDuckGo.

## Troubleshooting

### "SerpAPI provider not available"

**Cause**: API key not set or `google-search-results` not installed

**Solution**:
```bash
pip install google-search-results
# Add SERPAPI_API_KEY to .env
```

### "SerpAPI authentication failed"

**Cause**: Invalid API key

**Solution**: Verify your API key at [serpapi.com/manage-api-key](https://serpapi.com/manage-api-key)

### "SerpAPI rate limit exceeded"

**Cause**: Exceeded your plan's search limit

**Solution**:
- Check usage at [serpapi.com/dashboard](https://serpapi.com/dashboard)
- Upgrade plan or wait for limit reset
- Enable caching to reduce API calls:
  ```bash
  WEB_SEARCH_ENABLE_CACHE=true
  WEB_SEARCH_CACHE_TTL=3600
  ```

### Results Quality Issues

**Issue**: Getting unexpected or low-quality results

**Solution**: 
- SerpAPI returns real Google results, so issues may be with the query
- Try refining search queries
- Adjust `max_results` parameter
- Check if safe search is affecting results

## Reverting to Tavily

To switch back to Tavily:

```bash
# .env
# Comment out or remove SerpAPI key
# SERPAPI_API_KEY=your_key

# Keep or add Tavily key
TAVILY_API_KEY=your_tavily_key

# Optionally force provider
WEB_SEARCH_PROVIDER=tavily
```

The system will automatically fall back to Tavily.

## Support

- **SerpAPI Documentation**: [https://serpapi.com/docs](https://serpapi.com/docs)
- **SerpAPI Dashboard**: [https://serpapi.com/dashboard](https://serpapi.com/dashboard)
- **Python Client GitHub**: [https://github.com/serpapi/google-search-results-python](https://github.com/serpapi/google-search-results-python)
- **Support**: [support@serpapi.com](mailto:support@serpapi.com)

## Next Steps

1. ✅ SerpAPI is now integrated and ready to use
2. Configure your API key in `.env`
3. Test the integration
4. Monitor usage and adjust rate limits as needed
5. Consider upgrading to paid plan for production use
