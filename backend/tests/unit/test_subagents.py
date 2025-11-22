import asyncio

import pytest

from backend.src.agents import subagents


def test_web_research_subagent_monkeypatch(monkeypatch):
    # Monkeypatch web_search_tool to return simple results
    monkeypatch.setattr("backend.src.agents.tools.web_search_tool", lambda q, max_results=3: [{"title":"T1","url":"https://a.example","snippet":"s1"}])

    # Monkeypatch fetch_multiple in web_fetch_enhanced
    async def fake_fetch(urls):
        return [{"url": urls[0], "content": "Fetched content"}]

    monkeypatch.setattr("backend.src.services.web_fetch_enhanced.fetch_multiple", fake_fetch)

    res = asyncio.get_event_loop().run_until_complete(subagents.web_research_subagent("what"))
    assert res["question"] == "what"
    assert len(res["sources"]) == 1
