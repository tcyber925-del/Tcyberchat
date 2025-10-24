import time
import requests

URL = "http://127.0.0.1:3001/chat/stream"
PAYLOAD = {"message": "Hello from SSE client", "model": "dummy"}

# Wait for server to be ready
for attempt in range(10):
    try:
        r = requests.get('http://127.0.0.1:3001/health', timeout=2)
        if r.status_code == 200:
            print('Server ready')
            break
    except Exception as e:
        print('Server not ready, retrying...', attempt)
        time.sleep(0.5)
else:
    print('Server did not become ready; exiting')
    raise SystemExit(1)

print('Starting SSE POST to', URL)
with requests.post(URL, json=PAYLOAD, stream=True, timeout=60) as r:
    print('Response status:', r.status_code)
    if r.status_code != 200:
        try:
            print('Response body:', r.text)
        except Exception:
            pass
    else:
        # Print up to 200 lines or until timeout
        try:
            for i, line in enumerate(r.iter_lines(decode_unicode=True)):
                if not line:
                    continue
                print('LINE:', line)
                if i > 200:
                    break
        except Exception as e:
            print('Error while streaming:', e)

print('Client finished')
