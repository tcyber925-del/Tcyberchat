import asyncio
import traceback

from backend.src.services.mcp.clients.stdio_client import StdioMcpConnection

async def main():
    conn = StdioMcpConnection('python', args=['-u','backend/scripts/mock_stdio_mcp_server.py'], env={})
    try:
        await conn.start()
        print('Started OK')
        tools = await conn.list_tools()
        print('Tools:', tools)
        await conn.stop()
    except Exception as e:
        print('EXCEPTION:', repr(e))
        print('str(e):', str(e))
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(main())
