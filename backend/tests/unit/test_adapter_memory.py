from src.services.rag_adapter import create_memory


def test_adapter_memory_add_and_context():
    mem = create_memory(k=3)
    assert mem is not None

    # Add messages
    mem.add_user("Hello there")
    mem.add_ai("Hi, how can I help?")

    ctx = mem.get_context()
    assert isinstance(ctx, list)
    assert len(ctx) >= 2
    assert ctx[0]["role"] == "user"
    assert "hello" in ctx[0]["content"].lower()
    assert ctx[1]["role"] == "assistant"
