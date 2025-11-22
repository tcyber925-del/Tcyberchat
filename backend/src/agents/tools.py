"""Simple agent tool wrappers to expose search, fetch, and retriever functionality.

These are lightweight wrappers intended for use by agents/subagents. They are
kept minimal and return JSON-serializable dicts/lists so tests can mock
underlying services easily.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List

# Import services lazily inside functions to allow tests to monkeypatch the
# service factory functions before `tools` is imported.
from .retriever_tool import create_retriever_tool as _create_retriever_factory


def web_search_tool(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    from ..services.web_search_service import get_web_search_service
    import asyncio

    svc = get_web_search_service()
    # Support multiple service interfaces: prefer .search_sync, else await .search
    if hasattr(svc, "search_sync"):
        results = svc.search_sync(query, max_results=max_results)
    else:
        # assume async search; create a fresh event loop and run the coroutine
        new_loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(new_loop)
            try:
                results = new_loop.run_until_complete(svc.search(query, max_results=max_results))
            finally:
                asyncio.set_event_loop(None)
        finally:
            new_loop.close()
    # normalize to dicts
    out = []
    for r in results:
        try:
            out.append(r.to_dict())
        except Exception:
            out.append({"title": getattr(r, "title", None), "url": getattr(r, "url", None), "snippet": getattr(r, "snippet", None)})
    return out


def web_fetch_tool(urls: List[str], force_fresh: bool = False) -> List[Dict[str, Any]]:
    from ..services.web_fetch_service import get_web_fetch_service
    import asyncio

    svc = get_web_fetch_service()
    # If a sync helper exists, use it
    if hasattr(svc, "fetch_multiple_sync"):
        try:
            return svc.fetch_multiple_sync(urls, force_fresh=force_fresh)
        except TypeError:
            return svc.fetch_multiple_sync(urls)
    # Otherwise, call async and handle signature differences; create a loop if needed
    # Use a fresh event loop for the coroutine call to avoid thread-local loop issues
    new_loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(new_loop)
        try:
            try:
                return new_loop.run_until_complete(svc.fetch_multiple(urls, force_fresh=force_fresh))
            except TypeError:
                return new_loop.run_until_complete(svc.fetch_multiple(urls))
        finally:
            asyncio.set_event_loop(None)
    finally:
        new_loop.close()


def create_retriever_tool(retriever: Any, name: str = "retriever", description: str | None = None) -> Callable[[str], List[Dict[str, Any]]]:
    """Wrap a LangChain-like retriever into a simple callable tool.

    The returned function accepts a query string and returns a list of documents
    represented as dicts with `page_content` and `metadata`.
    """

    def _tool(query: str, k: int | None = None):
        k = k or getattr(retriever, "k", None) or 5
        # retriever may provide a `.get_relevant_documents` or `get_relevant_documents`
        docs = None
        if hasattr(retriever, "get_relevant_documents"):
            docs = retriever.get_relevant_documents(query)
        elif hasattr(retriever, "similarity_search"):
            docs = retriever.similarity_search(query, k=k)
        else:
            # try generic call
            docs = retriever(query)

        out = []
        for d in docs:
            try:
                out.append({"page_content": d.page_content, "metadata": d.metadata})
            except Exception:
                out.append({"page_content": getattr(d, "page_content", str(d)), "metadata": getattr(d, "metadata", {})})
        return out

    _tool.__name__ = name
    _tool.__doc__ = description or "Retriever tool"
    return _tool


def create_retriever_tool_from_vectorstore(vectorstore: Any, top_k: int = 5, name: str = "vector_retriever", description: str | None = None) -> Callable[[str], List[Dict[str, Any]]]:
    """Convenience wrapper that builds a retriever tool from a vectorstore.

    This delegates to `backend.src.agents.retriever_tool.create_retriever_tool`
    but returns a callable shaped like the other `create_retriever_tool` above
    (returns list of dicts with `page_content` and `metadata`).
    """
    factory = _create_retriever_factory(vectorstore=vectorstore, top_k=top_k)

    def _tool(query: str, k: int | None = None):
        k = k or top_k
        results = factory(query, k=k)
        out = []
        for r in results:
            out.append({"page_content": r.get("text"), "metadata": {"title": r.get("title"), "source": r.get("source")}})
        return out

    _tool.__name__ = name
    _tool.__doc__ = description or "Vectorstore retriever tool"
    return _tool
