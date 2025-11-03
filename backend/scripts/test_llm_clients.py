"""Small script to test the Gemini and OpenRouter clients locally.

It will attempt to import the thin wrappers in `backend/src/clients/` and call
them if API keys are present in the environment. The script is defensive and
prints helpful instructions if dependencies or keys are missing.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
# Ensure the project's `backend` package directory is on the path so
# `from src.clients...` imports resolve when running this script directly.
BACKEND_DIR = os.path.join(ROOT, "backend")
sys.path.insert(0, BACKEND_DIR)

from src.clients.gemini_client import GeminiClient
from src.clients.openrouter_client import OpenRouterClient


def try_gemini():
    print("\n=== Gemini test ===")
    try:
        client = GeminiClient()
    except Exception as e:
        print("Gemini client init error:", e)
        return

    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        print("GEMINI_API_KEY not set — set it or put it in backend/.env")
        return

    try:
        resp = client.generate("Say hello in one sentence.")
        print("Gemini response:\n", resp)
    except Exception as e:
        print("Gemini call failed:", e)


def try_openrouter():
    print("\n=== OpenRouter test ===")
    try:
        client = OpenRouterClient()
    except Exception as e:
        print("OpenRouter client init error:", e)
        return

    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        print("OPENROUTER_API_KEY not set — set it or put it in backend/.env")
        return

    try:
        resp = client.chat("Say hello in one sentence.")
        print("OpenRouter response:\n", resp)
    except Exception as e:
        print("OpenRouter call failed:", e)


if __name__ == "__main__":
    print("This script will run quick smoke tests for Gemini and OpenRouter.")
    try_gemini()
    try_openrouter()
