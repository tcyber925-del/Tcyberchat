"""
LangChain-based URL loader used as an optional backend for WebFetchService
"""

from __future__ import annotations

import asyncio
from datetime import datetime


class LangChainWebLoader:
    def is_available(self) -> bool:  # pragma: no cover
        try:
            return True
        except Exception:
            return False

    async def fetch(
        self, url: str
    ) -> tuple[str | None, str | None, datetime | None, str | None]:
        """Fetch URL using LangChain WebBaseLoader and return (content, title, published_at, content_type)."""
        from langchain_community.document_loaders import WebBaseLoader  # type: ignore

        loop = asyncio.get_event_loop()

        def _load():
            loader = WebBaseLoader([url])
            docs = loader.load()
            return docs

        docs = await loop.run_in_executor(None, _load)
        if not docs:
            return None, None, None, None
        # Combine content
        content = "\n".join(
            d.page_content for d in docs if getattr(d, "page_content", None)
        )
        md = getattr(docs[0], "metadata", {}) or {}
        title = md.get("title") or md.get("source")
        # published_at is often not provided; leave None
        published_at = None
        content_type = "text/html"
        return content, title, published_at, content_type
