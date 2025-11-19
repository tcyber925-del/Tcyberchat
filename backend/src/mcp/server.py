"""
MCP Server using the official SDK, exposing tools: web_search, deep_research.
"""
from __future__ import annotations

from typing import Any, Dict
import logging
import time

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

RETRIEVER_SCHEMA = {
    "type": "object",
    "properties": {
        "query": {"type": "string", "minLength": 1},
        "k": {"type": "integer", "minimum": 1, "maximum": 50, "default": 5}
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


async def tool_retriever(params: Dict[str, Any]) -> Dict[str, Any]:
    """Expose a simple retriever tool via MCP. Feature-guarded and defensive.

    Returns: {"results": [ {"page_content": ..., "metadata": {...}}, ... ]}
    """
    enabled = (str.__call__(__import__('os').environ.get('MCP_RETRIEVER_ENABLED', 'false')).lower() == 'true')
    if not enabled:
        return {"error": "Retriever MCP tool is disabled. Set MCP_RETRIEVER_ENABLED=true to enable."}

    q = str(params.get("query", "")).strip()
    k = int(params.get("k", 5))

    # Rate limiting (in-process). Uses optional client-provided key from params
    from ..services.rate_limit import get_rate_limiter

    rl = get_rate_limiter()
    client_key = params.get("client_id") or "mcp_retriever_global"
    limit = int(__import__("os").environ.get("MCP_RETRIEVER_RATE_LIMIT", "60"))
    window = int(__import__("os").environ.get("MCP_RETRIEVER_RATE_WINDOW", "60"))

    allowed = await rl.allow(str(client_key), limit=limit, window_seconds=window)
    if not allowed:
        logging.warning("Retriever rate limit exceeded for key=%s", client_key)
        return {"error": "Rate limit exceeded. Try again later."}

    start = time.time()
    try:
        from ..agents.tools import create_retriever_tool_from_vectorstore
        from ..services.rag_service import RAGService

        rs = RAGService()
        if not getattr(rs, "vectorstore", None):
            return {"results": []}

        tool = create_retriever_tool_from_vectorstore(rs.vectorstore, top_k=k)
        docs = tool(q)
        duration = time.time() - start
        logging.info("Retriever executed: q=%s, k=%d, results=%d, duration=%.3fs", q[:80], k, len(docs), duration)
        return {"results": docs}
    except Exception as e:
        logging.exception("Retriever tool failed")
        return {"error": str(e)}

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

    @server.tool(name="retriever", description="Retrieve docs from vectorstore", input_schema=RETRIEVER_SCHEMA)
    async def _t3(params: Dict[str, Any]):
        return await tool_retriever(params)

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

    @server.tool(name="retriever", description="Retrieve docs from vectorstore", input_schema=RETRIEVER_SCHEMA)
    async def _t3(params: Dict[str, Any]):
        return await tool_retriever(params)

    await server.run_ws(host=host, port=port, token=token)
