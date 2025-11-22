"""Sub-agent implementations used by a supervisor agent.

Provides `web_research_subagent` which performs search+fetch for a single
sub-question and returns structured findings that the supervisor can synthesize.
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict, List

from .tools import web_search_tool
from ..services import web_fetch_enhanced


async def web_research_subagent(question: str, max_results: int = 3) -> Dict[str, Any]:
    """Investigate a single sub-question: search, fetch top results, summarize findings.

    Returns a dict: {question, sources: [..], findings: str}
    """
    # 1) Search (tool is synchronous; run in thread if needed)
    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(None, lambda: web_search_tool(question, max_results=max_results))

    urls = [r.get("url") for r in results if r.get("url")][: max_results]

    # 2) Fetch pages (use enhanced fetch which is async)
    fetched = await web_fetch_enhanced.fetch_multiple(urls)

    sources: List[Dict[str, Any]] = []
    findings_parts: List[str] = []
    for idx, (r, fr) in enumerate(zip(results, fetched), start=1):
        url = r.get("url")
        title = r.get("title") or (fr.get("title") if isinstance(fr, dict) else getattr(fr, "title", None))
        snippet = r.get("snippet") or (fr.get("content", "")[:200] if isinstance(fr, dict) else getattr(fr, "content", "")[:200])
        findings_parts.append(f"[{idx}] {title or url}\n{snippet}")
        sources.append({"id": idx, "title": title, "url": url, "snippet": snippet})

    return {"question": question, "sources": sources, "findings": "\n\n".join(findings_parts)}
