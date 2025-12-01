"""
Groq Client for ultrafast LLM inference
Supports standard models and reasoning models for complex problem solving
"""
import os
import logging
from typing import AsyncGenerator, Optional

logger = logging.getLogger(__name__)

class GroqClient:
    """Client for Groq API with support for reasoning models"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.3-70b-versatile"):
        """
        Initialize Groq client
        
        Args:
            api_key: Groq API key (defaults to GROQ_API_KEY env var)
            model: Model name (default: llama-3.3-70b-versatile)
                  Reasoning models: openai/gpt-oss-120b, qwen/qwen3-32b
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        
        self.model_name = model
        self._client = None
        self._is_reasoning_model = self._check_reasoning_model(model)
        
        logger.info(f"Groq client initialized with model: {model} (reasoning: {self._is_reasoning_model})")
    
    def _check_reasoning_model(self, model: str) -> bool:
        """Check if model is a reasoning model"""
        reasoning_models = [
            "openai/gpt-oss-20b",
            "openai/gpt-oss-120b",
            "openai/gpt-oss-safeguard-20b",
            "qwen/qwen3-32b"
        ]
        return any(rm in model for rm in reasoning_models)
    
    @property
    def client(self):
        """Lazy load Groq client"""
        if self._client is None:
            try:
                from groq import Groq
                # Explicitly use default base_url to avoid environment variable pollution
                self._client = Groq(
                    api_key=self.api_key
                )

            except ImportError:
                raise ImportError("groq package not installed. Install with: pip install groq")
        return self._client
    
    def generate(self, prompt: str, max_tokens: int = 1024, temperature: float = 0.7, 
                 enable_reasoning: bool = None) -> str:
        """
        Generate a complete response
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            enable_reasoning: Enable reasoning format (auto-detected for reasoning models)
        
        Returns:
            Generated text
        """
        messages = [{"role": "user", "content": prompt}]
        
        # Auto-enable reasoning for reasoning models
        if enable_reasoning is None:
            enable_reasoning = self._is_reasoning_model
        
        params = {
            "messages": messages,
            "model": self.model_name,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        # Add reasoning format for reasoning models
        if enable_reasoning and self._is_reasoning_model:
            params["reasoning_format"] = "parsed"  # Options: "raw" or "parsed"
        
        try:
            response = self.client.chat.completions.create(**params)
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq generation failed: {e}")
            raise
    
    async def generate_stream(self, prompt: str, max_tokens: int = 1024, 
                             temperature: float = 0.7, enable_reasoning: bool = None) -> AsyncGenerator[str, None]:
        """
        Generate a streaming response
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            enable_reasoning: Enable reasoning format
        
        Yields:
            Text chunks
        """
        messages = [{"role": "user", "content": prompt}]
        
        # Auto-enable reasoning for reasoning models
        if enable_reasoning is None:
            enable_reasoning = self._is_reasoning_model
        
        params = {
            "messages": messages,
            "model": self.model_name,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }
        
        # Add reasoning format for reasoning models
        if enable_reasoning and self._is_reasoning_model:
            params["reasoning_format"] = "parsed"
        
        try:
            stream = self.client.chat.completions.create(**params)
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"Groq streaming failed: {e}")
            raise
