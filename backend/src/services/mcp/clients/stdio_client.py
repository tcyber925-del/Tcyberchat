"""
Stdio MCP connection (scaffold) — spawn a process and talk JSON over stdio.
Replace with a real MCP stdio client from an official SDK.
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional


class StdioMcpConnection:
    def __init__(self, command: str, args: Optional[list[str]] = None) -> None:
        self._command = command
        self._args = args or []
        self._proc: Optional[asyncio.subprocess.Process] = None

    async def start(self) -> None:
        # Scaffold: do not actually spawn to avoid platform issues in CI
        return

    async def stop(self) -> None:
        return

    async def list_tools(self) -> List[Dict[str, Any]]:
        return []

    async def call_tool(self, name: str, params: Dict[str, Any], stream: bool = False) -> Dict[str, Any]:
        return {"error": "stdio mcp not implemented in scaffold"}