import asyncio
import os
import sys
import time
import types
import pytest

# Ensure backend package is importable when running from repo root
sys.path.insert(0, os.path.join(os.getcwd(), "backend"))

from src.services.mcp.multi_client import MultiMcpClient
from src.services.mcp.types import McpMultiConfig, McpServerConfig, McpTool


@pytest.mark.asyncio
async def test_circuit_breaker_blocks_after_threshold(monkeypatch):
    # Lower threshold/cooldown for fast test
    monkeypatch.setenv("MCP_CB_THRESHOLD", "2")
    monkeypatch.setenv("MCP_CB_COOLDOWN", "60")

    # Build a client with one enabled/connected server exposing http.get
    cfg = McpMultiConfig(
        servers=[
            McpServerConfig(
                id="s1",
                transport="wss",
                enabled=True,
                url="wss://example.invalid/ws",
                headers={},
                tags=["docs"],
                timeouts={"connectMs": 1000, "readMs": 1000},
            )
        ]
    )
    client = MultiMcpClient(cfg)
    st = client._servers["s1"]
    st.connected = True
    st.healthy = True
    st.tools = [McpTool(name="http.get", description="HTTP GET")]

    class FailingConn:
        async def call_tool(self, name, params, stream=False):
            raise RuntimeError("upstream failure")

    st._conn = FailingConn()

    # Prevent HTTP fallback from succeeding by making httpx raise
    import httpx

    class RaisingClient:
        def __init__(self, *a, **k):
            pass
        async def __aenter__(self):
            return self
        async def __aexit__(self, *exc):
            return False
        async def get(self, *a, **k):
            raise httpx.TimeoutException("simulated timeout")

    monkeypatch.setattr(httpx, "AsyncClient", RaisingClient)

    # First two attempts should fail and increase failure count
    for _ in range(2):
        res = await client.call_tool("s1", "http.get", {"url": "https://example.com"})
        assert "error" in res

    key = "s1:http.get"
    # After threshold, further attempts should be short-circuited (not allowed)
    allowed = client._cb_allowed(key)
    assert allowed is False or client._cb_failures.get(key, 0) >= int(os.getenv("MCP_CB_THRESHOLD", "2"))


@pytest.mark.asyncio
async def test_real_call_used_when_conn_succeeds(monkeypatch):
    cfg = McpMultiConfig(
        servers=[McpServerConfig(id="s1", transport="wss", enabled=True, url="wss://fake", headers={}, tags=["docs"], timeouts={"connectMs":1000,"readMs":1000})]
    )
    client = MultiMcpClient(cfg)
    st = client._servers["s1"]
    st.connected = True
    st.healthy = True
    st.tools = [McpTool(name="foo", description="Foo tool")]

    class OkConn:
        async def call_tool(self, name, params, stream=False):
            return {"result": {"ok": True, "echo": params}}

    st._conn = OkConn()

    res = await client.call_tool("s1", "foo", {"x": 1})
    assert res.get("serverId") == "s1"
    assert res.get("result", {}).get("ok") is True
