"""
Quick test for Groq integration
Tests both GroqClient and AI Service with Groq provider
"""
import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

async def test_groq_client():
    """Test GroqClient directly"""
    print("=" * 60)
    print("Testing GroqClient")
    print("=" * 60)
    
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        print("❌ GROQ_API_KEY not found. Please add it to .env")
        return False
    
    print(f"✅ GROQ_API_KEY found")
    
    try:
        from src.clients.groq_client import GroqClient
        
        # Test with reasoning model
        print("\n📝 Testing with GPT-OSS 120B (reasoning model)...")
        client = GroqClient(api_key=groq_key, model="openai/gpt-oss-120b")
        
        prompt = "What is 2+2? Think step by step."
        print(f"Prompt: {prompt}")
        
        response = client.generate(prompt, max_tokens=512)
        print(f"\n✅ Response ({len(response)} chars):\n{response[:200]}...")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_ai_service_groq():
    """Test AIService with Groq provider"""
    print("\n" + "=" * 60)
    print("Testing AIService with Groq")
    print("=" * 60)
    
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        print("⏭️  Skipping (no GROQ_API_KEY)")
        return True
    
    try:
        from src.services.ai_service import AIService
        
        print("\n📝 Creating AIService with Groq model...")
        ai_service = AIService(model_name="groq:llama-3.3-70b-versatile")
        
        prompt = "Explain AI in 2 sentences."
        print(f"Prompt: {prompt}")
        
        result = await ai_service.generate_response(prompt)
        
        if result.get("error"):
            print(f"⚠️  Error: {result['error']}")
            return False
        
        response = result.get("response", "")
        print(f"\n✅ Response ({len(response)} chars):\n{response[:200]}...")
        print(f"Provider: {result.get('provider')}")
        print(f"Processing time: {result.get('processing_time', 0):.2f}s")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("\n🚀 Groq Integration Test Suite\n")
    
    results = []
    
    # Test 1: GroqClient
    results.append(await test_groq_client())
    
    # Test 2: AIService with Groq
    results.append(await test_ai_service_groq())
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"✅ Passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n⚠️  Some tests failed")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
