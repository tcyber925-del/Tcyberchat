"""
WebSocket MCP connection using the official MCP SDK.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


class WsMcpConnection:
    """WebSocket-based MCP client connection."""

    def __init__(self, url: str, headers: Optional[Dict[str, str]] = None, connect_timeout: float = 3.0) -> None:
        self._url = url
        self._headers = headers or {}
        self._connect_timeout = connect_timeout
        self._session = None
        self._client = None
        self._context = None

    async def start(self) -> None:
        """Connect to the MCP server via WebSocket."""
        try:
            from mcp.client.session import ClientSession
            # Prefer SDK-provided websocket client if available, otherwise fall back to local adapter
            try:
                from mcp.client.websocket import websocket_client  # type: ignore
            except Exception:
                from ..clients.websocket_client import websocket_client

            # Create websocket transport and session
            self._context = websocket_client(self._url, headers=self._headers or {})
            read, write = await self._context.__aenter__()
            self._session = ClientSession(read, write)
            await self._session.initialize()
            self._client = self._session
        except Exception as e:
            # Failed to connect or SDK not available
            self._session = None
            self._client = None
            raise RuntimeError(f"Failed to start WS MCP connection: {e}") from e

    async def stop(self) -> None:
        """Close the MCP client session."""
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
            return {"error": "ws mcp client not available"}
        try:
            result = await self._client.call_tool(name, params)
            # MCP SDK returns CallToolResult with content list
            out: Dict[str, Any] = {}
            if hasattr(result, "content"):
                # Combine content blocks
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
