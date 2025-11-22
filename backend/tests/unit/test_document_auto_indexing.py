import asyncio
from types import SimpleNamespace

from backend.src.services.document_service import DocumentService


def test_generate_chunks_fallback_indexes(monkeypatch):
    # Create a DocumentService with no DB (not used in this method)
    ds = DocumentService(db=None)

    # Dummy document
    doc = SimpleNamespace()
    doc.id = "d1"
    doc.filename = "test.txt"
    doc.mime_type = "text/plain"
    doc.uploaded_at = None
    doc.size = 10
    doc.content = "This is a test document. " * 50  # long content

    # Mock get_rag_service to return an object whose add_document_with_chunking returns False
    async def _fake_add_document_with_chunking(document_id, full_text, metadata=None):
        return False

    class FakeRAG:
        def __init__(self):
            pass

        async def add_document_with_chunking(self, document_id, full_text, metadata=None):
            return await _fake_add_document_with_chunking(document_id, full_text, metadata)

    monkeypatch.setattr("backend.src.services.rag_service.get_rag_service", lambda: FakeRAG())

    called = {"indexed": False}

    def fake_add_texts(texts, metadatas=None, ids=None):
        called["indexed"] = True
        return True

    monkeypatch.setattr("backend.src.services.vectorstore_manager.add_texts", fake_add_texts)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(ds._generate_chunks(doc))

    assert called["indexed"] is True
    assert getattr(doc, "has_embeddings", False) is True
    assert isinstance(getattr(doc, "chunks", None), list)
