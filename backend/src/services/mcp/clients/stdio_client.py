"""
Stdio MCP connection using the official MCP SDK.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


class StdioMcpConnection:
    """Stdio-based MCP client connection."""

    def __init__(self, command: str, args: Optional[list[str]] = None) -> None:
        self._command = command
        self._args = args or []
        self._session = None
        self._client = None
        self._context = None

    async def start(self) -> None:
        """Spawn the MCP server process and connect via stdio."""
        try:
            from mcp.client.session import ClientSession
            from mcp.client.stdio import stdio_client

            # Start stdio server process
            server_params = {"command": self._command, "args": self._args}
            self._context = stdio_client(server_params)
            read, write = await self._context.__aenter__()
            self._session = ClientSession(read, write)
            await self._session.initialize()
            self._client = self._session
        except Exception as e:
            self._session = None
            self._client = None
            raise RuntimeError(f"Failed to start stdio MCP connection: {e}") from e

    async def stop(self) -> None:
        """Stop the MCP server process."""
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
            return {"error": "stdio mcp client not available"}
        try:
            result = await self._client.call_tool(name, params)
            # MCP SDK returns CallToolResult with content list
            if hasattr(result, "content"):
                content_text = ""
                for block in result.content:
                    if hasattr(block, "text"):
                        content_text += block.text
                return {"content": content_text, "isError": getattr(result, "isError", False)}
            return {"result": str(result)}
        except Exception as e:
            return {"error": str(e)}
