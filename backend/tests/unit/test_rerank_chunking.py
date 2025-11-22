import os
import pytest

from backend.src.services.web_research_orchestrator import WebResearchOrchestrator, _chunk_text


@pytest.mark.asyncio
async def test_chunk_text_basic():
    text = "abcdefghij" * 100
    chunks = _chunk_text(text, max_chars=100, overlap=10)
    assert chunks, "should chunk"
    # Ensure overlap behavior roughly holds
    assert len(chunks[0]) <= 100
    if len(chunks) > 1:
        assert chunks[0][-10:] == chunks[1][:10]


@pytest.mark.asyncio
async def test_rerank_chunk_selection(monkeypatch):
    # Enable rerank and set dummy model env (we'll mock scorer)
    monkeypatch.setenv("WEB_RERANK_ENABLED", "true")
    monkeypatch.setenv("WEB_RERANK_MODEL", "test-model")
    monkeypatch.setenv("DEEP_RESEARCH_ENABLED", "true")  # not used here but harmless

    # Dummy services
    class DummyRes:
        def __init__(self, title, url, snippet):
            self.title = title
            self.url = url
            self.snippet = snippet
            self.relevance_score = 1.0

    class DummySearchSvc:
        def __init__(self):
            self.provider_name = "dummy"
            self.impl = "custom"
            class P: pass
            self.primary_provider = P()
            self.primary_provider.name = "dummy"
        async def search(self, q, max_results=5, use_cache=True, force_fresh=False):
            return [
                DummyRes("A", "http://a", ""),
                DummyRes("B", "http://b", ""),
            ]

    class DummyFetch:
        def __init__(self, url, content):
            self.url = url
            self.canonical_url = url
            self.content = content
            self.tokens_estimate = len(content.split())
            self.published_at = None
            self.title = None

    class DummyFetchSvc:
        enabled = True
        async def fetch_multiple(self, urls):
            return [
                DummyFetch("http://a", "alpha chunk1. alpha chunk2."),
                DummyFetch("http://b", "beta chunk1. beta chunk2."),
            ]

    # We'll set services on the orchestrator instance directly to avoid provider auto-detection

    # Mock AI service to avoid model calls
    class DummyAI:
        async def generate_response(self, prompt, context=None, max_tokens=1024):
            return {"response": "ok"}

    async def fake_get_ai_service(model):
        return DummyAI()

    monkeypatch.setattr(
        "backend.src.services.ai_service.get_ai_service", fake_get_ai_service
    )

    # Mock reranker.score_pairs to favor beta chunk2 > alpha chunk1
    def fake_score_pairs(query, passages):
        scores = []
        for p in passages:
            if "beta" in p and "chunk2" in p:
                scores.append(0.99)
            elif "alpha" in p and "chunk1" in p:
                scores.append(0.80)
            else:
                scores.append(0.10)
        return scores

    monkeypatch.setenv("WEB_RERANK_PASSAGE_CHARS", "12")  # to force small chunks
    monkeypatch.setenv("WEB_RERANK_PASSAGE_OVERLAP", "0")

    # Patch reranker.score_pairs used by orchestrator
    monkeypatch.setattr("backend.src.services.reranker.score_pairs", fake_score_pairs, raising=False)

    orch_service = WebResearchOrchestrator()
    orch_service.web_search = DummySearchSvc()  # type: ignore
    orch_service.web_fetch = DummyFetchSvc()  # type: ignore
    out = await orch_service.run("q test", model_name=None, max_results=2, max_fetch=2)
    assert "citations" in out
    # Expect a citation from url http://b due to higher score
    assert any(c.get("url", "").startswith("http://b") for c in out["citations"]) \
        or any(c.get("url", "").startswith("http://b") for c in (out.get("results", []) or []))
