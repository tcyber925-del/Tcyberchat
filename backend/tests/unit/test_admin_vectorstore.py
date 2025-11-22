from fastapi.testclient import TestClient

from backend.main import app


def test_index_all_documents_no_docs(monkeypatch):
    # Simulate no documents
    monkeypatch.setattr("backend.src.services.document_service.list_all_documents_texts", lambda: [])

    client = TestClient(app)
    resp = client.post("/api/admin/vectorstore/index")
    assert resp.status_code == 200
    assert resp.json() == {"indexed": 0, "message": "No documents to index"}


def test_index_all_documents_success(monkeypatch):
    # Return two docs
    docs = [("text1", {"id": "1"}), ("text2", {"id": "2"})]
    # The app imports services under `src.*` module path; patch both to be safe
    import importlib
    for mod_path in ("backend.src.services.document_service", "src.services.document_service"):
        try:
            mod = importlib.import_module(mod_path)
            monkeypatch.setattr(mod, "list_all_documents_texts", lambda: docs)
        except Exception:
            pass

    called = {"add_texts": False}
    def fake_add_texts(texts, metadatas=None, ids=None):
        called["add_texts"] = True
        return True

    # Patch vectorstore_manager under both import paths
    for mod_path in ("backend.src.services.vectorstore_manager", "src.services.vectorstore_manager"):
        try:
            mod = importlib.import_module(mod_path)
            monkeypatch.setattr(mod, "add_texts", fake_add_texts)
        except Exception:
            pass

    client = TestClient(app)
    resp = client.post("/api/admin/vectorstore/index")
    assert resp.status_code == 200
    assert resp.json() == {"indexed": 2}
    assert called["add_texts"]
