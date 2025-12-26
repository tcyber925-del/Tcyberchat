import asyncio
import traceback

async def main():
    try:
        from mcp.client.session import ClientSession
        from mcp.client.stdio import stdio_client, StdioServerParameters
        params = StdioServerParameters(command='python', args=['-u','backend/scripts/mock_stdio_mcp_server.py'], env=None)
        ctx = stdio_client(params)
        read, write = await ctx.__aenter__()
        from mcp.client.session import ClientSession
        sess = ClientSession(read, write)
        print('Created ClientSession, calling initialize...')
        await sess.initialize()
        print('Session initialized successfully')
        await ctx.__aexit__(None, None, None)
    except Exception as e:
        print('EXC TYPE:', type(e))
        print('EXC REPR:', repr(e))
        print('EXC STR:', str(e))
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(main())
