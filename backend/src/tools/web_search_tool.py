"""
LangChain tool wrapper for web search service
"""

import asyncio
import logging

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Check if LangChain is available
try:
    from langchain.callbacks.manager import (
        AsyncCallbackManagerForToolRun,
        CallbackManagerForToolRun,
    )
    from langchain.tools import BaseTool

    LANGCHAIN_AVAILABLE = True
except ImportError:
    logger.warning("LangChain not available. WebSearchTool will not be functional.")
    LANGCHAIN_AVAILABLE = False

    # Create dummy base class for type hints
    class BaseTool:
        name: str = ""
        description: str = ""

        def _run(self, *args, **kwargs):
            pass

        async def _arun(self, *args, **kwargs):
            pass


class WebSearchInput(BaseModel):
    """Input schema for web search tool"""

    query: str = Field(description="The search query to look up on the web")
    max_results: int = Field(
        default=5, description="Maximum number of search results to return (default: 5)"
    )


class WebSearchTool(BaseTool):
    """
    Tool for searching the web using DuckDuckGo or Tavily

    This tool searches the web for information and returns formatted results
    with titles, URLs, and snippets. Can be used by agents to gather real-time
    information from the internet.
    """

    name: str = "web_search"
    description: str = (
        "Search the web for current information using natural language queries. "
        "Returns a list of relevant web pages with titles, URLs, and content snippets. "
        "Use this when you need up-to-date information, news, or facts not in your knowledge base. "
        "Input should be a clear search query."
    )
    args_schema: type[BaseModel] = WebSearchInput
    return_direct: bool = False

    def __init__(self, **kwargs):
        """Initialize the web search tool"""
        super().__init__(**kwargs)
        if not LANGCHAIN_AVAILABLE:
            raise ImportError(
                "LangChain is required to use WebSearchTool. "
                "Install with: pip install langchain"
            )

    def _run(
        self,
        query: str,
        max_results: int = 5,
        run_manager: CallbackManagerForToolRun | None = None,
    ) -> str:
        """
        Synchronous version - runs async in event loop

        Args:
            query: Search query
            max_results: Maximum number of results
            run_manager: Callback manager

        Returns:
            Formatted search results as string
        """
        try:
            # Run async version in event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is already running (e.g., in Jupyter), create a new one
                import nest_asyncio

                nest_asyncio.apply()
                return loop.run_until_complete(
                    self._arun(query, max_results, run_manager)
                )
            else:
                return asyncio.run(self._arun(query, max_results, run_manager))
        except Exception as e:
            logger.error(f"Web search failed: {e}", exc_info=True)
            return f"Error performing web search: {str(e)}"

    async def _arun(
        self,
        query: str,
        max_results: int = 5,
        run_manager: AsyncCallbackManagerForToolRun | None = None,
    ) -> str:
        """
        Asynchronous version - performs web search

        Args:
            query: Search query
            max_results: Maximum number of results
            run_manager: Async callback manager

        Returns:
            Formatted search results as string
        """
        try:
            from ..services.web_search_service import get_web_search_service

            search_service = get_web_search_service()

            # Perform search
            results = await search_service.search(query, max_results=max_results)

            if not results:
                return f"No results found for query: {query}"

            # Format results for agent consumption
            formatted_results = [f"Search results for '{query}':"]

            for i, result in enumerate(results, 1):
                formatted_results.append(f"\n{i}. {result.title}")
                formatted_results.append(f"   URL: {result.url}")
                formatted_results.append(f"   Snippet: {result.snippet}")

                # Include enrichment info if available
                if result.content and result.tokens_estimate:
                    formatted_results.append(
                        f"   (Full content available: {result.tokens_estimate} tokens)"
                    )

                if result.published_at:
                    formatted_results.append(
                        f"   Published: {result.published_at.strftime('%Y-%m-%d')}"
                    )

            formatted_output = "\n".join(formatted_results)

            logger.info(
                f"Web search returned {len(results)} results for query: '{query[:50]}'"
            )

            return formatted_output

        except Exception as e:
            logger.error(f"Web search failed: {e}", exc_info=True)
            return f"Error performing web search: {str(e)}"


def get_web_search_tool() -> WebSearchTool:
    """
    Get an instance of the web search tool

    Returns:
        WebSearchTool instance

    Raises:
        ImportError: If LangChain is not available
    """
    if not LANGCHAIN_AVAILABLE:
        raise ImportError(
            "LangChain is required to use WebSearchTool. "
            "Install with: pip install langchain"
        )

    return WebSearchTool()
