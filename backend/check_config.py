import os
from dotenv import load_dotenv

load_dotenv()

print("Current Web Search Configuration:")
print("=" * 50)
print(f"WEB_SEARCH_PROVIDER: {os.getenv('WEB_SEARCH_PROVIDER', 'NOT SET')}")
print(f"TAVILY_API_KEY: {'SET' if os.getenv('TAVILY_API_KEY') else 'NOT SET'}")
print(f"SERPAPI_API_KEY: {'SET' if os.getenv('SERPAPI_API_KEY') else 'NOT SET'}")
print("=" * 50)

# Recommendation
provider = os.getenv('WEB_SEARCH_PROVIDER', 'duckduckgo')
print(f"\nCurrent provider will be: {provider}")

if provider == 'serpapi' and not os.getenv('SERPAPI_API_KEY'):
    print("\nWARNING: Provider set to 'serpapi' but no API key!")
    print("RECOMMENDATION: Change to 'duckduckgo' or set SERPAPI_API_KEY")

if provider == 'tavily' and not os.getenv('TAVILY_API_KEY'):
    print("\nWARNING: Provider set to 'tavily' but no API key!")
    print("RECOMMENDATION: Change to 'duckduckgo' or set TAVILY_API_KEY")
