# Deep Research Agent - Full Implementation Plan

## Current Status Analysis

### ✅ What's Working
1. **LangGraph Infrastructure**: `deep_research_graph.py` has a complete graph-based implementation
2. **Enhanced Prompt Template**: `deep_research_synthesis.txt` provides structured output
3. **Tavily API**: API key is configured and package is installed
4. **Web Search Service**: Has TavilyProvider implementation with advanced search

### ❌ What's NOT Working
1. **Provider Selection**: `WEB_SEARCH_PROVIDER=serpapi` is set, blocking Tavily
2. **Streaming**: `run_deep_research_stream()` doesn't emit events properly for UI
3. **Deep Research Agent**: Might be falling back to simple web orchestrator
4. **Tavily Configuration**: Not using Tavily-specific features (search_depth, topic, etc.)

---

## Root Causes

### Issue #1: Web Search Provider Override
**File**: `backend/.env`
**Problem**: `WEB_SEARCH_PROVIDER=serpapi` overrides the auto-detection logic
**Impact**: Even though Tavily key is set, SerpAPI is being used (and may be failing)

### Issue #2: Deep Research Not Running
**File**: `backend/src/agents/deep_research_agent.py` (lines 40-44)
**Problem**: Falls back to `WebResearchOrchestrator` if GROQ_API_KEY is missing
**Impact**: The LangGraph-based agent never runs

### Issue #3: Streaming Not Implemented
**File**: `backend/src/agents/deep_research_agent.py` (lines 65-76)
**Problem**: `run_deep_research_stream()` just yields final result, no step-by-step events
**Impact**: UI doesn't show progress (planning, investigating, synthesizing steps)

### Issue #4: Tavily Features Underutilized
**File**: `backend/src/agents/deep_research_graph.py` (line 186)
**Problem**: Only uses `web_search.search(query, max_results=3)` - basic parameters
**Impact**: Missing Tavily's advanced features:
- `search_depth="advanced"` for deeper, fresher results
- `topic="general"` or `"news"` for specialized searches
- `include_raw_content=True` for detailed content
- `time_range` for temporal queries

---

## Implementation Plan

### Phase 1: Configure Tavily as Primary Provider ⚡ CRITICAL

**Goal**: Switch from SerpAPI to Tavily for all web searches

**Changes Required**:
1. Update `.env` to set `WEB_SEARCH_PROVIDER=tavily`
2. Verify Tavily connectivity with a test script
3. Restart backend to load new configuration

**Files Modified**:
- `backend/.env`

**Verification**:
```bash
curl http://localhost:8000/api/tools/web-search/health
# Should show: "provider": "tavily"
```

---

### Phase 2: Enhance Deep Research Graph with Tavily Features 🚀

**Goal**: Make Deep Research use Tavily-specific optimizations

**Changes Required**:

#### 2.1: Update `investigate_node` to Use Tavily Features
**File**: `backend/src/agents/deep_research_graph.py`

**Current** (lines 184-193):
```python
async def search_single(query):
    try:
        results = await web_search.search(query, max_results=3)
        # ...
```

**Enhanced**:
```python
async def search_single(query):
    try:
        # Detect if query needs news/temporal context
        is_temporal = any(kw in query.lower() for kw in ['latest', 'recent', 'news', 'today', '2024', '2025'])
        
        # Use Tavily-specific parameters if available
        search_kwargs = {"max_results": 5}  # Increase from 3 to 5
        
        # If provider is Tavily, add advanced params
        if hasattr(web_search.primary_provider, 'name') and web_search.primary_provider.name == 'tavily':
            search_kwargs["search_depth"] = "advanced"  # Key for fresh results
            if is_temporal:
                search_kwargs["topic"] = "news"  # Optimize for recent news
        
        results = await web_search.search(query, **search_kwargs)
        # ...
```

#### 2.2: Add Direct Tavily Integration (Optional Turbo Mode)
**File**: Create `backend/src/agents/tavily_deep_research.py`

This would be a specialized version that directly uses Tavily's Python SDK for maximum control:

```python
from tavily import AsyncTavilyClient

async def tavily_deep_search(query: str, max_results: int = 5):
    """Direct Tavily integration for deep research"""
    client = AsyncTavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    
    response = await client.search(
        query=query,
        max_results=max_results,
        search_depth="advanced",  # Critical for quality
        include_raw_content=True,  # Get full content
        include_images=False,  # Save bandwidth
        topic="general"  # or "news" for temporal queries
    )
    
    return response['results']
```

---

### Phase 3: Fix Streaming for Real-Time UI Updates 📡

**Goal**: Show progress in UI (Planning → Investigating → Synthesizing)

**File**: `backend/src/agents/deep_research_agent.py`

**Current** (lines 65-76):
```python
async def run_deep_research_stream(...):
    result = await run_deep_research(query, model_name, max_iterations)
    yield result.get("answer", "")
```

**Enhanced**:
```python
async def run_deep_research_stream(query: str, model_name: str = None, max_iterations: int = 3):
    """Streaming version with step-by-step events"""
    
    # Emit planning event
    yield {"event": "step", "data": {"step": "Planning research queries..."}}
    
    # Run graph with callbacks
    from .deep_research_graph import run_deep_research_graph_stream
    
    async for event in run_deep_research_graph_stream(query, max_iterations):
        yield event  # Events like: {"event": "step", "data": {...}}
    
    # Emit final result
    yield {"event": "final", "data": {"answer": result["answer"], "citations": result["citations"]}}
```

**File**: `backend/src/agents/deep_research_graph.py`

**Add New Function**:
```python
async def run_deep_research_graph_stream(query: str, max_iterations: int = 1):
    """Streaming version that emits events for each step"""
    graph = create_research_graph()
    
    initial_state = {
        "query": query,
        "plan": [],
        "findings": [],
        "draft": "",
        "critique": None,
        "iteration": 0,
        "max_iterations": max_iterations
    }
    
    # Emit planning step
    yield {"event": "step", "data": {"step": "plan", "message": "Creating research plan..."}}
    
    # Run nodes one by one with event emission
    # (This requires modifying the graph to support streaming or using manual invocation)
    
    for step_name in ["plan", "investigate", "synthesize"]:
        yield {"event": "step", "data": {"step": step_name, "message": f"Running {step_name}..."}}
        # ... execute step ...
    
    # Final event with complete result
    citations = parse_citations_from_draft(final_state["draft"])
    
    yield {
        "event": "final",
        "data": {
            "answer": final_state["draft"],
            "citations": citations,
            "metadata": {
                "iterations": final_state["iteration"],
                "model": "groq:openai/gpt-oss-120b"
            }
        }
    }
```

---

### Phase 4: Verify GROQ_API_KEY and Remove Fallback 🔐

**File**: `backend/src/agents/deep_research_agent.py` (lines 40-44)

**Problem**: Fallback to simple orchestrator defeats the purpose

**Current**:
```python
if not os.getenv("GROQ_API_KEY"):
    logger.warning("GROQ_API_KEY not found. Falling back to simple search.")
    from src.services.web_research_orchestrator import WebResearchOrchestrator
    orchestrator = WebResearchOrchestrator()
    return await orchestrator.run(query)
```

**Enhanced**:
```python
if not os.getenv("GROQ_API_KEY"):
    raise ValueError(
        "GROQ_API_KEY is required for Deep Research. "
        "Please set it in your .env file or disable Deep Research."
    )
```

**Justification**: Better to fail fast and inform user than silently fall back to inferior mode

---

## Priority Order

### 🔥 IMMEDIATE (Phase 1)
1. Change `.env`: `WEB_SEARCH_PROVIDER=tavily`
2. Restart backend
3. Test: `curl http://localhost:8000/api/tools/web-search/test -X POST -H "Content-Type: application/json" -d '{"q":"latest AI news"}'`

### 🚀 HIGH (Phase 2)
4. Update `investigate_node` to use Tavily `search_depth="advanced"`
5. Add temporal query detection for `topic="news"`

### 💡 MEDIUM (Phase 3)
6. Implement streaming events for UI feedback
7. Update frontend to show progress

### 🔧 LOW (Phase 4)
8. Remove fallback logic (make GROQ_API_KEY required)
9. Add direct Tavily SDK integration (optional turbo mode)

---

## Testing Plan

### Test 1: Provider Verification
```bash
cd backend
uv run python -c "
from src.services.web_search_service import get_web_search_service
svc = get_web_search_service()
print('Provider:', svc.provider_name)
print('Primary:', svc.primary_provider.name if svc.primary_provider else 'None')
"
```
**Expected**: `Provider: tavily`, `Primary: tavily`

### Test 2: Deep Research End-to-End
```bash
cd backend
uv run python test_deep_agent_manual.py
```
**Expected**: 
- Uses Tavily for searches
- Generates structured report
- Returns 5+ citations

### Test 3: UI Integration
1. Open `http://localhost:3000`
2. Click `+` → `Deep Research`
3. Ask: "What are the latest advancements in quantum computing in 2025?"
4. Verify:
   - Progress indicators show
   - Results appear with citations
   - Citations link to real sources

---

## Success Criteria

✅ **Tavily is Primary Provider**: Health endpoint shows `"provider": "tavily"`
✅ **Advanced Search Used**: Logs show `search_depth=advanced`  
✅ **Quality Results**: Queries return specific, recent, relevant articles (not generic homepages)
✅ **Structured Output**: Reports have Summary, Analysis, Insights, Sources sections
✅ **Working Citations**: Citations parse correctly and link to actual sources
✅ **UI Streaming**: Frontend shows "Planning...", "Investigating...", "Synthesizing..." steps
✅ **No Fallbacks**: Deep Research runs the LangGraph, not WebResearchOrchestrator

---

## Files to Modify

1. `backend/.env` - Set `WEB_SEARCH_PROVIDER=tavily`
2. `backend/src/agents/deep_research_graph.py` - Enhance Tavily usage in `investigate_node`
3. `backend/src/agents/deep_research_agent.py` - Implement streaming, remove fallback
4. `frontend/src/app/page.tsx` - Update streaming event handlers (already exists, verify)

---

## Next Steps

**Ready to implement?** I can start with Phase 1 (switch to Tavily) immediately.
Would you like me to proceed with the implementation?
