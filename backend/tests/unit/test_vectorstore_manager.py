from backend.src.services import vectorstore_manager as vsm


def test_get_vectorstore_returns_none_when_adapter_missing(monkeypatch):
    # Simulate adapter failure
    monkeypatch.setattr("backend.src.services.rag_adapter.create_vectorstore", lambda *a, **k: None)
    vs = vsm.get_vectorstore()
    assert vs is None


def test_add_texts_calls_add_texts(monkeypatch):
    called = {"add_texts": False, "persist": False}

    class DummyVS:
        def add_texts(self, texts, metadatas=None, ids=None):
            called["add_texts"] = True

        def persist(self):
            called["persist"] = True

    monkeypatch.setattr("backend.src.services.rag_adapter.create_vectorstore", lambda *a, **k: DummyVS())

    ok = vsm.add_texts(["a", "b"], metadatas=[{"x": 1}, {"x": 2}], ids=["i1", "i2"])
    assert ok is True
    assert called["add_texts"]
    assert called["persist"]
