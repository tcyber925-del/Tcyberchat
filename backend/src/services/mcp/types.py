"""
Types and config structures for MultiMcpClient.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any


@dataclass
class McpServerConfig:
    id: str
    transport: str  # "stdio" | "wss"
    enabled: bool = True
    # stdio
    command: Optional[str] = None
    args: Optional[List[str]] = None
    # wss
    url: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    # meta
    tags: List[str] = field(default_factory=list)
    # timeouts
    timeouts: Dict[str, int] = field(default_factory=lambda: {"connectMs": 3000, "readMs": 15000})


@dataclass
class McpMultiConfig:
    servers: List[McpServerConfig] = field(default_factory=list)


@dataclass
class McpTool:
    name: str
    description: Optional[str] = None
    input_schema: Optional[Dict[str, Any]] = None


@dataclass
class McpServerState:
    config: McpServerConfig
    connected: bool = False
    healthy: bool = False
    tools: List[McpTool] = field(default_factory=list)
    last_error: Optional[str] = None


__all__ = [
    "McpServerConfig",
    "McpMultiConfig",
    "McpTool",
    "McpServerState",
]