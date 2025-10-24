import pytest

from src.services.rag_adapter import create_memory, create_splitter, create_embeddings, create_vectorstore, AIServiceLLMAdapter


class DummyAI:
    def generate_response(self, prompt: str):
        return f"echo:{prompt}"


def test_adapter_memory_and_splitter_basic():
    mem = create_memory(3)
    mem.add_user("hello")
    mem.add_ai("hi")
    ctx = mem.get_context()
    assert isinstance(ctx, list)

    splitter = create_splitter(50, 5)
    parts = splitter.split("a short text")
    assert isinstance(parts, list)


def test_embeddings_and_vectorstore_stubs():
    emb = create_embeddings()
    # In test env, langchain likely not present; emb should be None or an object
    assert emb is None or hasattr(emb, 'embed')

    vs = create_vectorstore(client=None)
    assert vs is None or hasattr(vs, 'get')


def test_ai_service_llm_adapter():
    ai = DummyAI()
    adapter = AIServiceLLMAdapter(ai)
    out = adapter.generate("ping")
    assert "echo:ping" in out
