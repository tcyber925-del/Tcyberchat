"""Helper to manage the persistent vectorstore used by RAG.

This thin wrapper uses `rag_adapter.create_vectorstore` to obtain a vectorstore
and exposes small helper functions to add texts/documents and persist the
store. Designed to be defensive so tests don't require heavy dependencies.
"""
from typing import Any, List, Optional


def get_vectorstore(collection_name: str = "documents", embedding: Optional[Any] = None) -> Any:
    try:
        from .rag_adapter import create_vectorstore

        vs = create_vectorstore(client=None, collection_name=collection_name, embedding=embedding)
        return vs
    except Exception:
        return None


def add_texts(texts: List[str], metadatas: Optional[List[dict]] = None, ids: Optional[List[str]] = None, collection_name: str = "documents", embedding: Optional[Any] = None) -> bool:
    vs = get_vectorstore(collection_name=collection_name, embedding=embedding)
    if vs is None:
        return False

    try:
        # Prefer add_texts if available
        if hasattr(vs, "add_texts"):
            vs.add_texts(texts, metadatas=metadatas, ids=ids)
        elif hasattr(vs, "add_documents"):
            # create simple doc dicts
            docs = []
            for t, m, i in zip(texts, metadatas or [{} for _ in texts], ids or [None]*len(texts)):
                docs.append({"page_content": t, "metadata": m})
            vs.add_documents(docs)
        else:
            # Unsupported vectorstore interface
            return False

        # Persist if supported
        if hasattr(vs, "persist"):
            try:
                vs.persist()
            except Exception:
                pass
        return True
    except Exception:
        return False
