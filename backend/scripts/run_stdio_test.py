#!/usr/bin/env python3
"""
Run a standalone stdio connection test to the mock MCP server and print results.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))


async def main():
    try:
        from services.mcp.clients.stdio_client import StdioMcpConnection
    except Exception as e:
        print("Import error:", e)
        return

    script = Path(__file__).resolve().parents[1] / 'scripts' / 'mock_stdio_mcp_server.py'
    conn = StdioMcpConnection('python', args=[str(script)])
    try:
        await conn.start()
        tools = await conn.list_tools()
        print('tools=', tools)
        await conn.stop()
    except Exception as e:
        print('Connection error:', repr(e))


if __name__ == '__main__':
    asyncio.run(main())
