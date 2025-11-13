"""
MCP integrations API: configure servers and fetch docs via MultiMcpClient.
"""
from __future__ import annotations

import os
from typing import Any, Dict

from fastapi import APIRouter, Body

from ..services.mcp.multi_client import get_multi_mcp_client
from ..services.web_fetch_service import get_web_fetch_service
from ..services.web_search_service import SearchResult
from ..services.web_research_orchestrator import Evidence
from ..services.web_fetch_service import sanitize_web_content

router = APIRouter(prefix="/integrations/mcp", tags=["integrations-mcp"])


@router.get("/servers")
async def list_servers():
    client = get_multi_mcp_client()
    return {"servers": client.list_servers()}


@router.post("/fetch-doc")
async def fetch_doc(body: Dict[str, Any] = Body(...)):
    url = str(body.get("url", "")).strip()
    if not url:
        return {"error": "missing url"}
    server = body.get("server") or "auto"
    tool = body.get("tool") or "http.get"
    preferred_tags = body.get("preferredTags") or ["docs"]

    client = get_multi_mcp_client()
    res = await client.call_tool(server, tool, {"url": url}, preferred_tags=preferred_tags)
    if res.get("error"):
        return {"error": res["error"], "serverId": res.get("serverId")}

    text = res.get("content") or ""
    clean, suspicious = sanitize_web_content(text)

    # Build a normalized source card (compatible with UI citations)
    title = url
    try:
        # very small title heuristic
        import re
        m = re.search(r"https?://([^/]+)", url)
        if m:
            title = m.group(1)
    except Exception:
        pass

    return {
        "url": url,
        "content": clean[:10000],
        "suspicious": suspicious,
        "serverId": res.get("serverId"),
        "tool": res.get("tool"),
        "citation": {
            "title": title,
            "url": url,
            "snippet": clean[:200],
            "source": "mcp",
            "source_type": "web",
        },
    }