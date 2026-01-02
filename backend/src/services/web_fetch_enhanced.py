"""
Enhanced web fetch service: layered fetching + simple HTML extraction + caching.

This module is intentionally conservative: optional heavy deps (playwright,
trafilatura, readability) are imported only if available. The implementation
provides a sensible default using `httpx` + `BeautifulSoup` and an in-memory
TTL cache. It exposes `fetch_one` and `fetch_multiple` with a stable schema.

Keep this module feature-flag friendly and non-breaking: callers can continue
to use `fetch_multiple(urls)` and opt into advanced strategies later.
"""
from __future__ import annotations

import asyncio
import os
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse, urlunparse

try:
    import httpx
except Exception:  # pragma: no cover - httpx should be installed in runtime
    httpx = None  # type: ignore

try:
    from bs4 import BeautifulSoup
except Exception:  # pragma: no cover
    BeautifulSoup = None  # type: ignore

CACHE_TTL = int(os.getenv("WEB_FETCH_CACHE_TTL_SECONDS", "3600"))
CONCURRENCY = int(os.getenv("WEB_FETCH_MAX_WORKERS", "6"))
SUBTASK_TIMEOUT = int(os.getenv("WEB_FETCH_TIMEOUT_SECONDS", "12"))

# Simple in-memory cache: url -> (timestamp, record)
_FETCH_CACHE: Dict[str, tuple[float, Dict[str, Any]]] = {}


def _normalize_url(url: str) -> str:
    p = urlparse(url)
    # strip fragment
    np = p._replace(fragment="")
    return urlunparse(np)


def sanitize_web_content(text: str) -> str:
    if not text:
        return ""
    # Basic sanitization: collapse whitespace
    return " ".join(text.split())


async def _http_get_text(url: str, timeout: int = SUBTASK_TIMEOUT) -> Dict[str, Any]:
    if httpx is None:
        raise RuntimeError("httpx is required for web fetching")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    async with httpx.AsyncClient(timeout=timeout, headers=headers, follow_redirects=True) as client:
        resp = await client.get(url)
        # raise_for_status may raise; let caller handle
        resp.raise_for_status()
        ct = resp.headers.get("content-type", "")
        text = resp.text
        return {"status_code": resp.status_code, "content_type": ct, "text": text, "headers": dict(resp.headers)}


def _extract_with_bs4(html: str) -> Dict[str, Any]:
    title = None
    content = ""
    if BeautifulSoup is None:
        # fallback: return raw html truncated
        return {"title": None, "content": html[:10000], "html": html}
    soup = BeautifulSoup(html, "html.parser")
    # Try common article selectors
    article = None
    for sel in ["article", "main", "div.post-content", "div.article", "#content"]:
        article = soup.select_one(sel)
        if article:
            break
    if not article:
        # fallback to body
        article = soup.body or soup
    # get text
    content = article.get_text(separator="\n\n")
    # title
    t = soup.title.string if soup.title else None
    if not t:
        og = soup.find("meta", property="og:title")
        if og and og.get("content"):
            t = og.get("content")
    return {"title": t, "content": content, "html": str(article)[:2000]}


async def fetch_one(
    url: str,
    strategy: str = "auto",
    force_fresh: bool = False,
    timeout_seconds: Optional[int] = None,
) -> Dict[str, Any]:
    """Fetch a single URL and return a normalized record.

    The returned record contains keys: url, canonical_url, title, content,
    html_snippet, tokens_estimate, published_at (optional), domain,
    content_type, fetch_strategy_used, timings.
    """
    t0 = time.time()
    url_n = _normalize_url(url)
    # Cache check
    if not force_fresh and url_n in _FETCH_CACHE:
        ts, rec = _FETCH_CACHE[url_n]
        if time.time() - ts <= CACHE_TTL:
            rec2 = {**rec, "cached": True, "timings": {"total": round(time.time() - t0, 3)}}
            return rec2

    timeout = timeout_seconds or SUBTASK_TIMEOUT

    # Default fast path using httpx + bs4
    try:
        http_res = await _http_get_text(url_n, timeout=timeout)
        ct = http_res.get("content_type", "")
        text = http_res.get("text", "")
        if "html" in ct or text.strip().startswith("<"):
            parsed = _extract_with_bs4(text)
            content = sanitize_web_content(parsed.get("content", ""))
            title = parsed.get("title")
            html_snip = parsed.get("html")
            strategy_used = "http+bs4"
        else:
            # treat as text-like (e.g., text/plain)
            content = sanitize_web_content(text)
            title = None
            html_snip = None
            strategy_used = "http"

        rec = {
            "url": url,
            "canonical_url": url_n,
            "title": title,
            "content": content[:30000],
            "html_snippet": html_snip,
            "tokens_estimate": int(len(content.split()) * 1.3) if content else 0,
            "published_at": None,
            "domain": urlparse(url_n).netloc,
            "content_type": ct,
            "trust_score": 0.5,
            "is_suspicious": False,
            "fetch_strategy_used": strategy_used,
            "cached": False,
        }

        # store in cache
        _FETCH_CACHE[url_n] = (time.time(), rec)
        rec["timings"] = {"total": round(time.time() - t0, 3)}
        return rec

    except Exception as e:
        # Return error-like record
        return {
            "url": url,
            "error": str(e),
            "cached": False,
            "timings": {"total": round(time.time() - t0, 3)},
        }


async def fetch_multiple(urls: List[str], strategy: str = "auto", force_fresh: bool = False) -> List[Dict[str, Any]]:
    sem = asyncio.Semaphore(CONCURRENCY)

    async def worker(u: str):
        async with sem:
            try:
                return await asyncio.wait_for(fetch_one(u, strategy=strategy, force_fresh=force_fresh), timeout=SUBTASK_TIMEOUT + 2)
            except asyncio.TimeoutError:
                return {"url": u, "error": "timeout"}

    tasks = [worker(u) for u in urls]
    return await asyncio.gather(*tasks)


async def fetch_and_load(url: str, strategy: str = "auto", force_fresh: bool = False) -> Dict[str, Any]:
    """Fetch a URL and return a LangChain-like Document dict: {page_content, metadata}.

    This helper simplifies integration with downstream splitters and vectorstores.
    """
    rec = await fetch_one(url, strategy=strategy, force_fresh=force_fresh)
    if rec.get("error"):
        return {"page_content": "", "metadata": {"url": url, "error": rec.get("error")}}

    metadata = {
        "source": rec.get("canonical_url") or rec.get("url"),
        "title": rec.get("title"),
        "domain": rec.get("domain"),
        "content_type": rec.get("content_type"),
    }
    return {"page_content": rec.get("content", ""), "metadata": metadata}
