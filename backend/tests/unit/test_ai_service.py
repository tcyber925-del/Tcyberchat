import os
import pytest
from unittest.mock import patch, MagicMock

# Mock the cloud clients before they are imported by the service
@pytest.fixture(autouse=True)
def mock_clients():
    with patch('backend.src.clients.gemini_client.GeminiClient') as mock_gemini, \
         patch('backend.src.clients.openrouter_client.OpenRouterClient') as mock_openrouter, \
         patch('ollama.Client') as mock_ollama:
        yield mock_gemini, mock_openrouter, mock_ollama

# Since get_ai_service is a singleton, we need to clear its instance between tests
@pytest.fixture(autouse=True)
def reset_ai_service_singleton():
    from backend.src.services import ai_service
    ai_service._ai_service_instance = None
    yield
    ai_service._ai_service_instance = None


def test_get_ai_service_prioritizes_openrouter():
    """Tests that OpenRouter is prioritized when its API key is set."""
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test_key"}):
        from backend.src.services.ai_service import get_ai_service
        service = get_ai_service()
        assert service.model_name == "google/gemini-flash-1.5"
        assert service.openrouter_client is not None
        assert service.gemini_client is None # Gemini key is not set

def test_get_ai_service_falls_back_to_gemini():
    """Tests that Gemini is used when only its API key is set."""
    with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key", "OPENROUTER_API_KEY": ""}):
        from backend.src.services.ai_service import get_ai_service
        service = get_ai_service()
        assert service.model_name == "gemini-1.5-flash"
        assert service.gemini_client is not None
        assert service.openrouter_client is None

def test_get_ai_service_falls_back_to_ollama():
    """Tests that Ollama is used when no cloud API keys are set."""
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "", "GEMINI_API_KEY": ""}):
        from backend.src.services.ai_service import get_ai_service
        # We need to mock OLLAMA_AVAILABLE to be True for this test
        with patch('backend.src.services.ai_service.OLLAMA_AVAILABLE', True):
            service = get_ai_service()
            assert service.model_name == "llama3.2:latest"
            assert service.client is not None
            assert service.gemini_client is None
            assert service.openrouter_client is None

@pytest.mark.asyncio
async def test_streaming_response_with_openrouter():
    """Tests that generate_streaming_response calls the correct client method."""
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test_key"}):
        from backend.src.services.ai_service import get_ai_service
        service = get_ai_service()

        # Configure the mock OpenRouter client to return a stream
        mock_stream_content = ["Hello", ", ", "world!"]
        async def mock_stream_generator(prompt):
            for item in mock_stream_content:
                yield item
        
        service.openrouter_client.chat_stream = mock_stream_generator

        # Collect the streaming response
        result = [chunk async for chunk in service.generate_streaming_response("test prompt")]

        assert result == mock_stream_content
