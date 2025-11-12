import asyncio
import os
import sys

from dotenv import load_dotenv

# Add backend src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.clients.gemini_client import GeminiClient
from src.clients.llama_cpp_client import LlamaCppClient
from src.clients.openrouter_client import OpenRouterClient


async def main():
    """
    Tests connectivity and basic functionality of all available AI clients.
    """
    load_dotenv()

    print("--- Testing AI Clients ---")

    # Test Gemini
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        print("\n--- Testing Google Gemini ---")
        try:
            gemini_client = GeminiClient(api_key=gemini_key)
            prompt = "Hello from the Gemini test script!"
            print(f"Sending prompt: '{prompt}'")
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: gemini_client.generate(prompt)
            )
            print(f"Received response: {response}")
        except Exception as e:
            print(f"Error testing Gemini: {e}")
    else:
        print("\n--- Skipping Google Gemini (GEMINI_API_KEY not set) ---")

    # Test OpenRouter
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if openrouter_key:
        print("\n--- Testing OpenRouter ---")
        try:
            openrouter_client = OpenRouterClient(api_key=openrouter_key)
            prompt = "Hello from the OpenRouter test script!"
            print(f"Sending prompt: '{prompt}'")
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: openrouter_client.chat(prompt)
            )
            print(f"Received response: {response}")
        except Exception as e:
            print(f"Error testing OpenRouter: {e}")
    else:
        print("\n--- Skipping OpenRouter (OPENROUTER_API_KEY not set) ---")

    # Test Llama.cpp
    llama_server_url = os.getenv("LLAMA_CPP_SERVER_URL", "http://localhost:8080")
    if llama_server_url:
        print("\n--- Testing Llama.cpp ---")
        try:
            llama_client = LlamaCppClient(base_url=llama_server_url)
            models = await llama_client.get_available_models()
            if not models:
                print("No models found on Llama.cpp server.")
            else:
                model_name = models[0]
                print(f"Found models: {models}. Using model: {model_name}")
                prompt = "Hello from the Llama.cpp test script!"
                messages = [{"role": "user", "content": prompt}]
                print(f"Sending prompt: '{prompt}'")
                response = await llama_client.generate(messages, model=model_name)
                print(f"Received response: {response}")
        except Exception as e:
            print(f"Error testing Llama.cpp: {e}")
    else:
        print("\n--- Skipping Llama.cpp (LLAMA_CPP_SERVER_URL not set) ---")


if __name__ == "__main__":
    asyncio.run(main())
