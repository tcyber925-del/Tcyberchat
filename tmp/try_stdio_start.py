import asyncio
import sys

async def main():
    try:
        from mcp.client.stdio import stdio_client, StdioServerParameters
        server_params = StdioServerParameters(command=sys.executable, args=['-u','backend/scripts/mock_stdio_mcp_server.py'], env=None)
        ctx = stdio_client(server_params)
        print('Created context:', ctx)
        read, write = await ctx.__aenter__()
        print('Acquired read/write')
        await ctx.__aexit__(None, None, None)
        print('Exited')
    except Exception as e:
        import traceback
        print('EXCEPTION:', repr(e))
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
