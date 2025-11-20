import os
import sys
from fastapi.testclient import TestClient
from fastapi import FastAPI

# Ensure backend package is importable when running from repo root
sys.path.insert(0, os.path.join(os.getcwd(), "backend"))

from src.api.integrations_mcp import router as mcp_router  # noqa: E402

app = FastAPI()
app.include_router(mcp_router, prefix="/api")
client = TestClient(app)


def test_list_servers_initially_empty():
    r = client.get("/api/integrations/mcp/servers")
    assert r.status_code == 200
    data = r.json()
    assert "servers" in data
    # May be empty when MCP_MULTI not set
    assert isinstance(data["servers"], list)


def test_warm_connect_ok():
    r = client.post("/api/integrations/mcp/warm-connect")
    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") is True
    assert "servers" in data


def test_fetch_doc_missing_url():
    r = client.post("/api/integrations/mcp/fetch-doc", json={})
    assert r.status_code == 200
    data = r.json()
    assert data.get("error") == "missing url"


def test_fetch_doc_with_mocked_mcp(monkeypatch):
    # Monkeypatch the MultiMcpClient to simulate SDK-backed fetch
    from src.services.mcp import multi_client as mcp_mod

    class FakeClient:
        async def warm_connect(self):
            return None
        async def call_tool(self, server, tool, params, **kwargs):
            assert tool in ("http.get", "fetch_url")
            assert "url" in params
            return {"serverId": "fake", "tool": tool, "url": params["url"], "content": "Hello from MCP"}
        def list_servers(self):
            return [{"id": "fake", "tools": ["http.get"]}]

    def fake_get_multi_mcp_client():
        return FakeClient()

    monkeypatch.setattr(mcp_mod, "get_multi_mcp_client", fake_get_multi_mcp_client)

    r = client.post(
        "/api/integrations/mcp/fetch-doc",
        json={"url": "https://example.com/x", "server": "auto", "tool": "http.get"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data.get("serverId") == "fake"
    assert data.get("content", "").startswith("Hello")
    assert data.get("citation", {}).get("url") == "https://example.com/x"
