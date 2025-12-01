# Tavily Setup Instructions

## Current Status

- **TAVILY_API_KEY**: ✓ Configured (dev key)
- **Issue**: Dev API key has restrictions (ForbiddenError)
- **Provider Setting**: Currently set to `serpapi` (which is failing)

## Solution Options

### Option 1: Get Production Tavily Key (RECOMMENDED)

1. Go to: https://tavily.com
2. Sign up or login
3. Upgrade from dev to production key (may have free tier)
4. Update `.env`:
   ```env
   TAVILY_API_KEY=tvly-your-production-key-here
   ```

### Option 2: Remove Provider Restriction (IMMEDIATE FIX)

Since SerpAPI is failing and Tavily dev key has limits, let DuckDuckGo work properly:

1. Edit `backend/.env`
2. Comment out or remove the `WEB_SEARCH_PROVIDER` line:
   ```env
   # WEB_SEARCH_PROVIDER=serpapi  <- Comment this out
   ```
3. Or set it to `duckduckgo`:
   ```env
   WEB_SEARCH_PROVIDER=duckduckgo
   ```

4. Restart the backend server

This will allow the system to use DuckDuckGo.which is working (just with variable quality).

### Option 3: Fix SerpAPI

If you have a SerpAPI key:

1. Verify `SERPAPI_API_KEY` is set in `.env`
2. Install: `uv pip install google-search-results`
3. Restart backend

## Quick Action (Recommended Now)

**Set provider to `duckduckgo` to unblock immediately:**

```bash
# In backend directory
# Edit .env and change:
WEB_SEARCH_PROVIDER=duckduckgo

# Then restart backend (Ctrl+C in terminal, then):
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## What This Means

DuckDuckGo will work, but results may be generic for complex "latest/recent" queries. 

**For Production**: Get a working Tavily production key or SerpAPI key for best results.

**For Testing Now**: Use DuckDuckGo with simpler queries:
- ✓ "solid state battery technology"
- ✓ "solid state battery companies 2024"
- ✗ "What are the latest advancements in solid state batteries?"
