"""
Base interfaces for MCP client connections (stdio / WSS).
This is a scaffold to be replaced/augmented by a real MCP SDK integration.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


class McpConnection:
    async def start(self) -> None:  # pragma: no cover
        raise NotImplementedError

    async def stop(self) -> None:  # pragma: no cover
        raise NotImplementedError

    async def list_tools(self) -> List[Dict[str, Any]]:  # pragma: no cover
        raise NotImplementedError

    async def call_tool(self, name: str, params: Dict[str, Any], stream: bool = False) -> Dict[str, Any]:  # pragma: no cover
        raise NotImplementedError