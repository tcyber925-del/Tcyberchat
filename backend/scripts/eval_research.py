"""
Simple evaluation harness to benchmark web research and deep research.
Usage: python -m backend.scripts.eval_research --queries "q1; q2; q3" --deep true
"""
from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List

from backend.src.services.web_research_orchestrator import WebResearchOrchestrator

try:
    from backend.src.agents.deep_research_agent import run_deep_research
except Exception:  # pragma: no cover
    run_deep_research = None  # type: ignore


async def eval_query(q: str, deep: bool, model: str | None) -> Dict[str, Any]:
    started = datetime.utcnow()
    if deep and run_deep_research is not None:
        res = await run_deep_research(q, model_name=model, max_iterations=2)
        duration = (datetime.utcnow() - started).total_seconds()
        return {
            "query": q,
            "mode": "deep",
            "duration_s": duration,
            "citations": len(res.get("citations", [])),
            "chars": len(res.get("answer", "")),
        }
    else:
        orch = WebResearchOrchestrator()
        res = await orch.run(q, model_name=model, max_results=5, max_fetch=3)
        duration = (datetime.utcnow() - started).total_seconds()
        return {
            "query": q,
            "mode": "orchestrator",
            "duration_s": duration,
            "citations": len(res.get("citations", [])),
            "chars": len(res.get("response", "")),
        }


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queries", type=str, required=True, help="Semicolon-separated queries")
    parser.add_argument("--deep", type=str, default="false")
    parser.add_argument("--model", type=str, default=None)
    args = parser.parse_args()

    queries: List[str] = [s.strip() for s in args.queries.split(";") if s.strip()]
    deep = args.deep.lower() == "true"

    rows: List[Dict[str, Any]] = []
    for q in queries:
        try:
            rows.append(await eval_query(q, deep, args.model))
        except Exception as e:  # pragma: no cover
            rows.append({"query": q, "mode": "error", "error": str(e)})

    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
