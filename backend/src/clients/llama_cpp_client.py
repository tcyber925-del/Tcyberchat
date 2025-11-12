"""
LlamaCppClient for llama.cpp server interactions.
"""

import json
import logging
import os
from collections.abc import AsyncGenerator

import httpx

logger = logging.getLogger(__name__)


class LlamaCppClient:
    """
    Client for interacting with a remote llama.cpp server.
    """

    def __init__(self, base_url: str = "http://localhost:8080"):
        """
        Initializes the LlamaCppClient.

        Args:
            base_url (str): The base URL of the llama.cpp server.
        """
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=None)
        logger.info(f"Llama.cpp client initialized for server at {self.base_url}")

    async def get_available_models(self) -> list[str]:
        """
        Retrieves the list of available models from the server.
        """
        try:
            response = await self.client.get("/v1/models")
            response.raise_for_status()
            models_data = response.json()
            # The expected format is a dictionary with a 'data' key containing a list of models
            return [
                os.path.basename(model["id"]) for model in models_data.get("data", [])
            ]
        except (httpx.RequestError, json.JSONDecodeError) as e:
            logger.error(
                f"Failed to get available models from llama.cpp server: {e}",
                exc_info=True,
            )
            return []

    async def generate_stream(
        self, messages: list[dict[str, str]], model: str | None = None, **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Generate a streaming response from the Llama.cpp server.

        Args:
            messages (List[Dict[str, str]]): A list of message dictionaries, e.g., [{"role": "user", "content": "..."}].
            model (Optional[str]): The model to use for the completion. If not provided, the server's default is used.
            **kwargs: Additional arguments for the chat completion API.

        Yields:
            str: Chunks of the generated text.
        """
        request_body = {
            "messages": messages,
            "stream": True,
            **kwargs,
        }
        if model:
            request_body["model"] = model

        try:
            async with self.client.stream(
                "POST", "/v1/chat/completions", json=request_body
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        data_str = line[len("data: ") :].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                            if "choices" in chunk and chunk["choices"]:
                                content = (
                                    chunk["choices"][0].get("delta", {}).get("content")
                                )
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            logger.warning(
                                f"Failed to decode SSE data chunk: {data_str}"
                            )
                            continue
        except httpx.RequestError as e:
            logger.error(f"Llama.cpp streaming generation failed: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(
                f"An unexpected error occurred during streaming: {e}", exc_info=True
            )
            raise

    async def generate(
        self, messages: list[dict[str, str]], model: str | None = None, **kwargs
    ) -> str:
        """
        Generate a non-streaming response from the Llama.cpp server.

        Args:
            messages (List[Dict[str, str]]): A list of message dictionaries.
            model (Optional[str]): The model to use for the completion.
            **kwargs: Additional arguments for the chat completion API.

        Returns:
            str: The generated text.
        """
        request_body = {
            "messages": messages,
            "stream": False,
            **kwargs,
        }
        if model:
            request_body["model"] = model

        try:
            response = await self.client.post("/v1/chat/completions", json=request_body)
            response.raise_for_status()
            completion = response.json()
            return completion["choices"][0]["message"]["content"]
        except (httpx.RequestError, json.JSONDecodeError, KeyError) as e:
            logger.error(
                f"Llama.cpp non-streaming generation failed: {e}", exc_info=True
            )
            raise
