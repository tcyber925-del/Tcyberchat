"""
MCP integrations API: configure servers and fetch docs via MultiMcpClient.
"""
from __future__ import annotations

import os
import time
import subprocess
import logging
import traceback
from typing import Any, Dict

from fastapi import APIRouter, Body, BackgroundTasks

from ..services.ai_service import get_ai_service

logger = logging.getLogger(__name__)

# Simple in-process cooldown to avoid repeated heavy init calls
_last_init_ts: float | None = None
_INIT_COOLDOWN_SECONDS = int(os.getenv("MCP_INIT_COOLDOWN", "30"))
_MCP_HEALTH_FLOW = os.getenv("MCP_HEALTH_FLOW", "true").lower() == "true"
# Timeout (seconds) for stdio server process to start during test-connection
_STDIO_START_TIMEOUT = int(os.getenv("MCP_STDIO_START_TIMEOUT", "30"))
# Simple in-memory metrics for basic instrumentation (reset on process restart)
_metrics = {
    "health_check_count": 0,
    "init_request_count": 0,
    "init_started_count": 0,
    "init_failed_count": 0,
}

from ..services.mcp.multi_client import get_multi_mcp_client
import asyncio
from ..services.web_fetch_service import get_web_fetch_service
from ..services.web_search_service import SearchResult
from ..services.web_research_orchestrator import Evidence
from ..services.web_fetch_service import sanitize_web_content

router = APIRouter(prefix="/integrations/mcp", tags=["integrations-mcp"])

# Simple in-memory store for OAuth tokens (server_id -> token)
_OAUTH_TOKENS: Dict[str, Dict[str, str]] = {}

from pathlib import Path

def _validate_stdio_command(command: str) -> bool:
    allowlist = os.getenv("MCP_STDIO_ALLOWLIST")
    if not allowlist:
        return True
    
    if allowlist.strip() == "*":
        return True
        
    allowed = [c.strip() for c in allowlist.split(",")]
    return command in allowed

def _get_runner_script_path() -> Path:
    # Resolve relative to this file: backend/src/api/integrations_mcp.py
    # We want: backend/scripts/mcp_stdio_runner.py
    return Path(__file__).resolve().parents[2] / "scripts" / "mcp_stdio_runner.py"

def _is_admin(headers: Dict[str, str]) -> bool:
    # Simple admin protection: require header X-Admin-Token matching env ADMIN_TOKEN
    admin_token = os.getenv("ADMIN_TOKEN")
    if not admin_token:
        return False
    return headers.get("x-admin-token") == admin_token


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


@router.get("/servers/{server_id}/env")
async def get_server_env(server_id: str, request_headers: Dict[str, str] = None):
    """Return masked env for a server. If an admin token header is provided (X-Admin-Token matching ADMIN_TOKEN), return full env."""
    # FastAPI provides request headers differently; accept from the request object via dependency isn't wired here,
    # so use os.environ check and a simple header pass-through via request headers if provided by client code.
    # For security, require X-Admin-Token header matching ADMIN_TOKEN to return full values.
    from fastapi import Request
    # obtain headers
    # (fastapi will inject Request automatically if declared, but keep signature backward-compatible)
    async def _inner(req: Request):
        client = get_multi_mcp_client()
        servers = {s["id"]: s for s in client.list_servers()}
        st = servers.get(server_id)
        if not st:
            return {"ok": False, "error": "server not found"}
        # locate state
        # access underlying server state
        target = None
        for sid, state in client._servers.items():
            if sid == server_id:
                target = state
                break
        if not target:
            return {"ok": False, "error": "server not found"}
        headers = {k.lower(): v for k, v in req.headers.items()}
        if _is_admin(headers):
            return {"ok": True, "env": target.config.env or {}}
        # mask values
        masked = {k: '*****' for k in (target.config.env or {}).keys()}
        return {"ok": True, "env_masked": masked}

    return await _inner


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


@router.post("/test-connection")
async def test_connection(body: Dict[str, Any] = Body(...)):
    """Test connection to a single MCP server config without saving it."""
    from ..services.mcp.clients.ws_client import WsMcpConnection
    from ..services.mcp.clients.stdio_client import StdioMcpConnection
    from ..services.mcp.clients.sse_client import SseMcpConnection

    transport = body.get("transport")
    if transport not in ("wss", "stdio", "sse"):
        return {"ok": False, "error": f"Unknown transport: {transport}"}

    conn = None
    try:
        if transport == "wss":
            url = body.get("url")
            if not url:
                return {"ok": False, "error": "Missing URL for WSS"}
            conn = WsMcpConnection(url, headers=body.get("headers"))
        elif transport == "sse":
            url = body.get("url")
            if not url:
                return {"ok": False, "error": "Missing URL for SSE"}
            conn = SseMcpConnection(url, headers=body.get("headers"))
        elif transport == "stdio":
            command = body.get("command")
            if not command:
                return {"ok": False, "error": "Missing command for stdio"}
            
            if not _validate_stdio_command(command):
                return {"ok": False, "error": f"Command '{command}' is not in MCP_STDIO_ALLOWLIST"}

            # Use an external runner process to perform stdio startup and
            # list tools. Running the MCP stdio SDK in a separate process
            # avoids mixing anyio/asyncio taskgroups with the FastAPI event
            # loop and prevents the cancel-scope errors observed when the
            # SDK runs inside the webserver process.
            runner_script_path = _get_runner_script_path()
            if not runner_script_path.exists():
                return {"ok": False, "error": f"runner script not found: {runner_script_path}"}
            payload = {
                "command": command,
                "args": body.get("args") or [],
                "env": body.get("env") or {},
                "timeout": _STDIO_START_TIMEOUT,
            }
            try:
                # Invoke the runner and capture JSON output
                proc = subprocess.run([sys.executable, str(runner_script_path)], input=json.dumps(payload).encode('utf-8'), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=_STDIO_START_TIMEOUT)
                if proc.returncode != 0:
                    # include stderr for diagnostics
                    stderr = proc.stderr.decode('utf-8', errors='replace')
                    return {"ok": False, "error": "runner failed", "stderr": stderr}
                out = json.loads(proc.stdout.decode('utf-8'))
                return out
            except subprocess.TimeoutExpired:
                return {"ok": False, "error": f"stdio runner timed out after {_STDIO_START_TIMEOUT}s"}
            except Exception as e:
                return {"ok": False, "error": str(e)}

        if conn:
            # To avoid blocking the HTTP request and to reduce the chance of
            # mixing concurrency primitives between the request context and
            # the MCP SDK, start stdio connections in the background. The
            # background task will log results and write a small diagnostic
            # JSON file under `backend/logs/` which can be inspected.
            async def _start_background_and_record(c: Any, body_payload: Dict[str, Any]):
                out = {"ok": False}
                ts = int(time.time())
                diag_path = os.path.join(os.getcwd(), 'logs', f'mcp_stdio_background_{ts}.json')
                try:
                    try:
                        await asyncio.wait_for(c.start(), timeout=_STDIO_START_TIMEOUT)
                    except asyncio.TimeoutError:
                        out = {"ok": False, "error": f'stdio start timed out after {_STDIO_START_TIMEOUT}s'}
                        try:
                            await c.stop()
                        except Exception:
                            pass
                        try:
                            lp = os.path.join(os.getcwd(), 'logs', 'api.log')
                            if os.path.exists(lp):
                                with open(lp, 'rb') as f:
                                    f.seek(0, 2)
                                    size = f.tell()
                                    to_read = min(size, 8 * 1024)
                                    f.seek(max(0, size - to_read))
                                    out['log_tail'] = f.read().decode('utf-8', errors='replace')[-4000:]
                        except Exception:
                            pass
                        with open(diag_path, 'w', encoding='utf-8') as df:
                            import json as _json

                            df.write(_json.dumps(out))
                        return
                    try:
                        tools = await c.list_tools()
                        out = {"ok": True, "tools": tools}
                    except Exception as _e:
                        out = {"ok": False, "error": str(_e)}
                    try:
                        await c.stop()
                    except Exception:
                        pass
                except Exception as e:
                    out = {"ok": False, "error": repr(e)}
                try:
                    import json as _json

                    with open(diag_path, 'w', encoding='utf-8') as df:
                        df.write(_json.dumps(out))
                except Exception:
                    logger.exception('Failed to write background diag file')

            try:
                asyncio.create_task(_start_background_and_record(conn, body))
                return {"ok": True, "started": True, "note": "stdio start scheduled in background; check backend/logs for details"}
            except Exception:
                # Fallback to synchronous behavior if background scheduling fails
                try:
                    await asyncio.wait_for(conn.start(), timeout=_STDIO_START_TIMEOUT)
                    tools = await conn.list_tools()
                    await conn.stop()
                    return {"ok": True, "tools": tools}
                except Exception as e:
                    tb = traceback.format_exc()
                    return {"ok": False, "error": str(e), "error_trace": tb}

        return {"ok": False, "error": "Failed to create connection"}
    except Exception as e:
        # Log the full exception with traceback to help debugging why the
        # connection failed (some exceptions may have empty messages).
        # Ensure we always capture and log the full traceback.
        tb = traceback.format_exc()
        try:
            logger.error("Test-connection failed: %s", e)
            logger.error("Full traceback:\n%s", tb)
        except Exception:
            # Ensure logging errors don't mask original failure
            pass

        if conn:
            try:
                await conn.stop()
            except Exception:
                logger.debug("Failed to stop connection during exception cleanup", exc_info=True)

        # Prepare a safe error message. In some exception types str(e) is empty,
        # so fall back to repr(e). Optionally include the full traceback in the
        # JSON response when MCP_DEBUG_ERRORS=true (useful for local debugging).
        err_msg = str(e) or repr(e)
        # Include the traceback in the response to aid debugging in the development
        # environment. This should be safe locally but can be gated behind an env
        # var in production if desired.
        resp = {"ok": False, "error": err_msg, "error_trace": tb}
        return resp


@router.get("/health")
async def mcp_health():
    """Return basic status about AI service and MCP integration for the UI."""
    start = time.time()
    try:
        # `get_ai_service` returns an awaitable facade; await it to get the
        # real AIService instance and then call its async `get_available_models`.
        ai_service = await get_ai_service()
        models = await ai_service.get_available_models()
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

    async def _init_task_async():
        t0 = time.time()
        try:
            svc = await get_ai_service(model)
            await svc.get_available_models()
            _metrics["init_started_count"] = _metrics.get("init_started_count", 0) + 1
            logger.info("Background model init completed for model=%s time=%.3fs", model, time.time() - t0)
        except Exception as e:
            _metrics["init_failed_count"] = _metrics.get("init_failed_count", 0) + 1
            logger.exception("Background model init failed: %s", e)

    # Schedule the async init task
    background_tasks.add_task(_init_task_async)
    
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
        "structuredContent": res.get("structuredContent"),
        "citation": {
            "title": title,
            "url": url,
            "snippet": clean[:200],
            "source": "mcp",
            "source_type": "web",
        },
    }