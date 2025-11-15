"""
CLI to run the local MCP server (stdio or websocket) using the official SDK.

Usage examples:
  python -m scripts.mcp_server --mode stdio
  python -m scripts.mcp_server --mode ws --host 0.0.0.0 --port 8765 --token "${TOKEN}"
"""
from __future__ import annotations

import argparse
import asyncio

from src.mcp.server import run_stdio, run_ws


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run local MCP server")
    p.add_argument("--mode", choices=["stdio", "ws"], default="stdio")
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--token", default=None)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    if args.mode == "stdio":
        asyncio.run(run_stdio())
    else:
        asyncio.run(run_ws(host=args.host, port=args.port, token=args.token))


if __name__ == "__main__":
    main()
