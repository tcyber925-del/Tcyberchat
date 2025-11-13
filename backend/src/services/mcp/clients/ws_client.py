"""
WebSocket MCP connection (hybrid):
- If an official MCP SDK is available, use it for connect/list/call.
- Otherwise, gracefully fall back to a stub that reports not implemented.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


class WsMcpConnection:
    def __init__(self, url: str, headers: Optional[Dict[str, str]] = None, connect_timeout: float = 3.0) -> None:
        self._url = url
        self._headers = headers or {}
        self._connect_timeout = connect_timeout
        self._cli = None  # SDK client when available

    async def start(self) -> None:
        try:
            # Example API – adjust when wiring the official SDK
            from mcp.client import Client  # type: ignore
            self._cli = await Client.connect_ws(self._url, headers=self._headers, timeout=self._connect_timeout)
        except Exception:
            # SDK not available or failed to connect
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
            # Normalize to list[{name, description, input_schema?}]
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
            return {"error": "ws mcp client not available"}
        try:
            if stream:
                # Example streaming interface – adapt to SDK
                result_chunks = []
                async for evt in self._cli.call_tool_stream(name, params):
                    result_chunks.append(evt)
                return {"events": result_chunks}
            else:
                res = await self._cli.call_tool(name, params)
                # Normalize known shapes (e.g., http.get)
                if isinstance(res, dict):
                    return res
                return {"result": res}
        except Exception as e:
            return {"error": str(e)}
