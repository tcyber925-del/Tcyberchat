"""
Web Search Service for retrieving real-time information from the internet
Supports multiple providers with fallback and caching
"""

import asyncio
import logging
import os
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Represents a single web search result"""

    title: str
    url: str
    snippet: str
    source: str = "web_search"
    relevance_score: float = 1.0
    timestamp: datetime | None = None
    # Optional enrichment fields (added for web fetch integration)
    content: str | None = None
    canonical_url: str | None = None
    content_type: str | None = None
    published_at: datetime | None = None
    tokens_estimate: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses"""
        result = {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "source": self.source,
            "relevance_score": self.relevance_score,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
        # Include optional enrichment fields only if present
        if self.content is not None:
            result["content"] = self.content
        if self.canonical_url is not None:
            result["canonical_url"] = self.canonical_url
        if self.content_type is not None:
            result["content_type"] = self.content_type
        if self.published_at is not None:
            result["published_at"] = self.published_at.isoformat()
        if self.tokens_estimate is not None:
            result["tokens_estimate"] = self.tokens_estimate
        return result


class WebSearchProvider:
    """Abstract base class for web search providers"""

    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
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
        """Check if DuckDuckGo (ddgs) is available"""
        if self._available is None:
            try:
                # Prefer the new package name first
                self._available = True
            except Exception:
                try:
                    self._available = True
                except Exception:
                    logger.warning(
                        "DuckDuckGo search package not installed. Install with: pip install ddgs (or duckduckgo-search)"
                    )
                    self._available = False
        return self._available

    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        """Search using DuckDuckGo"""
        if not self.is_available():
            raise RuntimeError("DuckDuckGo provider not available")

        try:
            # Try the renamed package first, then fall back to the legacy one
            try:
                from ddgs import DDGS  # type: ignore
            except Exception:
                from duckduckgo_search import DDGS  # type: ignore

            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None, lambda: list(DDGS().text(query, max_results=max_results))
            )

            search_results = []
            for i, result in enumerate(results):
                try:
                    search_result = SearchResult(
                        title=result.get("title", "No title"),
                        url=result.get("href", ""),
                        snippet=result.get("body", ""),
                        source="web_search",
                        relevance_score=max(
                            0.1, 1.0 - (i * 0.1)
                        ),  # Decreasing relevance
                        timestamp=datetime.now(),
                    )
                    search_results.append(search_result)
                except Exception as e:
                    logger.warning(f"Error processing DuckDuckGo result: {e}")
                    continue

            logger.info(
                f"DuckDuckGo search returned {len(search_results)} results for query: {query[:50]}"
            )
            return search_results

        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}", exc_info=True)
            raise


class SerpAPIProvider(WebSearchProvider):
    """SerpAPI search provider (requires API key, Google search results)"""

    def __init__(self, api_key: str | None = None):
        self.name = "serpapi"
        self.api_key = api_key or os.getenv("SERPAPI_API_KEY")
        self._available = None

    def is_available(self) -> bool:
        """Check if SerpAPI is available (API key configured)"""
        if self._available is None:
            if not self.api_key:
                self._available = False
                return False
            try:
                import serpapi

                self._available = True
            except ImportError:
                logger.warning(
                    "google-search-results not installed. Install with: pip install google-search-results"
                )
                self._available = False
        return self._available

    async def search(
        self, query: str, max_results: int = 5, **kwargs
    ) -> list[SearchResult]:
        """Search using SerpAPI

        Args:
            query: Search query string
            max_results: Maximum number of results to return
            **kwargs: Additional arguments (ignored for compatibility)
        """
        if not self.is_available():
            raise RuntimeError(
                "SerpAPI provider not available (API key not configured)"
            )

        try:
            from serpapi import GoogleSearch

            # Build search parameters
            params = {
                "q": query,
                "num": max_results,
                "engine": "google",
                "api_key": self.api_key,
            }

            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            try:
                response = await loop.run_in_executor(
                    None, lambda: GoogleSearch(params).get_dict()
                )
            except Exception as e:
                error_msg = str(e)
                if "Invalid API key" in error_msg or "401" in error_msg:
                    raise RuntimeError(
                        "SerpAPI authentication failed. Please verify your API key. "
                        "Get your API key from https://serpapi.com/manage-api-key"
                    ) from e
                elif "403" in error_msg or "Rate limit" in error_msg:
                    raise RuntimeError(
                        "SerpAPI rate limit exceeded or access forbidden. "
                        "Check your plan limits at https://serpapi.com/dashboard"
                    ) from e
                else:
                    raise

            search_results = []
            organic_results = response.get("organic_results", []) or []

            for i, result in enumerate(organic_results[:max_results]):
                try:
                    search_result = SearchResult(
                        title=result.get("title", "No title"),
                        url=result.get("link", ""),
                        snippet=result.get("snippet", result.get("content", "")),
                        source="web_search",
                        relevance_score=max(
                            0.1, 1.0 - (i * 0.1)
                        ),  # Decreasing relevance
                        timestamp=datetime.now(),
                    )
                    search_results.append(search_result)
                except Exception as e:
                    logger.warning(f"Error processing SerpAPI result: {e}")
                    continue

            logger.info(
                f"SerpAPI search returned {len(search_results)} results for query: {query[:50]}"
            )
            return search_results

        except Exception as e:
            logger.error(f"SerpAPI search failed: {e}", exc_info=True)
            raise


class TavilyProvider(WebSearchProvider):
    """Tavily AI search provider (requires API key, better for AI use cases)"""

    def __init__(self, api_key: str | None = None):
        self.name = "tavily"
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
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
                logger.warning(
                    "tavily-python not installed. Install with: pip install tavily-python"
                )
                self._available = False
        return self._available

    async def search(
        self, query: str, max_results: int = 5, search_depth: str = "advanced", **kwargs
    ) -> list[SearchResult]:
        """Search using Tavily

        Args:
            query: Search query string
            max_results: Maximum number of results to return
            search_depth: Search depth ("basic" or "advanced") - advanced gets fresher results
            **kwargs: Additional arguments (ignored for compatibility)
        """
        if not self.is_available():
            raise RuntimeError("Tavily provider not available (API key not configured)")

        try:
            from tavily import TavilyClient

            client = TavilyClient(api_key=self.api_key)

            # Build search parameters
            # Note: Free/dev API keys may have limited parameters
            search_params = {
                "query": query,
                "max_results": max_results,
            }

            # Add optional parameters (may not be available on all plans)
            # For free/dev keys, these might cause ForbiddenError
            # We'll try with them first, and fall back if needed
            if search_depth and search_depth != "basic":
                search_params["search_depth"] = search_depth

            # include_answer may not be available on all plans
            # search_params["include_answer"] = True  # Commented out for compatibility

            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            try:
                response = await loop.run_in_executor(
                    None, lambda: client.search(**search_params)
                )
            except Exception as e:
                error_msg = str(e)
                # Check if it's a ForbiddenError (API key issue)
                if "Forbidden" in error_msg or "403" in error_msg:
                    logger.error(
                        f"Tavily API access forbidden. This might indicate: "
                        f"1) Invalid API key, 2) API key doesn't have required permissions, "
                        f"3) Rate limit exceeded, or 4) Dev API key restrictions. "
                        f"Error: {error_msg}"
                    )
                    # Try with minimal parameters as last resort
                    if "search_depth" in search_params or len(search_params) > 2:
                        logger.info("Attempting search with minimal parameters...")
                        minimal_params = {
                            "query": query,
                            "max_results": min(
                                max_results, 3
                            ),  # Limit results for dev keys
                        }
                        try:
                            response = await loop.run_in_executor(
                                None, lambda: client.search(**minimal_params)
                            )
                        except Exception as e2:
                            raise RuntimeError(
                                f"Tavily API error: {error_msg}. "
                                f"Please verify your API key is valid and has the required permissions. "
                                f"Dev API keys may have restrictions. Get a production key from https://tavily.com"
                            ) from e2
                    else:
                        raise RuntimeError(
                            f"Tavily API error: {error_msg}. "
                            f"Please verify your API key is valid and has the required permissions."
                        ) from e
                else:
                    raise

            search_results = []
            for i, result in enumerate(response.get("results", [])):
                try:
                    search_result = SearchResult(
                        title=result.get("title", "No title"),
                        url=result.get("url", ""),
                        snippet=result.get("content", "")[:500],  # Limit snippet length
                        source="web_search",
                        relevance_score=result.get("score", max(0.1, 1.0 - (i * 0.1))),
                        timestamp=datetime.now(),
                    )
                    search_results.append(search_result)
                except Exception as e:
                    logger.warning(f"Error processing Tavily result: {e}")
                    continue

            logger.info(
                f"Tavily search returned {len(search_results)} results for query: {query[:50]}"
            )
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
        enable_cache: bool = True,
        timeout_sec: int = 8,
        impl: str = "custom",  # "custom" or "langchain"
    ):
        """
        Initialize web search service

        Args:
            provider: Primary provider name ("duckduckgo" or "tavily")
            cache_ttl: Cache time-to-live in seconds
            rate_limit: Maximum requests per minute
            enable_cache: Enable result caching
            timeout_sec: Max seconds to wait for a single provider before falling back
            impl: Backend implementation (custom or langchain)
        """
        self.provider_name = provider.lower()
        self.cache_ttl = cache_ttl
        self.rate_limit = rate_limit
        self.enable_cache = enable_cache
        self.timeout_sec = timeout_sec
        self.impl = (impl or "custom").lower()

        # Initialize providers (custom)
        self.duckduckgo = DuckDuckGoProvider()
        self.serpapi = SerpAPIProvider()
        self.tavily = TavilyProvider()

        # Initialize optional LangChain providers lazily
        self.lc_duckduckgo = None
        self.lc_serpapi = None
        self.lc_tavily = None
        if self.impl == "langchain":
            try:
                from .web_search_lc_providers import (
                    LangChainDuckDuckGoProvider,
                    LangChainSerpAPIProvider,
                    LangChainTavilyProvider,
                )

                self.lc_duckduckgo = LangChainDuckDuckGoProvider()
                self.lc_serpapi = LangChainSerpAPIProvider()
                self.lc_tavily = LangChainTavilyProvider()
            except Exception:
                # If LC not installed, silently fall back to custom
                self.impl = "custom"

        # Determine primary and fallback providers
        self.primary_provider = self._get_provider(self.provider_name)
        self.fallback_provider = self._get_fallback_provider()

        # Cache: query -> (results, timestamp)
        self._cache: dict[str, tuple] = {}
        # Circuit breaker state per provider
        self._cb_failures: dict[str, int] = {}
        self._cb_open_until: dict[str, float] = {}

        # Rate limiting: track requests per minute
        self._rate_limit_tracker: dict[str, list[float]] = defaultdict(list)

        logger.info(
            f"WebSearchService initialized: provider={self.provider_name}, impl={self.impl}, "
            f"cache_ttl={cache_ttl}s, rate_limit={rate_limit}/min"
        )

    def _get_provider(self, provider_name: str) -> WebSearchProvider | None:
        """Get provider by name, honoring implementation backend."""
        if self.impl == "langchain":
            if (
                provider_name == "duckduckgo"
                and self.lc_duckduckgo
                and self.lc_duckduckgo.is_available()
            ):
                return self.lc_duckduckgo
            if (
                provider_name == "serpapi"
                and self.lc_serpapi
                and self.lc_serpapi.is_available()
            ):
                return self.lc_serpapi
            if (
                provider_name == "tavily"
                and self.lc_tavily
                and self.lc_tavily.is_available()
            ):
                return self.lc_tavily
        # custom fallback
        if provider_name == "duckduckgo":
            return self.duckduckgo if self.duckduckgo.is_available() else None
        elif provider_name == "serpapi":
            return self.serpapi if self.serpapi.is_available() else None
        elif provider_name == "tavily":
            return self.tavily if self.tavily.is_available() else None
        return None

    def _get_custom_provider(self, provider_name: str) -> WebSearchProvider | None:
        """Get a custom (non-LangChain) provider regardless of impl."""
        if provider_name == "duckduckgo":
            return self.duckduckgo if self.duckduckgo.is_available() else None
        if provider_name == "serpapi":
            return self.serpapi if self.serpapi.is_available() else None
        if provider_name == "tavily":
            return self.tavily if self.tavily.is_available() else None
        return None

    def _get_fallback_provider(self) -> WebSearchProvider | None:
        """Get fallback provider (opposite of primary) honoring backend implementation."""
        if self.provider_name == "duckduckgo":
            # Prefer SerpAPI over Tavily for fallback
            cand_serp = self._get_provider("serpapi")
            if cand_serp is not None:
                return cand_serp
            return self._get_provider("tavily")
        elif self.provider_name == "serpapi":
            return self._get_provider("duckduckgo")
        elif self.provider_name == "tavily":
            # Prefer SerpAPI as fallback if available, then DuckDuckGo
            cand_serp = self._get_provider("serpapi")
            if cand_serp is not None:
                return cand_serp
            return self._get_provider("duckduckgo")
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
            "latest",
            "recent",
            "news",
            "update",
            "what's new",
            "current",
            "today",
            "now",
            "this week",
            "this month",
            "2024",
            "2025",
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

    def _get_cached_result(self, query: str) -> list[SearchResult] | None:
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

    def _cache_result(self, query: str, results: list[SearchResult]):
        """Cache search results"""
        if not self.enable_cache:
            return

        self._cache[query] = (results, datetime.now())

        # Simple cache size management (keep last 100 queries)
        if len(self._cache) > 100:
            # Remove oldest entry
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
            del self._cache[oldest_key]

    async def enrich_results(self, results: list[SearchResult]) -> list[SearchResult]:
        """
        Enrich search results with fetched content

        Args:
            results: List of SearchResult objects to enrich

        Returns:
            List of enriched SearchResult objects
        """
        # Import here to avoid circular dependency
        try:
            from .web_fetch_service import get_web_fetch_service
        except ImportError:
            logger.debug("web_fetch_service not available, returning original results")
            return results

        fetch_service = get_web_fetch_service()

        if not fetch_service.enabled:
            # Web fetch disabled, return original results
            return results

        # Extract URLs to fetch
        urls = [result.url for result in results]

        if not urls:
            return results

        logger.info(f"Enriching {len(urls)} search results with fetched content")

        # Fetch content for all URLs
        fetch_results = await fetch_service.fetch_multiple(urls)

        # Create mapping of URL -> FetchResult
        fetch_map = {fr.url: fr for fr in fetch_results}

        # Enrich search results with fetched content
        enriched_results = []
        for result in results:
            fetch_result = fetch_map.get(result.url)

            if fetch_result and fetch_result.content and not fetch_result.error:
                # Create enriched result with fetched content
                enriched_result = SearchResult(
                    title=result.title or fetch_result.title or result.title,
                    url=result.url,
                    snippet=result.snippet,
                    source=result.source,
                    relevance_score=result.relevance_score,
                    timestamp=result.timestamp,
                    content=fetch_result.content,
                    canonical_url=fetch_result.canonical_url,
                    content_type=fetch_result.content_type,
                    published_at=fetch_result.published_at,
                    tokens_estimate=fetch_result.tokens_estimate,
                )
                enriched_results.append(enriched_result)
                logger.debug(
                    f"Enriched result for {result.url[:60]} with {fetch_result.tokens_estimate} tokens"
                )
            else:
                # Keep original result if fetch failed
                enriched_results.append(result)
                if fetch_result and fetch_result.error:
                    logger.debug(
                        f"Failed to enrich {result.url[:60]}: {fetch_result.error}"
                    )

        success_count = sum(1 for r in enriched_results if r.content is not None)
        logger.info(
            f"Successfully enriched {success_count}/{len(results)} search results"
        )

        return enriched_results

    def _cb_allowed(self, name: str) -> bool:
        import time
        cool = int(os.getenv("WEB_PROVIDER_CB_COOLDOWN", "60"))
        until = self._cb_open_until.get(name, 0)
        return time.time() >= until

    def _cb_record_failure(self, name: str):
        import time
        thr = int(os.getenv("WEB_PROVIDER_CB_THRESHOLD", "3"))
        cool = int(os.getenv("WEB_PROVIDER_CB_COOLDOWN", "60"))
        self._cb_failures[name] = self._cb_failures.get(name, 0) + 1
        if self._cb_failures[name] >= thr:
            self._cb_open_until[name] = time.time() + cool

    def _cb_record_success(self, name: str):
        self._cb_failures[name] = 0
        self._cb_open_until[name] = 0

    async def search(
        self,
        query: str,
        max_results: int = 5,
        use_cache: bool = True,
        force_fresh: bool = False,
    ) -> list[SearchResult]:
        """
        Perform web search with caching and rate limiting

        Args:
            query: Search query string
            max_results: Maximum number of results to return
            use_cache: Whether to use cached results
            force_fresh: Force fresh results (skip cache) - useful for time-sensitive queries

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
        enhanced_query = (
            self._enhance_query_for_freshness(original_query)
            if is_time_sensitive
            else original_query
        )

        # For time-sensitive queries, disable cache or use very short TTL
        if is_time_sensitive or force_fresh:
            use_cache = False  # Disable cache for time-sensitive queries
            logger.info(
                f"Time-sensitive query detected: '{original_query[:50]}' - cache disabled"
            )

        # Check cache first (only if not time-sensitive and cache enabled)
        if use_cache and not force_fresh:
            cached = self._get_cached_result(enhanced_query)
            if cached is not None:
                logger.debug(
                    f"Returning cached result for query: {enhanced_query[:50]}"
                )
                return cached[:max_results]

        # Check rate limit
        if not self._check_rate_limit(enhanced_query):
            logger.warning(f"Rate limit exceeded for query: {enhanced_query[:50]}")
            # Return cached result even if expired, or empty list
            if enhanced_query in self._cache:
                return self._cache[enhanced_query][0][:max_results]
            return []

        # Use enhanced query for search
        search_query = (
            enhanced_query if enhanced_query != original_query else original_query
        )

        # Log search details
        logger.info(
            f"Web search: query='{original_query[:50]}', "
            f"enhanced='{search_query[:50]}', "
            f"time_sensitive={is_time_sensitive}, "
            f"use_cache={use_cache}, "
            f"max_results={max_results}"
        )

        # Try primary provider (respect circuit breaker)
        if self.primary_provider and self._cb_allowed(self.provider_name):
            try:
                # Pass search_depth for Tavily provider (SerpAPI doesn't need this)
                if isinstance(self.primary_provider, TavilyProvider):
                    search_depth = "advanced" if is_time_sensitive else "basic"
                    results = await asyncio.wait_for(
                        self.primary_provider.search(
                            search_query, max_results, search_depth=search_depth
                        ),
                        timeout=self.timeout_sec,
                    )
                else:
                    results = await asyncio.wait_for(
                        self.primary_provider.search(search_query, max_results),
                        timeout=self.timeout_sec,
                    )

                if results:
                    logger.info(
                        f"Web search returned {len(results)} results for query: '{search_query[:50]}' "
                        f"(time_sensitive={is_time_sensitive})"
                    )
                    # Only cache if not time-sensitive
                    if not is_time_sensitive and use_cache:
                        self._cache_result(search_query, results)
                    self._cb_record_success(self.provider_name)
                    return results
            except Exception as e:
                logger.warning(
                    f"Primary provider ({self.provider_name}) failed: {e}",
                    exc_info=True,
                )
                self._cb_record_failure(self.provider_name)

        # Try fallback provider (respect circuit breaker)
        if self.fallback_provider:
            fb_name = getattr(self.fallback_provider, "name", "fallback")
            if not self._cb_allowed(fb_name):
                logger.warning(f"Circuit open for fallback provider '{fb_name}', skipping")
            else:
                try:
                logger.info(f"Using fallback provider for query: {search_query[:50]}")
                if isinstance(self.fallback_provider, TavilyProvider):
                    search_depth = "advanced" if is_time_sensitive else "basic"
                    results = await asyncio.wait_for(
                        self.fallback_provider.search(
                            search_query, max_results, search_depth=search_depth
                        ),
                        timeout=self.timeout_sec,
                    )
                else:
                    results = await asyncio.wait_for(
                        self.fallback_provider.search(search_query, max_results),
                        timeout=self.timeout_sec,
                    )

                if results:
                    logger.info(
                        f"Fallback web search returned {len(results)} results for query: '{search_query[:50]}'"
                    )
                    # Only cache if not time-sensitive
                    if not is_time_sensitive and use_cache:
                        self._cache_result(search_query, results)
                    self._cb_record_success(fb_name)
                    return results
                except Exception as e:
                    logger.warning(f"Fallback provider also failed: {e}", exc_info=True)
                    self._cb_record_failure(fb_name)

        # If LangChain impl failed, try custom providers as a last resort
        if self.impl == "langchain":
            try:
                # Try same primary via custom
                custom_primary = self._get_custom_provider(self.provider_name)
                if custom_primary:
                    logger.info(
                        "LangChain providers failed; attempting CUSTOM primary provider"
                    )
                    try:
                        if isinstance(custom_primary, TavilyProvider):
                            search_depth = "advanced" if is_time_sensitive else "basic"
                            results = await asyncio.wait_for(
                                custom_primary.search(
                                    search_query, max_results, search_depth=search_depth
                                ),
                                timeout=self.timeout_sec,
                            )
                        else:
                            results = await asyncio.wait_for(
                                custom_primary.search(search_query, max_results),
                                timeout=self.timeout_sec,
                            )
                        if results:
                            return results
                    except Exception:
                        pass
                # Custom fallback mapping
                fallback_name = "duckduckgo"
                if self.provider_name == "duckduckgo":
                    fallback_name = (
                        "serpapi" if self.serpapi.is_available() else "tavily"
                    )
                elif self.provider_name == "tavily":
                    fallback_name = (
                        "serpapi" if self.serpapi.is_available() else "duckduckgo"
                    )
                elif self.provider_name == "serpapi":
                    fallback_name = (
                        "duckduckgo" if self.duckduckgo.is_available() else "tavily"
                    )
                custom_fallback = self._get_custom_provider(fallback_name)
                if custom_fallback:
                    logger.info(
                        f"LangChain providers failed; attempting CUSTOM fallback provider: {fallback_name}"
                    )
                    try:
                        if isinstance(custom_fallback, TavilyProvider):
                            search_depth = "advanced" if is_time_sensitive else "basic"
                            results = await asyncio.wait_for(
                                custom_fallback.search(
                                    search_query, max_results, search_depth=search_depth
                                ),
                                timeout=self.timeout_sec,
                            )
                        else:
                            results = await asyncio.wait_for(
                                custom_fallback.search(search_query, max_results),
                                timeout=self.timeout_sec,
                            )
                        if results:
                            return results
                    except Exception:
                        pass
            except Exception:
                pass

        # No providers available or all failed
        if not self.primary_provider and not self.fallback_provider:
            raise RuntimeError(
                "No web search providers available. "
                "Install duckduckgo-search or configure SERPAPI_API_KEY/TAVILY_API_KEY"
            )

        logger.error(
            f"All web search providers failed for query: '{search_query[:50]}'. "
            f"Primary: {self.primary_provider is not None}, Fallback: {self.fallback_provider is not None}"
        )
        return []

    async def search_with_sources(
        self, query: str, max_results: int = 5
    ) -> dict[str, Any]:
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
            "cached": query in self._cache,
        }

    def clear_cache(self):
        """Clear the search result cache"""
        self._cache.clear()
        logger.info("Web search cache cleared")

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics"""
        return {
            "cache_size": len(self._cache),
            "cache_ttl": self.cache_ttl,
            "rate_limit": self.rate_limit,
            "primary_provider": self.provider_name,
            "primary_available": self.primary_provider is not None,
            "fallback_available": self.fallback_provider is not None,
        }


# Global singleton instance
_web_search_service_instance: WebSearchService | None = None


def get_web_search_service() -> WebSearchService:
    """Get singleton WebSearchService instance"""
    global _web_search_service_instance

    if _web_search_service_instance is None:
        # Auto-detect provider: prefer SerpAPI, then Tavily, then DuckDuckGo
        provider = os.getenv("WEB_SEARCH_PROVIDER", "").lower()
        if not provider:
            # Check if SerpAPI key is available (preferred)
            if os.getenv("SERPAPI_API_KEY"):
                provider = "serpapi"
                logger.info("SerpAPI key detected, using SerpAPI as primary provider")
            # Check if Tavily API key is available
            elif os.getenv("TAVILY_API_KEY"):
                provider = "tavily"
                logger.info("Tavily API key detected, using Tavily as primary provider")
            else:
                provider = "duckduckgo"
                logger.info(
                    "No SerpAPI/Tavily API key found, using DuckDuckGo as primary provider"
                )

        cache_ttl = int(os.getenv("WEB_SEARCH_CACHE_TTL", "3600"))
        rate_limit = int(os.getenv("WEB_SEARCH_RATE_LIMIT", "10"))
        enable_cache = os.getenv("WEB_SEARCH_ENABLE_CACHE", "true").lower() == "true"

        _web_search_service_instance = WebSearchService(
            provider=provider,
            cache_ttl=cache_ttl,
            rate_limit=rate_limit,
            enable_cache=enable_cache,
            timeout_sec=int(os.getenv("WEB_SEARCH_TIMEOUT", "8")),
            impl=os.getenv("WEB_SEARCH_IMPL", "custom").lower(),
        )

    return _web_search_service_instance
