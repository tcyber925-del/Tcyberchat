from src import database
from src.services.rag_adapter import _FallbackVectorStore


def test_fallback_vectorstore_basic_operations():
    # Ensure any global chroma client is disabled so fallback uses in-memory storage
    database.chroma_client = None
    database.vector_store_initialized = False

    # Prefer the explicit fallback vectorstore for tests to avoid depending on
    # environment-installed LangChain/Chroma embedding configuration.
    vs = _FallbackVectorStore(
        client=None, collection_name="test_vec", embedding_function=None
    )
    assert vs is not None

    # Add texts
    texts = ["Paris is the capital of France.", "Berlin is the capital of Germany."]
    metas = [{"document_id": "d_paris"}, {"document_id": "d_berlin"}]
    ids = ["t1", "t2"]

    vs.add_texts(texts, metadatas=metas, ids=ids)

    got = vs.get()
    assert isinstance(got, dict)
    assert len(got.get("documents", [])) >= 2

    # Count should reflect in-memory storage
    assert vs.count() >= 2

    # Search for 'capital' should return relevant docs
    results = vs.get_relevant_documents("capital", k=2)
    assert isinstance(results, list)
    assert any("capital" in getattr(r, "page_content", "").lower() for r in results)
