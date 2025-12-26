import os
import sys
import asyncio

# Ensure runner-only mode
os.environ['MCP_STDIO_RUNNER_ONLY'] = '1'
os.environ['MCP_STDIO_WIRE_LOG'] = '1'

# Point to the mock stdio server script
PY = sys.executable
MOCK = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend', 'scripts', 'mock_stdio_mcp_server.py'))

# Add repo root to sys.path so imports work
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

async def main():
    try:
        from backend.src.services.mcp.clients.stdio_client import StdioMcpConnection
    except Exception as e:
        print('IMPORT_FAILED', e)
        raise

    conn = StdioMcpConnection(command=PY, args=['-u', MOCK], env={})
    try:
        print('STARTING')
        await conn.start()
        print('START_OK')
    except Exception as e:
        print('START_FAILED', repr(e))
        import traceback
        traceback.print_exc()
        raise

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception:
        sys.exit(2)
    sys.exit(0)
