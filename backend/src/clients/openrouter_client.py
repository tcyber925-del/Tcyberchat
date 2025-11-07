import os
from typing import Optional, AsyncGenerator
import asyncio

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - package may not be installed
    OpenAI = None


class OpenRouterClient:
    """Minimal wrapper for OpenRouter using the OpenAI-compatible SDK.

    Example usage:
        client = OpenRouterClient()
        client.chat("Hello")
    """

    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://openrouter.ai/api/v1", model: str = "openai/gpt-oss-20b:free"):
        self.model = model
        self.base_url = base_url
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")

        if not self.api_key or OpenAI is None:
            self.client = None
        else:
            # The OpenAI SDK used by OpenRouter accepts base_url and api_key params
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def chat(self, prompt: str) -> str:
        if self.client is None:
            raise RuntimeError("OpenAI SDK not installed or OPENROUTER_API_KEY not set")

        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
        )

        # SDK returns choices -> message -> content for chat responses
        try:
            return completion.choices[0].message.content
        except Exception:
            return str(completion)

    async def chat_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        if self.client is None:
            raise RuntimeError("OpenAI SDK not installed or OPENROUTER_API_KEY not set")

        def _sync_stream_iterator():
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                stream=True
            )
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        loop = asyncio.get_event_loop()
        for content_chunk in await loop.run_in_executor(None, _sync_stream_iterator):
            yield content_chunk
