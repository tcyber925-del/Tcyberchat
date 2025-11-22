import importlib
import types

from src.services.rag_adapter import create_embeddings


class DummyHuggingFaceEmbeddings:
    def __init__(self, model_name=None):
        self.model_name = model_name

    def embed_documents(self, texts):
        return [len(t) for t in texts]


def test_create_embeddings_prefers_langchain_huggingface(monkeypatch):
    # Create a fake module that provides HuggingFaceEmbeddings
    fake_module = types.SimpleNamespace(
        HuggingFaceEmbeddings=DummyHuggingFaceEmbeddings
    )

    # Monkeypatch importlib to return our fake module when langchain_huggingface is requested
    real_import = importlib.import_module

    def fake_import(name, package=None):
        if name == "langchain_huggingface":
            return fake_module
        return real_import(name, package=package)

    monkeypatch.setattr(importlib, "import_module", fake_import)

    emb = create_embeddings(model_name="all-MiniLM-L6-v2")
    # The adapter returns an object with .embed method; test that it yields expected behavior
    assert emb is not None
    out = emb.embed(["a", "ab", "abc"])
    assert isinstance(out, list) or isinstance(out, (int, float))
    # If list returned, check lengths from DummyHuggingFaceEmbeddings
    if isinstance(out, list):
        assert out == [1, 2, 3]
