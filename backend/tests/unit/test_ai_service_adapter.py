import asyncio
from types import SimpleNamespace
from src.services.rag_adapter import AIServiceLLMAdapter


def test_ai_service_adapter_sync():
    class SyncService:
        def generate_response(self, prompt=None):
            return f"sync:{prompt}"

    svc = SyncService()
    adapter = AIServiceLLMAdapter(svc)
    out = adapter.generate("hello")
    assert out == "sync:hello"


def test_ai_service_adapter_async():
    class AsyncService:
        async def generate_response(self, prompt=None):
            await asyncio.sleep(0)
            return f"async:{prompt}"

    svc = AsyncService()
    adapter = AIServiceLLMAdapter(svc)
    out = adapter.generate("world")
    assert out == "async:world"


def test_ai_service_adapter_fallback():
    # Service without generate_response should be stringified
    svc = SimpleNamespace()
    adapter = AIServiceLLMAdapter(svc)
    out = adapter.generate("x")
    assert isinstance(out, str)
