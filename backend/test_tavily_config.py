#!/usr/bin/env python3
"""
Test script to verify Tavily API configuration
"""

import asyncio
import sys
import os

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"✓ Loaded .env file from {env_path}")
except ImportError:
    # python-dotenv not installed, try to load manually
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
        print(f"✓ Loaded .env file manually from {env_path}")

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_tavily_config():
    """Test Tavily API configuration"""
    print("=" * 60)
    print("TAVILY API CONFIGURATION TEST")
    print("=" * 60)
    
    # Check environment variable
    tavily_key = os.getenv('TAVILY_API_KEY')
    if not tavily_key:
        print("\n⚠ TAVILY_API_KEY not set in environment")
        print("Please set it using one of these methods:")
        print("  1. Windows PowerShell: $env:TAVILY_API_KEY='your-key'")
        print("  2. Windows CMD: set TAVILY_API_KEY=your-key")
        print("  3. Linux/Mac: export TAVILY_API_KEY='your-key'")
        print("  4. Create backend/.env file with: TAVILY_API_KEY=your-key")
        print("\nYou can get an API key from: https://tavily.com")
        return False
    
    print(f"\n✓ TAVILY_API_KEY is set (length: {len(tavily_key)} characters)")
    
    # Test Tavily provider directly
    try:
        from src.services.web_search_service import TavilyProvider
        
        provider = TavilyProvider()
        if not provider.is_available():
            print("✗ Tavily provider reports as not available")
            return False
        
        print("✓ Tavily provider is available")
        
        # Test search
        print("\nTesting Tavily search with query: 'latest AI news 2024'...")
        results = await provider.search("latest AI news 2024", max_results=3, search_depth="advanced")
        
        print(f"✓ Found {len(results)} results")
        for i, result in enumerate(results, 1):
            print(f"\n  Result {i}:")
            print(f"    Title: {result.title[:70]}")
            print(f"    URL: {result.url[:70]}")
            print(f"    Snippet: {result.snippet[:100]}...")
        
        return len(results) > 0
        
    except Exception as e:
        print(f"✗ Error testing Tavily: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_web_search_service_with_tavily():
    """Test WebSearchService with Tavily as provider"""
    print("\n" + "=" * 60)
    print("WEB SEARCH SERVICE WITH TAVILY")
    print("=" * 60)
    
    # Set provider to tavily
    os.environ['WEB_SEARCH_PROVIDER'] = 'tavily'
    
    try:
        from src.services.web_search_service import get_web_search_service
        
        # Get fresh instance (will use tavily)
        service = get_web_search_service()
        print(f"✓ Service initialized with provider: {service.provider_name}")
        print(f"  Primary available: {service.primary_provider is not None}")
        print(f"  Fallback available: {service.fallback_provider is not None}")
        
        if service.provider_name != 'tavily':
            print(f"⚠ Warning: Provider is '{service.provider_name}', expected 'tavily'")
            print("  This might be due to cached singleton instance")
        
        # Test search
        query = "latest AI news 2024"
        print(f"\nTesting query: '{query}'")
        results = await service.search(query, max_results=5, use_cache=False, force_fresh=True)
        
        print(f"✓ Found {len(results)} results")
        for i, result in enumerate(results[:3], 1):
            print(f"  {i}. {result.title[:60]}")
            print(f"     {result.url[:60]}")
        
        return len(results) > 0
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    results = []
    
    # Test 1: Tavily configuration
    results.append(await test_tavily_config())
    
    # Test 2: Web search service with Tavily
    if results[0]:  # Only if Tavily is configured
        results.append(await test_web_search_service_with_tavily())
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Tavily Configuration: {'✓ PASS' if results[0] else '✗ FAIL'}")
    if len(results) > 1:
        print(f"Web Search Service: {'✓ PASS' if results[1] else '✗ FAIL'}")
    
    all_passed = all(results)
    print(f"\nOverall: {'✓ ALL TESTS PASSED' if all_passed else '✗ SOME TESTS FAILED'}")
    
    if all_passed:
        print("\n✅ Tavily is configured and working!")
        print("You can now use Tavily for better web search results.")
        print("Set WEB_SEARCH_PROVIDER=tavily to use it as primary provider.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

