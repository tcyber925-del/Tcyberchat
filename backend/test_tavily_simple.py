#!/usr/bin/env python3
"""
Simple Tavily API test to check error details
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_tavily():
    """Test Tavily API directly"""
    try:
        from tavily import TavilyClient
        
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            print("❌ TAVILY_API_KEY not found in environment")
            return
        
        print(f"✓ API Key found (length: {len(api_key)})")
        print(f"  Key starts with: {api_key[:10]}...")
        
        # Initialize client
        client = TavilyClient(api_key=api_key)
        print("✓ Client initialized")
        
        # Try a simple search with basic depth (free tier)
        print("\n🔍 Testing with 'basic' search depth (free tier)...")
        try:
            response = client.search(
                query="Python programming",
                max_results=1,
                search_depth="basic"  # Use basic instead of advanced
            )
            print(f"✅ Basic search successful!")
            print(f"   Found {len(response.get('results', []))} results")
            if response.get('results'):
                print(f"   First result: {response['results'][0].get('title', 'N/A')}")
        except Exception as e:
            print(f"❌ Basic search failed: {e}")
            print(f"   Error type: {type(e).__name__}")
            
        # Try advanced search
        print("\n🔍 Testing with 'advanced' search depth...")
        try:
            response = client.search(
                query="Python programming",
                max_results=1,
                search_depth="advanced"
            )
            print(f"✅ Advanced search successful!")
            print(f"   Found {len(response.get('results', []))} results")
        except Exception as e:
            print(f"❌ Advanced search failed: {e}")
            print(f"   Error type: {type(e).__name__}")
            if "forbidden" in str(e).lower() or "ForbiddenError" in str(type(e).__name__):
                print("\n💡 Possible causes:")
                print("   - API key is invalid or expired")
                print("   - Free tier doesn't support 'advanced' search depth")
                print("   - API quota/limit reached")
                print("   - Account needs upgrade")
                print("\n📝 Check your plan at: https://app.tavily.com/")
            
    except ImportError:
        print("❌ tavily package not installed")
        print("   Install with: pip install tavily-python")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_tavily())
