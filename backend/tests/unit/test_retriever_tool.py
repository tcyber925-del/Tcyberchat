from backend.src.agents.retriever_tool import create_retriever_tool


class DummyVectorStore:
    def __init__(self, docs):
        self._docs = docs

    def similarity_search(self, query, k=5):
        # ignore query for simplicity
        return self._docs[:k]


def test_retriever_tool_with_dummy_vectorstore():
    docs = [
        {"page_content": "doc1 text", "metadata": {"title": "Doc1", "source": "s1"}},
        {"page_content": "doc2 text", "metadata": {"title": "Doc2", "source": "s2"}},
    ]

    vs = DummyVectorStore(docs)
    tool = create_retriever_tool(vectorstore=vs, top_k=2)

    res = tool("some query")
    assert isinstance(res, list)
    assert len(res) == 2
    assert res[0]["title"] == "Doc1"
    assert "doc1 text" in res[0]["text"]
