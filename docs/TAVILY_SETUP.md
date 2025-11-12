# Tavily API Configuration Guide

## Overview
Tavily provides better, more accurate web search results compared to DuckDuckGo, especially for AI/RAG use cases. It's designed specifically for retrieving information for LLMs.

## Setup Instructions

### 1. Get Tavily API Key
1. Visit https://tavily.com
2. Sign up for an account
3. Navigate to API Keys section
4. Copy your API key

### 2. Configure Environment Variable

#### Option A: Environment Variable (Recommended)
```bash
# Windows (PowerShell)
$env:TAVILY_API_KEY="your-api-key-here"

# Windows (CMD)
set TAVILY_API_KEY=your-api-key-here

# Linux/Mac
export TAVILY_API_KEY="your-api-key-here"
```

#### Option B: .env File
Create or edit `backend/.env`:
```
TAVILY_API_KEY=your-api-key-here
WEB_SEARCH_PROVIDER=tavily
```

#### Option C: System Environment Variables
Add to your system environment variables permanently.

### 3. Install Tavily Package
```bash
cd backend
uv pip install tavily-python
# OR
pip install tavily-python
```

### 4. Verify Configuration
Run the test script:
```bash
python test_web_search_rag.py
```

You should see:
- Provider: tavily
- Primary available: True

## Benefits of Tavily

1. **Better Relevance**: Results are optimized for LLM/RAG use cases
2. **Fresher Results**: Advanced search depth provides more recent information
3. **Structured Data**: Includes direct answers when available
4. **Better API**: More reliable and consistent than free alternatives

## Configuration Options

### Environment Variables
- `TAVILY_API_KEY`: Your Tavily API key (required)
- `WEB_SEARCH_PROVIDER`: Set to "tavily" to use Tavily as primary (default: "duckduckgo")
- `WEB_SEARCH_CACHE_TTL`: Cache TTL in seconds (default: 3600)
- `WEB_SEARCH_RATE_LIMIT`: Rate limit per minute (default: 10)

### Example Configuration
```bash
TAVILY_API_KEY=tvly-xxxxxxxxxxxxx
WEB_SEARCH_PROVIDER=tavily
WEB_SEARCH_CACHE_TTL=3600
WEB_SEARCH_RATE_LIMIT=10
```

## Testing

After configuration, test with:
```bash
python test_web_search_rag.py
```

Or test directly:
```python
from src.services.web_search_service import get_web_search_service
import asyncio

async def test():
    service = get_web_search_service()
    results = await service.search("latest AI news 2024", max_results=5)
    print(f"Found {len(results)} results")
    for r in results:
        print(f"- {r.title}: {r.url}")

asyncio.run(test())
```

## Troubleshooting

### Issue: "Tavily provider not available"
- Check that `TAVILY_API_KEY` is set correctly
- Verify the API key is valid
- Check that `tavily-python` is installed

### Issue: "No web search providers available"
- Install either `duckduckgo-search` or configure `TAVILY_API_KEY`
- Check environment variables are loaded

### Issue: Rate limiting
- Tavily has rate limits based on your plan
- Adjust `WEB_SEARCH_RATE_LIMIT` if needed
- Consider upgrading your Tavily plan for higher limits


