"""
SSE (Streamable HTTP) MCP connection using the official MCP SDK.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


class SseMcpConnection:
    """SSE-based MCP client connection."""

    def __init__(self, url: str, headers: Optional[Dict[str, str]] = None) -> None:
        self._url = url
        self._headers = headers or {}
        self._session = None
        self._client = None
        self._context = None

    async def start(self) -> None:
        """Connect to the MCP server via SSE (Streamable HTTP)."""
        try:
            from mcp.client.session import ClientSession
            from mcp.client.streamable_http import streamablehttp_client

            # Start SSE client (streamable http)
            self._context = streamablehttp_client(self._url, headers=self._headers)
            # streamablehttp_client yields (read, write, worker)
            read, write, _ = await self._context.__aenter__()
            
            self._session = ClientSession(read, write)
            await self._session.initialize()
            self._client = self._session
        except Exception as e:
            self._session = None
            self._client = None
            raise RuntimeError(f"Failed to start SSE MCP connection: {e}") from e

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
