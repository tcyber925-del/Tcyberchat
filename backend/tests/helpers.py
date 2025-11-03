"""Test helper utilities and shims used by unit tests.

Keep light-weight shims here to avoid importing heavy optional deps during unit tests.
"""
from typing import Any


def inject_rag_shims(rag_mod: Any):
    """Inject minimal shims into the rag_service module for deterministic tests.

    This sets:
      - LangChainDocument: simple wrapper with page_content and metadata
      - BM25Retriever: minimal from_documents/get_relevant_documents
      - get_ai_service: returns a simple async AI stub
    """
    class LangChainDocumentShim:
        def __init__(self, page_content=None, metadata=None):
            self.page_content = page_content
            self.metadata = metadata or {}

    class BM25Shim:
        @classmethod
        def from_documents(cls, docs):
            class Retriever:
                def __init__(self, docs):
                    self.docs = docs

                def get_relevant_documents(self, query, k=5):
                    q = query.lower()
                    out = []
                    for d in self.docs:
                        pc = getattr(d, 'page_content', '') or ''
                        if q in pc.lower() or any(kw in pc.lower() for kw in ["paris", "capital"]):
                            out.append(d)
                    return out[:k]

            return Retriever(docs)

    class AIStub:
        def __init__(self):
            self.model_name = "stub"

        async def generate_response(self, prompt: str, context=None):
            return {"response": "(stub) " + str(prompt)}

    rag_mod.LangChainDocument = LangChainDocumentShim
    rag_mod.BM25Retriever = BM25Shim
    rag_mod.get_ai_service = lambda m=None: AIStub()
