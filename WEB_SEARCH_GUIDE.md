# Web Search Feature Guide

## Overview

The TcyberChatbot now includes intelligent web search capabilities that automatically fetch real-time information from the internet when needed.

## How to Use Web Search

### Option 1: Automatic Detection (Recommended) ✨

The chatbot **automatically enables web search** when it detects queries that need current information. Simply type your question naturally, and if it contains time-sensitive keywords, web search will activate automatically.

**Keywords that trigger auto web search:**
- `latest`, `recent`, `news`, `today`, `current`, `now`
- `this week`, `this month`, `2024`, `2025`, `update`
- `what is`, `what are`, `who is`, `when did`

**Examples:**
- ✅ "What is the latest AI news?" → Web search AUTO
- ✅ "What are recent developments in quantum computing?" → Web search AUTO
- ✅ "Who is the current president?" → Web search AUTO
- ✅ "What happened today in technology?" → Web search AUTO

### Option 2: Manual Toggle

You can also manually enable web search for any query:

1. Click the **"+"** button next to the message input
2. Click **"Web search"** in the popup menu
3. Type your question
4. Send (web search will be enabled for this message only)

### Visual Indicators

- 🌐 **"Web"** badge: Web search is enabled
- 🌐 **"Web AUTO"** badge: Web search was auto-detected and will be used
- No badge: Regular chat (no web search)

## Configuration

### Environment Variables

Make sure you have at least one search provider configured in your `.env`:

```bash
# Option 1: SerpAPI (Recommended - Real Google results)
SERPAPI_API_KEY=your_serpapi_key_here

# Option 2: Tavily (AI-optimized search)
TAVILY_API_KEY=your_tavily_key_here

# Option 3: DuckDuckGo (Free, no API key needed)
# No configuration needed - works out of the box!
```

### Provider Priority

The system uses providers in this order:
1. **SerpAPI** (if `SERPAPI_API_KEY` is set)
2. **Tavily** (if `TAVILY_API_KEY` is set)
3. **DuckDuckGo** (always available as fallback)

## Troubleshooting

### "503 The model is overloaded"

This error means:
- Your AI model is busy/overloaded
- **This is NOT a web search issue**
- Wait a moment and try again

### "I don't have real-time capabilities"

This message means:
- **Web search was NOT enabled** for your query
- Try using keywords like "latest", "recent", "news", "today"
- Or manually enable web search using the + button

### Web Search Not Working

**Check:**

1. **Is web search enabled?**
   - Look for the 🌐 "Web" or "Web AUTO" badge before sending
   - If not visible, your query didn't trigger auto-detection

2. **Do you have an API key configured?**
   - Check `.env` file has `SERPAPI_API_KEY` or `TAVILY_API_KEY`
   - DuckDuckGo works without API key but may be rate-limited

3. **Backend running?**
   - Make sure backend is running: `cd backend && python main.py`
   - Check backend logs for errors

4. **Test the provider:**
   ```bash
   # In backend directory
   python -m pytest tests/unit/test_serpapi_provider.py -v
   # Or
   python -m pytest tests/unit/test_web_search_service.py -v
   ```

## Examples

### Good Queries (Auto Web Search)

```
✅ "What is the latest news about AI?"
✅ "What are the recent updates to ChatGPT?"
✅ "Who is the current CEO of OpenAI?"
✅ "What happened today in the stock market?"
✅ "What is the latest version of Python?"
```

### Queries That Need Manual Toggle

```
⚠️ "Tell me about AI" (too general, no time indicator)
⚠️ "Explain machine learning" (educational, not time-sensitive)
⚠️ "How does a computer work?" (general knowledge)
```

For these, click **+ → Web search** to enable it manually.

## API Keys Setup

### Get SerpAPI Key (Recommended)

1. Sign up: [serpapi.com/users/sign_up](https://serpapi.com/users/sign_up)
2. Get key: [serpapi.com/manage-api-key](https://serpapi.com/manage-api-key)
3. Free tier: 100 searches/month
4. Add to `.env`: `SERPAPI_API_KEY=your_key_here`

### Get Tavily Key

1. Sign up: [tavily.com](https://tavily.com)
2. Get API key from dashboard
3. Add to `.env`: `TAVILY_API_KEY=your_key_here`

### Use DuckDuckGo (Free)

- No API key needed!
- Already works out of the box
- May be rate-limited under heavy use
- Good for development and testing

## Technical Details

- **Auto-detection**: Client-side keyword matching
- **Provider fallback**: SerpAPI → Tavily → DuckDuckGo
- **Citations**: Web search results include source URLs
- **Caching**: Results cached for 1 hour (configurable)
- **Rate limiting**: 10 requests/minute (configurable)

## Support

For more details, see:
- `SERPAPI_QUICKSTART.md` - Quick setup guide
- `backend/docs/SERPAPI_MIGRATION.md` - Complete migration guide
- `backend/docs/WEB_FETCH.md` - Technical documentation

---

**Happy searching! 🚀**
