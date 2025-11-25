import json
import urllib.request
import urllib.error
import sys

url = 'http://localhost:8000/api/integrations/mcp/test-connection'
import os

# Prefer to use the same Python executable that's running this script
python_exe = os.environ.get('PYTHON_EXE') or sys.executable
# Build an absolute path to the mock stdio server script so the API
# receives a resolvable path regardless of the server's cwd handling.
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
mock_script = os.path.join(repo_root, 'backend', 'scripts', 'mock_stdio_mcp_server.py')
payload = {
    "transport": "stdio",
    "command": python_exe,
    "args": ["-u", mock_script],
    "env": {}
}

data = json.dumps(payload).encode('utf-8')
req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
max_retries = 5
for attempt in range(1, max_retries + 1):
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            status = resp.getcode()
            headers = dict(resp.getheaders())
            body = resp.read().decode('utf-8')
            print('STATUS:', status)
            print('HEADERS:', json.dumps(headers, indent=2))
            try:
                parsed = json.loads(body)
                print('BODY (json):')
                print(json.dumps(parsed, indent=2))
            except Exception:
                print('BODY (raw):')
                print(body)
            break
    except urllib.error.HTTPError as e:
        print('HTTP ERROR:', e.code)
        try:
            print(e.read().decode('utf-8'))
        except Exception:
            pass
        break
    except Exception as e:
        msg = str(e)
        # Retry on connection-refused / refused errors which can happen
        # when the backend process is starting up or restarting.
        if 'Connection refused' in msg or 'No connection could be made' in msg:
            print(f'Attempt {attempt}/{max_retries}: connection refused, retrying...')
            if attempt == max_retries:
                print('ERROR:', e)
                sys.exit(1)
            import time

            time.sleep(1)
            continue
        print('ERROR:', e)
        sys.exit(1)
