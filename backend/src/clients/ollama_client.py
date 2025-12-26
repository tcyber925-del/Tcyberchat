"""
OllamaClient for local Ollama server interactions.
"""

import json
import logging
import os
from collections.abc import AsyncGenerator
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class OllamaClient:
    """
    Client for interacting with a local Ollama server.
    """

    def __init__(self, base_url: str | None = None):
        """
        Initializes the OllamaClient.

        Args:
            base_url (str, optional): The base URL of the Ollama server.
                                      Defaults to OLLAMA_BASE_URL env var or http://localhost:11501.
        """
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11501")
        # Ensure no trailing slash
        self.base_url = self.base_url.rstrip("/")
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=httpx.Timeout(30.0, connect=5.0))
        logger.info(f"Ollama client initialized for server at {self.base_url}")

    async def get_available_models(self) -> list[str]:
        """
        Get the list of available models from the Ollama server.

        Returns:
            List[str]: A list of model names.
        """
        try:
            response = await self.client.get("/api/tags")
            response.raise_for_status()
            data = response.json()
            # Format: {"models": [{"name": "llama2", ...}, ...]}
            return [model["name"] for model in data.get("models", [])]
        except (httpx.RequestError, json.JSONDecodeError) as e:
            logger.error(
                f"Failed to get available models from Ollama server: {e}",
                exc_info=True,
            )
            return []

    async def generate_stream(
        self, messages: list[dict[str, str]], model: str, **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Generate a streaming response from the Ollama server.

        Args:
            messages (List[Dict[str, str]]): A list of message dictionaries.
            model (str): The model to use.
            **kwargs: Additional arguments.

        Yields:
            str: Chunks of the generated text.
        """
        # Convert messages to Ollama format if needed, or just pass prompt if using /api/generate
        # But /api/chat is better for chat history
        request_body = {
            "model": model,
            "messages": messages,
            "stream": True,
            **kwargs,
        }

        try:
            async with self.client.stream(
                "POST", "/api/chat", json=request_body
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                        if "message" in chunk and "content" in chunk["message"]:
                            yield chunk["message"]["content"]
                        if chunk.get("done", False):
                            break
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to decode Ollama data chunk: {line}")
                        continue
        except httpx.RequestError as e:
            logger.error(f"Ollama streaming generation failed: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(
                f"An unexpected error occurred during Ollama streaming: {e}", exc_info=True
            )
            raise

    async def generate(
        self, messages: list[dict[str, str]], model: str, **kwargs
    ) -> str:
        """
        Generate a non-streaming response from the Ollama server.

        Args:
            messages (List[Dict[str, str]]): A list of message dictionaries.
            model (str): The model to use.
            **kwargs: Additional arguments.

        Returns:
            str: The generated text.
        """
        request_body = {
            "model": model,
            "messages": messages,
            "stream": False,
            **kwargs,
        }

        try:
            response = await self.client.post("/api/chat", json=request_body)
            response.raise_for_status()
            data = response.json()
            return data.get("message", {}).get("content", "")
        except (httpx.RequestError, json.JSONDecodeError, KeyError) as e:
            logger.error(f"Ollama non-streaming generation failed: {e}", exc_info=True)
            raise
