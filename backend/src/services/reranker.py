"""
Local cross-encoder reranker using sentence-transformers.
Loads model lazily and provides a simple score API.
"""
from __future__ import annotations

import os
from typing import List, Optional

_RERANKER = None


def _load_model(model_name: str):
    try:
        from sentence_transformers import CrossEncoder  # type: ignore
    except Exception as e:  # pragma: no cover
        return None
    try:
        return CrossEncoder(model_name)
    except Exception:
        return None


def get_reranker() -> Optional[object]:
    global _RERANKER
    if _RERANKER is not None:
        return _RERANKER
    model_name = os.getenv("WEB_RERANK_MODEL", "").strip()
    if not model_name:
        return None
    _RERANKER = _load_model(model_name)
    return _RERANKER


def score_pairs(query: str, passages: List[str]) -> Optional[List[float]]:
    """Return relevance scores for (query, passage) pairs, or None if model not available."""
    model = get_reranker()
    if model is None:
        return None
    try:
        pairs = [(query, p) for p in passages]
        # type: ignore[attr-defined]
        scores = model.predict(pairs)  # returns list[float]
        return list(map(float, scores))
    except Exception:
        return None