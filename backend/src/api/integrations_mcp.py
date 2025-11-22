"""
MCP integrations API: configure servers and fetch docs via MultiMcpClient.
"""
from __future__ import annotations

import os
import time
import logging
from typing import Any, Dict

from fastapi import APIRouter, Body, BackgroundTasks

from ..services.ai_service import get_ai_service

logger = logging.getLogger(__name__)

# Simple in-process cooldown to avoid repeated heavy init calls
_last_init_ts: float | None = None
_INIT_COOLDOWN_SECONDS = int(os.getenv("MCP_INIT_COOLDOWN", "30"))
_MCP_HEALTH_FLOW = os.getenv("MCP_HEALTH_FLOW", "true").lower() == "true"
# Simple in-memory metrics for basic instrumentation (reset on process restart)
_metrics = {
    "health_check_count": 0,
    "init_request_count": 0,
    "init_started_count": 0,
    "init_failed_count": 0,
}

from ..services.mcp.multi_client import get_multi_mcp_client
from ..services.web_fetch_service import get_web_fetch_service
from ..services.web_search_service import SearchResult
from ..services.web_research_orchestrator import Evidence
from ..services.web_fetch_service import sanitize_web_content

router = APIRouter(prefix="/integrations/mcp", tags=["integrations-mcp"])


@router.get("/servers")
async def list_servers():
    client = get_multi_mcp_client()
    # Try to enrich with cached capabilities from Redis
    from ..services.redis_client import get_redis
    import json
    servers = client.list_servers()
    r = get_redis()
    if r is not None:
        for s in servers:
            try:
                raw = r.get(f"mcp:server:capabilities:{s.get('id')}")
                if raw:
                    caps = json.loads(raw)
                    s["cached_capabilities"] = caps
            except Exception:
                continue
    return {"servers": servers}


@router.post("/servers")
async def upsert_server(body: Dict[str, Any] = Body(...)):
    client = get_multi_mcp_client()
    client.upsert_server(body)
    return {"ok": True}


@router.delete("/servers/{server_id}")
async def disable_server(server_id: str):
    client = get_multi_mcp_client()
    client.disable_server(server_id)
    return {"ok": True}


@router.post("/warm-connect")
async def warm_connect():
    client = get_multi_mcp_client()
    await client.warm_connect()
    return {"ok": True, "servers": client.list_servers()}


@router.get("/health")
async def mcp_health():
    """Return basic status about AI service and MCP integration for the UI."""
    start = time.time()
    try:
        ai_service = get_ai_service()
        models = ai_service.get_available_models()
        resp = {
            "ok": True,
            "ai": {"available_models": len(models), "models": models},
        }
        # instrumentation
        _metrics["health_check_count"] = _metrics.get("health_check_count", 0) + 1
        logger.info("MCP health checked: available_models=%d time=%.3fs", len(models), time.time() - start)
        return resp
    except Exception as e:
        logger.exception("MCP health check failed: %s", e)
        return {"ok": False, "error": str(e)}


@router.post("/init-model")
async def init_model(background_tasks: BackgroundTasks, body: Dict[str, Any] = Body({})):
    """Start a background warm initialization for the AI service/model. Non-blocking.

    The UI may call this if it detects the model is not yet ready. This endpoint
    will return immediately and run initialization in the background.
    """
    model = body.get("model")

    global _last_init_ts
    now = time.time()
    # instrumentation: record request
    _metrics["init_request_count"] = _metrics.get("init_request_count", 0) + 1

    if not _MCP_HEALTH_FLOW:
        logger.info("Init model requested but MCP_HEALTH_FLOW is disabled")
        return {"ok": False, "error": "mcp health flow disabled"}

    if _last_init_ts and now - _last_init_ts < _INIT_COOLDOWN_SECONDS:
        logger.info("Init model called too frequently; cooldown active")
        return {"ok": False, "error": "cooldown active"}

    _last_init_ts = now

    def _init_task():
        t0 = time.time()
        try:
            svc = get_ai_service(model)
            svc.get_available_models()
            _metrics["init_started_count"] = _metrics.get("init_started_count", 0) + 1
            logger.info("Background model init completed for model=%s time=%.3fs", model, time.time() - t0)
        except Exception as e:
            _metrics["init_failed_count"] = _metrics.get("init_failed_count", 0) + 1
            logger.exception("Background model init failed: %s", e)

    background_tasks.add_task(_init_task)
    logger.info("Background model init started for model=%s", model)
    return {"ok": True, "started": True}


@router.get("/metrics")
async def mcp_metrics():
    """Return simple in-memory metrics for MCP integration (useful for quick monitoring)."""
    # Return a shallow copy to avoid accidental mutation by callers
    return {"ok": True, "metrics": dict(_metrics)}


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