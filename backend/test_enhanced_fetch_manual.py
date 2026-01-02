
import asyncio
import os
import sys
import logging

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services import web_fetch_enhanced

async def test_enhanced_fetch():
    print("\n" + "=" * 60)
    print("TESTING ENHANCED WEB FETCH SERVICE")
    print("=" * 60)
    
    urls = [
        "https://example.com",
        "https://en.wikipedia.org/wiki/SpaceX_Starship",
        "https://www.spacex.com/launches"
    ]
    
    for url in urls:
        print(f"\nURL: {url}")
        try:
            # fetch_one returns a dict
            result = await web_fetch_enhanced.fetch_one(url)
            
            if result and not result.get('error'):
                print("✅ SUCCESS")
                print(f"   Title: {result.get('title')}")
                print(f"   Content length: {len(result.get('content', ''))} characters")
                print(f"   Strategy: {result.get('fetch_strategy_used')}")
                print(f"   Preview: {result.get('content', '')[:150].replace('\n', ' ')}...")
            else:
                print(f"❌ FAILED: {result.get('error')}")
                
        except Exception as e:
            print(f"❌ Enhanced Fetch unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(test_enhanced_fetch())
