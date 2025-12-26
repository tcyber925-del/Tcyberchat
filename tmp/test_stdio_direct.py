import asyncio
from backend.src.services.mcp.clients.stdio_client import StdioMcpConnection

async def main():
    conn = StdioMcpConnection('python', args=['-u','backend/scripts/mock_stdio_mcp_server.py'], env={})
    try:
        await conn.start()
        tools = await conn.list_tools()
        print('TOOLS:', tools)
        await conn.stop()
    except Exception as e:
        import traceback
        print('EXCEPTION:', repr(e))
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(main())
