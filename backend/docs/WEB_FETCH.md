# Web Fetch Enhancement

## Overview

The Web Fetch feature extends the existing web search functionality by fetching and extracting full content from URLs returned by search providers. This enables the RAG system to use richer, more complete information when answering queries, beyond just search result snippets.

## Key Features

- **Async HTTP Fetching**: Concurrent fetching with configurable timeouts and retries
- **Multi-Format Extraction**: Supports HTML and PDF content extraction
- **Fallback Strategy**: Multiple extraction libraries with graceful degradation
- **Caching**: Separate fetch cache with TTL to reduce redundant requests
- **Rate Limiting**: Per-domain rate limiting to be a good web citizen
- **Domain Control**: Allow/block lists for domain filtering
- **Safety**: Content size limits, timeout protection, error handling

## Architecture

### Components

1. **WebFetchService** (`backend/src/services/web_fetch_service.py`)
   - Core service for fetching and extracting content
   - Manages caching, rate limiting, and concurrency
   - Supports multiple extraction libraries with fallback

2. **SearchResult Extensions** (`backend/src/services/web_search_service.py`)
   - Extended with optional fields: `content`, `canonical_url`, `content_type`, `published_at`, `tokens_estimate`
   - Backward compatible—fields only included when present

3. **enrich_results Method** (`WebSearchService`)
   - Enriches search results with fetched content
   - Only active when `WEB_FETCH_ENABLED=true`

4. **RAG Integration** (`backend/src/services/rag_service.py`)
   - Automatically enriches web search results before building context
   - Prefers fetched content over snippets when available

## Configuration

All configuration is via environment variables. **Defaults ensure backward compatibility**—web fetch is disabled by default.

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WEB_FETCH_ENABLED` | `false` | Enable web content fetching |
| `WEB_FETCH_CONCURRENCY` | `5` | Max concurrent fetch requests |
| `WEB_FETCH_TIMEOUT_MS` | `8000` | Request timeout in milliseconds |
| `WEB_FETCH_CACHE_TTL` | `3600` | Cache time-to-live in seconds (1 hour) |
| `WEB_FETCH_MAX_BYTES` | `2000000` | Max response size (2MB) |
| `WEB_FETCH_PDF_ENABLED` | `true` | Enable PDF extraction |
| `WEB_FETCH_USER_AGENT` | `LocalChatbot/1.0` | HTTP User-Agent string |
| `WEB_FETCH_MAX_FETCH` | `3` | Max URLs to fetch per search |
| `WEB_FETCH_BLOCKLIST_DOMAINS` | _(empty)_ | Comma-separated blocked domains |
| `WEB_FETCH_ALLOWLIST_DOMAINS` | _(empty)_ | Comma-separated allowed domains (if set, only these) |

### Example Configuration

**Basic Enable:**
```bash
export WEB_FETCH_ENABLED=true
```

**Production Settings:**
```bash
export WEB_FETCH_ENABLED=true
export WEB_FETCH_CONCURRENCY=10
export WEB_FETCH_TIMEOUT_MS=5000
export WEB_FETCH_MAX_FETCH=5
export WEB_FETCH_BLOCKLIST_DOMAINS="spam.com,blocked.org"
```

**Windows PowerShell:**
```powershell
$env:WEB_FETCH_ENABLED="true"
$env:WEB_FETCH_CONCURRENCY="10"
```

## Content Extraction

### HTML Extraction

The service uses a **fallback strategy** with multiple libraries:

1. **trafilatura** (preferred)
   - Best for article/content extraction
   - Extracts metadata (title, published_at)
   - Removes boilerplate automatically

2. **readability-lxml** (fallback)
   - Mozilla Readability port
   - Good for general web pages

3. **BeautifulSoup** (final fallback)
   - Basic text extraction
   - Removes scripts, styles, navigation

### PDF Extraction

Supports PDF documents with fallback:

1. **PyMuPDF (pymupdf)** (preferred)
   - Fast and accurate
   - Extracts metadata

2. **pypdf** (fallback)
   - Pure Python fallback
   - Slower but works without binary dependencies

### Installing Optional Dependencies

None of the extraction libraries are required—the system degrades gracefully. Install what you need:

```bash
# Basic HTML extraction (recommended minimum)
pip install beautifulsoup4 lxml

# Better HTML extraction
pip install trafilatura readability-lxml

# PDF support
pip install pymupdf  # or pypdf

# HTTP client (required if WEB_FETCH_ENABLED=true)
pip install httpx
```

**All-in-one:**
```bash
pip install httpx beautifulsoup4 lxml trafilatura readability-lxml pymupdf
```

## Usage

### Enabling Web Fetch

1. **Set environment variable:**
   ```bash
   export WEB_FETCH_ENABLED=true
   ```

2. **Use existing web search API:**
   - The chat API already supports `enableWebSearch`
   - No code changes needed
   - Results are automatically enriched when fetch is enabled

### API Request Example

```json
POST /api/chat/stream
{
  "message": "What are the latest AI developments?",
  "enableWebSearch": true
}
```

When `WEB_FETCH_ENABLED=true`, the system:
1. Performs web search (DuckDuckGo/Tavily)
2. Fetches full content from top search results
3. Extracts readable content
4. Uses enriched content in RAG context
5. Returns response with full citations

### Programmatic Usage

```python
from backend.src.services.web_search_service import get_web_search_service

# Get service instance
search_service = get_web_search_service()

# Search (returns SearchResult objects)
results = await search_service.search("latest AI news", max_results=5)

# Enrich with fetched content (only if WEB_FETCH_ENABLED=true)
enriched_results = await search_service.enrich_results(results)

# Check enrichment
for result in enriched_results:
    if result.content:
        print(f"✓ Fetched {result.tokens_estimate} tokens from {result.url}")
    else:
        print(f"✗ Using snippet only for {result.url}")
```

## Observability

### Stats and Monitoring

```python
from backend.src.services.web_fetch_service import get_web_fetch_service

fetch_service = get_web_fetch_service()
stats = fetch_service.get_stats()

print(f"Fetched: {stats['fetched_count']}")
print(f"Cache hits: {stats['cache_hits']}")
print(f"Cache hit rate: {stats['cache_hit_rate']:.2%}")
print(f"Failures: {stats['failures']}")
print(f"Avg fetch time: {stats['avg_fetch_ms']:.0f}ms")
print(f"Available libraries: {stats['extraction_libs_available']}")
```

### Logging

The service logs at appropriate levels:

- **INFO**: Successful fetches, enrichment summary
- **DEBUG**: Cache hits, domain checks, extraction details
- **WARNING**: Fetch disabled due to missing httpx, extraction fallbacks
- **ERROR**: Network errors, HTTP errors

## Troubleshooting

### Web Fetch Not Working

**Issue**: `WEB_FETCH_ENABLED=true` but no enrichment happening

**Solution**:
1. Check httpx is installed: `pip install httpx`
2. Check logs for "Web fetch disabled" warnings
3. Verify environment variable is set correctly
4. Check stats: `fetch_service.get_stats()`

### Content Extraction Failing

**Issue**: Fetching URLs but no content extracted

**Solution**:
1. Install extraction libraries: `pip install beautifulsoup4 lxml`
2. For better extraction: `pip install trafilatura`
3. Check logs for extraction failures
4. Verify content-type is supported (HTML, PDF)

### Rate Limiting

**Issue**: Many "Rate limit exceeded" errors

**Solution**:
1. Reduce `WEB_FETCH_MAX_FETCH` (default: 3)
2. The service uses per-domain rate limiting (5 req/min by default)
3. Cache helps—only first request to a URL is fetched

### Domains Blocked

**Issue**: Specific domains not being fetched

**Solution**:
1. Check `WEB_FETCH_BLOCKLIST_DOMAINS`
2. If `WEB_FETCH_ALLOWLIST_DOMAINS` is set, domain must be in list
3. Review logs for "Domain blocked" messages

## Performance Considerations

### Concurrency

- Default: 5 concurrent fetches
- Increase for faster enrichment: `WEB_FETCH_CONCURRENCY=10`
- Don't set too high to avoid overwhelming target sites

### Timeouts

- Default: 8 seconds per request
- Adjust based on network: `WEB_FETCH_TIMEOUT_MS=5000`
- Balance between completeness and responsiveness

### Caching

- Fetch cache is separate from search cache
- Default TTL: 1 hour
- Cache size: max 200 entries (LRU-style eviction)
- Use `fetch_service.clear_cache()` to reset

### Token Budgets

- Fetched content is capped at ~10,000 chars per page
- Context preview limited to ~300 chars in web_search_context
- Token estimates capped at 3000 to prevent context overflow

## Security & Privacy

### User Agent

- Default: "LocalChatbot/1.0"
- Customize: `WEB_FETCH_USER_AGENT="MyBot/1.0 (+https://mysite.com)"`
- Be transparent about your bot

### Robots.txt

- Currently: Best-effort respect (not enforced)
- Recommendation: Use allow/block lists for sensitive domains

### Data Privacy

- No external data is sent during fetch (only HTTP GET)
- Fetched content cached locally only
- No tracking or analytics

### Safety Features

- Content size limits (2MB default)
- Timeout protection (8s default)
- Per-domain rate limiting (5 req/min)
- Graceful error handling—never breaks existing flow

## Testing

### Unit Tests

```bash
cd backend
uv run pytest tests/unit/test_web_fetch_service.py -v
```

Tests cover:
- Caching behavior
- Rate limiting
- Domain allow/block lists
- Error handling (timeouts, HTTP errors)
- Extraction fallbacks

### Integration Testing

```bash
# Enable web fetch for testing
export WEB_FETCH_ENABLED=true

# Run web search integration test
uv run python test_web_search_rag.py
```

### Manual Testing

```python
import asyncio
from backend.src.services.web_fetch_service import get_web_fetch_service

async def test():
    service = get_web_fetch_service()
    result = await service.fetch_url("https://example.com")
    
    print(f"URL: {result.url}")
    print(f"Canonical: {result.canonical_url}")
    print(f"Title: {result.title}")
    print(f"Content length: {len(result.content) if result.content else 0}")
    print(f"Tokens: {result.tokens_estimate}")
    print(f"Error: {result.error}")

asyncio.run(test())
```

## Backward Compatibility

### Guaranteed Compatibility

- **Default behavior unchanged**: Web fetch is OFF by default
- **Existing tests pass**: No breaking changes to SearchResult or APIs
- **Optional fields**: New SearchResult fields only appear when enriched
- **Graceful degradation**: Missing libraries don't break the system

### Migration Path

1. **Phase 1**: Deploy with `WEB_FETCH_ENABLED=false` (default)
2. **Phase 2**: Install optional deps on a test instance
3. **Phase 3**: Enable on test: `WEB_FETCH_ENABLED=true`
4. **Phase 4**: Monitor stats and logs
5. **Phase 5**: Roll out to production when confident

## LangChain Tools (Optional)

Web search and fetch capabilities are exposed as LangChain-compatible tools for agent workflows.

### WebSearchTool

Searches the web and returns formatted results:

```python
from backend.src.tools.web_search_tool import get_web_search_tool

# Get tool instance
tool = get_web_search_tool()

# Use directly
result = tool.run("latest AI news")
print(result)

# Or use with LangChain agent
from langchain.agents import initialize_agent, AgentType
from langchain_community.llms import OpenAI

llm = OpenAI(temperature=0)
agent = initialize_agent([tool], llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION)
response = agent.run("Find information about llama.cpp")
```

### WebFetchTool

Fetches and extracts content from a specific URL:

```python
from backend.src.tools.web_fetch_tool import get_web_fetch_tool

# Get tool instance
tool = get_web_fetch_tool()

# Fetch content
result = tool.run("https://example.com/article")
print(result)
```

### Web Agent (Complete Example)

Pre-configured agent with both tools:

```python
from backend.src.agents.web_agent import get_web_agent

# Create agent (requires llama.cpp server or OpenAI-compatible endpoint)
agent = get_web_agent(
    model_endpoint="http://localhost:8080/v1",  # Optional, defaults to localhost
    model_name="local-llama",  # Optional
    verbose=True
)

if agent:
    # Ask questions that require web search
    response = agent.run("What are the latest developments in llama.cpp?")
    print(response)
    
    # The agent will automatically:
    # 1. Use web_search to find relevant URLs
    # 2. Use web_fetch to get full content if needed
    # 3. Synthesize a final answer
```

### Environment Variables for Agents

```bash
# LLM endpoint for agent (default: http://localhost:8080/v1)
export AGENT_LLM_ENDPOINT="http://localhost:8080/v1"

# Model name (default: local-llama)
export AGENT_LLM_MODEL="llama-3-8b"
```

### Starting llama.cpp Server

For agent usage, start llama.cpp with OpenAI-compatible API:

```bash
# Start llama-server with OpenAI API
llama-server --model ./models/llama-3-8b.Q4_K_M.gguf \
  --host 127.0.0.1 --port 8080 --api-type openai
```

### Tool Dependencies

```bash
# Install LangChain for tools
pip install langchain langchain-community

# Optional: for async support in notebooks
pip install nest-asyncio
```

### Testing Tools

```bash
# Test web search tool
cd backend
uv run python -c "from src.tools.web_search_tool import get_web_search_tool; tool = get_web_search_tool(); print(tool.run('llama.cpp'))"

# Test web agent (requires llama.cpp server)
uv run python src/agents/web_agent.py
```

## Future Enhancements

Potential future additions (not yet implemented):

- Persistent cache (SQLite/Redis) across restarts
- Content summarization for very long pages
- Robots.txt strict enforcement
- JavaScript rendering for SPA sites (via Playwright/Selenium)
- Hybrid search mode (combine multiple providers)
- MCP tool exposure for external agents

## Support

For issues or questions:
- Check logs for detailed error messages
- Review stats: `get_web_fetch_service().get_stats()`
- Ensure httpx and extraction libraries are installed
- Verify environment variables are set correctly

## Related Documentation

- [WEB_SEARCH_IMPLEMENTATION_PLAN.md](./WEB_SEARCH_IMPLEMENTATION_PLAN.md) - Web search architecture
- [TAVILY_SETUP.md](./TAVILY_SETUP.md) - Tavily API configuration
- [WARP.md](../../WARP.md) - Development guide
