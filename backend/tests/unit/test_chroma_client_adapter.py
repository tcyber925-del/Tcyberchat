from src.services.rag_adapter import create_vectorstore


class DummyCollection:
    def __init__(self):
        self._data = []

    def add(self, documents=None, metadatas=None, ids=None, **kwargs):
        for d, m, i in zip(documents or [], metadatas or [], ids or [], strict=False):
            self._data.append((d, m, i))

    def get(self, include=None):
        # return shape similar to Chroma.get()
        return {
            "documents": [[d for d, m, i in self._data]],
            "metadatas": [[m for d, m, i in self._data]],
            "ids": [[i for d, m, i in self._data]],
        }

    def count(self):
        return len(self._data)

    def persist(self):
        return True


class DummyClient:
    def __init__(self):
        self._col = DummyCollection()

    def get_or_create_collection(self, name):
        return self._col


def test_create_vectorstore_uses_chroma_client():
    client = DummyClient()
    vs = create_vectorstore(client=client, collection_name="testcol", embedding=None)

    # The adapter should return an object with add_texts/get/count methods
    assert hasattr(vs, "add_texts") or hasattr(vs, "add_documents")

    # Use add_texts and ensure count and get reflect added data
    vs.add_texts(["hello world"], metadatas=[{"document_id": "doc1"}], ids=["doc1"])

    # count() should return 1
    assert vs.count() == 1

    got = vs.get()
    assert "hello world" in got.get("documents", []) or any(
        "hello world" in d for d in got.get("documents", [])
    )
