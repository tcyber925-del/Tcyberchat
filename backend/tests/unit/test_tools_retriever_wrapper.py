from backend.src.agents.tools import create_retriever_tool_from_vectorstore


class DummyVectorStore:
    def __init__(self, docs):
        self._docs = docs

    def similarity_search(self, query, k=5):
        return self._docs[:k]


def test_create_retriever_tool_from_vectorstore():
    docs = [
        {"page_content": "alpha", "metadata": {"title": "A", "source": "s1"}},
        {"page_content": "beta", "metadata": {"title": "B", "source": "s2"}},
    ]

    vs = DummyVectorStore(docs)
    tool = create_retriever_tool_from_vectorstore(vs, top_k=2)

    res = tool("q")
    assert isinstance(res, list)
    assert res[0]["page_content"] == "alpha"
    assert res[0]["metadata"]["title"] == "A"
