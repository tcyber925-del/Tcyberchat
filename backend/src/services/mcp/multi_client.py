"""
MultiMcpClient — manages connections to multiple MCP servers (stdio and WSS).
This is a scaffold designed to be extended with a real MCP SDK.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Tuple

from ..redis_client import get_redis
from .types import McpMultiConfig, McpServerConfig, McpServerState, McpTool


class MultiMcpClient:
    def __init__(self, config: McpMultiConfig) -> None:
        self._config = config
        self._servers: Dict[str, McpServerState] = {
            s.id: McpServerState(config=s) for s in (config.servers or [])
        }

    @classmethod
    def from_env(cls) -> "MultiMcpClient":
        raw = os.getenv("MCP_MULTI", "").strip()
        servers: List[McpServerConfig] = []
        if raw:
            try:
                data = json.loads(raw)
                for s in data.get("servers", []) or []:
                    servers.append(
                        McpServerConfig(
                            id=s.get("id"),
                            transport=s.get("transport"),
                            enabled=bool(s.get("enabled", True)),
                            command=s.get("command"),
                            args=s.get("args") or [],
                            url=s.get("url"),
                            headers=s.get("headers") or {},
                            tags=s.get("tags") or [],
                            timeouts=s.get("timeouts") or {"connectMs": 3000, "readMs": 15000},
                        )
                    )
            except Exception:
                # Invalid config — fall back to empty
                servers = []
        return cls(McpMultiConfig(servers=servers))

    # --- Introspection ---
    def list_servers(self) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for sid, st in self._servers.items():
            out.append(
                {
                    "id": sid,
                    "transport": st.config.transport,
                    "enabled": st.config.enabled,
                    "tags": st.config.tags,
                    "connected": st.connected,
                    "healthy": st.healthy,
                    "tools": [t.name for t in st.tools],
                    "last_error": st.last_error,
                }
            )
        return out

    # --- Connection management (scaffold) ---
    async def warm_connect(self) -> None:
        """Attempt to connect and discover tools for all enabled servers.
        In this scaffold, we simulate discovery; integrate a real MCP SDK later.
        """
        for sid, st in self._servers.items():
            if not st.config.enabled:
                continue
            try:
                # TODO: integrate real MCP connect + list_tools
                # For now, mark connected and add a common http.get alias if tags include 'docs' or 'http'
                st.connected = True
                st.healthy = True
                tools: List[McpTool] = []
                if any(t in st.config.tags for t in ["docs", "http", "official"]):
                    tools.append(McpTool(name="http.get", description="HTTP GET"))
                    tools.append(McpTool(name="fetch_url", description="Fetch a URL"))
                st.tools = tools
                st.last_error = None
            except Exception as e:
                st.connected = False
                st.healthy = False
                st.last_error = str(e)

    # --- Routing helpers ---
    def _find_servers_for_tool(self, tool: str) -> List[McpServerState]:
        matches: List[McpServerState] = []
        for st in self._servers.values():
            if not st.config.enabled or not st.connected or not st.healthy:
                continue
            if any(tool == t.name for t in st.tools):
                matches.append(st)
        return matches

    def _select_server_auto(self, desired_tool: str, preferred_tags: Optional[List[str]] = None) -> Optional[McpServerState]:
        cands = self._find_servers_for_tool(desired_tool)
        if preferred_tags:
            cands = sorted(cands, key=lambda s: int(any(t in s.config.tags for t in preferred_tags)), reverse=True)
        return cands[0] if cands else None

    # --- Tool invocation (scaffold) ---
    async def call_tool(
        self,
        server_id_or_auto: str,
        tool_name: str,
        params: Dict[str, Any],
        *,
        preferred_tags: Optional[List[str]] = None,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """Call a tool on a specific or auto-selected server.
        This scaffold implements only a special-case for http.get/fetch_url: it will perform a direct HTTP fetch as a
        placeholder when no SDK is wired, caching the content. Replace with a real MCP call.
        """
        # Resolve server
        st: Optional[McpServerState] = None
        if server_id_or_auto == "auto":
            st = self._select_server_auto(tool_name, preferred_tags)
        else:
            st = self._servers.get(server_id_or_auto)
        # If not found or tool unsupported, attempt a fallback for docs fetch
        if tool_name in ("http.get", "fetch_url"):
            url = str(params.get("url", "")).strip()
            if not url:
                return {"error": "missing url"}
            # Cache check
            r = get_redis()
            cache_key = f"mcpdoc:{(st.config.id if st else 'auto')}:{url}"
            if r is not None:
                try:
                    cached = r.get(cache_key)
                    if cached:
                        return {"serverId": st.config.id if st else "auto", "tool": tool_name, "url": url, "content": cached}
                except Exception:
                    pass
            # Placeholder direct fetch (not MCP): replace with real MCP invocation
            try:
                import httpx

                timeout = httpx.Timeout(15.0)
                headers = {"User-Agent": "MultiMcpClient/1.0"}
                async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                    resp = await client.get(url, headers=headers)
                    resp.raise_for_status()
                    text = resp.text
                # Cache
                if r is not None:
                    try:
                        r.setex(cache_key, int(os.getenv("MCP_DOC_TTL", "86400")), text)
                    except Exception:
                        pass
                return {"serverId": st.config.id if st else "auto", "tool": tool_name, "url": url, "content": text}
            except Exception as e:
                return {"error": str(e), "serverId": st.config.id if st else "auto"}
        # Default unsupported
        return {"error": f"tool '{tool_name}' not supported by scaffold"}


# Singleton access
_multi_mcp_client: Optional[MultiMcpClient] = None


def get_multi_mcp_client() -> MultiMcpClient:
    global _multi_mcp_client
    if _multi_mcp_client is None:
        _multi_mcp_client = MultiMcpClient.from_env()
    return _multi_mcp_client