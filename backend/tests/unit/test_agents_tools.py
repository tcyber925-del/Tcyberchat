import pytest

from backend.src.agents import tools, middleware


class DummySearchResult:
    def __init__(self, title, url, snippet):
        self.title = title
        self.url = url
        self.snippet = snippet

    def to_dict(self):
        return {"title": self.title, "url": self.url, "snippet": self.snippet}


class DummySearchService:
    def search_sync(self, q, max_results=5):
        return [DummySearchResult("A", "https://a.example", "s1"), DummySearchResult("B", "https://b.example", "s2")]


class DummyFetchService:
    def fetch_multiple_sync(self, urls, force_fresh=False):
        return [{"url": u, "content": "ok"} for u in urls]


def test_web_search_tool_monkeypatch(monkeypatch):
    monkeypatch.setattr("backend.src.services.web_search_service.get_web_search_service", lambda: DummySearchService())
    out = tools.web_search_tool("test")
    assert isinstance(out, list)
    assert out[0]["url"] == "https://a.example"


def test_web_fetch_tool_monkeypatch(monkeypatch):
    monkeypatch.setattr("backend.src.services.web_fetch_service.get_web_fetch_service", lambda: DummyFetchService())
    out = tools.web_fetch_tool(["https://a.example"])
    assert isinstance(out, list)
    assert out[0]["url"] == "https://a.example"


def test_wrap_tool_call_decorator():
    @middleware.wrap_tool_call
    def fail_tool(x):
        raise ValueError("bad")

    res = fail_tool(1)
    assert res.get("tool_error") is True
    assert "bad" in res.get("error")
