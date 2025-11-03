import os
from typing import Optional, AsyncGenerator
import logging

try:
    import google.generativeai as genai
except Exception:  # pragma: no cover - import may not be installed in CI
    genai = None

logger = logging.getLogger(__name__)

class GeminiClient:
    """Minimal wrapper around Google Gemini (google-genai).

    Usage:
        client = GeminiClient()
        client.generate("Hello")

    The library `google-genai` is optional — this wrapper will raise a clear
    error if it's not installed.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "models/gemini-2.5-flash"):
        self.model_name = model
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")

        if genai is None:
            self.model_client = None
        else:
            if self.api_key:
                genai.configure(api_key=self.api_key)
            else:
                raise RuntimeError("GEMINI_API_KEY not set")
            self.model_client = genai.GenerativeModel(self.model_name)

    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text for the given prompt.

        Returns the textual content (response.text) when available.
        """
        if self.model_client is None:
            raise RuntimeError("google-genai is not installed or client not configured (set GEMINI_API_KEY)")

        try:
            response = self.model_client.generate_content(contents=prompt, **kwargs)
            if hasattr(response, "text"):
                return response.text
            return str(response)
        except Exception as e:
            logger.error(f"Gemini generate failed: {e}", exc_info=True)
            raise

    async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """Generate streaming text for the given prompt.

        Yields textual content chunks.
        """
        if self.model_client is None:
            raise RuntimeError("google-genai is not installed or client not configured (set GEMINI_API_KEY)")

        try:
            response = self.model_client.generate_content(contents=prompt, stream=True, **kwargs)
            for chunk in response:
                if hasattr(chunk, "text"):
                    yield chunk.text
        except Exception as e:
            logger.error(f"Gemini generate_stream failed: {e}", exc_info=True)
            raise

    @staticmethod
    def list_models() -> list[str]:
        if genai is None:
            raise RuntimeError("google-genai is not installed")
        models = genai.list_models()
        return [m.name for m in models if "generateContent" in m.supported_generation_methods]
