"""
AIService for LLM interactions and general AI processing
"""

from typing import Dict, List, Optional, Any, AsyncGenerator
import asyncio
import time
import logging
import os
from dotenv import load_dotenv

from backend.src.clients.gemini_client import GeminiClient
from backend.src.clients.openrouter_client import OpenRouterClient
from backend.src.clients.llama_cpp_client import LlamaCppClient

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class AIService:
    """Service for AI model interactions and processing with fallback chain"""

    _llama_cpp_client: Optional[LlamaCppClient] = None
    _llama_cpp_models: List[str] = []
    _llama_cpp_last_fetch: float = 0

    def __init__(self, model_name: str = "default"):
        self.model_name = model_name
        self.gemini_client: Optional[GeminiClient] = None
        self.openrouter_client: Optional[OpenRouterClient] = None
        
        # Initialize clients based on available API keys
        gemini_key = os.getenv('GEMINI_API_KEY')
        if gemini_key:
            try:
                self.gemini_client = GeminiClient(api_key=gemini_key, model="models/gemini-2.5-flash")
                logger.info(f"Google Gemini client initialized with model: {self.gemini_client.model_name}")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}", exc_info=True)

        openrouter_key = os.getenv('OPENROUTER_API_KEY')
        if openrouter_key:
            try:
                self.openrouter_client = OpenRouterClient(api_key=openrouter_key, model="openai/gpt-oss-20b:free")
                logger.info(f"OpenRouter client initialized with model: {self.openrouter_client.model}")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenRouter client: {e}")

        # Initialize Llama.cpp client
        llama_server_url = os.getenv("LLAMA_CPP_SERVER_URL", "http://localhost:8080")
        if not AIService._llama_cpp_client:
            AIService._llama_cpp_client = LlamaCppClient(base_url=llama_server_url)

    async def _get_provider_for_model(self, model_name: str) -> str:
        """Determine which AI provider to use for a given model name."""
        await self._fetch_llama_cpp_models_if_needed()

        # Handle provider prefixes (e.g., "google: models/gemini-2.5-flash", "openrouter: openai/gpt-3.5-turbo")
        # Only treat as provider prefix if the part before colon is a known provider name (not a model path)
        if ":" in model_name:
            parts = model_name.split(":", 1)
            provider_prefix = parts[0].lower().strip()
            # Only treat as provider prefix if it's a simple provider name (not a path like "openai/gpt-oss-20b")
            if "/" not in provider_prefix:
                if provider_prefix in ("google", "gemini"):
                    return "google"
                elif provider_prefix in ("openrouter", "openai"):
                    return "openrouter"
                elif provider_prefix == "llama.cpp":
                    return "llama.cpp"
                # If prefix doesn't match known providers, continue with normal logic
                # Use the part after the colon as the model name
                model_name = parts[1].strip()
            # If there's a "/" in the prefix, it's likely a model path (e.g., "openai/gpt-oss-20b:free")
            # Continue with normal logic using the full model_name

        # Normalize model name by removing version/tag if present
        base_model_name = model_name.split(":")[0]

        # Provider-specific checks first
        if model_name.startswith(("gemini", "models/")):
            return "google"

        if "/" in model_name or model_name.startswith(("openai/", "google/", "mistralai/", "meta-llama/")):
            return "openrouter"

        # Handle llama.cpp models, which may have a prefix
        if model_name.startswith("llama.cpp:"):
            lookup_name = model_name.split(":", 1)[1]
            # Check for exact match or if a loaded model starts with the requested name
            if lookup_name in self._llama_cpp_models:
                return "llama.cpp"
            for m in self._llama_cpp_models:
                if m.startswith(lookup_name):
                    return "llama.cpp"

        if base_model_name in self._llama_cpp_models:
            return "llama.cpp"

        # Fallback for llama.cpp models if server is down or model not listed
        if "llama" in model_name.lower():
            return "llama.cpp"

        return "unknown"

    async def generate_streaming_response(self, prompt: str, context: Optional[List[str]] = None,
                                        max_tokens: int = 1024) -> AsyncGenerator[str, None]:
        """
        Generate streaming AI response with optional context
        Yields response chunks as they become available
        """
        provider = await self._get_provider_for_model(self.model_name)
        
        messages = []
        if context:
            messages.append({"role": "system", "content": "Context:\n" + "\n".join(context)})
        messages.append({"role": "user", "content": prompt})

        try:
            if provider == "llama.cpp" and self._llama_cpp_client:
                logger.info(f"Attempting streaming response with Llama.cpp using model: {self.model_name}...")
                async for chunk in self._llama_cpp_client.generate_stream(messages, model=self.model_name, max_tokens=max_tokens):
                    yield chunk
            elif provider == "google" and self.gemini_client:
                logger.info(f"Attempting streaming response with Google Gemini using model: {self.model_name}...")
                full_prompt = self._construct_full_prompt(prompt, context)
                # Use the selected model, not the hardcoded one
                # Extract model name (remove provider prefix if present, e.g., "google: models/gemini-2.5-flash" -> "models/gemini-2.5-flash")
                if ":" in self.model_name:
                    parts = self.model_name.split(":", 1)
                    # Check if the first part is a provider prefix
                    provider_prefix = parts[0].lower().strip()
                    if provider_prefix in ("google", "gemini"):
                        actual_model = parts[1].strip()
                    else:
                        actual_model = self.model_name
                else:
                    actual_model = self.model_name
                # Create a new client with the correct model if needed
                if self.gemini_client.model_name != actual_model:
                    try:
                        from ..clients.gemini_client import GeminiClient
                        gemini_key = os.getenv('GEMINI_API_KEY')
                        if gemini_key:
                            self.gemini_client = GeminiClient(api_key=gemini_key, model=actual_model)
                    except Exception as e:
                        logger.warning(f"Failed to update Gemini client model: {e}")
                async for chunk in self.gemini_client.generate_stream(full_prompt):
                    yield chunk
            elif provider == "openrouter" and self.openrouter_client:
                logger.info(f"Attempting streaming response with OpenRouter using model: {self.model_name}...")
                full_prompt = self._construct_full_prompt(prompt, context)
                # Use the selected model, not the hardcoded one
                # Extract model name (remove provider prefix if present, e.g., "openrouter: openai/gpt-3.5-turbo" -> "openai/gpt-3.5-turbo")
                if ":" in self.model_name:
                    parts = self.model_name.split(":", 1)
                    # Check if the first part is a provider prefix
                    provider_prefix = parts[0].lower().strip()
                    if provider_prefix in ("openrouter", "openai"):
                        actual_model = parts[1].strip()
                    else:
                        actual_model = self.model_name
                else:
                    actual_model = self.model_name
                # Create a new client with the correct model if needed
                if self.openrouter_client.model != actual_model:
                    try:
                        from ..clients.openrouter_client import OpenRouterClient
                        openrouter_key = os.getenv('OPENROUTER_API_KEY')
                        if openrouter_key:
                            self.openrouter_client = OpenRouterClient(api_key=openrouter_key, model=actual_model)
                    except Exception as e:
                        logger.warning(f"Failed to update OpenRouter client model: {e}")
                async for chunk in self.openrouter_client.chat_stream(full_prompt):
                    yield chunk
            else:
                logger.error(f"No suitable provider found for model: {self.model_name}")
                yield "I'm sorry, I don't have an answer right now."

        except Exception as e:
            logger.error(f"Streaming response failed for {self.model_name}: {str(e)}")
            yield f"I apologize, but there was an error generating the response: {str(e)}"

    async def generate_response(self, prompt: str, context: Optional[List[str]] = None,
                               max_tokens: int = 1024) -> Dict[str, Any]:
        """
        Generate AI response with optional context
        Returns dict with response text and metadata
        """
        start_time = time.time()
        provider = await self._get_provider_for_model(self.model_name)
        model_used = self.model_name
        error_message = None
        response_text = ""

        messages = []
        if context:
            messages.append({"role": "system", "content": "Context:\n" + "\n".join(context)})
        messages.append({"role": "user", "content": prompt})

        try:
            if provider == "llama.cpp" and self._llama_cpp_client:
                logger.info(f"Attempting non-streaming response with Llama.cpp using model: {self.model_name}...")
                response_text = await self._llama_cpp_client.generate(messages, model=self.model_name, max_tokens=max_tokens)
            elif provider == "google" and self.gemini_client:
                logger.info(f"Attempting non-streaming response with Google Gemini using model: {self.model_name}...")
                full_prompt = self._construct_full_prompt(prompt, context)
                # Use the selected model, not the hardcoded one
                # Extract model name (remove provider prefix if present)
                if ":" in self.model_name:
                    parts = self.model_name.split(":", 1)
                    provider_prefix = parts[0].lower().strip()
                    if provider_prefix in ("google", "gemini"):
                        actual_model = parts[1].strip()
                    else:
                        actual_model = self.model_name
                else:
                    actual_model = self.model_name
                if self.gemini_client.model_name != actual_model:
                    try:
                        from ..clients.gemini_client import GeminiClient
                        gemini_key = os.getenv('GEMINI_API_KEY')
                        if gemini_key:
                            self.gemini_client = GeminiClient(api_key=gemini_key, model=actual_model)
                    except Exception as e:
                        logger.warning(f"Failed to update Gemini client model: {e}")
                if self.gemini_client:
                    response_text = await asyncio.get_event_loop().run_in_executor(None, lambda: self.gemini_client.generate(full_prompt))
            elif provider == "openrouter" and self.openrouter_client:
                logger.info(f"Attempting non-streaming response with OpenRouter using model: {self.model_name}...")
                full_prompt = self._construct_full_prompt(prompt, context)
                # Use the selected model, not the hardcoded one
                # Extract model name (remove provider prefix if present)
                if ":" in self.model_name:
                    parts = self.model_name.split(":", 1)
                    provider_prefix = parts[0].lower().strip()
                    if provider_prefix in ("openrouter", "openai"):
                        actual_model = parts[1].strip()
                    else:
                        actual_model = self.model_name
                else:
                    actual_model = self.model_name
                if self.openrouter_client.model != actual_model:
                    try:
                        from ..clients.openrouter_client import OpenRouterClient
                        openrouter_key = os.getenv('OPENROUTER_API_KEY')
                        if openrouter_key:
                            self.openrouter_client = OpenRouterClient(api_key=openrouter_key, model=actual_model)
                    except Exception as e:
                        logger.warning(f"Failed to update OpenRouter client model: {e}")
                if self.openrouter_client:
                    response_text = await asyncio.get_event_loop().run_in_executor(None, lambda: self.openrouter_client.chat(full_prompt))
            else:
                error_message = f"No suitable AI provider found for model: {self.model_name}"
                response_text = "I apologize, but there was an error generating the response: No suitable AI provider available."

        except Exception as e:
            logger.error(f"AI response generation failed for {self.model_name}: {str(e)}")
            error_message = str(e)
            response_text = f"I apologize, but there was an error generating the response: {error_message}"

        return {
            "response": response_text,
            "model": model_used,
            "processing_time": time.time() - start_time,
            "error": error_message,
            "provider": provider
        }

    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Get a list of available models from all configured providers."""
        available_models = []

        if self.openrouter_client:
            # This is a simplification. In a real scenario, you might fetch models from OpenRouter API
            available_models.append({"name": "openai/gpt-oss-20b:free", "provider": "openrouter"})
            available_models.append({"name": "google/gemini-flash-1.5", "provider": "openrouter"})


        if self.gemini_client:
            available_models.append({"name": "models/gemini-2.5-flash", "provider": "google"})

        await self._fetch_llama_cpp_models_if_needed()
        for model_name in self._llama_cpp_models:
            available_models.append({"name": model_name, "provider": "llama.cpp"})

        if not available_models:
            return [{"name": "mock-model", "provider": "none"}]

        return available_models

    async def check_model_availability(self, model_name: str) -> bool:
        """Check if a specific model is available from any configured provider"""
        models = await self.get_available_models()
        return any(model['name'] == model_name for model in models)

    @classmethod
    async def _fetch_llama_cpp_models_if_needed(cls):
        """Fetch models from the Llama.cpp server if they haven't been fetched recently."""
        current_time = time.time()
        # Cache for 5 minutes
        if current_time - cls._llama_cpp_last_fetch > 300:
            if cls._llama_cpp_client:
                try:
                    logger.info("Fetching available models from Llama.cpp server...")
                    cls._llama_cpp_models = await cls._llama_cpp_client.get_available_models()
                    cls._llama_cpp_last_fetch = current_time
                    logger.info(f"Found Llama.cpp models: {cls._llama_cpp_models}")
                except Exception as e:
                    logger.warning(f"Could not retrieve Llama.cpp models: {e}")
                    cls._llama_cpp_models = []
            else:
                cls._llama_cpp_models = []
    
    def _construct_full_prompt(self, prompt: str, context: Optional[List[str]] = None) -> str:
        if context:
            context_str = "\n".join(context)
            return f"Context:\n{context_str}\n\nQuestion: {prompt}"
        return prompt

# Global instance management
_ai_service_instance_cache: Dict[str, AIService] = {}

async def get_ai_service(model_name: Optional[str] = None) -> AIService:
    """Get singleton AIService instance with optional model override"""
    
    if not model_name:
        # If no model is specified, try to find a default
        if os.getenv('OPENROUTER_API_KEY'):
            model_name = "openai/gpt-3.5-turbo"
        elif os.getenv('GEMINI_API_KEY'):
            model_name = "models/gemini-1.5-flash"
        else:
            # Fallback to the first available llama.cpp model
            llama_server_url = os.getenv("LLAMA_CPP_SERVER_URL", "http://localhost:8080")
            if not AIService._llama_cpp_client:
                AIService._llama_cpp_client = LlamaCppClient(base_url=llama_server_url)
            await AIService._fetch_llama_cpp_models_if_needed()
            if AIService._llama_cpp_models:
                model_name = AIService._llama_cpp_models[0]
            else:
                model_name = "mock-model"

    if model_name not in _ai_service_instance_cache:
        if model_name:
            _ai_service_instance_cache[model_name] = AIService(model_name)
    
    if model_name:
        return _ai_service_instance_cache[model_name]
    return _ai_service_instance_cache["mock-model"]