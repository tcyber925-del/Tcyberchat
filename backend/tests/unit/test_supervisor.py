import asyncio

from unittest.mock import AsyncMock

import pytest

from backend.src.agents import supervisor


@pytest.mark.asyncio
async def test_supervise_research(monkeypatch):
    # Mock ai_service.get_ai_service to return an object with generate_response
    class DummyAI:
        async def generate_response(self, prompt, context=None):
            # If planning prompt, return a JSON plan
            if "Break down" in prompt:
                return {"response": '{"sub_questions": ["Q1", "Q2"]}'}
            return {"response": "This is the synthesized answer."}

    async def dummy_get_ai(model_name):
        return DummyAI()

    monkeypatch.setattr("backend.src.services.ai_service.get_ai_service", lambda model=None: dummy_get_ai(model))
    # Mock subagent to return predictable findings
    monkeypatch.setattr("backend.src.agents.subagents.web_research_subagent", lambda q, max_results=3: asyncio.get_event_loop().create_future().set_result({"question": q, "sources": [{"title":"T","url":"https://a","snippet":"s"}], "findings":"f"}) or {"question": q, "sources": [{"title":"T","url":"https://a","snippet":"s"}], "findings":"f"})

    res = await supervisor.supervise_research("test query")
    assert "answer" in res
    assert isinstance(res["citations"], list)
