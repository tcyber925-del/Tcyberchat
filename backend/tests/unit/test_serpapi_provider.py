"""
Unit tests for SerpAPI provider
"""

from unittest.mock import Mock, patch

import pytest

from backend.src.services.web_search_service import SerpAPIProvider


class TestSerpAPIProvider:
    """Test SerpAPI provider"""

    def test_initialization(self):
        """Test provider can be initialized"""
        provider = SerpAPIProvider(api_key="test_key")

        assert provider.name == "serpapi"
        assert provider.api_key == "test_key"

    def test_initialization_from_env(self):
        """Test provider reads API key from environment"""
        with patch.dict("os.environ", {"SERPAPI_API_KEY": "env_key"}):
            provider = SerpAPIProvider()
            assert provider.api_key == "env_key"

    def test_is_available_no_api_key(self):
        """Test provider not available without API key"""
        provider = SerpAPIProvider()
        assert not provider.is_available()

    def test_is_available_no_module(self):
        """Test provider not available without serpapi module"""
        with patch(
            "backend.src.services.web_search_service.os.getenv", return_value="test_key"
        ):
            provider = SerpAPIProvider(api_key="test_key")

            with patch("builtins.__import__", side_effect=ImportError):
                assert not provider.is_available()

    @pytest.mark.asyncio
    async def test_search_success(self):
        """Test successful search"""
        provider = SerpAPIProvider(api_key="test_key")

        # Mock serpapi module and response
        mock_response = {
            "organic_results": [
                {
                    "title": "Test Result 1",
                    "link": "https://example.com/1",
                    "snippet": "Test snippet 1",
                },
                {
                    "title": "Test Result 2",
                    "link": "https://example.com/2",
                    "snippet": "Test snippet 2",
                },
            ]
        }

        with patch(
            "backend.src.services.web_search_service.SerpAPIProvider.is_available",
            return_value=True,
        ):
            # Mock serpapi.Client where it's imported in the search method
            with patch("serpapi.Client") as mock_client_class:
                mock_client = Mock()
                # client.search() returns a SerpResults object that acts like a dict
                mock_client.search.return_value = mock_response
                mock_client_class.return_value = mock_client

                results = await provider.search("test query", max_results=5)

                assert len(results) == 2
                assert results[0].title == "Test Result 1"
                assert results[0].url == "https://example.com/1"
                assert results[0].snippet == "Test snippet 1"
                assert results[0].source == "web_search"
                assert 0 < results[0].relevance_score <= 1.0

    @pytest.mark.asyncio
    async def test_search_not_available(self):
        """Test search fails when provider not available"""
        provider = SerpAPIProvider()

        with pytest.raises(RuntimeError, match="SerpAPI provider not available"):
            await provider.search("test query")

    @pytest.mark.asyncio
    async def test_search_invalid_api_key(self):
        """Test search handles invalid API key"""
        provider = SerpAPIProvider(api_key="invalid_key")

        with patch(
            "backend.src.services.web_search_service.SerpAPIProvider.is_available",
            return_value=True,
        ):
            # Mock serpapi.Client where it's imported in the search method
            with patch("serpapi.Client") as mock_client_class:
                mock_client = Mock()
                mock_client.search.side_effect = Exception("Invalid API key")
                mock_client_class.return_value = mock_client

                with pytest.raises(RuntimeError, match="SerpAPI authentication failed"):
                    await provider.search("test query")

    @pytest.mark.asyncio
    async def test_search_rate_limit(self):
        """Test search handles rate limit errors"""
        provider = SerpAPIProvider(api_key="test_key")

        with patch(
            "backend.src.services.web_search_service.SerpAPIProvider.is_available",
            return_value=True,
        ):
            # Mock serpapi.Client where it's imported in the search method
            with patch("serpapi.Client") as mock_client_class:
                mock_client = Mock()
                mock_client.search.side_effect = Exception("Rate limit exceeded")
                mock_client_class.return_value = mock_client

                with pytest.raises(RuntimeError, match="SerpAPI rate limit exceeded"):
                    await provider.search("test query")

    @pytest.mark.asyncio
    async def test_search_empty_results(self):
        """Test search with empty results"""
        provider = SerpAPIProvider(api_key="test_key")

        mock_response = {"organic_results": []}

        with patch(
            "backend.src.services.web_search_service.SerpAPIProvider.is_available",
            return_value=True,
        ):
            # Mock serpapi.Client where it's imported in the search method
            with patch("serpapi.Client") as mock_client_class:
                mock_client = Mock()
                mock_client.search.return_value = mock_response
                mock_client_class.return_value = mock_client

                results = await provider.search("test query", max_results=5)

                assert len(results) == 0

    @pytest.mark.asyncio
    async def test_search_max_results_respected(self):
        """Test max_results parameter is respected"""
        provider = SerpAPIProvider(api_key="test_key")

        # Mock 10 results
        mock_response = {
            "organic_results": [
                {
                    "title": f"Test Result {i}",
                    "link": f"https://example.com/{i}",
                    "snippet": f"Test snippet {i}",
                }
                for i in range(10)
            ]
        }

        with patch(
            "backend.src.services.web_search_service.SerpAPIProvider.is_available",
            return_value=True,
        ):
            # Mock serpapi.Client where it's imported in the search method
            with patch("serpapi.Client") as mock_client_class:
                mock_client = Mock()
                mock_client.search.return_value = mock_response
                mock_client_class.return_value = mock_client

                results = await provider.search("test query", max_results=3)

                # Should return only 3 results
                assert len(results) == 3

    @pytest.mark.asyncio
    async def test_search_handles_missing_fields(self):
        """Test search handles results with missing fields gracefully"""
        provider = SerpAPIProvider(api_key="test_key")

        mock_response = {
            "organic_results": [
                {
                    "title": "Test Result 1",
                    "link": "https://example.com/1",
                    # Missing snippet
                },
                {
                    "snippet": "Test snippet 2"
                    # Missing title and link
                },
            ]
        }

        with patch(
            "backend.src.services.web_search_service.SerpAPIProvider.is_available",
            return_value=True,
        ):
            # Mock serpapi.Client where it's imported in the search method
            with patch("serpapi.Client") as mock_client_class:
                mock_client = Mock()
                mock_client.search.return_value = mock_response
                mock_client_class.return_value = mock_client

                results = await provider.search("test query", max_results=5)

                assert len(results) == 2
                assert results[0].title == "Test Result 1"
                assert results[0].snippet == ""  # Default for missing field
                assert results[1].title == "No title"  # Default for missing field
