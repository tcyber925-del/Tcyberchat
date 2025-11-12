# Configure Tavily API for Better Web Search Results

## Quick Setup Guide

### Step 1: Get Tavily API Key
1. Visit https://tavily.com
2. Sign up for a free account (or use existing account)
3. Go to Dashboard → API Keys
4. Copy your API key (starts with `tvly-`)

### Step 2: Set Environment Variable

**Option A: PowerShell (Recommended for Windows)**
```powershell
# Set for current session
$env:TAVILY_API_KEY="tvly-your-api-key-here"

# Set permanently (requires restart)
[System.Environment]::SetEnvironmentVariable('TAVILY_API_KEY', 'tvly-your-api-key-here', 'User')
```

**Option B: Command Prompt (CMD)**
```cmd
set TAVILY_API_KEY=tvly-your-api-key-here
```

**Option C: Create .env File**
1. Copy `backend/.env.example` to `backend/.env`
2. Edit `backend/.env` and add your API key:
   ```
   TAVILY_API_KEY=tvly-your-api-key-here
   WEB_SEARCH_PROVIDER=tavily
   ```
3. The backend will automatically load this file

**Option D: System Environment Variables (Windows)**
1. Press `Win + R`, type `sysdm.cpl`, press Enter
2. Go to "Advanced" tab → "Environment Variables"
3. Under "User variables", click "New"
4. Variable name: `TAVILY_API_KEY`
5. Variable value: `tvly-your-api-key-here`
6. Click OK and restart your terminal/IDE

### Step 3: Install Tavily Package
```bash
cd backend
uv pip install tavily-python
# OR
pip install tavily-python
```

### Step 4: Verify Configuration
```bash
cd backend
python test_tavily_config.py
```

You should see:
```
✓ TAVILY_API_KEY is set
✓ Tavily provider is available
✓ Found X results
```

### Step 5: Test with RAG
```bash
python test_web_search_rag.py
```

You should see:
- Provider: tavily
- Primary available: True
- Better quality results

## Benefits of Tavily

✅ **Better Relevance**: Results optimized for LLM/RAG use cases  
✅ **Fresher Results**: Advanced search depth for recent information  
✅ **Structured Data**: Includes direct answers when available  
✅ **More Reliable**: Better API than free alternatives  
✅ **Better for AI**: Designed specifically for AI applications  

## Troubleshooting

### "TAVILY_API_KEY not set"
- Make sure you've set the environment variable
- Restart your terminal/IDE after setting
- Check that `.env` file is in the `backend/` directory

### "Tavily provider not available"
- Verify API key is correct
- Check that `tavily-python` is installed: `pip install tavily-python`
- Test API key directly: `python -c "from tavily import TavilyClient; print('OK')"`

### Still using DuckDuckGo?
- Set `WEB_SEARCH_PROVIDER=tavily` in environment or `.env`
- Restart the backend server
- Check logs to see which provider is being used

## Testing After Configuration

1. **Test Tavily directly:**
   ```bash
   python test_tavily_config.py
   ```

2. **Test with RAG:**
   ```bash
   python test_web_search_rag.py
   ```

3. **Test in frontend:**
   - Enable web search toggle
   - Ask: "what is the latest AI news?"
   - Check that results are more relevant and recent

## Example API Key Format
```
tvly-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Your API key should start with `tvly-` and be about 40+ characters long.


