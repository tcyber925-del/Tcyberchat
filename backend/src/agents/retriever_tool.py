"""Simple retriever-tool factory used by agents.

This module provides `create_retriever_tool` which returns a callable that
accepts a query and returns a normalized list of results. The implementation
is defensive and avoids importing heavy vectorstore libraries at module import
time; it operates on any object that implements one of the common retrieval
interfaces: `similarity_search`, `get_relevant_documents`, or `as_retriever`.

The callable is intentionally simple so unit tests can be run without
installing external ML/vector packages.
"""
from typing import Any, Callable, List, Optional


def _normalize_doc(d: Any) -> dict:
    """Normalize many common Document shapes into a simple dict."""
    result = {"title": None, "text": None, "source": None}

    # dict-like
    if isinstance(d, dict):
        meta = d.get("metadata", {}) or {}
        result["title"] = meta.get("title")
        result["text"] = d.get("page_content") or d.get("content")
        result["source"] = meta.get("source") or meta.get("source_id")
        return result

    # object-like (LangChain Document, etc.)
    meta = getattr(d, "metadata", None)
    if isinstance(meta, dict):
        result["title"] = meta.get("title")
        result["source"] = meta.get("source") or meta.get("source_id")

    result["text"] = getattr(d, "page_content", None) or getattr(d, "content", None)
    return result


def create_retriever_tool(vectorstore: Optional[Any] = None, top_k: int = 5) -> Callable[[str], List[dict]]:
    """Return a callable retriever tool.

    Parameters
    - vectorstore: an object that implements one of the retrieval interfaces
      (similarity_search(query, k=...), get_relevant_documents(query), or
      as_retriever()). If omitted, the returned tool will raise at call time.
    - top_k: default number of results to return.

    The returned callable has the signature `tool(query, k=None)` where `k`
    overrides `top_k` if provided.
    """

    def retriever_tool(query: str, k: Optional[int] = None) -> List[dict]:
        nonlocal vectorstore
        if k is None:
            k = top_k

        if vectorstore is None:
            raise RuntimeError("No vectorstore provided to retriever tool.")

        # Try common method names in order of prevalence
        docs = None
        if hasattr(vectorstore, "similarity_search"):
            try:
                docs = vectorstore.similarity_search(query, k=k)
            except TypeError:
                # some implementations expect (query, k) vs (query, top_k)
                docs = vectorstore.similarity_search(query, k)

        elif hasattr(vectorstore, "get_relevant_documents"):
            docs = vectorstore.get_relevant_documents(query)
            if isinstance(docs, list) and len(docs) > k:
                docs = docs[:k]

        elif hasattr(vectorstore, "as_retriever"):
            retr = vectorstore.as_retriever(search_kwargs={"k": k})
            # retr may implement get_relevant_documents
            if hasattr(retr, "get_relevant_documents"):
                docs = retr.get_relevant_documents(query)

        else:
            raise RuntimeError("Provided vectorstore does not implement a supported retrieval interface.")

        if docs is None:
            return []

        return [_normalize_doc(d) for d in docs]

    return retriever_tool
