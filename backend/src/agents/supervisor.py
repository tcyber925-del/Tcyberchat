"""Lightweight supervisor agent implemented in Python.

This is a conservative supervisor that uses the existing `web_research_subagent`
and the project's `ai_service` for planning and synthesis. It is feature-flag
free and intended to be used when LangChain agent machinery is not enabled.
"""
from __future__ import annotations

from typing import Any, Dict, List
from datetime import datetime

from .agent_utils import generate_run_id, safe_extract_json
from .subagents import web_research_subagent


async def supervise_research(query: str, model_name: str | None = None, max_results: int = 3) -> Dict[str, Any]:
    """Run a simple supervisor flow: plan -> investigate (subagents) -> synthesize.

    Returns: {answer, citations, metadata}
    """
    run_id = generate_run_id()
    start = datetime.now()

    # Lazy import AI service
    from ..services.ai_service import get_ai_service

    ai_service = await get_ai_service(model_name)

    # 1) Plan
    planning_prompt = f"""You are a research planner. Break down the following query into 2-4 focused sub-questions as JSON: {{\"sub_questions\": [...]}}\n\nQuery: {query}\n"""
    plan_resp = await ai_service.generate_response(planning_prompt, context=None)
    plan_text = plan_resp.get("response", "") if isinstance(plan_resp, dict) else str(plan_resp)
    plan = safe_extract_json(plan_text) or {"sub_questions": [query]}

    sub_questions = plan.get("sub_questions", [query])[:max_results]

    # 2) Investigate each sub-question via subagent
    investigations = []
    for sq in sub_questions:
        inv = await web_research_subagent(sq, max_results=max_results)
        investigations.append(inv)

    # 3) Synthesize
    findings_text = "\n\n".join([f"Sub-question: {inv['question']}\nFindings:\n{inv['findings']}" for inv in investigations])
    synth_prompt = f"You are a synthesizer. Using ONLY the findings below, write a comprehensive answer to the original query.\n\nOriginal Query: {query}\n\nFindings:\n{findings_text}\n\nAnswer:"
    synth_resp = await ai_service.generate_response(synth_prompt, context=None)
    draft = synth_resp.get("response", "") if isinstance(synth_resp, dict) else str(synth_resp)

    # Build citations from investigations
    citations = []
    for inv in investigations:
        for s in inv.get("sources", []):
            citations.append({"title": s.get("title"), "url": s.get("url"), "snippet": s.get("snippet")})

    end = datetime.now()
    duration = (end - start).total_seconds()

    return {
        "answer": draft,
        "citations": citations,
        "metadata": {"run_id": run_id, "duration_seconds": duration, "sub_questions": sub_questions},
    }
