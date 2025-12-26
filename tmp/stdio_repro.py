#!/usr/bin/env python3
"""
Repro script to start StdioMcpConnection outside FastAPI/uvicorn to reproduce anyio/asyncio issues.
Writes a diagnostic JSON to backend/logs/stdio_repro_<ts>.json and prints output to stdout.
"""
import os
import sys
import asyncio
import time
import json
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Ensure backend package is importable
backend_path = os.path.join(repo_root, 'backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Import the connection class
try:
    from src.services.mcp.clients.stdio_client import StdioMcpConnection
except Exception as e:
    print(f"Failed to import StdioMcpConnection: {e}")
    raise

async def run_once():
    ts = int(time.time())
    diag_file = os.path.join(repo_root, 'backend', 'logs', f'stdio_repro_{ts}.json')

    python_exe = sys.executable
    mock_script = os.path.join(repo_root, 'backend', 'scripts', 'mock_stdio_mcp_server.py')
    cmd = python_exe
    args = ['-u', mock_script]
    env = {}

    conn = StdioMcpConnection(cmd, args=args, env=env)
    out = {"ok": False}
    try:
        logging.info('Starting StdioMcpConnection (repro) with command=%s args=%s cwd=%s', cmd, args, os.getcwd())
        await asyncio.wait_for(conn.start(), timeout=30)
        logging.info('Started connection, listing tools...')
        tools = await conn.list_tools()
        out = {"ok": True, "tools": tools}
        await conn.stop()
    except Exception as e:
        tb = ''.join(logging.Formatter().formatException(sys.exc_info()))
        out = {"ok": False, "error": str(e), "traceback": tb}
        try:
            # attempt to stop
            await conn.stop()
        except Exception:
            pass
    try:
        os.makedirs(os.path.join(repo_root, 'backend', 'logs'), exist_ok=True)
        with open(diag_file, 'w', encoding='utf-8') as f:
            json.dump(out, f, indent=2)
        print('Wrote diag file:', diag_file)
    except Exception as e:
        print('Failed to write diag file:', e)
    print(json.dumps(out, indent=2))

if __name__ == '__main__':
    asyncio.run(run_once())
