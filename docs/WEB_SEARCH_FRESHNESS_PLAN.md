# Web Search Freshness and Grounding Enhancement Plan

## Problem Statement

The current web search implementation returns outdated results for time-sensitive queries like "what is the latest AI news?". This plan addresses the root causes and implements comprehensive fixes to ensure fresh, grounded responses.

## Root Causes Identified

1. **Aggressive Caching**: Default cache TTL of 3600 seconds (1 hour) prevents fresh results for "latest" queries
2. **Suboptimal Search Configuration**: Tavily provider not using optimal parameters for freshness (search_depth, include_answer)
3. **No Query Enhancement**: Time-sensitive queries not enhanced with temporal keywords
4. **Context Prioritization**: Web search results appended after document context, not prioritized for time-sensitive queries
5. **Weak Prompt Engineering**: LLM not explicitly instructed to prioritize recent web search results
6. **No Query Analysis**: System doesn't detect time-sensitive queries to apply special handling

## Comprehensive Solution

### Phase 1: Web Search Service Enhancements

#### 1.1 Dynamic Cache Management
- **Problem**: 1-hour cache TTL too long for "latest" queries
- **Solution**: 
  - Detect time-sensitive queries (contains "latest", "recent", "news", "update", "what's new", "current")
  - Disable cache or use very short TTL (60 seconds) for time-sensitive queries
  - Keep longer TTL for general queries
- **Files**: `backend/src/services/web_search_service.py`

#### 1.2 Query Enhancement
- **Problem**: Raw queries may not optimize for freshness
- **Solution**:
  - For time-sensitive queries, enhance with temporal keywords (e.g., "latest AI news 2024")
  - Add current year/month for better recency
  - Preserve original query intent
- **Files**: `backend/src/services/web_search_service.py`

#### 1.3 Tavily Configuration Optimization
- **Problem**: Not using optimal Tavily parameters for freshness
- **Solution**:
  - Use `search_depth="advanced"` for better recency
  - Enable `include_answer=True` for direct answers
  - Increase `max_results` for time-sensitive queries
- **Files**: `backend/src/services/web_search_service.py`

### Phase 2: RAG Pipeline Integration

#### 2.1 Query Analysis
- **Problem**: System doesn't detect time-sensitive queries
- **Solution**:
  - Implement heuristic to detect time-sensitive queries
  - Keywords: "latest", "recent", "news", "update", "what's new", "current", "today", "now"
  - Return `is_time_sensitive` flag
- **Files**: `backend/src/services/rag_service.py`

#### 2.2 Dynamic Context Prioritization
- **Problem**: Web search context appended after document context
- **Solution**:
  - For time-sensitive queries: prioritize web search context (place first)
  - For general queries: balanced approach (web search first, then documents)
  - Reduce document chunks if web search results are abundant and relevant
- **Files**: `backend/src/services/rag_service.py`

#### 2.3 Enhanced Prompt Engineering
- **Problem**: LLM not explicitly instructed to prioritize recent web search
- **Solution**:
  - Add explicit instructions to prioritize "Web Search Results" section
  - Instruct LLM to state "According to web search..." when using web sources
  - For "latest" queries, emphasize using most up-to-date data
  - Clear structure: Web Search Results first, then Document Context
- **Files**: `backend/src/services/rag_service.py`

#### 2.4 Improved Citation Handling
- **Problem**: Web citations not prominently distinguished
- **Solution**:
  - Ensure web citations have `source: "web_search"` and `url`
  - Present web citations prominently in response
  - Add visual distinction in frontend (globe icon, clickable links)
- **Files**: `backend/src/services/rag_service.py`, `frontend/src/components/ui/chat.tsx`

### Phase 3: Logging and Debugging

#### 3.1 Enhanced Logging
- **Problem**: Insufficient logging to diagnose outdated results
- **Solution**:
  - Log exact query sent to web search
  - Log raw results received (URLs, snippets, timestamps)
  - Log web_search_context string passed to LLM
  - Log citations generated
  - Log cache hits/misses
- **Files**: `backend/src/services/web_search_service.py`, `backend/src/services/rag_service.py`

### Phase 4: Frontend Enhancements

#### 4.1 Web Search Citation Display
- **Problem**: Web citations not visually distinct
- **Solution**:
  - Display web citations with globe icon
  - Make URLs clickable
  - Show "Web Source" label
  - Group web citations separately from document citations
- **Files**: `frontend/src/components/ui/chat.tsx`, `frontend/src/components/ui/markdown-renderer.tsx`

#### 4.2 Web Search Status Indicator
- **Problem**: User may not know web search is active
- **Solution**:
  - Show "Searching the web..." indicator during search
  - Display "Web search enabled" badge when active
  - Show number of web results found
- **Files**: `frontend/src/app/page.tsx`

## Implementation Strategy

### Step 1: Web Search Service Enhancements
1. Add `is_time_sensitive_query()` helper function
2. Add `enhance_query_for_freshness()` function
3. Modify `search()` to disable cache for time-sensitive queries
4. Optimize Tavily provider with better parameters
5. Add enhanced logging

### Step 2: RAG Service Integration
1. Add query analysis function
2. Modify context building to prioritize web search for time-sensitive queries
3. Enhance prompts with explicit instructions
4. Improve citation handling
5. Add comprehensive logging

### Step 3: Frontend Updates
1. Enhance citation display for web sources
2. Add web search status indicators
3. Improve visual distinction

### Step 4: Testing
1. Test time-sensitive queries ("latest AI news")
2. Test general queries (should still work)
3. Verify cache behavior
4. Verify citation display
5. Regression testing

## Backward Compatibility

All changes maintain backward compatibility:
- Default behavior unchanged for non-time-sensitive queries
- Cache still works for general queries
- Document-only RAG still works
- Web search remains optional (opt-in)
- No breaking API changes

## Success Criteria

1. ✅ Time-sensitive queries return fresh results (no stale cache)
2. ✅ Web search results prioritized for "latest" queries
3. ✅ LLM explicitly cites web sources
4. ✅ Citations clearly distinguish web vs document sources
5. ✅ No existing functionality broken
6. ✅ Comprehensive logging for debugging

## Configuration Options

New environment variables:
- `WEB_SEARCH_CACHE_TTL_TIME_SENSITIVE`: Cache TTL for time-sensitive queries (default: 60 seconds)
- `WEB_SEARCH_ENABLE_QUERY_ENHANCEMENT`: Enable query enhancement (default: true)
- `WEB_SEARCH_TAVILY_SEARCH_DEPTH`: Tavily search depth ("basic" or "advanced", default: "advanced")


