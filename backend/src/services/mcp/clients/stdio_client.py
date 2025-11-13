"""
Stdio MCP connection (hybrid):
- If an official MCP SDK is available, spawn/connect and relay calls.
- Otherwise, return not-implemented gracefully.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


class StdioMcpConnection:
    def __init__(self, command: str, args: Optional[list[str]] = None) -> None:
        self._command = command
        self._args = args or []
        self._cli = None

    async def start(self) -> None:
        try:
            from mcp.client import Client  # type: ignore
            self._cli = await Client.connect_stdio(self._command, self._args)
        except Exception:
            self._cli = None

    async def stop(self) -> None:
        try:
            if self._cli is not None:
                await self._cli.close()
        except Exception:
            pass

    async def list_tools(self) -> List[Dict[str, Any]]:
        if self._cli is None:
            return []
        try:
            tools = await self._cli.list_tools()
            out: List[Dict[str, Any]] = []
            for t in tools or []:
                name = getattr(t, "name", None) or (t.get("name") if isinstance(t, dict) else None)
                desc = getattr(t, "description", None) or (t.get("description") if isinstance(t, dict) else None)
                if name:
                    out.append({"name": name, "description": desc})
            return out
        except Exception:
            return []

    async def call_tool(self, name: str, params: Dict[str, Any], stream: bool = False) -> Dict[str, Any]:
        if self._cli is None:
            return {"error": "stdio mcp client not available"}
        try:
            if stream:
                result_chunks = []
                async for evt in self._cli.call_tool_stream(name, params):
                    result_chunks.append(evt)
                return {"events": result_chunks}
            else:
                res = await self._cli.call_tool(name, params)
                if isinstance(res, dict):
                    return res
                return {"result": res}
        except Exception as e:
            return {"error": str(e)}
