"""
Web search tools endpoints for health and test
"""

import os

from fastapi import APIRouter, Body, Request, Depends, HTTPException, status

from ..services.web_research_orchestrator import WebResearchOrchestrator
from ..services.web_search_service import (
    get_web_search_service,
)

router = APIRouter(prefix="/tools/web-search", tags=["tools-web-search"]) 

# --- Rate limiting helpers ---
from ..services.rate_limit import get_rate_limiter

def _client_ip(request: Request) -> str:
    # Best-effort; in production consider X-Forwarded-For with care
    try:
        return request.client.host or "unknown"
    except Exception:
        return "unknown"

async def rate_limit_dep(request: Request, key: str, per_min: int) -> None:
    limiter = get_rate_limiter()
    ok = await limiter.allow(f"{key}:{_client_ip(request)}", per_min, 60)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please retry later.",
        )


@router.get("/health")
async def health():
    svc = get_web_search_service()

    # Provider availability checks
    primary_avail = svc.primary_provider is not None
    fallback_avail = svc.fallback_provider is not None

    # Keys
    serp_key = bool(os.getenv("SERPAPI_API_KEY"))
    tavily_key = bool(os.getenv("TAVILY_API_KEY"))

    # Packages
    ddgs_pkg = False
    ddg_legacy_pkg = False
    try:
        ddgs_pkg = True
    except Exception:
        pass
    try:
        ddg_legacy_pkg = True
    except Exception:
        pass

    return {
        "provider": svc.provider_name,
        "impl": getattr(svc, "impl", "custom"),
        "primary_available": primary_avail,
        "fallback_available": fallback_avail,
        "keys": {
            "serpapi": serp_key,
            "tavily": tavily_key,
        },
        "packages": {
            "ddgs": ddgs_pkg,
            "duckduckgo_search": ddg_legacy_pkg,
        },
        "config": {
            "cache_ttl": svc.cache_ttl,
            "rate_limit": svc.rate_limit,
            "timeout_sec": svc.timeout_sec,
            "WEB_SEARCH_IMPL": os.getenv("WEB_SEARCH_IMPL", "custom"),
            "WEB_FETCH_IMPL": os.getenv("WEB_FETCH_IMPL", "custom"),
        },
    }


class TestBody:
    q: str
    maxResults: int | None = 3


@router.post("/test")
async def test_query(body: dict = Body(...), request: Request = None, dep: None = Depends(lambda request: rate_limit_dep(request, "web_test", int(os.getenv("WEB_TOOLS_RATE_PER_MIN", "30"))))):
    q = str(body.get("q", "")).strip()
    max_results = int(body.get("maxResults", 3))
    if not q:
        return {"error": "missing query 'q'"}

    svc = get_web_search_service()
    # Bump timeout a bit for this endpoint
    try:
        svc.timeout_sec = max(getattr(svc, "timeout_sec", 8), 12)
    except Exception:
        pass

    # Try up to 2 attempts
    attempts = 0
    last_error = None
    results = []
    while attempts < 2:
        attempts += 1
        try:
            results = await svc.search(
                q, max_results=max_results, use_cache=False, force_fresh=True
            )
            if results:
                break
        except Exception as e:
            last_error = str(e)
        # small backoff and widen
        max_results = min(max_results + 2, 8)

    try:
        enriched = await svc.enrich_results(results)
    except Exception:
        enriched = results

    resp = {
        "query": q,
        "provider": getattr(svc.primary_provider, "name", svc.provider_name)
        if getattr(svc, "primary_provider", None)
        else svc.provider_name,
        "impl": getattr(svc, "impl", "custom"),
        "count": len(enriched),
        "attempts": attempts,
        "results": [r.to_dict() for r in enriched],
    }
    if last_error:
        resp["last_error"] = last_error
    return resp


@router.post("/research")
async def research(body: dict = Body(...), request: Request = None, dep: None = Depends(lambda request: rate_limit_dep(request, "web_research", int(os.getenv("WEB_RESEARCH_RATE_PER_MIN", "20"))))):
    q = str(body.get("q", "")).strip()
    model = body.get("model")
    max_results = int(body.get("maxResults", 5))
    max_fetch = int(body.get("maxFetch", 3))
    if not q:
        return {"error": "missing query 'q'"}
    orch = WebResearchOrchestrator()
    data = await orch.run(
        q, model_name=model, max_results=max_results, max_fetch=max_fetch
    )
    return data


@router.post("/deep-research")
async def deep_research(body: dict = Body(...), request: Request = None, dep: None = Depends(lambda request: rate_limit_dep(request, "deep_research", int(os.getenv("DEEP_RESEARCH_RATE_PER_MIN", "5"))))):
    """
    Deep Research endpoint: multi-step agentic workflow using LangGraph.
    
    Body:
        - query: research question (required)
        - model: AI model name (optional)
        - maxIterations: max refinement loops (optional, default 2)
    
    Returns:
        - answer: final markdown report with citations
        - citations: list of sources [{id, title, url, snippet, tokens}]
        - metadata: {duration_seconds, iterations, started_at, finalized_at}
    """
    query = str(body.get("query", "")).strip()
    if not query:
        return {"error": "missing 'query' field"}
    
    model = body.get("model")
    max_iterations = int(body.get("maxIterations", 2))
    
    # Feature gate check
    enabled = os.getenv("DEEP_RESEARCH_ENABLED", "false").lower() == "true"
    if not enabled:
        return {
            "error": "Deep research feature is disabled. Set DEEP_RESEARCH_ENABLED=true to enable."
        }
    
    # Telemetry trace
    from ..services.telemetry import new_trace_id, log_event, time_block
    trace_id = new_trace_id()
    done = time_block()
    log_event("deep_research_start", trace_id, {"query": query, "model": model, "max_iterations": max_iterations})

    from ..agents.deep_research_agent import run_deep_research

    try:
        result = await run_deep_research(
            query=query,
            model_name=model,
            max_iterations=max_iterations,
        )
        dur = done()
        log_event("deep_research_end", trace_id, {"duration_sec": dur, "citations": len(result.get("citations", []))})
        # attach trace id for client correlation
        result["metadata"] = {**result.get("metadata", {}), "trace_id": trace_id, "duration_sec": dur}
        return result
    except Exception as e:
        log_event("deep_research_error", trace_id, {"error": str(e)})
        raise


# Streaming deep research (SSE)
try:
    from sse_starlette.sse import EventSourceResponse
except Exception:  # pragma: no cover
    EventSourceResponse = None  # type: ignore

@router.get("/deep-research/stream")
async def deep_research_stream(request: Request, query: str, model: str | None = None, maxIterations: int = 2, dep: None = Depends(lambda request: rate_limit_dep(request, "deep_research", int(os.getenv("DEEP_RESEARCH_RATE_PER_MIN", "5"))))):
    enabled = os.getenv("DEEP_RESEARCH_ENABLED", "false").lower() == "true"
    if not enabled:
        return {"error": "Deep research feature is disabled. Set DEEP_RESEARCH_ENABLED=true to enable."}
    if EventSourceResponse is None:
        return {"error": "SSE not available on server"}
    
    from ..agents.deep_research_agent import run_deep_research_stream

    async def gen():
        async for evt in run_deep_research_stream(query=query, model_name=model, max_iterations=int(maxIterations)):
            # Abort if client disconnects
            if await request.is_disconnected():
                break
            yield {"event": evt.get("event", "message"), "data": evt.get("data", {})}

    return EventSourceResponse(gen())


# Background job endpoints for deep research
from ..services.job_queue import get_job_queue

@router.post("/deep-research/jobs")
async def create_deep_research_job(body: dict = Body(...), request: Request = None, dep: None = Depends(lambda request: rate_limit_dep(request, "deep_research", int(os.getenv("DEEP_RESEARCH_RATE_PER_MIN", "5"))))):
    query = str(body.get("query", "")).strip()
    if not query:
        return {"error": "missing 'query'"}
    model = body.get("model")
    max_iterations = int(body.get("maxIterations", 2))
    jq = get_job_queue()
    job = jq.enqueue(query, model, max_iterations)
    return job.to_dict()


@router.get("/deep-research/jobs/{job_id}")
async def get_deep_research_job(job_id: str):
    jq = get_job_queue()
    job = jq.get(job_id)
    if not job:
        return {"error": "not found"}
    resp = job.to_dict()
    if job.status == "done" and job.result:
        resp["result"] = job.result
    return resp


@router.delete("/deep-research/jobs/{job_id}")
async def cancel_deep_research_job(job_id: str):
    jq = get_job_queue()
    ok = jq.cancel(job_id)
    return {"cancelled": bool(ok)}
