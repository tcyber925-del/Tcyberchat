#!/usr/bin/env python3
"""Simple Tavily test to verify API key"""

import os

# Load .env
try:
    from dotenv import load_dotenv

    load_dotenv()
except:
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()

api_key = os.getenv("TAVILY_API_KEY")
print(f"API Key: {api_key[:10]}...{api_key[-4:] if api_key else 'NOT SET'}")
print(
    f"Key type: {'DEV' if api_key and 'dev' in api_key.lower() else 'PROD' if api_key else 'NONE'}"
)

if api_key:
    try:
        from tavily import TavilyClient

        client = TavilyClient(api_key=api_key)
        print("\nTesting with minimal query...")
        result = client.search(query="AI", max_results=1)
        print(f"✓ Success! Got {len(result.get('results', []))} result(s)")
        if result.get("results"):
            print(f"  First result: {result['results'][0].get('title', 'N/A')[:50]}")
    except Exception as e:
        print(f"\n✗ Error: {type(e).__name__}: {e}")
        if "Forbidden" in str(e):
            print("\n⚠ ForbiddenError usually means:")
            print("  1. API key is invalid or expired")
            print("  2. API key doesn't have required permissions")
            print("  3. Dev API keys may have restrictions")
            print("  4. Rate limit exceeded")
            print("\n  Try getting a new API key from https://tavily.com")
else:
    print("✗ TAVILY_API_KEY not set")
