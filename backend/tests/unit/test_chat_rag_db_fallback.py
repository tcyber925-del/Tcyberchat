import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

from main import app
from src.database import SessionLocal, Base, engine
from src.models.document import Document


@pytest.fixture(autouse=True)
def setup_db():
    # Create tables for the test database
    Base.metadata.create_all(bind=engine)
    yield
    # Drop tables after test
    Base.metadata.drop_all(bind=engine)


def test_document_id_db_fallback_returns_snippet(monkeypatch):
    # Insert a document containing the word 'Paris' which the chat endpoint
    # looks for as a quick DB-backed snippet fallback
    session = SessionLocal()
    doc = Document(filename="test.txt", path="/tmp/test.txt", size=123, mime_type="text/plain", content="The capital of France is Paris. It is beautiful.")
    session.add(doc)
    session.commit()
    session.refresh(doc)

    client = TestClient(app)

    payload = {
        "message": "What is the capital of France?",
        "documentId": str(doc.id)
    }

    response = client.post("/api/chat/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "Paris" in data["response"] or "paris" in data["response"].lower()
    assert data.get("citations") and isinstance(data.get("citations"), list)


def test_no_document_rag_global_search(monkeypatch):
    # Mock the RAG service to return a known response when called without documentId
    class MockRAG:
        async def generate_rag_response(self, query, document_id=None, model_name=None):
            return {"response": "This is an answer from the mocked RAG.", "citations": [{"docId": "mockdoc", "snippet": "mock snippet"}]}

    monkeypatch.setattr("src.api.chat.get_rag_service", lambda: MockRAG())

    client = TestClient(app)
    payload = {"message": "Tell me something from uploaded docs."}
    response = client.post("/api/chat/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["response"] == "This is an answer from the mocked RAG."
    assert data.get("citations") and data["citations"][0]["docId"] == "mockdoc"
