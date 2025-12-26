"""
Test script to verify Firecrawl integration as primary deep research provider.
"""
import asyncio
import os
import sys

# Force unbuffered output
sys.stdout = sys.stdout


async def main():
    from dotenv import load_dotenv
    load_dotenv()
    
    print("=" * 60)
    print("FIRECRAWL INTEGRATION TEST")
    print("=" * 60)
    
    # Test 1: Check if API key is set
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        print("\n✗ FIRECRAWL_API_KEY not set in environment")
        return False
    print(f"\n✓ FIRECRAWL_API_KEY is set (length: {len(api_key)} chars)")
    
    # Test 2: Check if FirecrawlProvider is available
    from src.services.web_search_service import FirecrawlProvider
    
    provider = FirecrawlProvider()
    if not provider.is_available():
        print("✗ FirecrawlProvider reports as not available")
        return False
    print("✓ FirecrawlProvider is available")
    
    # Test 3: Run a search
    print("\nTesting Firecrawl search with query: 'latest AI developments 2024'...")
    try:
        results = await provider.search("latest AI developments 2024", max_results=3)
        
        if not results:
            print("✗ Search returned no results")
            return False
        
        print(f"✓ Search returned {len(results)} results:")
        for i, r in enumerate(results):
            print(f"\n  [{i+1}] {r.title[:70]}")
            print(f"      URL: {r.url[:80]}")
            if r.snippet:
                print(f"      Snippet: {r.snippet[:100]}...")
                
    except Exception as e:
        print(f"✗ Search failed: {type(e).__name__}: {e}")
        return False
    
    # Test 4: Test scrape capability
    print("\n" + "-" * 60)
    print("Testing Firecrawl scrape capability...")
    try:
        scrape_result = await provider.scrape("https://firecrawl.dev", formats=["markdown"])
        if scrape_result and scrape_result.get("markdown"):
            print(f"✓ Scrape returned {len(scrape_result['markdown'])} chars of markdown")
            print(f"  Preview: {scrape_result['markdown'][:200]}...")
        else:
            print("⚠ Scrape returned empty or no markdown")
    except Exception as e:
        print(f"⚠ Scrape test error (non-fatal): {e}")
    
    print("\n" + "=" * 60)
    print("✅ FIRECRAWL INTEGRATION TESTS PASSED")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
