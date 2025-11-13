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
from .clients.ws_client import WsMcpConnection
from .clients.stdio_client import StdioMcpConnection


class MultiMcpClient:
    def __init__(self, config: McpMultiConfig) -> None:
        self._config = config
        self._servers: Dict[str, McpServerState] = {
            s.id: McpServerState(config=s) for s in (config.servers or [])
        }
        # Circuit breaker state
        self._cb_failures: Dict[str, int] = {}
        self._cb_open_until: Dict[str, float] = {}

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

    # --- Admin/config helpers ---
    def upsert_server(self, cfg: Dict[str, Any]) -> None:
        sid = cfg.get("id")
        if not sid:
            raise ValueError("server id is required")
        server = McpServerConfig(
            id=sid,
            transport=cfg.get("transport"),
            enabled=bool(cfg.get("enabled", True)),
            command=cfg.get("command"),
            args=cfg.get("args") or [],
            url=cfg.get("url"),
            headers=cfg.get("headers") or {},
            tags=cfg.get("tags") or [],
            timeouts=cfg.get("timeouts") or {"connectMs": 3000, "readMs": 15000},
        )
        self._servers[sid] = McpServerState(config=server)

    def disable_server(self, server_id: str) -> None:
        st = self._servers.get(server_id)
        if st:
            st.config.enabled = False

    # --- Connection management (scaffold) ---
    async def warm_connect(self) -> None:
        """Attempt to connect and discover tools for all enabled servers.
        In this scaffold, we simulate discovery; integrate a real MCP SDK later.
        """
        for sid, st in self._servers.items():
            if not st.config.enabled:
                continue
            try:
                # Choose connector by transport
                conn = None
                if st.config.transport == "wss" and st.config.url:
                    conn = WsMcpConnection(st.config.url, headers=st.config.headers)
                elif st.config.transport == "stdio" and st.config.command:
                    conn = StdioMcpConnection(st.config.command, st.config.args)
                st._conn = conn  # attach dynamically
                if conn:
                    await conn.start()
                    tools_raw = await conn.list_tools()
                    st.tools = [McpTool(name=t.get("name"), description=t.get("description")) for t in (tools_raw or []) if t.get("name")]
                # Fallback add common http.get alias if tagged docs
                if not st.tools and any(t in st.config.tags for t in ["docs", "http", "official"]):
                    st.tools = [McpTool(name="http.get", description="HTTP GET"), McpTool(name="fetch_url", description="Fetch a URL")]
                st.connected = True
                st.healthy = True
                st.last_error = None
                # Cache capabilities in Redis
                r = get_redis()
                if r is not None:
                    try:
                        import json
                        caps = {
                            "id": st.config.id,
                            "transport": st.config.transport,
                            "tags": st.config.tags,
                            "tools": [{"name": t.name, "description": t.description} for t in st.tools],
                        }
                        r.setex(f"mcp:server:capabilities:{st.config.id}", 3600, json.dumps(caps))
                    except Exception:
                        pass
            except Exception as e:
                st.connected = False
                st.healthy = False
                st.last_error = str(e)

    # --- Routing helpers ---
    def _cb_allowed(self, key: str) -> bool:
        import time
        until = self._cb_open_until.get(key, 0)
        cool = int(os.getenv("MCP_CB_COOLDOWN", "60"))
        return time.time() >= until

    def _cb_fail(self, key: str) -> None:
        import time
        thr = int(os.getenv("MCP_CB_THRESHOLD", "3"))
        cool = int(os.getenv("MCP_CB_COOLDOWN", "60"))
        self._cb_failures[key] = self._cb_failures.get(key, 0) + 1
        if self._cb_failures[key] >= thr:
            self._cb_open_until[key] = time.time() + cool

    def _cb_ok(self, key: str) -> None:
        self._cb_failures[key] = 0
        self._cb_open_until[key] = 0

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
        strategy: str = "auto",  # auto | broadcast_first
    ) -> Dict[str, Any]:
        """Call a tool on a specific or auto-selected server.
        This scaffold implements only a special-case for http.get/fetch_url: it will perform a direct HTTP fetch as a
        placeholder when no SDK is wired, caching the content. Replace with a real MCP call.
        """
        # Resolve server(s)
        if strategy == "broadcast_first":
            servers = self._find_servers_for_tool(tool_name)
            if preferred_tags:
                servers = sorted(servers, key=lambda s: int(any(t in s.config.tags for t in preferred_tags)), reverse=True)
        else:
            st: Optional[McpServerState] = None
            if server_id_or_auto == "auto":
                st = self._select_server_auto(tool_name, preferred_tags)
            else:
                st = self._servers.get(server_id_or_auto)
            servers = [st] if st else []
        # If not found or tool unsupported, attempt a fallback for docs fetch
        if tool_name in ("http.get", "fetch_url") and os.getenv("MCP_PLACEHOLDER_ONLY", "false").lower() != "true":
            # If we have a real connection and tool, try it
            for s in servers:
                if not s:
                    continue
                conn = getattr(s, "_conn", None)
                if conn:
                    try:
                        res = await conn.call_tool(tool_name, params, stream=stream)
                        if not res.get("error"):
                            self._cb_ok(f"{s.config.id}:{tool_name}")
                            return {"serverId": s.config.id, **res}
                    except Exception as e:
                        self._cb_fail(f"{s.config.id}:{tool_name}")
                        last_err = str(e)
                        continue
        if tool_name in ("http.get", "fetch_url"):
            url = str(params.get("url", "")).strip()
            if not url:
                return {"error": "missing url"}
            # Attempt servers in order; on success, cache and return
            last_err = None
            for s in servers:
                if not s:
                    continue
                key = f"{s.config.id}:{tool_name}"
                if not self._cb_allowed(key):
                    continue
                # Cache check
                r = get_redis()
                cache_key = f"mcpdoc:{s.config.id}:{url}"
                if r is not None:
                    try:
                        cached = r.get(cache_key)
                        if cached:
                            self._cb_ok(key)
                            return {"serverId": s.config.id, "tool": tool_name, "url": url, "content": cached}
                    except Exception:
                        pass
                # Placeholder for real MCP invoke
                try:
                    import httpx
                    timeout = httpx.Timeout(15.0)
                    headers = {"User-Agent": "MultiMcpClient/1.0"}
                    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                        resp = await client.get(url, headers=headers)
                        resp.raise_for_status()
                        text = resp.text
                    if r is not None:
                        try:
                            r.setex(cache_key, int(os.getenv("MCP_DOC_TTL", "86400")), text)
                        except Exception:
                            pass
                    self._cb_ok(key)
                    return {"serverId": s.config.id, "tool": tool_name, "url": url, "content": text}
                except Exception as e:
                    last_err = str(e)
                    self._cb_fail(key)
                    continue
            return {"error": last_err or "no server available"}
        # Default unsupported
        return {"error": f"tool '{tool_name}' not supported by scaffold"}


# Singleton access
_multi_mcp_client: Optional[MultiMcpClient] = None


def get_multi_mcp_client() -> MultiMcpClient:
    global _multi_mcp_client
    if _multi_mcp_client is None:
        _multi_mcp_client = MultiMcpClient.from_env()
    return _multi_mcp_client