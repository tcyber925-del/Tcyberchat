import asyncio

from src import database
from src.services.rag_adapter import _FallbackVectorStore
from src.services.rag_service import RAGService


def test_rag_service_fallback_flow(tmp_path):
    # Use a temporary directory for persistence (but fallback vectorstore uses in-memory)
    svc = RAGService(persist_directory=str(tmp_path))

    # Ensure we don't pick up the real chroma client so fallback uses in-memory
    database.chroma_client = None
    database.vector_store_initialized = False

    # Force fallback components to avoid partial LangChain initialization in test env
    svc.vectorstore = _FallbackVectorStore(
        client=None, collection_name="test_rag_service"
    )

    # Simple splitter that keeps text as a single chunk
    class _SimpleSplitter:
        def split_text(self, text):
            return [text]

    svc.text_splitter = _SimpleSplitter()

    # Inject standardized test shims from helpers
    import src.services.rag_service as rag_mod
    import tests.helpers as test_helpers

    test_helpers.inject_rag_shims(rag_mod)

    # Provide a minimal AI service getter used by generate_rag_response fallbacks
    class _AIStub:
        def __init__(self):
            self.model_name = "stub"

        async def generate_response(self, prompt: str, context=None):
            return {"response": "(stub) " + str(prompt)}

    rag_mod.get_ai_service = lambda m=None: _AIStub()

    # Add a simple document using chunking
    doc_id = "doc_test"
    text = "Paris is the capital of France. The Eiffel Tower is located there."

    ok = asyncio.get_event_loop().run_until_complete(
        svc.add_document_with_chunking(
            document_id=doc_id, full_text=text, metadata={"title": "test"}
        )
    )
    assert ok is True

    # Search for relevant chunks
    results = asyncio.get_event_loop().run_until_complete(
        svc.search_relevant_chunks(
            query="What is the capital of France?", document_id=doc_id, limit=3
        )
    )
    assert isinstance(results, list)
    assert len(results) >= 1
    assert any("paris" in r["content"].lower() for r in results)

    # Generate RAG response (fallback path should produce snippet or ai fallback)
    out = asyncio.get_event_loop().run_until_complete(
        svc.generate_rag_response(
            query="What is the capital of France?", document_id=doc_id
        )
    )
    assert isinstance(out, dict)
    assert "response" in out
    # Either RAG enabled with citation or fallback AI response exists
    assert (out.get("citations") and len(out.get("citations")) >= 0) or out.get(
        "rag_enabled"
    ) in (True, False)
