"""
MCP Server using the official SDK, exposing tools: web_search, deep_research.
"""
from __future__ import annotations

from typing import Any, Dict

# JSON Schemas for tool inputs
WEB_SEARCH_SCHEMA = {
    "type": "object",
    "properties": {
        "q": {"type": "string", "minLength": 1, "description": "Search query"},
        "maxResults": {"type": "integer", "minimum": 1, "maximum": 10, "default": 5}
    },
    "required": ["q"],
}

DEEP_RESEARCH_SCHEMA = {
    "type": "object",
    "properties": {
        "query": {"type": "string", "minLength": 1, "description": "Research question"},
        "model": {"type": "string"},
        "maxIterations": {"type": "integer", "minimum": 1, "maximum": 5, "default": 2}
    },
    "required": ["query"],
}

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
    from mcp.server.fastmcp import FastMCP

    server = FastMCP("tcyber-chatbot")

    @server.tool(name="web_search", description="Search the web", input_schema=WEB_SEARCH_SCHEMA)
    async def _t1(params: Dict[str, Any]):
        return await tool_web_search(params)

    @server.tool(name="deep_research", description="Run multi-step deep research", input_schema=DEEP_RESEARCH_SCHEMA)
    async def _t2(params: Dict[str, Any]):
        return await tool_deep_research(params)

    await server.run_stdio()

async def run_ws(host: str = "0.0.0.0", port: int = 8765, token: str | None = None) -> None:  # pragma: no cover
    from mcp.server.fastmcp import FastMCP

    server = FastMCP("tcyber-chatbot")

    @server.tool(name="web_search", description="Search the web", input_schema=WEB_SEARCH_SCHEMA)
    async def _t1(params: Dict[str, Any]):
        return await tool_web_search(params)

    @server.tool(name="deep_research", description="Run multi-step deep research", input_schema=DEEP_RESEARCH_SCHEMA)
    async def _t2(params: Dict[str, Any]):
        return await tool_deep_research(params)

    await server.run_ws(host=host, port=port, token=token)
