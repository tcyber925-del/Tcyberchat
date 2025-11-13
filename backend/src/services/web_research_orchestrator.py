"""
WebResearchOrchestrator: search → fetch → synthesize → cite
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, List

from .web_fetch_service import get_web_fetch_service
from .web_search_service import SearchResult, get_web_search_service

# Simple in-memory synthesis cache: key -> (timestamp, result)
_SYNTH_CACHE: dict[str, tuple] = {}

# Optional Redis cache
try:
    from .redis_client import get_redis
except Exception:
    get_redis = lambda: None  # type: ignore


# Lazy import AI service to avoid cycles
async def _get_ai_service(model_name: str | None):
    from .ai_service import get_ai_service

    return await get_ai_service(model_name)


def _is_time_sensitive(q: str) -> bool:
    if not q:
        return False
    ql = q.lower()
    return any(
        k in ql
        for k in [
            "latest",
            "recent",
            "news",
            "today",
            "current",
            "now",
            "this week",
            "this month",
            "2024",
            "2025",
        ]
    )


def _chunk_text(text: str, max_chars: int = 600, overlap: int = 60) -> List[str]:
    if not text:
        return []
    text = text.strip()
    if len(text) <= max_chars:
        return [text]
    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + max_chars)
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start = end - overlap
        if start < 0:
            start = 0
    return chunks


@dataclass
class Evidence:
    title: str
    url: str
    content: str
    tokens: int
    published_at: datetime | None = None


class WebResearchOrchestrator:
    def __init__(self):
        self.web_search = get_web_search_service()
        self.web_fetch = get_web_fetch_service()
        self.max_fetch_default = int(os.getenv("WEB_FETCH_MAX_FETCH", "3"))

    async def run(
        self,
        query: str,
        model_name: str | None = None,
        max_results: int = 5,
        max_fetch: int | None = None,
    ) -> dict[str, Any]:
        time_sensitive = _is_time_sensitive(query)

        # Check synthesis cache for non-time-sensitive queries
        cache_ttl = int(os.getenv("WEB_SYNTH_CACHE_TTL", "300"))
        cache_key = f"{(model_name or 'default')}:::{query.strip()}"
        # Redis first
        if not time_sensitive and cache_ttl > 0:
            r = get_redis()
            if r is not None:
                try:
                    cached = r.get(f"synth:{cache_key}")
                    if cached:
                        import json
                        return json.loads(cached)
                except Exception:
                    pass
        # In-memory fallback
        if not time_sensitive and cache_ttl > 0 and cache_key in _SYNTH_CACHE:
            ts, cached = _SYNTH_CACHE[cache_key]
            if (datetime.now() - ts).total_seconds() <= cache_ttl:
                return cached
            else:
                del _SYNTH_CACHE[cache_key]

        # 1) Search
        results: list[SearchResult] = await self.web_search.search(
            query,
            max_results=max_results,
            use_cache=not time_sensitive,
            force_fresh=time_sensitive,
        )
        # Provider info
        provider_name = (
            getattr(
                self.web_search.primary_provider, "name", self.web_search.provider_name
            )
            if getattr(self.web_search, "primary_provider", None)
            else self.web_search.provider_name
        )
        impl = getattr(self.web_search, "impl", "custom")

        if not results:
            return {
                "response": "No recent results found.",
                "citations": [],
                "web_provider": provider_name,
                "web_impl": impl,
            }

        # Deduplicate by URL
        seen = set()
        deduped: list[SearchResult] = []
        for r in results:
            if r.url and r.url not in seen:
                seen.add(r.url)
                deduped.append(r)
        results = deduped

        # 2) Fetch/enrich
        max_fetch = max_fetch or self.max_fetch_default
        top_urls = [r.url for r in results[:max_fetch] if r.url]
        enriched = await self.web_fetch.fetch_multiple(top_urls) if top_urls else []

        # Optional: rerank results before packaging evidence
        def _simple_overlap_score(text: str, query: str) -> float:
            q_tokens = {t for t in query.lower().split() if len(t) > 2}
            if not text:
                return 0.0
            hits = sum(1 for t in q_tokens if t in text.lower())
            return hits / max(1, len(q_tokens))

        rerank_enabled = os.getenv("WEB_RERANK_ENABLED", "false").lower() == "true"
        if rerank_enabled:
            # Try local cross-encoder first
            try:
                from .reranker import score_pairs
            except Exception:
                score_pairs = None  # type: ignore
            candidates = results[: max_fetch * 2]
            # Build chunked passages
            passage_records: list[tuple[SearchResult, str]] = []
            max_chars = int(os.getenv("WEB_RERANK_PASSAGE_CHARS", "600"))
            overlap = int(os.getenv("WEB_RERANK_PASSAGE_OVERLAP", "60"))
            for r in candidates:
                fr = next((f for f in enriched if f.url == r.url or f.canonical_url == r.url), None)
                base = (fr.content if fr and fr.content else (r.snippet or "")) or ""
                for chunk in _chunk_text(base, max_chars=max_chars, overlap=overlap):
                    passage_records.append((r, chunk))
            ce_scores = None
            if score_pairs is not None and os.getenv("WEB_RERANK_MODEL"):
                try:
                    ce_scores = score_pairs(query, [p for _, p in passage_records])
                except Exception:
                    ce_scores = None
            if ce_scores and len(ce_scores) == len(passage_records):
                ranked_chunks = sorted(zip(ce_scores, passage_records), key=lambda x: x[0], reverse=True)
                top_k = int(os.getenv("WEB_RERANK_TOP_CHUNKS", str(max_fetch)))
                # Select top chunks ensuring we don't exceed content size
                selected: list[tuple[SearchResult, str]] = []
                for score, (r, chunk) in ranked_chunks:
                    selected.append((r, chunk))
                    if len(selected) >= top_k:
                        break
                # Rebuild results order based on selected chunk parent results
                ordered = []
                seen = set()
                for r, _ in selected:
                    if r.url not in seen:
                        ordered.append(r)
                        seen.add(r.url)
                results = ordered + [r for r in results if r.url not in seen]
                # Replace evidence_pack later using selected chunks
                selected_chunks = selected
            else:
                # Fallback heuristic mix of overlap + provider relevance
                scored: list[tuple[float, SearchResult]] = []
                for r in results[:max_fetch]:
                    fr = next((f for f in enriched if f.url == r.url or f.canonical_url == r.url), None)
                    basis = (fr.content if fr and fr.content else (r.snippet or ""))
                    s = 0.7 * _simple_overlap_score(basis, query) + 0.3 * float(r.relevance_score or 0.0)
                    scored.append((s, r))
                scored.sort(key=lambda x: x[0], reverse=True)
                results = [r for _, r in scored] + results[max_fetch:]
                selected_chunks = None

        evidence_pack: list[Evidence] = []
        if rerank_enabled and 'selected_chunks' in locals() and selected_chunks:
            # Build evidence from selected chunks
            for r, chunk in selected_chunks[:max_fetch]:
                fr = next((f for f in enriched if f.url == r.url or f.canonical_url == r.url), None)
                # Simple token estimate
                tokens = int(len(chunk.split()) * 1.3)
                evidence_pack.append(
                    Evidence(
                        title=r.title or (fr.title if fr else r.title) or "Untitled",
                        url=fr.canonical_url if fr and fr.canonical_url else r.url,
                        content=chunk[:8000],
                        tokens=tokens,
                        published_at=fr.published_at if fr else None,
                    )
                )
        else:
            for r in results[:max_fetch]:
                # find matching fetch result
                fr = next(
                    (f for f in enriched if f.url == r.url or f.canonical_url == r.url),
                    None,
                )
                content = fr.content if fr and fr.content else (r.snippet or "")
                tokens = fr.tokens_estimate if fr and fr.tokens_estimate else 0
                evidence_pack.append(
                    Evidence(
                        title=r.title or (fr.title if fr else r.title) or "Untitled",
                        url=fr.canonical_url if fr and fr.canonical_url else r.url,
                        content=content[:8000],
                        tokens=tokens,
                        published_at=fr.published_at if fr else None,
                    )
                )

        # 3) Build synthesis prompt
        def build_prompt(evidence: list[Evidence]) -> str:
            prompt_header = self._load_prompt()
            pack_lines: list[str] = []
            for idx, ev in enumerate(evidence, 1):
                meta_date = (
                    f" (published {ev.published_at.strftime('%Y-%m-%d')})"
                    if ev.published_at
                    else ""
                )
                pack_lines.append(
                    f"[{idx}] {ev.title}{meta_date}\nURL: {ev.url}\nContent:\n{ev.content}\n"
                )
            return f"{prompt_header}\n\n" + "\n".join(pack_lines)

        prompt = build_prompt(evidence_pack)

        # Optional deepening pass for low-confidence packs
        deepen_enabled = os.getenv("WEB_AGENT_DEEPEN", "false").lower() == "true"
        if deepen_enabled:
            min_docs = int(os.getenv("WEB_AGENT_DEEPEN_MIN_DOCS", "2"))
            min_tokens = int(os.getenv("WEB_AGENT_DEEPEN_MIN_TOKENS", "800"))
            total_tokens = sum(ev.tokens for ev in evidence_pack)
            if (
                len([ev for ev in evidence_pack if ev.content]) < min_docs
                or total_tokens < min_tokens
            ):
                # Try to fetch a couple more results not yet fetched
                extra_candidates = [
                    r.url
                    for r in results
                    if r.url not in set(e.url for e in evidence_pack)
                ]
                extra_to_fetch = extra_candidates[
                    : max(0, (max_fetch or self.max_fetch_default))
                ]
                if extra_to_fetch:
                    extra_enriched = await self.web_fetch.fetch_multiple(extra_to_fetch)
                    for fr in extra_enriched:
                        # Find title from original results
                        rmatch = next(
                            (
                                r
                                for r in results
                                if r.url == fr.url or r.url == fr.canonical_url
                            ),
                            None,
                        )
                        title = (
                            rmatch.title
                            if rmatch and rmatch.title
                            else (fr.title or "Untitled")
                        )
                        content = fr.content or (rmatch.snippet if rmatch else "")
                        evidence_pack.append(
                            Evidence(
                                title=title,
                                url=fr.canonical_url or fr.url,
                                content=(content or "")[:8000],
                                tokens=fr.tokens_estimate or 0,
                                published_at=fr.published_at,
                            )
                        )
                    # Rebuild prompt with new evidence
                    prompt = build_prompt(evidence_pack)

        # 4) Synthesize via AIService
        ai_service = await _get_ai_service(model_name)
        # Use non-stream generate_response with 'context' set to None; pack goes in prompt
        result = await ai_service.generate_response(prompt, context=None)
        text = result.get("response", "") if isinstance(result, dict) else str(result)

        # 5) Build citations mapping with optional quotes and trust
        def _extract_quotes(text: str, query: str, max_quotes: int = 2) -> list[str]:
            if not text:
                return []
            sentences = [s.strip() for s in text.split(". ") if s.strip()]
            scores = []
            for s in sentences:
                score = _simple_overlap_score(s, query)
                scores.append((score, s))
            scores.sort(key=lambda x: x[0], reverse=True)
            return [s for sc, s in scores[:max_quotes] if sc > 0]

        # Build a quick lookup to fetch trust metadata if available
        trust_map: dict[str, dict[str, Any]] = {}
        for fr in enriched:
            trust_map[fr.canonical_url or fr.url] = {
                "trust_score": getattr(fr, "trust_score", 0.5),
                "is_suspicious": getattr(fr, "is_suspicious", False),
                "domain": getattr(fr, "domain", None),
            }

        citations: list[dict[str, Any]] = []
        for idx, ev in enumerate(evidence_pack, 1):
            tm = trust_map.get(ev.url, {})
            citations.append(
                {
                    "id": idx,
                    "title": ev.title,
                    "url": ev.url,
                    "snippet": ev.content[:200],
                    "source": "web_search",
                    "source_type": "web",
                    "quotes": _extract_quotes(ev.content, query),
                    "trust": tm.get("trust_score"),
                    "suspicious": tm.get("is_suspicious"),
                    "domain": tm.get("domain"),
                }
            )

        final = {
            "response": text or "No recent results found.",
            "citations": citations,
            "web_provider": provider_name,
            "web_impl": impl,
            "web_results_count": len(results),
        }

        # Store in synthesis cache for non-time-sensitive queries
        if not time_sensitive and cache_ttl > 0:
            # Redis write
            r = get_redis()
            if r is not None:
                try:
                    import json
                    r.setex(f"synth:{cache_key}", cache_ttl, json.dumps(final))
                except Exception:
                    pass
            _SYNTH_CACHE[cache_key] = (datetime.now(), final)

        return final

    def _load_prompt(self) -> str:
        base = os.path.join(
            os.path.dirname(__file__), "prompts", "web_synthesis_prompt.txt"
        )
        try:
            with open(base, encoding="utf-8") as f:
                return f.read()
        except Exception:
            # Safe fallback
            return (
                "You are a web research assistant. Use ONLY the sources below. "
                "Output a markdown summary with sections and numbered Sources. Use inline citations [1], [2].\nEvidence Pack:"
            )
