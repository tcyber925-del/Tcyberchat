"""
Web search tools endpoints for health and test
"""

import os

from fastapi import APIRouter, Body

from ..services.web_research_orchestrator import WebResearchOrchestrator
from ..services.web_search_service import (
    get_web_search_service,
)

router = APIRouter(prefix="/tools/web-search", tags=["tools-web-search"])


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
async def test_query(body: dict = Body(...)):
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
async def research(body: dict = Body(...)):
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
