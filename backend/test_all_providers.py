#!/usr/bin/env python
"""Test Tavily with fallback to other providers"""
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def test_providers():
    print("=" * 70)
    print("   Testing Web Search Providers")
    print("=" * 70)
    
    providers_tested = []
    working_provider = None
    
    # Test 1: Tavily
    print("\n[1/3] Testing Tavily...")
    tavily_key = os.getenv("TAVILY_API_KEY")
    if tavily_key:
        try:
            from tavily import TavilyClient
            client = TavilyClient(api_key=tavily_key)
            
            # Try with absolute minimal parameters for dev key
            result = client.search(query="python", max_results=1)
            
            if result and result.get('results'):
                print(f"  [OK] Tavily working! (key: {tavily_key[:12]}...)")
                print(f"  Sample result: {result['results'][0].get('title', 'N/A')[:60]}")
                working_provider = "tavily"
                providers_tested.append(("tavily", True, None))
            else:
                print("  [WARN] Tavily returned empty results")
                providers_tested.append(("tavily", False, "Empty results"))
        except Exception as e:
            error_msg = str(e)
            print(f"  [FAIL] Tavily error: {error_msg[:80]}")
            providers_tested.append(("tavily", False, error_msg[:80]))
    else:
        print("  [SKIP] No TAVILY_API_KEY found")
        providers_tested.append(("tavily", False, "No API key"))
    
    # Test 2: SerpAPI
    print("\n[2/3] Testing SerpAPI...")
    serpapi_key = os.getenv("SERPAPI_API_KEY")
    if serpapi_key:
        try:
            import serpapi
            client = serpapi.Client(api_key=serpapi_key)
            result = client.search({"q": "python", "num": 1, "engine": "google"})
            
            if result and result.get('organic_results'):
                print(f"  [OK] SerpAPI working! (key: {serpapi_key[:12]}...)")
                print(f"  Sample result: {result['organic_results'][0].get('title', 'N/A')[:60]}")
                if not working_provider:
                    working_provider = "serpapi"
                providers_tested.append(("serpapi", True, None))
            else:
                print("  [WARN] SerpAPI returned empty results")
                providers_tested.append(("serpapi", False, "Empty results"))
        except Exception as e:
            error_msg = str(e)
            print(f"  [FAIL] SerpAPI error: {error_msg[:80]}")
            providers_tested.append(("serpapi", False, error_msg[:80]))
    else:
        print("  [SKIP] No SERPAPI_API_KEY found")
        providers_tested.append(("serpapi", False, "No API key"))
    
    # Test 3: DuckDuckGo
    print("\n[3/3] Testing DuckDuckGo...")
    try:
        from duckduckgo_search import DDGS
        results = list(DDGS().text("python", max_results=1))
        
        if results:
            print(f"  [OK] DuckDuckGo working!")
            print(f"  Sample result: {results[0].get('title', 'N/A')[:60]}")
            if not working_provider:
                working_provider = "duckduckgo"
            providers_tested.append(("duckduckgo", True, None))
        else:
            print("  [WARN] DuckDuckGo returned empty results")
            providers_tested.append(("duckduckgo", False, "Empty results"))
    except Exception as e:
        error_msg = str(e)
        print(f"  [FAIL] DuckDuckGo error: {error_msg[:80]}")
        providers_tested.append(("duckduckgo", False, error_msg[:80]))
    
    # Summary
    print("\n" + "=" * 70)
    print("   Summary")
    print("=" * 70)
    
    for provider, success, error in providers_tested:
        status = "[OK]" if success else "[FAIL]"
        print(f"{status} {provider:15} - {error if error else 'Working'}")
    
    print("\n" + "=" * 70)
    if working_provider:
        print(f"RECOMMENDATION: Use WEB_SEARCH_PROVIDER={working_provider}")
        print("=" * 70)
        
        print(f"\nTo configure:")
        print(f"1. Edit backend/.env")
        print(f"2. Set: WEB_SEARCH_PROVIDER={working_provider}")
        print(f"3. Restart backend server")
        return working_provider
    else:
        print("ERROR: No working providers found!")
        print("=" * 70)
        return None

if __name__ == "__main__":
    asyncio.run(test_providers())
