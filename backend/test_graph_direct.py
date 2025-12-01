"""
Test Deep Research Graph Directly
"""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def test_graph():
    print("Testing Deep Research Graph...")
    print(f"GROQ_API_KEY: {'SET' if os.getenv('GROQ_API_KEY') else 'NOT SET'}")
    
    try:
        from src.agents.deep_research_graph import run_deep_research_graph
        
        print("\n[OK] Successfully imported run_deep_research_graph")
        
        query = "What are the latest developments in AI?"
        print(f"\nRunning query: {query}")
        
        result = await run_deep_research_graph(query, max_iterations=1)
        
        print(f"\n[OK] Graph executed successfully!")
        print(f"Answer length: {len(result.get('answer', ''))}")
        print(f"Citations: {len(result.get('citations', []))}")
        print(f"Metadata: {result.get('metadata', {})}")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Error running graph: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_graph())
    print(f"\n{'SUCCESS' if success else 'FAILED'}")
