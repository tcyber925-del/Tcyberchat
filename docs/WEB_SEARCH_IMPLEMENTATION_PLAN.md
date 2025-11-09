# Web Search Implementation Plan

## Overview
This document outlines the plan to add web search functionality to the chatbot backend, allowing the AI to search the internet for real-time information when answering questions.

## Goals
1. Add web search capability to enhance AI responses with real-time information
2. Integrate seamlessly with existing RAG pipeline
3. Make web search optional and configurable
4. Ensure no breaking changes to existing functionality
5. Support multiple web search providers with fallback options

## Architecture Design

### 1. Web Search Service Layer
**Location**: `backend/src/services/web_search_service.py`

**Responsibilities**:
- Abstract interface for web search providers
- Support multiple providers (DuckDuckGo, Tavily, SerpAPI)
- Handle rate limiting and error handling
- Cache results to reduce API calls
- Format search results for RAG integration

**Key Methods**:
```python
async def search(query: str, max_results: int = 5) -> List[SearchResult]
async def search_with_sources(query: str, max_results: int = 5) -> Dict[str, Any]
```

### 2. Integration Points

#### A. RAG Service Integration
- Add optional web search to RAG pipeline
- Use web search when:
  - Document search returns no results
  - Query appears to need real-time information (detected via keywords/patterns)
  - User explicitly requests web search
- Combine web search results with document context

#### B. Chat API Integration
- Add optional `enable_web_search` parameter to chat requests
- Add `web_search_enabled` setting in user settings
- Return web search sources in citations

### 3. Search Result Format
```python
class SearchResult:
    title: str
    url: str
    snippet: str
    source: str  # "web_search"
    relevance_score: float
    timestamp: datetime
```

## Implementation Phases

### Phase 1: Core Web Search Service (Non-Breaking)
**Files to Create**:
- `backend/src/services/web_search_service.py`
- `backend/src/models/web_search.py` (if needed for database storage)

**Files to Modify**:
- `backend/requirements.txt` (add web search dependencies)

**Changes**:
1. Create `WebSearchService` class with provider abstraction
2. Implement DuckDuckGo provider (free, no API key required)
3. Add optional Tavily provider (better for AI, requires API key)
4. Add configuration via environment variables
5. Implement result caching (in-memory, optional Redis later)

**Testing**:
- Unit tests for web search service
- Mock web search responses
- Test error handling and fallbacks

### Phase 2: RAG Integration (Optional Enhancement)
**Files to Modify**:
- `backend/src/services/rag_service.py`
- `backend/src/api/chat.py`

**Changes**:
1. Add `use_web_search` parameter to RAG methods
2. Integrate web search results into RAG context
3. Update RAG prompts to handle web search results
4. Add web search citations to response

**Integration Logic**:
```python
# In generate_rag_streaming_response:
if use_web_search:
    web_results = await web_search_service.search(query)
    if web_results:
        # Add web results to context
        context += format_web_results(web_results)
```

### Phase 3: Chat API Enhancement
**Files to Modify**:
- `backend/src/api/chat.py`
- `backend/src/models/chat.py` (if needed)

**Changes**:
1. Add `enableWebSearch` field to `ChatRequest` model
2. Pass web search flag to RAG service
3. Include web search sources in response citations
4. Add web search metadata to response

### Phase 4: Configuration & Settings
**Files to Modify**:
- `backend/src/api/chat.py`
- Frontend settings (if applicable)

**Changes**:
1. Add environment variables for web search configuration
2. Add user-level web search toggle
3. Add rate limiting configuration
4. Add provider selection configuration

## Technical Details

### Web Search Providers

#### Option 1: DuckDuckGo (Recommended for MVP)
**Pros**:
- Free, no API key required
- Privacy-focused
- Good for general web search

**Cons**:
- Rate limiting may be stricter
- Less structured results

**Implementation**:
```python
pip install duckduckgo-search
```

#### Option 2: Tavily (Recommended for Production)
**Pros**:
- AI-optimized search
- Better structured results
- Good API limits

**Cons**:
- Requires API key
- Paid service (free tier available)

**Implementation**:
```python
pip install tavily-python
```

#### Option 3: SerpAPI
**Pros**:
- Very reliable
- Good for structured data

**Cons**:
- Requires API key
- Paid service

### Error Handling Strategy
1. **Provider Failures**: Fallback to next provider
2. **Rate Limiting**: Cache results, implement backoff
3. **Network Errors**: Graceful degradation, continue without web search
4. **Invalid Queries**: Return empty results, don't break chat flow

### Caching Strategy
- Cache search results for 1 hour (configurable)
- Key: query string (normalized)
- Store in memory (simple dict) or Redis (if available)
- Cache size limit to prevent memory issues

### Rate Limiting
- Configurable per provider
- Default: 10 requests per minute
- Implement token bucket algorithm

## API Changes

### Chat Request (Optional Addition)
```python
class ChatRequest(BaseModel):
    message: str
    conversationId: Optional[UUID] = None
    documentId: Optional[UUID] = None
    model: Optional[str] = None
    enableWebSearch: Optional[bool] = False  # NEW: Optional web search flag
```

### Chat Response (Enhanced)
```python
{
    "response": "...",
    "messageId": "...",
    "citations": [
        {
            "docId": "...",
            "snippet": "...",
            "source": "document"  # or "web_search"
        },
        {
            "url": "https://...",
            "title": "...",
            "snippet": "...",
            "source": "web_search"  # NEW
        }
    ],
    "webSearchUsed": true,  # NEW: Indicates if web search was used
    "webSearchResults": [...]  # NEW: Optional web search metadata
}
```

## Configuration

### Environment Variables
```bash
# Web Search Configuration
ENABLE_WEB_SEARCH=true  # Global enable/disable
WEB_SEARCH_PROVIDER=duckduckgo  # duckduckgo, tavily, serpapi
WEB_SEARCH_MAX_RESULTS=5
WEB_SEARCH_CACHE_TTL=3600  # seconds
WEB_SEARCH_RATE_LIMIT=10  # requests per minute

# Provider-specific API keys (optional)
TAVILY_API_KEY=...
SERPAPI_KEY=...
```

## Testing Strategy

### Unit Tests
- Test web search service with mocked responses
- Test provider fallback logic
- Test caching behavior
- Test error handling

### Integration Tests
- Test RAG with web search enabled
- Test chat API with web search
- Test citation formatting

### Manual Testing
- Test with various query types
- Test rate limiting
- Test error scenarios
- Test with web search disabled (ensure no breaking changes)

## Rollout Plan

### Step 1: Implement Core Service (Week 1)
- Create web search service
- Implement DuckDuckGo provider
- Add basic tests
- **No API changes yet** - service is isolated

### Step 2: Add Optional Integration (Week 2)
- Integrate with RAG service (optional parameter)
- Add to chat API (optional flag)
- Test thoroughly
- **Backward compatible** - defaults to disabled

### Step 3: Configuration & Polish (Week 3)
- Add environment variable configuration
- Add rate limiting
- Add caching
- Add monitoring/logging

### Step 4: Production Deployment
- Deploy with feature flag disabled by default
- Enable for testing users
- Monitor performance and errors
- Gradually enable for all users

## Risk Mitigation

### Breaking Changes Prevention
1. **All changes are optional** - web search is opt-in
2. **Default behavior unchanged** - web search disabled by default
3. **Graceful degradation** - if web search fails, continue without it
4. **Backward compatible API** - existing requests work without changes

### Performance Considerations
1. **Async implementation** - don't block on web search
2. **Timeout handling** - limit web search time (e.g., 5 seconds)
3. **Caching** - reduce redundant API calls
4. **Rate limiting** - prevent abuse

### Security Considerations
1. **Input validation** - sanitize search queries
2. **Rate limiting** - prevent abuse
3. **API key security** - store keys securely
4. **Content filtering** - optional content filtering for safety

## Success Metrics

1. **Functionality**: Web search successfully enhances AI responses
2. **Performance**: No significant latency increase (< 2 seconds added)
3. **Reliability**: 95%+ success rate for web search requests
4. **User Experience**: Improved answer quality for real-time queries
5. **Stability**: No breaking changes to existing functionality

## Future Enhancements

1. **Multi-provider aggregation**: Combine results from multiple providers
2. **Result ranking**: Improve relevance scoring
3. **Persistent caching**: Use Redis for distributed caching
4. **Search result preview**: Extract more content from web pages
5. **User preferences**: Per-user web search settings
6. **Search history**: Track and analyze web search usage

## Dependencies to Add

```txt
# Web Search Providers
duckduckgo-search>=5.0.0  # Free, no API key
tavily-python>=0.3.0  # Optional, requires API key
# serpapi  # Optional, requires API key

# Caching (optional, for production)
# redis>=5.0.0
```

## Files Summary

### New Files
- `backend/src/services/web_search_service.py` - Core web search service
- `backend/src/providers/duckduckgo_provider.py` - DuckDuckGo implementation
- `backend/src/providers/tavily_provider.py` - Tavily implementation (optional)
- `backend/tests/unit/test_web_search_service.py` - Unit tests
- `docs/WEB_SEARCH_IMPLEMENTATION_PLAN.md` - This document

### Modified Files
- `backend/src/services/rag_service.py` - Add web search integration
- `backend/src/api/chat.py` - Add web search flag to requests
- `backend/requirements.txt` - Add web search dependencies
- `backend/src/services/ai_service.py` - Optional: enhance prompts with web context

## Conclusion

This implementation plan ensures:
- ✅ No breaking changes to existing functionality
- ✅ Optional feature that can be enabled/disabled
- ✅ Multiple provider support with fallbacks
- ✅ Proper error handling and graceful degradation
- ✅ Performance optimization through caching and rate limiting
- ✅ Comprehensive testing strategy
- ✅ Clear rollout plan

The implementation is designed to be incremental and safe, with each phase building on the previous one while maintaining backward compatibility.



