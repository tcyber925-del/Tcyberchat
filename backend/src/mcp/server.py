"""
MCP Server (hybrid): uses official SDK if available, else prints guidance.
Exposes tools: web_search, deep_research.
"""
from __future__ import annotations

from typing import Any, Dict

# Tool handlers
async def tool_web_search(params: Dict[str, Any]) -> Dict[str, Any]:
    from ..services.web_search_service import get_web_search_service
    q = str(params.get("q", "")).strip()
    k = int(params.get("maxResults", 5))
    svc = get_web_search_service()
    results = await svc.search(q, max_results=k)
    return {"results": [r.to_dict() for r in results]}

async def tool_deep_research(params: Dict[str, Any], emit=None) -> Dict[str, Any]:
    from ..agents.deep_research_agent import run_deep_research
    query = str(params.get("query", "")).strip()
    model = params.get("model")
    iters = int(params.get("maxIterations", 2))
    res = await run_deep_research(query=query, model_name=model, max_iterations=iters)
    return res

# Runners
async def run_stdio() -> None:  # pragma: no cover
    try:
        from mcp.server import Server  # type: ignore
    except Exception:
        print("Install the MCP server SDK to run stdio mode.")
        return
    server = Server(name="tcyber-chatbot")

    @server.tool(name="web_search", description="Search the web")
    async def _t1(params: Dict[str, Any]):
        return await tool_web_search(params)

    @server.tool(name="deep_research", description="Run multi-step deep research")
    async def _t2(params: Dict[str, Any]):
        return await tool_deep_research(params)

    await server.run_stdio()

async def run_ws(host: str = "0.0.0.0", port: int = 8765, token: str | None = None) -> None:  # pragma: no cover
    try:
        from mcp.server import Server  # type: ignore
    except Exception:
        print("Install the MCP server SDK to run websocket mode.")
        return
    server = Server(name="tcyber-chatbot")

    @server.tool(name="web_search", description="Search the web")
    async def _t1(params: Dict[str, Any]):
        return await tool_web_search(params)

    @server.tool(name="deep_research", description="Run multi-step deep research")
    async def _t2(params: Dict[str, Any]):
        return await tool_deep_research(params)

    await server.run_ws(host=host, port=port, token=token)
