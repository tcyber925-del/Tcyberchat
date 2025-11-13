"""
WebSocket MCP connection (scaffold).
Uses JSON-RPC-like envelopes; replace with real MCP SDK.
"""
from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List, Optional


class WsMcpConnection:
    def __init__(self, url: str, headers: Optional[Dict[str, str]] = None, connect_timeout: float = 3.0) -> None:
        self._url = url
        self._headers = headers or {}
        self._connect_timeout = connect_timeout
        self._ws = None  # lazy

    async def start(self) -> None:
        # Deferred: integrate websockets/anyio client here
        # Keep as no-op to avoid dependency issues in scaffold
        return

    async def stop(self) -> None:
        return

    async def list_tools(self) -> List[Dict[str, Any]]:
        # In scaffold, unknown. Return empty; discovery is simulated in warm_connect().
        return []

    async def call_tool(self, name: str, params: Dict[str, Any], stream: bool = False) -> Dict[str, Any]:
        # Scaffold: not implemented
        return {"error": "ws mcp not implemented in scaffold"}