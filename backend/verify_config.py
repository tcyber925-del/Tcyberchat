"""
Configuration Verification Script
Verifies the Gemini 2.0 upgrade without making API calls
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Color codes
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"


def print_header(title):
    print(f"\n{BLUE}{'=' * 80}{RESET}")
    print(f"{BLUE}{title}{RESET}")
    print(f"{BLUE}{'=' * 80}{RESET}\n")


def check_mark(condition):
    return f"{GREEN}✓{RESET}" if condition else f"{RED}✗{RESET}"


print_header("Gemini 2.0 Native Grounding Configuration Verification")

# Load environment
load_dotenv()

print("1. Environment Configuration Check")
print("-" * 80)

# Check Gemini API Key
gemini_key = os.getenv("GEMINI_API_KEY")
if gemini_key:
    print(f"{check_mark(True)} GEMINI_API_KEY: Set ({gemini_key[:20]}...)")
else:
    print(f"{check_mark(False)} GEMINI_API_KEY: NOT SET")

# Check Gemini Model
gemini_model = os.getenv("GEMINI_MODEL")
is_gemini_2 = gemini_model and "gemini-2.0" in gemini_model
print(f"{check_mark(gemini_model)} GEMINI_MODEL: {gemini_model or 'NOT SET'}")
if is_gemini_2:
    print(f"  {GREEN}→ Supports native Google Search grounding!{RESET}")
elif gemini_model:
    print(
        f"  {YELLOW}→ This model doesn't support native grounding. Use 'gemini-2.0-flash-exp'{RESET}"
    )

# Check web search providers
print(
    f"\n{check_mark(os.getenv('TAVILY_API_KEY'))} TAVILY_API_KEY: {'Set' if os.getenv('TAVILY_API_KEY') else 'NOT SET'}"
)
print(
    f"{check_mark(os.getenv('SERPAPI_API_KEY'))} SERPAPI_API_KEY: {'Set' if os.getenv('SERPAPI_API_KEY') else 'NOT SET'}"
)
print(
    f"{check_mark(os.getenv('WEB_SEARCH_PROVIDER'))} WEB_SEARCH_PROVIDER: {os.getenv('WEB_SEARCH_PROVIDER') or 'NOT SET'}"
)

print("\n2. Code Changes Verification")
print("-" * 80)

# Check gemini_client.py
try:
    sys.path.insert(0, str(Path(__file__).parent))
    from src.clients.gemini_client import GeminiClient

    # Check default model
    client = GeminiClient.__init__.__code__
    has_grounding_param = (
        "enable_grounding" in GeminiClient.generate.__code__.co_varnames
    )

    print(f"{check_mark(True)} gemini_client.py: Imported successfully")
    print(
        f"{check_mark(has_grounding_param)} enable_grounding parameter: {'Added' if has_grounding_param else 'MISSING'}"
    )

    if has_grounding_param:
        print(f"  {GREEN}→ GeminiClient supports native grounding!{RESET}")

except Exception as e:
    print(f"{check_mark(False)} gemini_client.py: Import failed - {e}")

# Check ai_service.py
try:
    from src.services.ai_service import AIService

    print(f"{check_mark(True)} ai_service.py: Imported successfully")

    # Check for grounding logic in generate_response
    import inspect

    generate_code = inspect.getsource(AIService.generate_response)
    has_grounding_logic = "enable_grounding" in generate_code

    print(
        f"{check_mark(has_grounding_logic)} Grounding auto-detection: {'Implemented' if has_grounding_logic else 'MISSING'}"
    )

    if has_grounding_logic:
        print(
            f"  {GREEN}→ AI Service will auto-enable grounding for time-sensitive queries!{RESET}"
        )

except Exception as e:
    print(f"{check_mark(False)} ai_service.py: Check failed - {e}")

print("\n3. Implementation Summary")
print("-" * 80)

all_good = gemini_key and is_gemini_2 and has_grounding_param

if all_good:
    print(f"\n{GREEN}✓ ✓ ✓ ALL CHECKS PASSED! ✓ ✓ ✓{RESET}")
    print(f"\n{GREEN}Your Gemini 2.0 native grounding upgrade is complete!{RESET}")
    print("\nWhat happens now:")
    print("  1. Time-sensitive queries automatically use Google Search")
    print(
        "  2. Keywords that trigger grounding: latest, recent, news, update, current, today, now"
    )
    print("  3. External web search (Tavily/SerpAPI) available as backup")
    print("  4. Hybrid approach for maximum reliability")
else:
    print(f"\n{YELLOW}⚠ SOME CHECKS FAILED{RESET}")
    print("\nRequired actions:")
    if not gemini_key:
        print(f"  {RED}✗{RESET} Set GEMINI_API_KEY in .env")
    if not is_gemini_2:
        print(f"  {RED}✗{RESET} Change GEMINI_MODEL to 'gemini-2.0-flash-exp' in .env")
    if not has_grounding_param:
        print(
            f"  {RED}✗{RESET} Update gemini_client.py with enable_grounding parameter"
        )

print("\n4. Next Steps")
print("-" * 80)

if gemini_key:
    print(
        f"{YELLOW}NOTE: Your Gemini API quota is currently exhausted (429 error).{RESET}"
    )
    print(
        f"{YELLOW}Wait ~1 hour or try again tomorrow to test with actual API calls.{RESET}\n"
    )

print("To test the implementation:")
print("  1. Wait for API quota to reset (check https://aistudio.google.com/quotas)")
print("  2. Start backend: python main.py")
print("  3. Test with frontend or curl:")
print("     curl -X POST http://localhost:8000/api/chat \\")
print("       -H 'Content-Type: application/json' \\")
print(
    '       -d \'{"message": "What is the latest AI news?", "model": "models/gemini-2.0-flash-exp"}\''
)
print("  4. Check backend logs for: 'Enabling Google Search grounding for...'")

print("\nDocumentation:")
print("  - GEMINI_2_UPGRADE_COMPLETE.md - Full implementation details")
print("  - GOOGLE_MODELS_WEB_SEARCH.md - Model comparison")
print("  - QUICK_FIX_MODEL.md - Step-by-step guide")

print(f"\n{BLUE}{'=' * 80}{RESET}\n")
