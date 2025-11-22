"""
LangChain-backed web search providers implementing the same interface as WebSearchProvider
"""

from __future__ import annotations

import asyncio
import os
from datetime import datetime

# We avoid importing WebSearchProvider/SearchResult at module import time to prevent
# circular imports. We'll import SearchResult inside methods when needed.


class _BaseLCProvider:
    name: str = "lc"

    def is_available(self) -> bool:  # pragma: no cover - simple import check
        return True

    async def search(
        self, query: str, max_results: int = 5, **kwargs
    ) -> list[SearchResult]:
        raise NotImplementedError


class LangChainSerpAPIProvider(_BaseLCProvider):
    """LangChain SerpAPI wrapper provider.

    Requires SERPAPI_API_KEY and langchain-community installed.
    """

    name = "serpapi"

    def is_available(self) -> bool:
        if not os.getenv("SERPAPI_API_KEY"):
            return False
        try:
            return True
        except Exception:
            return False

    async def search(
        self, query: str, max_results: int = 5, **kwargs
    ) -> list[SearchResult]:
        from langchain_community.utilities import SerpAPIWrapper  # type: ignore

        from .web_search_service import SearchResult  # local import to avoid cycle

        loop = asyncio.get_event_loop()
        wrapper = SerpAPIWrapper()
        # wrapper.results returns list of dicts similar to serpapi
        raw = await loop.run_in_executor(None, lambda: wrapper.results(query))
        # Some versions return a dict with 'organic_results'; normalize to list
        if isinstance(raw, dict):
            items = raw.get("organic_results", [])
        else:
            items = raw or []
        results: list[SearchResult] = []
        for i, r in enumerate(items[:max_results]):
            results.append(
                SearchResult(
                    title=r.get("title") or "No title",
                    url=r.get("link") or r.get("url") or "",
                    snippet=(r.get("snippet") or r.get("content") or "")[:500],
                    source="web_search",
                    relevance_score=max(0.1, 1.0 - i * 0.1),
                    timestamp=datetime.now(),
                )
            )
        return results


class LangChainTavilyProvider(_BaseLCProvider):
    """LangChain Tavily wrapper provider.

    Requires TAVILY_API_KEY and langchain-community installed.
    """

    name = "tavily"

    def is_available(self) -> bool:
        if not os.getenv("TAVILY_API_KEY"):
            return False
        try:
            return True
        except Exception:
            return False

    async def search(
        self, query: str, max_results: int = 5, **kwargs
    ) -> list[SearchResult]:
        from langchain_community.utilities import TavilySearchAPIWrapper  # type: ignore

        from .web_search_service import SearchResult  # local import to avoid cycle

        loop = asyncio.get_event_loop()
        wrapper = TavilySearchAPIWrapper(max_results=max_results)
        raw = await loop.run_in_executor(None, lambda: wrapper.results(query))
        results: list[SearchResult] = []
        for i, r in enumerate((raw or [])[:max_results]):
            results.append(
                SearchResult(
                    title=r.get("title") or "No title",
                    url=r.get("url") or "",
                    snippet=(r.get("content") or "")[:500],
                    source="web_search",
                    relevance_score=max(0.1, 1.0 - i * 0.1),
                    timestamp=datetime.now(),
                )
            )
        return results


class LangChainDuckDuckGoProvider(_BaseLCProvider):
    """LangChain DuckDuckGo wrapper provider."""

    name = "duckduckgo"

    def is_available(self) -> bool:
        try:
            return True
        except Exception:
            return False

    async def search(
        self, query: str, max_results: int = 5, **kwargs
    ) -> list[SearchResult]:
        from langchain_community.utilities import (
            DuckDuckGoSearchAPIWrapper,  # type: ignore
        )

        from .web_search_service import SearchResult  # local import to avoid cycle

        loop = asyncio.get_event_loop()
        wrapper = DuckDuckGoSearchAPIWrapper()
        # wrapper.results returns list of dicts with {link, title, snippet}
        raw = await loop.run_in_executor(
            None, lambda: wrapper.results(query, max_results=max_results)
        )
        results: list[SearchResult] = []
        for i, r in enumerate((raw or [])[:max_results]):
            results.append(
                SearchResult(
                    title=r.get("title") or "No title",
                    url=r.get("link") or r.get("url") or "",
                    snippet=(r.get("snippet") or "")[:500],
                    source="web_search",
                    relevance_score=max(0.1, 1.0 - i * 0.1),
                    timestamp=datetime.now(),
                )
            )
        return results
