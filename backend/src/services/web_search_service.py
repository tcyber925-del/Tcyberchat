"""
Web Search Service for retrieving real-time information from the internet
Supports multiple providers with fallback and caching
"""

import asyncio
import logging
import os
import time
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Represents a single web search result"""
    title: str
    url: str
    snippet: str
    source: str = "web_search"
    relevance_score: float = 1.0
    timestamp: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "source": self.source,
            "relevance_score": self.relevance_score,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }


class WebSearchProvider:
    """Abstract base class for web search providers"""
    
    async def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """
        Perform web search and return results
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of SearchResult objects
        """
        raise NotImplementedError("Subclasses must implement search method")
    
    def is_available(self) -> bool:
        """Check if provider is available (e.g., API key configured)"""
        return True


class DuckDuckGoProvider(WebSearchProvider):
    """DuckDuckGo web search provider (free, no API key required)"""
    
    def __init__(self):
        self.name = "duckduckgo"
        self._available = None
    
    def is_available(self) -> bool:
        """Check if DuckDuckGo is available"""
        if self._available is None:
            try:
                import duckduckgo_search
                self._available = True
            except ImportError:
                logger.warning("duckduckgo-search not installed. Install with: pip install duckduckgo-search")
                self._available = False
        return self._available
    
    async def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """Search using DuckDuckGo"""
        if not self.is_available():
            raise RuntimeError("DuckDuckGo provider not available")
        
        try:
            from duckduckgo_search import DDGS
            
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                lambda: list(DDGS().text(query, max_results=max_results))
            )
        
            search_results = []
            for i, result in enumerate(results):
                try:
                    search_result = SearchResult(
                        title=result.get('title', 'No title'),
                        url=result.get('href', ''),
                        snippet=result.get('body', ''),
                        source="web_search",
                        relevance_score=max(0.1, 1.0 - (i * 0.1)),  # Decreasing relevance
                        timestamp=datetime.now()
                    )
                    search_results.append(search_result)
                except Exception as e:
                    logger.warning(f"Error processing DuckDuckGo result: {e}")
                    continue
            
            logger.info(f"DuckDuckGo search returned {len(search_results)} results for query: {query[:50]}")
            return search_results
            
        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}", exc_info=True)
            raise


class TavilyProvider(WebSearchProvider):
    """Tavily AI search provider (requires API key, better for AI use cases)"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.name = "tavily"
        self.api_key = api_key or os.getenv('TAVILY_API_KEY')
        self._available = None
    
    def is_available(self) -> bool:
        """Check if Tavily is available (API key configured)"""
        if self._available is None:
            if not self.api_key:
                self._available = False
                return False
            try:
                import tavily
                self._available = True
            except ImportError:
                logger.warning("tavily-python not installed. Install with: pip install tavily-python")
                self._available = False
        return self._available
    
    async def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """Search using Tavily"""
        if not self.is_available():
            raise RuntimeError("Tavily provider not available (API key not configured)")
        
        try:
            from tavily import TavilyClient
            
            client = TavilyClient(api_key=self.api_key)
            
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.search(query=query, max_results=max_results)
            )
            
            search_results = []
            for i, result in enumerate(response.get('results', [])):
                try:
                    search_result = SearchResult(
                        title=result.get('title', 'No title'),
                        url=result.get('url', ''),
                        snippet=result.get('content', '')[:500],  # Limit snippet length
                        source="web_search",
                        relevance_score=result.get('score', max(0.1, 1.0 - (i * 0.1))),
                        timestamp=datetime.now()
                    )
                    search_results.append(search_result)
                except Exception as e:
                    logger.warning(f"Error processing Tavily result: {e}")
                    continue
            
            logger.info(f"Tavily search returned {len(search_results)} results for query: {query[:50]}")
            return search_results
            
        except Exception as e:
            logger.error(f"Tavily search failed: {e}", exc_info=True)
            raise


class WebSearchService:
    """Main web search service with provider fallback and caching"""
    
    def __init__(
        self,
        provider: str = "duckduckgo",
        cache_ttl: int = 3600,  # 1 hour default
        rate_limit: int = 10,  # requests per minute
        enable_cache: bool = True
    ):
        """
        Initialize web search service
        
        Args:
            provider: Primary provider name ("duckduckgo" or "tavily")
            cache_ttl: Cache time-to-live in seconds
            rate_limit: Maximum requests per minute
            enable_cache: Enable result caching
        """
        self.provider_name = provider.lower()
        self.cache_ttl = cache_ttl
        self.rate_limit = rate_limit
        self.enable_cache = enable_cache
        
        # Initialize providers
        self.duckduckgo = DuckDuckGoProvider()
        self.tavily = TavilyProvider()
        
        # Determine primary and fallback providers
        self.primary_provider = self._get_provider(self.provider_name)
        self.fallback_provider = self._get_fallback_provider()
        
        # Cache: query -> (results, timestamp)
        self._cache: Dict[str, tuple] = {}
        
        # Rate limiting: track requests per minute
        self._rate_limit_tracker: Dict[str, List[float]] = defaultdict(list)
        
        logger.info(
            f"WebSearchService initialized: provider={self.provider_name}, "
            f"cache_ttl={cache_ttl}s, rate_limit={rate_limit}/min"
        )
    
    def _get_provider(self, provider_name: str) -> Optional[WebSearchProvider]:
        """Get provider by name"""
        if provider_name == "duckduckgo":
            return self.duckduckgo if self.duckduckgo.is_available() else None
        elif provider_name == "tavily":
            return self.tavily if self.tavily.is_available() else None
        return None
    
    def _get_fallback_provider(self) -> Optional[WebSearchProvider]:
        """Get fallback provider (opposite of primary)"""
        if self.provider_name == "duckduckgo":
            return self.tavily if self.tavily.is_available() else None
        elif self.provider_name == "tavily":
            return self.duckduckgo if self.duckduckgo.is_available() else None
        return None
    
    def _check_rate_limit(self, query: str) -> bool:
        """Check if request is within rate limit"""
        if self.rate_limit <= 0:
            return True  # No rate limiting
        
        now = time.time()
        minute_ago = now - 60
        
        # Clean old entries
        self._rate_limit_tracker[query] = [
            t for t in self._rate_limit_tracker[query] if t > minute_ago
        ]
        
        # Check limit
        if len(self._rate_limit_tracker[query]) >= self.rate_limit:
            return False
        
        # Record this request
        self._rate_limit_tracker[query].append(now)
        return True
    
    def _is_time_sensitive_query(self, query: str) -> bool:
        """Detect if query is time-sensitive (e.g., latest news, recent updates)"""
        if not query:
            return False
        
        query_lower = query.lower()
        time_sensitive_keywords = [
            "latest", "recent", "news", "update", "what's new", "current",
            "today", "now", "this week", "this month", "2024", "2025"
        ]
        
        return any(keyword in query_lower for keyword in time_sensitive_keywords)
    
    def _enhance_query_for_freshness(self, query: str) -> str:
        """Enhance query with temporal keywords for better freshness"""
        if not self._is_time_sensitive_query(query):
            return query
        
        # Add current year if not present and query is time-sensitive
        current_year = datetime.now().year
        query_lower = query.lower()
        
        # Don't modify if already has year
        if str(current_year) not in query and str(current_year - 1) not in query:
            # For "latest" or "news" queries, add year
            if "latest" in query_lower or "news" in query_lower:
                return f"{query} {current_year}"
        
        return query
    
    def _get_cached_result(self, query: str) -> Optional[List[SearchResult]]:
        """Get cached result if available and not expired"""
        if not self.enable_cache:
            return None
        
        if query not in self._cache:
            return None
        
        results, timestamp = self._cache[query]
        age = (datetime.now() - timestamp).total_seconds()
        
        if age > self.cache_ttl:
            # Cache expired
            del self._cache[query]
            return None
        
        logger.debug(f"Returning cached result for query: {query[:50]}")
        return results
    
    def _cache_result(self, query: str, results: List[SearchResult]):
        """Cache search results"""
        if not self.enable_cache:
            return
        
        self._cache[query] = (results, datetime.now())
        
        # Simple cache size management (keep last 100 queries)
        if len(self._cache) > 100:
            # Remove oldest entry
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
            del self._cache[oldest_key]
    
    async def search(
        self,
        query: str,
        max_results: int = 5,
        use_cache: bool = True
    ) -> List[SearchResult]:
        """
        Perform web search with caching and rate limiting
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            use_cache: Whether to use cached results
            
        Returns:
            List of SearchResult objects
            
        Raises:
            RuntimeError: If no providers are available
        """
        if not query or not query.strip():
            return []
        
        original_query = query.strip()
        
        # Detect time-sensitive queries
        is_time_sensitive = self._is_time_sensitive_query(original_query)
        
        # Enhance query for freshness if time-sensitive
        enhanced_query = self._enhance_query_for_freshness(original_query) if is_time_sensitive else original_query
        
        # For time-sensitive queries, disable cache or use very short TTL
        if is_time_sensitive or force_fresh:
            use_cache = False  # Disable cache for time-sensitive queries
            logger.info(f"Time-sensitive query detected: '{original_query[:50]}' - cache disabled")
        
        # Check cache first (only if not time-sensitive and cache enabled)
        if use_cache and not force_fresh:
            cached = self._get_cached_result(enhanced_query)
            if cached is not None:
                logger.debug(f"Returning cached result for query: {enhanced_query[:50]}")
                return cached[:max_results]
        
        # Check rate limit
        if not self._check_rate_limit(enhanced_query):
            logger.warning(f"Rate limit exceeded for query: {enhanced_query[:50]}")
            # Return cached result even if expired, or empty list
            if enhanced_query in self._cache:
                return self._cache[enhanced_query][0][:max_results]
            return []
        
        # Use enhanced query for search
        search_query = enhanced_query if enhanced_query != original_query else original_query
        
        # Log search details
        logger.info(
            f"Web search: query='{original_query[:50]}', "
            f"enhanced='{search_query[:50]}', "
            f"time_sensitive={is_time_sensitive}, "
            f"use_cache={use_cache}, "
            f"max_results={max_results}"
        )
        
        # Try primary provider
        if self.primary_provider:
            try:
                # Pass search_depth for Tavily provider
                if isinstance(self.primary_provider, TavilyProvider):
                    search_depth = "advanced" if is_time_sensitive else "basic"
                    results = await self.primary_provider.search(search_query, max_results, search_depth=search_depth)
                else:
                    results = await self.primary_provider.search(search_query, max_results)
                
                if results:
                    logger.info(
                        f"Web search returned {len(results)} results for query: '{search_query[:50]}' "
                        f"(time_sensitive={is_time_sensitive})"
                    )
                    # Only cache if not time-sensitive
                    if not is_time_sensitive and use_cache:
                        self._cache_result(search_query, results)
                    return results
            except Exception as e:
                logger.warning(f"Primary provider ({self.provider_name}) failed: {e}", exc_info=True)
        
        # Try fallback provider
        if self.fallback_provider:
            try:
                logger.info(f"Using fallback provider for query: {search_query[:50]}")
                if isinstance(self.fallback_provider, TavilyProvider):
                    search_depth = "advanced" if is_time_sensitive else "basic"
                    results = await self.fallback_provider.search(search_query, max_results, search_depth=search_depth)
                else:
                    results = await self.fallback_provider.search(search_query, max_results)
                
                if results:
                    logger.info(
                        f"Fallback web search returned {len(results)} results for query: '{search_query[:50]}'"
                    )
                    # Only cache if not time-sensitive
                    if not is_time_sensitive and use_cache:
                        self._cache_result(search_query, results)
                    return results
            except Exception as e:
                logger.warning(f"Fallback provider also failed: {e}", exc_info=True)
        
        # No providers available or all failed
        if not self.primary_provider and not self.fallback_provider:
            raise RuntimeError(
                "No web search providers available. "
                "Install duckduckgo-search or configure TAVILY_API_KEY"
            )
        
        logger.error("All web search providers failed")
        return []
    
    async def search_with_sources(
        self,
        query: str,
        max_results: int = 5
    ) -> Dict[str, Any]:
        """
        Perform search and return formatted results with metadata
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            Dictionary with results and metadata
        """
        results = await self.search(query, max_results)
        
        return {
            "query": query,
            "results": [r.to_dict() for r in results],
            "count": len(results),
            "provider": self.provider_name,
            "cached": query in self._cache
        }
    
    def clear_cache(self):
        """Clear the search result cache"""
        self._cache.clear()
        logger.info("Web search cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "cache_size": len(self._cache),
            "cache_ttl": self.cache_ttl,
            "rate_limit": self.rate_limit,
            "primary_provider": self.provider_name,
            "primary_available": self.primary_provider is not None,
            "fallback_available": self.fallback_provider is not None
        }


# Global singleton instance
_web_search_service_instance: Optional[WebSearchService] = None


def get_web_search_service() -> WebSearchService:
    """Get singleton WebSearchService instance"""
    global _web_search_service_instance
    
    if _web_search_service_instance is None:
        provider = os.getenv('WEB_SEARCH_PROVIDER', 'duckduckgo').lower()
        cache_ttl = int(os.getenv('WEB_SEARCH_CACHE_TTL', '3600'))
        rate_limit = int(os.getenv('WEB_SEARCH_RATE_LIMIT', '10'))
        enable_cache = os.getenv('WEB_SEARCH_ENABLE_CACHE', 'true').lower() == 'true'
        
        _web_search_service_instance = WebSearchService(
            provider=provider,
            cache_ttl=cache_ttl,
            rate_limit=rate_limit,
            enable_cache=enable_cache
        )
    
    return _web_search_service_instance

