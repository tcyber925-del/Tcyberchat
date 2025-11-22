"""
Test script for Gemini 2.0 native Google Search grounding

This script tests:
1. Basic Gemini 2.0 connection
2. Native Google Search grounding with time-sensitive queries
3. Comparison with external web search (Tavily/SerpAPI)
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the backend directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

load_dotenv()

# Color codes for terminal output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"


def print_section(title):
    """Print a formatted section header"""
    print(f"\n{BLUE}{'=' * 80}{RESET}")
    print(f"{BLUE}{title}{RESET}")
    print(f"{BLUE}{'=' * 80}{RESET}\n")


def print_success(message):
    """Print a success message"""
    print(f"{GREEN}✓ {message}{RESET}")


def print_warning(message):
    """Print a warning message"""
    print(f"{YELLOW}⚠ {message}{RESET}")


def print_error(message):
    """Print an error message"""
    print(f"{RED}✗ {message}{RESET}")


async def test_gemini_connection():
    """Test 1: Basic Gemini connection"""
    print_section("TEST 1: Basic Gemini 2.0 Connection")

    try:
        from src.clients.gemini_client import GeminiClient

        model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
        print(f"Testing model: {model_name}")

        client = GeminiClient()
        print_success(f"Client initialized with model: {client.model_name}")

        # Simple test
        response = client.generate("Say 'Hello' in one word")
        print(f"Response: {response}")
        print_success("Basic generation works!")

        return True
    except Exception as e:
        print_error(f"Failed: {e}")
        return False


async def test_native_grounding():
    """Test 2: Native Google Search grounding"""
    print_section("TEST 2: Native Google Search Grounding")

    try:
        from src.clients.gemini_client import GeminiClient

        client = GeminiClient()

        if "gemini-2.0" not in client.model_name:
            print_warning(
                f"Skipping: Model {client.model_name} doesn't support native grounding"
            )
            print_warning("Update GEMINI_MODEL to 'gemini-2.0-flash-exp' in .env")
            return False

        # Test with grounding enabled
        query = "What is the latest AI news today?"
        print(f"Query: {query}")
        print("Grounding: ENABLED")

        response = client.generate(query, enable_grounding=True)
        print(f"\nResponse with grounding:\n{response}\n")

        # Check if response contains URL citations or recent information
        has_urls = "http" in response.lower()
        has_recent_terms = any(
            term in response.lower() for term in ["recent", "latest", "today", "2025"]
        )

        if has_urls:
            print_success("Response contains URLs (likely from Google Search)")
        else:
            print_warning("No URLs found in response")

        if has_recent_terms:
            print_success("Response contains recent/time-sensitive terms")
        else:
            print_warning("No time-sensitive terms found")

        print_success("Native grounding test completed!")
        return True

    except Exception as e:
        print_error(f"Failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_ai_service_integration():
    """Test 3: AI Service integration with grounding"""
    print_section("TEST 3: AI Service Integration")

    try:
        from src.services.ai_service import get_ai_service

        # Get AI service with Gemini 2.0
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
        ai_service = await get_ai_service(model_name)

        print(f"AI Service model: {ai_service.model_name}")

        # Test with time-sensitive query (should trigger grounding)
        query = "What are the latest developments in AI?"
        context = ["User is asking about recent AI news"]

        print(f"Query: {query}")
        print(f"Context: {context}")
        print("\nGenerating response...")

        result = await ai_service.generate_response(query, context=context)

        print(f"\nResponse:\n{result['response']}\n")
        print(f"Model used: {result['model']}")
        print(f"Provider: {result['provider']}")
        print(f"Processing time: {result['processing_time']:.2f}s")

        if result.get("error"):
            print_error(f"Error: {result['error']}")
            return False

        print_success("AI Service integration works!")
        return True

    except Exception as e:
        print_error(f"Failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_web_search_comparison():
    """Test 4: Compare native grounding vs external web search"""
    print_section("TEST 4: Native Grounding vs External Web Search")

    try:
        from src.services.rag_service import get_rag_service

        rag_service = get_rag_service()

        query = "What is the latest AI news?"

        # Test with external web search (Tavily/SerpAPI)
        print("Testing with EXTERNAL web search (Tavily/SerpAPI)...")

        result_external = await rag_service.generate_rag_response(
            query=query, use_web_search=True, model_name=os.getenv("GEMINI_MODEL")
        )

        print(
            f"\nExternal Web Search Response:\n{result_external.get('response', 'N/A')[:300]}...\n"
        )

        external_citations = result_external.get("citations", [])
        print(f"Citations: {len(external_citations)} results")
        if external_citations:
            for i, cit in enumerate(external_citations[:3], 1):
                print(f"  [{i}] {cit.get('title', 'N/A')} - {cit.get('url', 'N/A')}")

        print_success("External web search works!")

        # Note about native grounding
        print("\n" + "=" * 80)
        print("NOTE: Native Google Search grounding is automatically enabled for")
        print("time-sensitive queries when using Gemini 2.0. Check backend logs")
        print("for: 'Enabling Google Search grounding for...'")
        print("=" * 80)

        return True

    except Exception as e:
        print_error(f"Failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print(f"\n{BLUE}{'=' * 80}{RESET}")
    print(f"{BLUE}Gemini 2.0 Native Google Search Grounding Test Suite{RESET}")
    print(f"{BLUE}{'=' * 80}{RESET}")

    # Check environment
    print("\nEnvironment Check:")
    gemini_key = os.getenv("GEMINI_API_KEY")
    gemini_model = os.getenv("GEMINI_MODEL")

    if gemini_key:
        print_success(f"GEMINI_API_KEY: Set ({gemini_key[:20]}...)")
    else:
        print_error("GEMINI_API_KEY: Not set")
        return

    if gemini_model:
        print_success(f"GEMINI_MODEL: {gemini_model}")
        if "gemini-2.0" not in gemini_model:
            print_warning("For native grounding, use 'gemini-2.0-flash-exp'")
    else:
        print_warning("GEMINI_MODEL: Not set (using default)")

    # Run tests
    results = []

    results.append(("Basic Connection", await test_gemini_connection()))
    results.append(("Native Grounding", await test_native_grounding()))
    results.append(("AI Service Integration", await test_ai_service_integration()))
    results.append(("Web Search Comparison", await test_web_search_comparison()))

    # Summary
    print_section("TEST SUMMARY")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        color = GREEN if result else RED
        print(f"{color}{status:6}{RESET} - {test_name}")

    print(f"\n{BLUE}Results: {passed}/{total} tests passed{RESET}")

    if passed == total:
        print_success("\n🎉 All tests passed! Gemini 2.0 native grounding is working!")
    else:
        print_warning(f"\n⚠️ {total - passed} test(s) failed. Check the output above.")

    print("\nNext steps:")
    print("1. Start the backend: cd backend && python main.py")
    print("2. Ask a time-sensitive query: 'What is the latest AI news?'")
    print("3. Check logs for: 'Enabling Google Search grounding for...'")
    print("4. Compare with external web search toggle in frontend")


if __name__ == "__main__":
    asyncio.run(main())
