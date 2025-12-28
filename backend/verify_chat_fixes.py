import httpx
import json
import asyncio

async def test_non_streaming():
    url = "http://localhost:8000/api/chat/"
    payload = {
        "message": "say hi",
        "model": "llama3.2:1b"
    }
    
    print(f"\n--- Testing NON-STREAMING {url} with model {payload['model']} ---")
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(url, json=payload)
            if response.status_code != 200:
                print(f"Error: Status {response.status_code}")
                print(response.text)
                return
            
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            if data.get("content") or data.get("response"):
                print("Success: Received content/response!")
            else:
                print("FAILED: Response empty!")
    except Exception as e:
        print(f"Non-streaming test failed: {e}")

async def test_streaming():
    url = "http://localhost:8000/api/chat/stream"
    payload = {
        "message": "say hi",
        "model": "llama3.2:1b"
    }
    
    print(f"\n--- Testing STREAMING {url} with model {payload['model']} ---")
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream("POST", url, json=payload) as response:
                if response.status_code != 200:
                    print(f"Error: Status {response.status_code}")
                    print(await response.aread())
                    return
                
                print("Connected! Reading stream...")
                received_chunk = False
                async for line in response.aiter_lines():
                    if line.strip():
                        print(f"Stream: {line}")
                        if "event: chunk" in line:
                            received_chunk = True
                        if "event: message" in line:
                            print("Success: Received message event!")
                            break
                if not received_chunk:
                     print("FAILED: No chunks received!")
    except Exception as e:
        print(f"Streaming test failed: {e}")

async def main():
    # Wait for backend to be fully up
    print("Waiting for backend to be ready...")
    await asyncio.sleep(5) 
    await test_non_streaming()
    await test_streaming()

if __name__ == "__main__":
    asyncio.run(main())
