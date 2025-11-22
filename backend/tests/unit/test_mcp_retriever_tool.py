import asyncio

from unittest.mock import patch

import pytest

from backend.src.mcp import server as mcp_server


@pytest.mark.asyncio
async def test_tool_retriever_disabled():
    res = await mcp_server.tool_retriever({"query": "q"})
    assert "error" in res


@pytest.mark.asyncio
async def test_tool_retriever_returns_results(monkeypatch):
    # Enable the MCP retriever via env
    import os

    monkeypatch.setenv("MCP_RETRIEVER_ENABLED", "true")

    # Patch RAGService and factory to return predictable docs
    dummy_docs = [{"page_content": "doc text", "metadata": {"title": "T", "source": "s"}}]

    class DummyVS:
        pass

    class DummyRAG:
        def __init__(self):
            self.vectorstore = DummyVS()

    monkeypatch.setattr("backend.src.services.rag_service.RAGService", lambda *a, **k: DummyRAG())
    monkeypatch.setattr("backend.src.agents.tools.create_retriever_tool_from_vectorstore", lambda vs, top_k=5: (lambda q, k=5: dummy_docs))

    res = await mcp_server.tool_retriever({"query": "q", "k": 2})
    assert "results" in res
    assert isinstance(res["results"], list)
    assert res["results"][0]["page_content"] == "doc text"
