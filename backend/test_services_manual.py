
import asyncio
import os
import sys
import logging
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging to see what's happening
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')

from src.services.web_search_service import get_web_search_service
from src.services.web_fetch_service import get_web_fetch_service

async def test_web_search():
    print("\n" + "=" * 60)
    print("TESTING WEB SEARCH SERVICE")
    print("=" * 60)
    
    try:
        search_service = get_web_search_service()
        query = "Latest SpaceX Starship launch status December 2025"
        print(f"Query: {query}")
        print(f"Primary Provider: {search_service.provider_name}")
        
        results = await search_service.search(query, max_results=3)
        
        if not results:
            print("❌ No search results found.")
            return []
            
        print(f"✅ Found {len(results)} results:")
        for i, r in enumerate(results):
            print(f"  [{i+1}] {r.title}")
            print(f"      URL: {r.url}")
            
        return [r.url for r in results if r.url]
    except Exception as e:
        print(f"❌ Web Search failed: {e}")
        import traceback
        traceback.print_exc()
        return []

async def test_web_fetch(urls):
    print("\n" + "=" * 60)
    print("TESTING WEB FETCH SERVICE")
    print("=" * 60)
    
    if not urls:
        print("⚠ No URLs provided for fetching.")
        # Fallback to a reliable URL
        urls = ["https://en.wikipedia.org/wiki/SpaceX_Starship"]
        print(f"Using fallback: {urls[0]}")
        
    try:
        fetch_service = get_web_fetch_service()
        # Ensure it's enabled for the test
        fetch_service.enabled = True
        
        print(f"Fetching {len(urls)} URLs...")
        results = await fetch_service.fetch_multiple(urls)
        
        success_count = 0
        for i, r in enumerate(results):
            url = getattr(r, 'url', 'Unknown')
            content = getattr(r, 'content', '')
            error = getattr(r, 'error', None)
            
            if content and not error:
                success_count += 1
                print(f"  [{i+1}] ✅ SUCCESS: {url}")
                print(f"      Content length: {len(content)} characters")
                print(f"      Preview: {content[:150].replace('\n', ' ')}...")
            else:
                print(f"  [{i+1}] ❌ FAILED: {url}")
                print(f"      Error: {error}")
                
        print(f"\nSummary: {success_count}/{len(urls)} successful fetches.")
    except Exception as e:
        print(f"❌ Web Fetch failed: {e}")
        import traceback
        traceback.print_exc()

async def main():
    load_dotenv()
    
    # 1. Test Search
    urls = await test_web_search()
    
    # 2. Test Fetch
    await test_web_fetch(urls)

if __name__ == "__main__":
    asyncio.run(main())
