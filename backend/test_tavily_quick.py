#!/usr/bin/env python
"""Quick test to verify Tavily API works"""
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def test_tavily():
    print("Testing Tavily API...")
    print("=" * 60)
    
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        print("ERROR: TAVILY_API_KEY not found in .env")
        return False
    
    print(f"[OK] API Key found: {api_key[:10]}...")
    
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=api_key)
        
        print("\n[OK] Tavily client initialized")
        print("\nTesting search: 'solid state battery advancements'")
        
        # Use minimal parameters for dev API key
        result = client.search(
            query="solid state battery advancements",
            max_results=2  # Reduced for dev key
        )

        
        print(f"\n[OK] Search successful!")
        print(f"  Results: {len(result.get('results', []))}")
        
        for i, res in enumerate(result.get('results', [])[:3], 1):
            print(f"\n  {i}. {res.get('title', 'No title')[:80]}")
            print(f"     URL: {res.get('url', 'N/A')[:80]}")
            print(f"     Score: {res.get('score', 'N/A')}")
        
        print("\n" + "=" * 60)
        print("[OK] Tavily is working correctly!")

        print("=" * 60)
        return True
        
    except ImportError:
        print("\nERROR: tavily-python not installed")
        print("Install with: uv pip install tavily-python")
        return False
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_tavily())
    exit(0 if success else 1)
