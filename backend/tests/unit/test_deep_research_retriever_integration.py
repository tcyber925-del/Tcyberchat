import asyncio

import pytest

from backend.src.agents import deep_research_agent as dra


class DummyVectorStore:
    def __init__(self, docs):
        self._docs = docs

    def similarity_search(self, query, k=5):
        return self._docs[:k]


class DummyRAGService:
    def __init__(self, vectorstore):
        self.vectorstore = vectorstore


def test_investigate_parallel_includes_retriever(monkeypatch):
    # Prepare dummy web search results
    class R:
        def __init__(self, url, title, snippet):
            self.url = url
            self.title = title
            self.snippet = snippet

    results = [R("https://a", "A", "s1"), R("https://b", "B", "s2")]

    async def dummy_search(question, max_results=3, use_cache=True):
        return results

    async def dummy_fetch_multiple(urls):
        # return objects with attributes url, canonical_url, content, tokens_estimate
        class F:
            def __init__(self, url):
                self.url = url
                self.canonical_url = url
                self.content = "content for " + url
                self.tokens_estimate = 10

        return [F(u) for u in urls]

    monkeypatch.setattr("backend.src.services.web_search_service.get_web_search_service", lambda: type("S", (), {"search": dummy_search}))
    monkeypatch.setattr("backend.src.services.web_fetch_service.get_web_fetch_service", lambda: type("F", (), {"fetch_multiple": dummy_fetch_multiple}))

    # Monkeypatch RAGService to return a dummy vectorstore
    dummy_docs = [{"text": "retrieved text", "title": "RDoc", "source": "https://r"}]
    monkeypatch.setattr("backend.src.services.rag_service.RAGService", lambda *a, **k: DummyRAGService(DummyVectorStore(dummy_docs)))
    # Make sure the retriever factory returns a simple callable that yields our dummy docs
    monkeypatch.setattr("backend.src.agents.tools.create_retriever_tool_from_vectorstore", lambda vs, top_k=3, name=None, description=None: (lambda q, k=3: dummy_docs))

    # Build a minimal state with a plan
    state = {
        "query": "test",
        "plan": {"sub_questions": ["q1"]},
        "investigations": [],
        "draft_answer": None,
        "critique": None,
        "final_answer": None,
        "citations": [],
        "metadata": {},
        "iteration": 0,
        "max_iterations": 1,
    }

    loop = asyncio.get_event_loop()
    res = loop.run_until_complete(dra.investigate_parallel(state))

    assert "investigations" in res
    inv = res["investigations"][0]
    # Should include retriever-added source (by title or snippet)
    sources = inv.get("sources", [])
    titles = [s.get("title") for s in sources]
    snippets = [s.get("snippet") for s in sources]
    assert any("RDoc" == t for t in titles) or any("retrieved" in (sn or "") for sn in snippets)
