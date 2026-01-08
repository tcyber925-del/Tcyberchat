"""
SSE (Streamable HTTP) MCP connection using the official MCP SDK.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
import asyncio
import logging
import traceback

logger = logging.getLogger(__name__)


class SseMcpConnection:
    """SSE-based MCP client connection."""

    def __init__(self, url: str, headers: Optional[Dict[str, str]] = None, timeout: float = 60.0) -> None:
        self._url = url
        self._headers = headers or {}
        self._timeout = timeout
        self._session = None
        self._client = None
        self._context = None

    async def start(self) -> None:
        """Connect to the MCP server via SSE (Streamable HTTP)."""
        try:
            from mcp.client.session import ClientSession
            from mcp.client.streamable_http import streamablehttp_client

            logger.info(f"Connecting to SSE MCP server: {self._url} (timeout={self._timeout}s)")
            # Start SSE client (streamable http)
            # streamablehttp_client likely uses aiohttp or httpx underneath.
            # We enforce timeout on the connection phase.
            self._context = streamablehttp_client(self._url, headers=self._headers)
            
            # streamablehttp_client yields (read, write, worker)
            read, write, _ = await asyncio.wait_for(self._context.__aenter__(), timeout=self._timeout)
            
            self._session = ClientSession(read, write)
            await asyncio.wait_for(self._session.initialize(), timeout=self._timeout)
            self._client = self._session
            logger.info(f"Connected to SSE MCP server: {self._url}")
        except asyncio.TimeoutError:
            self._session = None
            self._client = None
            logger.error(f"Timeout connecting to SSE MCP server: {self._url}")
            raise RuntimeError(f"Timeout connecting to {self._url} after {self._timeout}s")
        except Exception as e:
            self._session = None
            self._client = None
            # Log full traceback for debugging
            logger.error(f"Failed to start SSE MCP connection to {self._url}: {e}")
            logger.debug(traceback.format_exc())
            # Try to extract more info if it's an HTTP error (generic check as we don't import aiohttp)
            msg = str(e)
            if hasattr(e, 'status'):
                msg = f"HTTP {e.status}: {msg}" # type: ignore
            raise RuntimeError(f"Failed to start SSE MCP connection: {msg}") from e

    async def stop(self) -> None:
        """Stop the MCP server connection."""
        if self._context is not None:
            try:
                await self._context.__aexit__(None, None, None)
            except Exception:
                pass
            finally:
                self._session = None
                self._client = None
                self._context = None

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from the MCP server."""
        if self._client is None:
            return []
        try:
            result = await self._client.list_tools()
            out: List[Dict[str, Any]] = []
            for tool in result.tools:
                out.append({
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema if hasattr(tool, "inputSchema") else None,
                })
            return out
        except Exception:
            return []

    async def call_tool(self, name: str, params: Dict[str, Any], stream: bool = False) -> Dict[str, Any]:
        """Call a tool on the MCP server."""
        if self._client is None:
            return {"error": "sse mcp client not available"}
        try:
            result = await self._client.call_tool(name, params)
            out: Dict[str, Any] = {}
            if hasattr(result, "content"):
                content_text = ""
                for block in result.content:
                    if hasattr(block, "text"):
                        content_text += block.text
                out["content"] = content_text
            if hasattr(result, "structuredContent") and getattr(result, "structuredContent") is not None:
                out["structuredContent"] = getattr(result, "structuredContent")
            out["isError"] = getattr(result, "isError", False)
            if out:
                return out
            return {"result": str(result)}
        except Exception as e:
            return {"error": str(e)}
