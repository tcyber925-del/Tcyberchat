import asyncio
import sys
import os

# Ensure backend src is importable
here = os.path.dirname(os.path.dirname(__file__))
backend_src = os.path.join(here, 'backend')
src_path = os.path.join(backend_src)
if src_path not in sys.path:
    sys.path.insert(0, src_path)

async def main():
    try:
        from src.services.mcp.clients.stdio_client import StdioMcpConnection
        python_exe = sys.executable
        cmd = python_exe
        args = ['-u', 'backend/scripts/mock_stdio_mcp_server.py']
        conn = StdioMcpConnection(cmd, args=args, env={})
        print('Created StdioMcpConnection')
        await conn.start()
        print('Started connection successfully')
        tools = await conn.list_tools()
        print('Tools:', tools)
        await conn.stop()
    except Exception as e:
        import traceback
        print('EXCEPTION:', repr(e))
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
