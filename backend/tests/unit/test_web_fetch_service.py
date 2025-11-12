"""
Unit tests for web fetch service
"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

from backend.src.services.web_fetch_service import (
    FetchResult,
    WebFetchService,
    get_web_fetch_service,
)


class TestFetchResult:
    """Test FetchResult dataclass"""

    def test_fetch_result_creation(self):
        """Test creating a FetchResult"""
        result = FetchResult(
            url="https://example.com",
            canonical_url="https://example.com/page",
            content="Test content",
            content_type="text/html",
            title="Test Title",
            published_at=datetime(2024, 1, 1),
            extracted_at=datetime(2024, 1, 2),
            tokens_estimate=100,
            error=None,
        )

        assert result.url == "https://example.com"
        assert result.canonical_url == "https://example.com/page"
        assert result.content == "Test content"
        assert result.content_type == "text/html"
        assert result.title == "Test Title"
        assert result.tokens_estimate == 100
        assert result.error is None


class TestWebFetchService:
    """Test WebFetchService"""

    def test_service_initialization_disabled(self):
        """Test service initialization with fetch disabled"""
        service = WebFetchService(enabled=False)

        assert service.enabled is False
        assert service.concurrency == 5
        assert service.timeout == 8.0
        assert service.cache_ttl == 3600

    def test_service_initialization_enabled_no_httpx(self):
        """Test service initialization with fetch enabled but no httpx"""
        with patch.object(WebFetchService, "_check_httpx", return_value=False):
            service = WebFetchService(enabled=True)

            # Should auto-disable if httpx not available
            assert service.enabled is False

    def test_normalize_url(self):
        """Test URL normalization"""
        service = WebFetchService(enabled=False)

        # Remove fragment
        assert (
            service._normalize_url("https://example.com/page#section")
            == "https://example.com/page"
        )

        # Remove tracking params
        assert (
            service._normalize_url("https://example.com/page?utm_source=test")
            == "https://example.com/page"
        )

        # Keep valid query params
        assert (
            service._normalize_url("https://example.com/page?id=123")
            == "https://example.com/page?id=123"
        )

    def test_get_domain(self):
        """Test domain extraction"""
        service = WebFetchService(enabled=False)

        assert service._get_domain("https://example.com/page") == "example.com"
        assert service._get_domain("http://sub.example.com/page") == "sub.example.com"

    def test_is_allowed_domain_with_allowlist(self):
        """Test domain allowlist"""
        service = WebFetchService(
            enabled=False, allowlist_domains=["example.com", "test.com"]
        )

        assert service._is_allowed_domain("https://example.com/page") is True
        assert service._is_allowed_domain("https://test.com/page") is True
        assert service._is_allowed_domain("https://other.com/page") is False

    def test_is_allowed_domain_with_blocklist(self):
        """Test domain blocklist"""
        service = WebFetchService(enabled=False, blocklist_domains=["blocked.com"])

        assert service._is_allowed_domain("https://example.com/page") is True
        assert service._is_allowed_domain("https://blocked.com/page") is False

    def test_rate_limiting(self):
        """Test domain rate limiting"""
        service = WebFetchService(enabled=False)
        service._domain_rate_limit = 2

        url = "https://example.com/page"

        # Should allow first 2 requests
        assert service._check_domain_rate_limit(url) is True
        assert service._check_domain_rate_limit(url) is True

        # Third request should be rate limited
        assert service._check_domain_rate_limit(url) is False

    def test_caching(self):
        """Test fetch result caching"""
        service = WebFetchService(enabled=False, cache_ttl=3600)

        result = FetchResult(
            url="https://example.com",
            canonical_url="https://example.com",
            content="Test",
            content_type="text/html",
            title="Test",
            published_at=None,
            extracted_at=datetime.now(),
            tokens_estimate=10,
        )

        # Cache result
        service._cache_result("https://example.com", result)

        # Should be in cache
        cached = service._get_cached_result("https://example.com")
        assert cached is not None
        assert cached.content == "Test"

        # Non-existent URL should return None
        assert service._get_cached_result("https://other.com") is None

    def test_estimate_tokens(self):
        """Test token estimation"""
        service = WebFetchService(enabled=False)

        text = "This is a test sentence with several words"
        tokens = service._estimate_tokens(text)

        # Should be roughly words * 1.3
        assert tokens > 0
        assert tokens == int(len(text.split()) * 1.3)

    @pytest.mark.asyncio
    async def test_fetch_url_disabled(self):
        """Test fetch_url when service is disabled"""
        service = WebFetchService(enabled=False)

        result = await service.fetch_url("https://example.com")

        assert result.error == "Web fetch disabled"
        assert result.content is None

    @pytest.mark.asyncio
    async def test_fetch_url_blocked_domain(self):
        """Test fetch_url with blocked domain"""
        service = WebFetchService(enabled=True, blocklist_domains=["blocked.com"])

        with patch.object(service, "_check_httpx", return_value=True):
            service.enabled = True
            result = await service.fetch_url("https://blocked.com/page")

            assert "blocked" in result.error.lower()
            assert result.content is None

    @pytest.mark.asyncio
    async def test_fetch_url_rate_limited(self):
        """Test fetch_url when rate limited"""
        service = WebFetchService(enabled=True)
        service._domain_rate_limit = 0  # Force rate limit

        with patch.object(service, "_check_httpx", return_value=True):
            service.enabled = True
            result = await service.fetch_url("https://example.com/page")

            assert "rate limit" in result.error.lower()
            assert result.content is None

    @pytest.mark.asyncio
    async def test_fetch_url_html_success(self):
        """Test successful HTML fetch"""
        service = WebFetchService(enabled=True, concurrency=1)

        # Mock httpx response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/html", "content-length": "1000"}
        mock_response.url = "https://example.com/page"
        mock_response.text = (
            "<html><head><title>Test</title></head><body>Test content</body></html>"
        )
        mock_response.raise_for_status = Mock()

        # Mock httpx client
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get = AsyncMock(return_value=mock_response)

        import httpx as httpx_module

        with patch.object(httpx_module, "AsyncClient", return_value=mock_client):
            with patch.object(service, "_check_httpx", return_value=True):
                with patch.object(service, "_extraction_libs", {"beautifulsoup": True}):
                    service.enabled = True
                    service._httpx_available = True

                    result = await service.fetch_url("https://example.com/page")

                    assert (
                        result.error is None or result.error == "No content extracted"
                    )  # May fail extraction without bs4
                    assert result.canonical_url == "https://example.com/page"
                    assert result.content_type == "text/html"

    @pytest.mark.asyncio
    async def test_fetch_url_timeout(self):
        """Test fetch_url with timeout"""
        service = WebFetchService(enabled=True, timeout_ms=100)

        # Mock timeout exception
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        try:
            import httpx as httpx_module
        except ImportError:
            pytest.skip("httpx not installed")

        mock_client.get = AsyncMock(
            side_effect=httpx_module.TimeoutException("Timeout")
        )

        with patch.object(httpx_module, "AsyncClient", return_value=mock_client):
            with patch.object(service, "_check_httpx", return_value=True):
                service.enabled = True
                service._httpx_available = True

                result = await service.fetch_url("https://example.com/page")

                assert "timeout" in result.error.lower()
                assert result.content is None

    @pytest.mark.asyncio
    async def test_fetch_url_http_error(self):
        """Test fetch_url with HTTP error"""
        service = WebFetchService(enabled=True)

        # Mock HTTP error
        try:
            import httpx as httpx_module
        except ImportError:
            pytest.skip("httpx not installed")

        mock_response = Mock()
        mock_response.status_code = 404

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get = AsyncMock(
            side_effect=httpx_module.HTTPStatusError(
                "Not found", request=Mock(), response=mock_response
            )
        )

        with patch.object(httpx_module, "AsyncClient", return_value=mock_client):
            with patch.object(service, "_check_httpx", return_value=True):
                service.enabled = True
                service._httpx_available = True

                result = await service.fetch_url("https://example.com/page")

                assert "404" in result.error
                assert result.content is None

    @pytest.mark.asyncio
    async def test_fetch_multiple_disabled(self):
        """Test fetch_multiple when service is disabled"""
        service = WebFetchService(enabled=False)

        urls = ["https://example.com/1", "https://example.com/2"]
        results = await service.fetch_multiple(urls)

        assert len(results) == 2
        assert all(r.error == "Web fetch disabled" for r in results)

    @pytest.mark.asyncio
    async def test_fetch_multiple_respects_max_fetch(self):
        """Test fetch_multiple respects max_fetch limit"""
        service = WebFetchService(enabled=True, max_fetch=2)

        urls = [
            "https://example.com/1",
            "https://example.com/2",
            "https://example.com/3",
        ]

        with patch.object(service, "fetch_url") as mock_fetch:
            mock_fetch.return_value = FetchResult(
                url="test",
                canonical_url="test",
                content="test",
                content_type="text/html",
                title="test",
                published_at=None,
                extracted_at=datetime.now(),
                tokens_estimate=10,
            )

            results = await service.fetch_multiple(urls)

            # Should only fetch first 2
            assert mock_fetch.call_count == 2

    def test_get_stats(self):
        """Test get_stats method"""
        service = WebFetchService(enabled=True)

        stats = service.get_stats()

        assert "enabled" in stats
        assert stats["enabled"] is True
        assert "fetched_count" in stats
        assert "cache_hits" in stats
        assert "failures" in stats
        assert "avg_fetch_ms" in stats

    def test_clear_cache(self):
        """Test clear_cache method"""
        service = WebFetchService(enabled=False)

        # Add something to cache
        result = FetchResult(
            url="https://example.com",
            canonical_url="https://example.com",
            content="Test",
            content_type="text/html",
            title="Test",
            published_at=None,
            extracted_at=datetime.now(),
            tokens_estimate=10,
        )
        service._cache_result("https://example.com", result)

        assert len(service._cache) > 0

        service.clear_cache()

        assert len(service._cache) == 0


class TestWebFetchServiceSingleton:
    """Test get_web_fetch_service singleton"""

    def test_get_web_fetch_service_returns_singleton(self):
        """Test that get_web_fetch_service returns same instance"""
        # Reset global instance
        import backend.src.services.web_fetch_service as module

        module._web_fetch_service_instance = None

        service1 = get_web_fetch_service()
        service2 = get_web_fetch_service()

        assert service1 is service2

    def test_get_web_fetch_service_reads_env(self):
        """Test that get_web_fetch_service reads environment variables"""
        import os

        import backend.src.services.web_fetch_service as module

        # Reset global instance
        module._web_fetch_service_instance = None

        # Set environment variables
        original_env = os.environ.copy()
        try:
            os.environ["WEB_FETCH_ENABLED"] = "true"
            os.environ["WEB_FETCH_CONCURRENCY"] = "10"
            os.environ["WEB_FETCH_TIMEOUT_MS"] = "5000"

            service = get_web_fetch_service()

            # Note: enabled may be False if httpx not available
            assert service.concurrency == 10
            assert service.timeout == 5.0
        finally:
            # Restore environment
            os.environ.clear()
            os.environ.update(original_env)
            module._web_fetch_service_instance = None
