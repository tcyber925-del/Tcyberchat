"""
Unit tests for LangChain web tool wrappers
"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest


# Helper functions
def _check_langchain_available() -> bool:
    """Check if LangChain is available"""
    try:
        import langchain

        return True
    except ImportError:
        return False


# Test WebSearchTool
class TestWebSearchTool:
    """Test WebSearchTool wrapper"""

    def test_tool_imports_gracefully_without_langchain(self):
        """Test that tool module can be imported even without LangChain"""
        try:
            from backend.src.tools import web_search_tool

            assert True
        except ImportError:
            pytest.fail("Tool module should import even without LangChain")

    @pytest.mark.skipif(
        not _check_langchain_available(), reason="LangChain not installed"
    )
    def test_tool_initialization(self):
        """Test WebSearchTool can be initialized"""
        from backend.src.tools.web_search_tool import WebSearchTool

        tool = WebSearchTool()

        assert tool.name == "web_search"
        assert "search" in tool.description.lower()
        assert tool.return_direct is False

    @pytest.mark.skipif(
        not _check_langchain_available(), reason="LangChain not installed"
    )
    @pytest.mark.asyncio
    async def test_tool_arun_success(self):
        """Test async tool execution with mocked service"""
        from backend.src.services.web_search_service import SearchResult
        from backend.src.tools.web_search_tool import WebSearchTool

        tool = WebSearchTool()

        # Mock search service
        mock_results = [
            SearchResult(
                title="Test Result 1",
                url="https://example.com/1",
                snippet="Test snippet 1",
                relevance_score=0.9,
                timestamp=datetime.now(),
            ),
            SearchResult(
                title="Test Result 2",
                url="https://example.com/2",
                snippet="Test snippet 2",
                relevance_score=0.8,
                timestamp=datetime.now(),
            ),
        ]

        with patch(
            "backend.src.services.web_search_service.get_web_search_service"
        ) as mock_get_service:
            mock_service = Mock()
            mock_service.search = AsyncMock(return_value=mock_results)
            mock_get_service.return_value = mock_service

            result = await tool._arun("test query")

            assert "Test Result 1" in result
            assert "https://example.com/1" in result
            assert "Test snippet 1" in result

    @pytest.mark.skipif(
        not _check_langchain_available(), reason="LangChain not installed"
    )
    @pytest.mark.asyncio
    async def test_tool_arun_no_results(self):
        """Test async tool execution with no results"""
        from backend.src.tools.web_search_tool import WebSearchTool

        tool = WebSearchTool()

        with patch(
            "backend.src.services.web_search_service.get_web_search_service"
        ) as mock_get_service:
            mock_service = Mock()
            mock_service.search = AsyncMock(return_value=[])
            mock_get_service.return_value = mock_service

            result = await tool._arun("test query")

            assert "No results found" in result


# Test WebFetchTool
class TestWebFetchTool:
    """Test WebFetchTool wrapper"""

    def test_tool_imports_gracefully_without_langchain(self):
        """Test that tool module can be imported even without LangChain"""
        try:
            from backend.src.tools import web_fetch_tool

            assert True
        except ImportError:
            pytest.fail("Tool module should import even without LangChain")

    @pytest.mark.skipif(
        not _check_langchain_available(), reason="LangChain not installed"
    )
    def test_tool_initialization(self):
        """Test WebFetchTool can be initialized"""
        from backend.src.tools.web_fetch_tool import WebFetchTool

        tool = WebFetchTool()

        assert tool.name == "web_fetch"
        assert "fetch" in tool.description.lower()
        assert tool.return_direct is False

    @pytest.mark.skipif(
        not _check_langchain_available(), reason="LangChain not installed"
    )
    @pytest.mark.asyncio
    async def test_tool_arun_success(self):
        """Test async tool execution with mocked service"""
        from backend.src.services.web_fetch_service import FetchResult
        from backend.src.tools.web_fetch_tool import WebFetchTool

        tool = WebFetchTool()

        # Mock fetch result
        mock_result = FetchResult(
            url="https://example.com",
            canonical_url="https://example.com/page",
            content="Test content from the page",
            content_type="text/html",
            title="Test Page",
            published_at=datetime(2024, 1, 1),
            extracted_at=datetime.now(),
            tokens_estimate=50,
            error=None,
        )

        with patch(
            "backend.src.services.web_fetch_service.get_web_fetch_service"
        ) as mock_get_service:
            mock_service = Mock()
            mock_service.enabled = True
            mock_service.fetch_url = AsyncMock(return_value=mock_result)
            mock_get_service.return_value = mock_service

            result = await tool._arun("https://example.com")

            assert "Test Page" in result
            assert "https://example.com" in result
            assert "Test content from the page" in result
            assert "50 tokens" in result

    @pytest.mark.skipif(
        not _check_langchain_available(), reason="LangChain not installed"
    )
    @pytest.mark.asyncio
    async def test_tool_arun_fetch_disabled(self):
        """Test async tool execution when fetch is disabled"""
        from backend.src.tools.web_fetch_tool import WebFetchTool

        tool = WebFetchTool()

        with patch(
            "backend.src.services.web_fetch_service.get_web_fetch_service"
        ) as mock_get_service:
            mock_service = Mock()
            mock_service.enabled = False
            mock_get_service.return_value = mock_service

            result = await tool._arun("https://example.com")

            assert "disabled" in result.lower()

    @pytest.mark.skipif(
        not _check_langchain_available(), reason="LangChain not installed"
    )
    @pytest.mark.asyncio
    async def test_tool_arun_fetch_error(self):
        """Test async tool execution with fetch error"""
        from backend.src.services.web_fetch_service import FetchResult
        from backend.src.tools.web_fetch_tool import WebFetchTool

        tool = WebFetchTool()

        mock_result = FetchResult(
            url="https://example.com",
            canonical_url="https://example.com",
            content=None,
            content_type=None,
            title=None,
            published_at=None,
            extracted_at=datetime.now(),
            tokens_estimate=0,
            error="Timeout",
        )

        with patch(
            "backend.src.services.web_fetch_service.get_web_fetch_service"
        ) as mock_get_service:
            mock_service = Mock()
            mock_service.enabled = True
            mock_service.fetch_url = AsyncMock(return_value=mock_result)
            mock_get_service.return_value = mock_service

            result = await tool._arun("https://example.com")

            assert "Error" in result or "Timeout" in result


# Test agent creation
class TestWebAgent:
    """Test web agent setup"""

    def test_agent_module_imports_gracefully(self):
        """Test that agent module can be imported even without LangChain"""
        try:
            from backend.src.agents import web_agent

            assert True
        except ImportError:
            pytest.fail("Agent module should import even without LangChain")

    @pytest.mark.skipif(
        not _check_langchain_available(), reason="LangChain not installed"
    )
    def test_get_web_agent_returns_none_without_llm(self):
        """Test that get_web_agent returns None gracefully when LLM cannot be created"""
        from backend.src.agents.web_agent import get_web_agent

        # Without a running llama.cpp server, should return None gracefully
        with patch(
            "backend.src.agents.web_agent.get_llm_for_agent",
            side_effect=Exception("No LLM"),
        ):
            agent = get_web_agent()
            assert agent is None
