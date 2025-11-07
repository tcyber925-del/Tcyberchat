import os
import pytest
from unittest.mock import patch, AsyncMock

# This fixture is essential to reset the state between tests
@pytest.fixture(autouse=True)
def reset_ai_service_cache():
    from backend.src.services import ai_service
    ai_service._ai_service_instance_cache.clear()
    ai_service.AIService._llama_cpp_client = None
    ai_service.AIService._llama_cpp_models = []
    ai_service.AIService._llama_cpp_last_fetch = 0
    yield
    ai_service._ai_service_instance_cache.clear()
    ai_service.AIService._llama_cpp_client = None
    ai_service.AIService._llama_cpp_models = []
    ai_service.AIService._llama_cpp_last_fetch = 0

@pytest.mark.asyncio
async def test_llama_cpp_integration():
    """An integration test for the Llama.cpp server functionality."""
    
    # 1. Define a fake LlamaCppClient that simulates the real one
    class FakeLlamaCppClient:
        async def get_available_models(self):
            return ["fake-model.gguf"]

        async def generate_stream(self, messages, model, **kwargs):
            assert model == "fake-model.gguf"
            assert messages == [{"role": "user", "content": "A test prompt"}]
            for chunk in ["This", " is", " a", " test."]:
                yield chunk

    # 2. Patch the real client with our fake one
    with patch('backend.src.services.ai_service.LlamaCppClient') as mock_llama_client:
        mock_llama_client.return_value = FakeLlamaCppClient()

        from backend.src.services.ai_service import AIService, get_ai_service

        # 3. Test fetching available models
        service_instance = AIService() # Use a direct instance to test get_available_models
        models = await service_instance.get_available_models()
        assert any(m['name'] == "fake-model.gguf" for m in models)

        # 4. Test getting the service and streaming a response
        # Use the singleton factory, which should now find our fake model
        service = await get_ai_service(model_name="fake-model.gguf")
        
        # Ensure the correct provider and model are set
        provider = await service._get_provider_for_model("fake-model.gguf")
        assert provider == "llama.cpp"
        assert service.model_name == "fake-model.gguf"

        # Generate and verify the streaming response
        result = [chunk async for chunk in service.generate_streaming_response("A test prompt")]
        assert result == ["This", " is", " a", " test."]