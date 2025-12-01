#!/usr/bin/env python
"""
Test script for Ollama integration.
"""
import asyncio
import os
import sys

# Add the parent directory to sys.path to allow importing from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from src.services.ai_service import aget_ai_service

# Load environment variables
load_dotenv()

# Override OLLAMA_BASE_URL for testing if needed
# os.environ["OLLAMA_BASE_URL"] = "http://localhost:11501"

async def test_ollama():
    print("=" * 70)
    print("   Testing Ollama Integration")
    print("=" * 70)

    # 1. Initialize AI Service
    print("\n[1/4] Initializing AI Service...")
    try:
        # We don't specify a model initially to let it discover available ones
        ai_service = await aget_ai_service()
        print("  [OK] AI Service initialized")
    except Exception as e:
        print(f"  [FAIL] Failed to initialize AI Service: {e}")
        return

    # 2. Check Available Models
    print("\n[2/4] Checking Available Models...")
    try:
        models = await ai_service.get_available_models()
        ollama_models = [m for m in models if m["provider"] == "ollama"]
        
        if ollama_models:
            print(f"  [OK] Found {len(ollama_models)} Ollama models:")
            for m in ollama_models:
                print(f"    - {m['name']}")
            
            # Select the first available Ollama model for testing
            test_model = ollama_models[0]["name"]
            print(f"  -> Selected model for testing: {test_model}")
        else:
            print("  [WARN] No Ollama models found. Is Ollama running?")
            print("  [TIP] Check OLLAMA_BASE_URL in .env")
            return
    except Exception as e:
        print(f"  [FAIL] Failed to list models: {e}")
        return

    # 3. Test Non-Streaming Generation
    print(f"\n[3/4] Testing Non-Streaming Generation ({test_model})...")
    try:
        # Get a service instance specifically for this model
        # Test with bare model name (should work now with the fix)
        model_id = test_model
        print(f"  Testing with model ID: {model_id}")
        service = await aget_ai_service(model_id)
        
        prompt = "What is 2 + 2? Answer in one word."
        print(f"  Prompt: {prompt}")
        
        response = await service.generate_response(prompt)
        
        if response.get("error"):
            print(f"  [FAIL] Error: {response['error']}")
        else:
            print(f"  [OK] Response: {response['response'].strip()}")
            print(f"  Provider used: {response.get('provider')}")
            
    except Exception as e:
        print(f"  [FAIL] Generation failed: {e}")

    # 4. Test Streaming Generation
    print(f"\n[4/4] Testing Streaming Generation ({test_model})...")
    try:
        model_id = test_model
        service = await aget_ai_service(model_id)
        
        prompt = "Count from 1 to 5."
        print(f"  Prompt: {prompt}")
        print("  Stream: ", end="", flush=True)
        
        async for chunk in service.generate_streaming_response(prompt):
            print(chunk, end="", flush=True)
        print("\n  [OK] Streaming completed")
            
    except Exception as e:
        print(f"\n  [FAIL] Streaming failed: {e}")

    print("\n" + "=" * 70)
    print("   Test Complete")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_ollama())
