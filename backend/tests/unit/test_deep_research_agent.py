import os
import json
import types
import pytest

from backend.src.agents.deep_research_agent import (
    plan_research,
    investigate_parallel,
    synthesize_findings,
    critique_answer,
    refine_research,
    finalize_report,
)


@pytest.mark.asyncio
async def test_plan_research_parses_json(monkeypatch):
    class DummyAI:
        async def generate_response(self, prompt, context=None, max_tokens=1024):
            return {"response": json.dumps({
                "sub_questions": ["A", "B"],
                "angles": ["tech"]
            })}

    async def fake_get_ai_service(model):
        return DummyAI()

    monkeypatch.setattr(
        "backend.src.services.ai_service.get_ai_service", fake_get_ai_service
    )

    state = {
        "query": "What is LangGraph?",
        "plan": None,
        "investigations": [],
        "draft_answer": None,
        "critique": None,
        "final_answer": None,
        "citations": [],
        "metadata": {},
        "iteration": 0,
        "max_iterations": 2,
    }

    out = await plan_research(state)  # type: ignore[arg-type]
    assert "plan" in out
    assert out["plan"]["sub_questions"] == ["A", "B"]


@pytest.mark.asyncio
async def test_plan_research_fallback_on_bad_json(monkeypatch):
    class DummyAI:
        async def generate_response(self, prompt, context=None, max_tokens=1024):
            return {"response": "not-json"}

    async def fake_get_ai_service(model):
        return DummyAI()

    monkeypatch.setattr(
        "backend.src.services.ai_service.get_ai_service", fake_get_ai_service
    )

    query = "Explain vector databases"
    state = {
        "query": query,
        "plan": None,
        "investigations": [],
        "draft_answer": None,
        "critique": None,
        "final_answer": None,
        "citations": [],
        "metadata": {},
        "iteration": 0,
        "max_iterations": 2,
    }

    out = await plan_research(state)  # type: ignore[arg-type]
    assert out["plan"]["sub_questions"] == [query]


@pytest.mark.asyncio
async def test_investigate_parallel_basic(monkeypatch):
    # Fake web search service
    class DummyRes:
        def __init__(self, title, url, snippet):
            self.title = title
            self.url = url
            self.snippet = snippet

    class DummySearchSvc:
        async def search(self, q, max_results=3, use_cache=True):
            return [DummyRes("Title1", "http://a", "Snippet1")]

    class DummyFetch:
        def __init__(self, url):
            self.url = url
            self.canonical_url = url
            self.content = "Fetched content"
            self.tokens_estimate = 100

    class DummyFetchSvc:
        async def fetch_multiple(self, urls):
            return [DummyFetch(u) for u in urls]

    def fake_get_web_search_service():
        return DummySearchSvc()

    def fake_get_web_fetch_service():
        return DummyFetchSvc()

    monkeypatch.setattr(
        "backend.src.services.web_search_service.get_web_search_service",
        fake_get_web_search_service,
    )
    monkeypatch.setattr(
        "backend.src.services.web_fetch_service.get_web_fetch_service",
        fake_get_web_fetch_service,
    )

    state = {
        "query": "q",
        "plan": {"sub_questions": ["sub1"]},
        "investigations": [],
        "draft_answer": None,
        "critique": None,
        "final_answer": None,
        "citations": [],
        "metadata": {},
        "iteration": 0,
        "max_iterations": 2,
    }

    out = await investigate_parallel(state)  # type: ignore[arg-type]
    assert out["investigations"], "should have investigations"
    assert out["citations"], "should have citations"


@pytest.mark.asyncio
async def test_synthesize_findings_uses_ai(monkeypatch):
    class DummyAI:
        async def generate_response(self, prompt, context=None, max_tokens=1024):
            return {"response": "Draft answer with [1] and sufficient content."}

    async def fake_get_ai_service(model):
        return DummyAI()

    monkeypatch.setattr(
        "backend.src.services.ai_service.get_ai_service", fake_get_ai_service
    )

    state = {
        "query": "What is X?",
        "plan": None,
        "investigations": [{"question": "A", "findings": "F"}],
        "draft_answer": None,
        "critique": None,
        "final_answer": None,
        "citations": [],
        "metadata": {},
        "iteration": 0,
        "max_iterations": 2,
    }

    out = await synthesize_findings(state)  # type: ignore[arg-type]
    assert "Draft answer" in out["draft_answer"]


@pytest.mark.asyncio
async def test_critique_answer_flags_missing_citations():
    state = {
        "query": "q",
        "draft_answer": "short text",  # <100 words, no [1]
        "iteration": 0,
        "max_iterations": 2,
    }
    out = await critique_answer(state)  # type: ignore[arg-type]
    crit = out["critique"]
    assert crit["needs_refinement"] is True
    assert "Missing citations" in crit["gaps"]


@pytest.mark.asyncio
async def test_refine_research_increments_and_adds_investigations(monkeypatch):
    # Reuse search/fetch fakes
    class DummyRes:
        def __init__(self, title, url, snippet):
            self.title = title
            self.url = url
            self.snippet = snippet

    class DummySearchSvc:
        async def search(self, q, max_results=3, use_cache=True):
            return [DummyRes("Title", "http://example", "Snippet")]  # one result

    class DummyFetch:
        def __init__(self, url):
            self.url = url
            self.canonical_url = url
            self.content = "Fetched content"
            self.tokens_estimate = 100

    class DummyFetchSvc:
        async def fetch_multiple(self, urls):
            return [DummyFetch(u) for u in urls]

    monkeypatch.setattr(
        "backend.src.services.web_search_service.get_web_search_service",
        lambda: DummySearchSvc(),
    )
    monkeypatch.setattr(
        "backend.src.services.web_fetch_service.get_web_fetch_service",
        lambda: DummyFetchSvc(),
    )

    state = {
        "query": "q",
        "plan": {"sub_questions": ["original"]},
        "investigations": [],
        "draft_answer": "short text",  # to trigger gaps
        "critique": {"gaps": ["Missing citations"], "needs_refinement": True},
        "final_answer": None,
        "citations": [],
        "metadata": {},
        "iteration": 0,
        "max_iterations": 2,
    }

    out = await refine_research(state)  # type: ignore[arg-type]
    assert out["iteration"] == 1
    assert out["investigations"], "should add investigations during refinement"


@pytest.mark.asyncio
async def test_finalize_report_dedups_citations():
    state = {
        "draft_answer": "Some draft",
        "citations": [
            {"title": "A", "url": "http://same", "snippet": "s", "tokens": 1},
            {"title": "B", "url": "http://same", "snippet": "t", "tokens": 2},
            {"title": "C", "url": "http://other", "snippet": "u", "tokens": 3},
        ],
        "metadata": {},
    }
    out = await finalize_report(state)  # type: ignore[arg-type]
    assert len(out["citations"]) == 2
    assert "## Sources" in out["final_answer"]
