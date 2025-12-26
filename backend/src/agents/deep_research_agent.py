"""
Deep Research Agent using custom LangGraph implementation.
Replaces the incompatible deepagents library.
"""
import os
import asyncio
import logging
from typing import Dict, Any, AsyncGenerator

# Import the new graph-based implementation
from .deep_research_graph import run_deep_research_graph

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define constant for compatibility with existing tests/imports
DEEPAGENTS_AVAILABLE = True 

async def validate_deep_research_requirements():
    """Validate all requirements before running deep research"""
    errors = []
    
    # Check GROQ_API_KEY
    if not os.getenv("GROQ_API_KEY"):
        errors.append("GROQ_API_KEY is not set")
    
    # Check web search provider
    from src.services.web_search_service import get_web_search_service
    try:
        svc = get_web_search_service()
        if not svc.primary_provider or not svc.primary_provider.is_available():
            errors.append(f"Web search provider '{svc.provider_name}' is not available")
    except Exception as e:
        errors.append(f"Web search service initialization failed: {e}")
    
    # Check Groq client
    try:
        from src.clients.groq_client import GroqClient
        # Use a lightweight model for validation if possible, or just init the client
        client = GroqClient(model="llama-3.3-70b-versatile")
        # We won't make an API call here to save time/quota, just verify init works
        if not client.client:
             errors.append("Groq client initialization failed")
    except Exception as e:
        errors.append(f"Groq client test failed: {e}")
    
    if errors:
        raise ValueError(
            "Deep Research requirements not met:\n" + 
            "\n".join(f"  - {err}" for err in errors)
        )
    
    logger.info("Deep Research requirements validated successfully")

async def run_deep_research(
    query: str, 
    model_name: str = None, 
    max_iterations: int = 3
) -> Dict[str, Any]:
    """
    Executes the deep research agent using the custom LangGraph implementation.
    
    Args:
        query: The research query
        model_name: Optional model name (ignored, uses Groq by default in graph)
        max_iterations: Maximum number of refinement loops
        
    Returns:
        Dict containing 'answer', 'citations', and 'metadata'
    """
    try:
        logger.info(f"Starting deep research for query: {query}")
        
        # Validate requirements first
        await validate_deep_research_requirements()
        
        # Run the graph - NO FALLBACKS ALLOWED
        result = await run_deep_research_graph(query, max_iterations=max_iterations)
        
        return result

    except ValueError as e:
        # Configuration/validation errors
        logger.error(f"Deep Research validation failed: {e}")
        raise
        
    except Exception as e:
        # Execution errors
        logger.error(f"Deep Research execution failed: {e}", exc_info=True)
        raise RuntimeError(
            f"Deep Research failed to execute. This could indicate:\n"
            f"1. Groq API configuration issue\n"
            f"2. Web search provider failure\n"
            f"3. LangGraph execution error\n"
            f"Original error: {str(e)}"
        ) from e

async def run_deep_research_stream(
    query: str, 
    model_name: str = None, 
    max_iterations: int = 3
) -> AsyncGenerator[str, None]:
    """
    Streaming version of deep research.
    Currently yields the final result as a single chunk since the graph is not yet streaming-optimized.
    """
    # Just await the result and yield it
    # In the future, we can hook into the graph events
    result = await run_deep_research(query, model_name, max_iterations)
    yield result.get("answer", "")
