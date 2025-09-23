"""
AIService for LLM interactions and general AI processing
"""

from typing import Dict, List, Optional, Any
import asyncio
import time

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False


class AIService:
    """Service for AI model interactions and processing"""

    def __init__(self, model_name: str = "llama3.2:latest"):
        self.model_name = model_name
        self.client = ollama.Client() if OLLAMA_AVAILABLE else None

    async def generate_response(self, prompt: str, context: Optional[List[str]] = None,
                              max_tokens: int = 1024) -> Dict[str, Any]:
        """
        Generate AI response with optional context
        Returns dict with response text and metadata
        """
        start_time = time.time()

        try:
            # Build full prompt with context
            full_prompt = prompt
            if context:
                context_str = "\n".join(context)
                full_prompt = f"Context:\n{context_str}\n\nQuestion: {prompt}"

            # Generate response using Ollama
            if not self.client:
                # Fallback for when Ollama is not available
                return {
                    "response": f"[Mock response] {prompt}",
                    "model": "mock-model",
                    "processing_time": 0.1,
                    "tokens_used": len(prompt.split())
                }

            response = self.client.generate(
                model=self.model_name,
                prompt=full_prompt,
                options={
                    "num_predict": max_tokens,
                    "temperature": 0.7,
                    "top_p": 0.9
                }
            )

            processing_time = time.time() - start_time

            return {
                "response": response["response"],
                "model": self.model_name,
                "processing_time": processing_time,
                "eval_count": response.get("eval_count", 0),
                "eval_duration": response.get("eval_duration", 0)
            }

        except Exception as e:
            processing_time = time.time() - start_time
            return {
                "response": f"Error generating response: {str(e)}",
                "model": self.model_name,
                "processing_time": processing_time,
                "error": str(e)
            }

    async def generate_summary(self, content: str, max_length: int = 500) -> Dict[str, Any]:
        """Generate a summary of the given content"""
        prompt = f"Please provide a concise summary of the following content in {max_length} words or less:\n\n{content}"

        summary_result = await self.generate_response(prompt, max_tokens=512)

        # Truncate if needed (simple approach)
        summary = summary_result["response"]
        if len(summary.split()) > max_length:
            words = summary.split()[:max_length]
            summary = " ".join(words) + "..."

        return {
            **summary_result,
            "summary": summary
        }

    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of text"""
        prompt = f"Analyze the sentiment of this text and respond with only: positive, negative, or neutral\n\nText: {text}"

        result = await self.generate_response(prompt, max_tokens=50)

        # Extract sentiment (simple parsing)
        response = result["response"].lower().strip()
        if "positive" in response:
            sentiment = "positive"
        elif "negative" in response:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        return {
            **result,
            "sentiment": sentiment
        }

    async def extract_keywords(self, text: str, max_keywords: int = 10) -> Dict[str, Any]:
        """Extract key topics/keywords from text"""
        prompt = f"Extract the {max_keywords} most important keywords or topics from this text. Return as a comma-separated list:\n\n{text}"

        result = await self.generate_response(prompt, max_tokens=200)

        # Parse keywords
        response = result["response"].strip()
        keywords = [k.strip() for k in response.split(",") if k.strip()]
        keywords = keywords[:max_keywords]  # Limit to requested number

        return {
            **result,
            "keywords": keywords
        }

    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available Ollama models"""
        if not self.client:
            return [{"name": "mock-model", "size": "unknown", "modified_at": "unknown"}]

        try:
            models = self.client.list()
            return models.get("models", [])
        except Exception:
            return []

    def check_model_availability(self, model_name: str) -> bool:
        """Check if a specific model is available"""
        models = self.get_available_models()
        return any(model["name"] == model_name for model in models)

    async def embed_text(self, texts: List[str]) -> Optional[List[List[float]]]:
        """
        Generate embeddings for text using sentence-transformers
        Returns None if embeddings service is not available
        """
        try:
            # Placeholder for sentence-transformers integration
            # In real implementation, this would use:
            # from sentence_transformers import SentenceTransformer
            # model = SentenceTransformer('all-MiniLM-L6-v2')
            # embeddings = model.encode(texts)

            # For now, return mock embeddings
            return [[0.1] * 384 for _ in texts]  # Mock 384-dimensional embeddings

        except ImportError:
            return None
        except Exception:
            return None

    async def embed_query(self, query: str) -> Optional[List[float]]:
        """Generate embedding for a single query"""
        embeddings = await self.embed_text([query])
        return embeddings[0] if embeddings else None


# Global instance for dependency injection
_ai_service_instance = None

def get_ai_service() -> AIService:
    """Get singleton AIService instance"""
    global _ai_service_instance
    if _ai_service_instance is None:
        _ai_service_instance = AIService()
    return _ai_service_instance