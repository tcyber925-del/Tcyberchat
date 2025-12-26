
import asyncio
import os
import logging
import sys

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.agents.deep_research_agent import run_deep_research, DEEPAGENTS_AVAILABLE

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from dotenv import load_dotenv
load_dotenv()

async def test_deep_research():
    print("=" * 60)
    print("   Deep Research Agent Test")
    print("=" * 60)
    
    print(f"\nDeepagents library available: {DEEPAGENTS_AVAILABLE}")
    
    # Check for API keys
    tavily_key = os.getenv("TAVILY_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")
    
    print(f"\nAPI Keys Status:")
    print(f"  GROQ_API_KEY:      {bool(groq_key)}")  # Groq first for deep research
    print(f"  TAVILY_API_KEY:    {bool(tavily_key)}")
    print(f"  GEMINI_API_KEY:    {bool(gemini_key)}")
    print(f"  OPENAI_API_KEY:    {bool(openai_key)}")
    print(f"  ANTHROPIC_API_KEY: {bool(anthropic_key)}")
    
    if not tavily_key:
        print("\nWARNING: TAVILY_API_KEY is missing. Search functionality will be limited.")
    
    # Enable the feature flag
    os.environ["DEEP_RESEARCH_ENABLED"] = "true"
    
    # Use the user's exact query
    query = "What are the latest advancements in solid state batteries?"
    print(f"\nQuery: {query}")
    
    try:
        # Determine which model to use
        # Prefer Groq reasoning models for deep research
        model_to_use = None
        if groq_key:
            model_to_use = "groq:openai/gpt-oss-120b"  # 120B reasoning model
            print(f"Using Groq (Reasoning): {model_to_use}")
        elif openai_key:
            model_to_use = "openai:gpt-4o-mini"
            print(f"Using OpenAI: {model_to_use}")
        elif anthropic_key:
            model_to_use = "anthropic:claude-3-5-sonnet-latest"
            print(f"Using Anthropic: {model_to_use}")
        elif gemini_key:
            # Ensure GOOGLE_API_KEY is set for langchain
            if not os.getenv("GOOGLE_API_KEY"):
                os.environ["GOOGLE_API_KEY"] = gemini_key
            model_to_use = "google_genai:gemini-1.5-flash"
            print(f"Using Gemini: {model_to_use}")
        else:
            print("No model API keys found. Will test with fallback mode.")
            # Disable deepagents to test fallback
            os.environ["DEEP_RESEARCH_ENABLED"] = "false"
        
        print("\nRunning deep research...")
        result = await run_deep_research(query, model_name=model_to_use, max_iterations=1)
        
        print("\n" + "=" * 60)
        print("   Results")
        print("=" * 60)
        
        answer = result.get('answer', '')
        citations = result.get('citations', [])
        metadata = result.get('metadata', {})
        
        print(f"\nStats:")
        print(f"  Answer length: {len(answer)} characters")
        print(f"  Citations: {len(citations)}")
        print(f"  Using deepagents: {metadata.get('deepagents_version', 'false')}")
        print(f"  Duration: {metadata.get('duration_seconds', 'N/A')}s")
        
        if metadata.get("error"):
            print(f"\nError: {metadata['error']}")
            print("\nTest FAILED")
            return False
        
        print(f"\nAnswer Preview (first 500 chars):")
        print("-" * 60)
        safe_answer = answer.encode('ascii', 'replace').decode('ascii')
        print(safe_answer[:500] + ("..." if len(safe_answer) > 500 else ""))
        print("-" * 60)
        
        if citations:
            print(f"\nCitations ({len(citations)}):")
            for i, cite in enumerate(citations[:3], 1):
                title = cite.get('title', cite.get('url', 'N/A'))
                safe_title = title.encode('ascii', 'replace').decode('ascii')
                print(f"  {i}. {safe_title}")
        
        print("\nTest PASSED!")
        return True
            
    except Exception as e:
        print(f"\nEXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        print("\nTest FAILED")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_deep_research())
    sys.exit(0 if success else 1)
