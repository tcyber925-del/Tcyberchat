import os
import json
import pytest
from fastapi.testclient import TestClient

# Import the FastAPI app
from backend.main import app


def test_deep_research_endpoint_happy_path(monkeypatch):
    # Enable the feature
    monkeypatch.setenv("DEEP_RESEARCH_ENABLED", "true")

    # Mock AI service to produce a deterministic plan and synthesis
    class DummyAI:
        async def generate_response(self, prompt, context=None, max_tokens=1024):
            if "Break down this question" in prompt:
                return {"response": json.dumps({
                    "sub_questions": ["Q1"],
                    "angles": ["tech"]
                })}
            # synthesis
            long_text = "word " * 120  # ensure >100 words
            return {"response": f"{long_text}\n\nIncludes citation [1]."}

    async def fake_get_ai_service(model):
        return DummyAI()

    # Mock web search and fetch services used by the agent
    class DummyRes:
        def __init__(self, title, url, snippet):
            self.title = title
            self.url = url
            self.snippet = snippet

    class DummySearchSvc:
        async def search(self, q, max_results=3, use_cache=True, force_fresh=False):
            return [DummyRes("Title1", "http://a", "Snippet1")]

    class DummyFetch:
        def __init__(self, url):
            self.url = url
            self.canonical_url = url
            self.content = "Fetched content"
            self.tokens_estimate = 100

    class DummyFetchSvc:
        enabled = True
        async def fetch_multiple(self, urls):
            return [DummyFetch(u) for u in urls]

    monkeypatch.setattr(
        "backend.src.services.ai_service.get_ai_service", fake_get_ai_service
    )
    monkeypatch.setattr(
        "backend.src.services.web_search_service.get_web_search_service",
        lambda: DummySearchSvc(),
    )
    monkeypatch.setattr(
        "backend.src.services.web_fetch_service.get_web_fetch_service",
        lambda: DummyFetchSvc(),
    )

    client = TestClient(app)
    resp = client.post(
        "/tools/web-search/deep-research",
        json={"query": "Explain LangGraph", "maxIterations": 1},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data
    assert "citations" in data
    assert isinstance(data["citations"], list)
    assert any("http://a" in c.get("url", "") for c in data["citations"])  # from dummy


def test_deep_research_endpoint_disabled(monkeypatch):
    # Ensure disabled
    monkeypatch.setenv("DEEP_RESEARCH_ENABLED", "false")

    client = TestClient(app)
    resp = client.post(
        "/tools/web-search/deep-research",
        json={"query": "anything"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "error" in data
    assert "disabled" in data["error"].lower()
