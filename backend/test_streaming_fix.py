import httpx
import json

async def test_stream():
    url = "http://localhost:8000/api/chat/stream"
    payload = {
        "message": "say hi",
        "model": "llama3.2:1b"
    }
    
    print(f"Testing {url} with model {payload['model']}...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream("POST", url, json=payload) as response:
                if response.status_code != 200:
                    print(f"Error: Status {response.status_code}")
                    print(await response.aread())
                    return
                
                print("Connected! Reading stream...")
                async for line in response.aiter_lines():
                    if line.strip():
                        print(f"Stream: {line}")
                        if "event: message" in line:
                            print("Success: Received message event!")
                            break
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_stream())
