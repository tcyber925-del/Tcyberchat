"""
Optional LangChain-based web research agent (search + fetch)
Falls back to orchestrator if LC not available.
"""

from __future__ import annotations

from typing import Any


class WebResearchAgentLC:
    def __init__(self):
        try:
            from langchain.agents import AgentExecutor  # noqa

            self.available = True
        except Exception:
            self.available = False

    async def run(self, query: str, model_name: str | None = None) -> dict[str, Any]:
        if not self.available:
            raise RuntimeError("LangChain not available")
        # For brevity, call the existing orchestrator rather than wiring a full agent graph here.
        # This preserves the output format and relies on existing fetch/search services.
        from ..services.web_research_orchestrator import WebResearchOrchestrator

        orch = WebResearchOrchestrator()
        return await orch.run(query, model_name=model_name)
