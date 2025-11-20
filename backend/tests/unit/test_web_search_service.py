"""
Unit tests for web search service
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest

from backend.src.services.web_search_service import (
    DuckDuckGoProvider,
    SearchResult,
    TavilyProvider,
    WebSearchService,
    get_web_search_service,
)


class TestSearchResult:
    """Test SearchResult dataclass"""

    def test_search_result_creation(self):
        """Test creating a SearchResult"""
        result = SearchResult(
            title="Test Title",
            url="https://example.com",
            snippet="Test snippet",
            source="web_search",
            relevance_score=0.9,
        )

        assert result.title == "Test Title"
        assert result.url == "https://example.com"
        assert result.snippet == "Test snippet"
        assert result.source == "web_search"
        assert result.relevance_score == 0.9

    def test_search_result_to_dict(self):
        """Test converting SearchResult to dictionary"""
        result = SearchResult(
            title="Test Title",
            url="https://example.com",
            snippet="Test snippet",
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
        )

        result_dict = result.to_dict()

        assert result_dict["title"] == "Test Title"
        assert result_dict["url"] == "https://example.com"
        assert result_dict["snippet"] == "Test snippet"
        assert result_dict["source"] == "web_search"
        assert "timestamp" in result_dict


class TestDuckDuckGoProvider:
    """Test DuckDuckGo provider"""

    def test_provider_initialization(self):
        """Test provider initialization"""
        provider = DuckDuckGoProvider()
        assert provider.name == "duckduckgo"

    @patch("backend.src.services.web_search_service.DDGS")
    def test_search_success(self, mock_ddgs):
        """Test successful search"""
        # Mock DDGS response
        mock_ddgs_instance = Mock()
        mock_ddgs_instance.text.return_value = [
            {
                "title": "Test Result 1",
                "href": "https://example.com/1",
                "body": "This is a test result",
            },
            {
                "title": "Test Result 2",
                "href": "https://example.com/2",
                "body": "Another test result",
            },
        ]
        mock_ddgs.return_value = mock_ddgs_instance

        provider = DuckDuckGoProvider()

        # Mock is_available to return True
        with patch.object(provider, "is_available", return_value=True):

            async def run_test():
                results = await provider.search("test query", max_results=2)
                assert len(results) == 2
                assert results[0].title == "Test Result 1"
                assert results[0].url == "https://example.com/1"
                assert results[1].title == "Test Result 2"

            asyncio.run(run_test())

    def test_search_not_available(self):
        """Test search when provider is not available"""
        provider = DuckDuckGoProvider()

        with patch.object(provider, "is_available", return_value=False):

            async def run_test():
                with pytest.raises(RuntimeError, match="not available"):
                    await provider.search("test query")

            asyncio.run(run_test())


class TestTavilyProvider:
    """Test Tavily provider"""

    def test_provider_initialization(self):
        """Test provider initialization"""
        provider = TavilyProvider(api_key="test_key")
        assert provider.name == "tavily"
        assert provider.api_key == "test_key"

    def test_provider_no_api_key(self):
        """Test provider without API key"""
        provider = TavilyProvider()
        # Should not be available without API key
        assert not provider.is_available()

    @patch("backend.src.services.web_search_service.TavilyClient")
    def test_search_success(self, mock_tavily_client):
        """Test successful search"""
        # Mock Tavily response
        mock_client_instance = Mock()
        mock_client_instance.search.return_value = {
            "results": [
                {
                    "title": "Test Result 1",
                    "url": "https://example.com/1",
                    "content": "This is a test result",
                    "score": 0.9,
                },
                {
                    "title": "Test Result 2",
                    "url": "https://example.com/2",
                    "content": "Another test result",
                    "score": 0.8,
                },
            ]
        }
        mock_tavily_client.return_value = mock_client_instance

        provider = TavilyProvider(api_key="test_key")

        # Mock is_available to return True
        with patch.object(provider, "is_available", return_value=True):

            async def run_test():
                results = await provider.search("test query", max_results=2)
                assert len(results) == 2
                assert results[0].title == "Test Result 1"
                assert results[0].url == "https://example.com/1"
                assert results[1].title == "Test Result 2"

            asyncio.run(run_test())


class TestWebSearchService:
    """Test WebSearchService"""

    def test_service_initialization(self):
        """Test service initialization"""
        service = WebSearchService(provider="duckduckgo", cache_ttl=3600, rate_limit=10)

        assert service.provider_name == "duckduckgo"
        assert service.cache_ttl == 3600
        assert service.rate_limit == 10

    @patch("backend.src.services.web_search_service.DuckDuckGoProvider")
    def test_search_with_caching(self, mock_provider_class):
        """Test search with caching enabled"""
        # Mock provider
        mock_provider = Mock()
        mock_provider.is_available.return_value = True
        mock_provider.search = AsyncMock(
            return_value=[
                SearchResult(
                    title="Test Result",
                    url="https://example.com",
                    snippet="Test snippet",
                )
            ]
        )
        mock_provider_class.return_value = mock_provider

        service = WebSearchService(
            provider="duckduckgo", cache_ttl=3600, enable_cache=True
        )
        service.primary_provider = mock_provider

        async def run_test():
            # First search - should call provider
            results1 = await service.search("test query")
            assert len(results1) == 1
            assert mock_provider.search.call_count == 1

            # Second search - should use cache
            results2 = await service.search("test query")
            assert len(results2) == 1
            assert mock_provider.search.call_count == 1  # Should not call again

            # Different query - should call provider
            results3 = await service.search("different query")
            assert len(results3) == 1
            assert mock_provider.search.call_count == 2

        asyncio.run(run_test())

    def test_search_empty_query(self):
        """Test search with empty query"""
        service = WebSearchService()

        async def run_test():
            results = await service.search("")
            assert results == []

            results = await service.search("   ")
            assert results == []

        asyncio.run(run_test())

    def test_rate_limiting(self):
        """Test rate limiting"""
        service = WebSearchService(rate_limit=2)

        # Should allow 2 requests
        assert service._check_rate_limit("test") == True
        assert service._check_rate_limit("test") == True

        # Third request should be rate limited
        assert service._check_rate_limit("test") == False

    def test_cache_management(self):
        """Test cache management"""
        service = WebSearchService(cache_ttl=1, enable_cache=True)

        # Add result to cache
        result = SearchResult(title="Test", url="https://example.com", snippet="Test")
        service._cache_result("test query", [result])

        # Should be in cache
        cached = service._get_cached_result("test query")
        assert cached is not None
        assert len(cached) == 1

        # Wait for expiration (simulate)
        service._cache["test query"] = (cached, datetime.now() - timedelta(seconds=2))

        # Should not be in cache anymore
        cached = service._get_cached_result("test query")
        assert cached is None

    def test_clear_cache(self):
        """Test clearing cache"""
        service = WebSearchService(enable_cache=True)

        # Add to cache
        result = SearchResult(title="Test", url="https://example.com", snippet="Test")
        service._cache_result("test query", [result])
        assert len(service._cache) == 1

        # Clear cache
        service.clear_cache()
        assert len(service._cache) == 0

    def test_get_cache_stats(self):
        """Test getting cache statistics"""
        service = WebSearchService(provider="duckduckgo", cache_ttl=3600, rate_limit=10)

        stats = service.get_cache_stats()

        assert stats["cache_size"] == 0
        assert stats["cache_ttl"] == 3600
        assert stats["rate_limit"] == 10
        assert stats["primary_provider"] == "duckduckgo"

    @patch("backend.src.services.web_search_service.DuckDuckGoProvider")
    def test_search_with_fallback(self, mock_provider_class):
        """Test search with provider fallback"""
        # Mock primary provider to fail
        mock_primary = Mock()
        mock_primary.is_available.return_value = True
        mock_primary.search = AsyncMock(side_effect=Exception("Primary failed"))

        # Mock fallback provider to succeed
        mock_fallback = Mock()
        mock_fallback.is_available.return_value = True
        mock_fallback.search = AsyncMock(
            return_value=[
                SearchResult(
                    title="Fallback Result",
                    url="https://example.com",
                    snippet="From fallback",
                )
            ]
        )

        mock_provider_class.return_value = mock_primary

        service = WebSearchService(provider="duckduckgo")
        service.primary_provider = mock_primary
        service.fallback_provider = mock_fallback

        async def run_test():
            results = await service.search("test query")
            # Should use fallback
            assert len(results) == 1
            assert results[0].title == "Fallback Result"
            assert mock_primary.search.call_count == 1
            assert mock_fallback.search.call_count == 1

        asyncio.run(run_test())

    def test_search_with_sources(self):
        """Test search_with_sources method"""
        service = WebSearchService()

        # Mock search method
        mock_results = [
            SearchResult(
                title="Test Result", url="https://example.com", snippet="Test snippet"
            )
        ]

        async def run_test():
            with patch.object(service, "search", return_value=mock_results):
                result = await service.search_with_sources("test query")

                assert result["query"] == "test query"
                assert result["count"] == 1
                assert len(result["results"]) == 1
                assert result["results"][0]["title"] == "Test Result"

        asyncio.run(run_test())


class TestGetWebSearchService:
    """Test singleton getter"""

    def test_get_service_singleton(self):
        """Test that get_web_search_service returns singleton"""
        # Clear global instance
        import backend.src.services.web_search_service as ws_module

        ws_module._web_search_service_instance = None

        with patch.dict(
            "os.environ",
            {
                "WEB_SEARCH_PROVIDER": "duckduckgo",
                "WEB_SEARCH_CACHE_TTL": "1800",
                "WEB_SEARCH_RATE_LIMIT": "5",
            },
        ):
            service1 = get_web_search_service()
            service2 = get_web_search_service()

            # Should be same instance
            assert service1 is service2
            assert service1.provider_name == "duckduckgo"
            assert service1.cache_ttl == 1800
            assert service1.rate_limit == 5
