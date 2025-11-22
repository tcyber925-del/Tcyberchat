"""
LangChain tool wrapper for web fetch service
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
    logger.warning("LangChain not available. WebFetchTool will not be functional.")
    LANGCHAIN_AVAILABLE = False

    # Create dummy base class for type hints
    class BaseTool:
        name: str = ""
        description: str = ""

        def _run(self, *args, **kwargs):
            pass

        async def _arun(self, *args, **kwargs):
            pass


class WebFetchInput(BaseModel):
    """Input schema for web fetch tool"""

    url: str = Field(
        description="The URL of the web page to fetch and extract content from"
    )


class WebFetchTool(BaseTool):
    """
    Tool for fetching and extracting content from web pages

    This tool fetches a web page from a URL and extracts its readable content,
    removing boilerplate, navigation, and ads. Supports both HTML and PDF documents.
    """

    name: str = "web_fetch"
    description: str = (
        "Fetch and extract the full text content from a specific web page URL. "
        "This tool downloads the page and extracts the main content, removing ads, "
        "navigation, and other boilerplate. Supports HTML pages and PDF documents. "
        "Use this when you have a specific URL and need the full content, not just a summary. "
        "Input should be a complete URL (e.g., https://example.com/article)."
    )
    args_schema: type[BaseModel] = WebFetchInput
    return_direct: bool = False

    def __init__(self, **kwargs):
        """Initialize the web fetch tool"""
        super().__init__(**kwargs)
        if not LANGCHAIN_AVAILABLE:
            raise ImportError(
                "LangChain is required to use WebFetchTool. "
                "Install with: pip install langchain"
            )

    def _run(
        self, url: str, run_manager: CallbackManagerForToolRun | None = None
    ) -> str:
        """
        Synchronous version - runs async in event loop

        Args:
            url: URL to fetch
            run_manager: Callback manager

        Returns:
            Extracted content as string
        """
        try:
            # Run async version in event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is already running (e.g., in Jupyter), create a new one
                import nest_asyncio

                nest_asyncio.apply()
                return loop.run_until_complete(self._arun(url, run_manager))
            else:
                return asyncio.run(self._arun(url, run_manager))
        except Exception as e:
            logger.error(f"Web fetch failed: {e}", exc_info=True)
            return f"Error fetching URL: {str(e)}"

    async def _arun(
        self, url: str, run_manager: AsyncCallbackManagerForToolRun | None = None
    ) -> str:
        """
        Asynchronous version - fetches and extracts content

        Args:
            url: URL to fetch
            run_manager: Async callback manager

        Returns:
            Extracted content as string
        """
        try:
            from ..services.web_fetch_service import get_web_fetch_service

            fetch_service = get_web_fetch_service()

            # Check if fetch is enabled
            if not fetch_service.enabled:
                return (
                    "Web fetch is disabled. Enable it by setting WEB_FETCH_ENABLED=true "
                    "and installing httpx: pip install httpx"
                )

            # Fetch and extract content
            result = await fetch_service.fetch_url(url)

            if result.error:
                return f"Error fetching {url}: {result.error}"

            if not result.content:
                return f"No content could be extracted from {url}"

            # Format extracted content
            output_parts = []

            if result.title:
                output_parts.append(f"Title: {result.title}")

            output_parts.append(f"URL: {result.canonical_url or result.url}")

            if result.published_at:
                output_parts.append(
                    f"Published: {result.published_at.strftime('%Y-%m-%d')}"
                )

            if result.content_type:
                output_parts.append(f"Content Type: {result.content_type}")

            output_parts.append(f"\nContent ({result.tokens_estimate} tokens):")
            output_parts.append("-" * 50)
            output_parts.append(result.content)

            formatted_output = "\n".join(output_parts)

            logger.info(
                f"Fetched content from {url}: {result.tokens_estimate} tokens, "
                f"title: {result.title[:50] if result.title else 'N/A'}"
            )

            return formatted_output

        except Exception as e:
            logger.error(f"Web fetch failed: {e}", exc_info=True)
            return f"Error fetching URL: {str(e)}"


def get_web_fetch_tool() -> WebFetchTool:
    """
    Get an instance of the web fetch tool

    Returns:
        WebFetchTool instance

    Raises:
        ImportError: If LangChain is not available
    """
    if not LANGCHAIN_AVAILABLE:
        raise ImportError(
            "LangChain is required to use WebFetchTool. "
            "Install with: pip install langchain"
        )

    return WebFetchTool()
