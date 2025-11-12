import logging
import os
from collections.abc import AsyncGenerator

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

    def __init__(
        self, api_key: str | None = None, model: str = "models/gemini-2.0-flash-exp"
    ):
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

    def generate(self, prompt: str, enable_grounding: bool = False, **kwargs) -> str:
        """Generate text for the given prompt with optional Google Search grounding.

        Args:
            prompt: The text prompt to generate from
            enable_grounding: If True and using Gemini 2.0, enables Google Search grounding
            **kwargs: Additional parameters passed to generate_content

        Returns:
            The generated text response
        """
        if self.model_client is None:
            raise RuntimeError(
                "google-genai is not installed or client not configured (set GEMINI_API_KEY)"
            )

        try:
            # Enable Google Search grounding for Gemini 2.0 models
            if enable_grounding and "gemini-2.0" in self.model_name:
                logger.info(f"Enabling Google Search grounding for {self.model_name}")
                kwargs["tools"] = "google_search_retrieval"

            response = self.model_client.generate_content(contents=prompt, **kwargs)
            if hasattr(response, "text"):
                return response.text
            return str(response)
        except Exception as e:
            logger.error(f"Gemini generate failed: {e}", exc_info=True)
            raise

    async def generate_stream(
        self, prompt: str, enable_grounding: bool = False, **kwargs
    ) -> AsyncGenerator[str, None]:
        """Generate streaming text for the given prompt with optional Google Search grounding.

        Args:
            prompt: The text prompt to generate from
            enable_grounding: If True and using Gemini 2.0, enables Google Search grounding
            **kwargs: Additional parameters passed to generate_content

        Yields:
            Text chunks from the streaming response
        """
        if self.model_client is None:
            raise RuntimeError(
                "google-genai is not installed or client not configured (set GEMINI_API_KEY)"
            )

        try:
            # Enable Google Search grounding for Gemini 2.0 models
            if enable_grounding and "gemini-2.0" in self.model_name:
                logger.info(
                    f"Enabling Google Search grounding for streaming with {self.model_name}"
                )
                kwargs["tools"] = "google_search_retrieval"

            response = self.model_client.generate_content(
                contents=prompt, stream=True, **kwargs
            )
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
        return [
            m.name
            for m in models
            if "generateContent" in m.supported_generation_methods
        ]
