#!/usr/bin/env python3
"""
Minimal stdio MCP server mock for local testing.

Behaviors implemented:
- Responds to `initialize` request with a simple capability set.
- Responds to `tools/list` with a single `http.get` tool.
- Responds to `tools/call` for `http.get` by returning a small content block
  and `structuredContent` JSON object.

This script reads JSON-RPC messages line-delimited from stdin and writes
JSON-RPC responses to stdout (one JSON object per line).
"""
from __future__ import annotations

import json
import sys
import os
import time
from typing import Any, Dict


LATEST_PROTOCOL = "2024-11-05"


def send_response(resp: Dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(resp, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def handle_initialize(req: Dict[str, Any]) -> None:
    resp = {
        "jsonrpc": "2.0",
        "id": req.get("id"),
        "result": {
            "protocolVersion": LATEST_PROTOCOL,
            "capabilities": {
                "tools": {"listChanged": False},
            },
            "serverInfo": {"name": "mock-stdio-server", "version": "0.1.0"},
        },
    }
    send_response(resp)


def handle_tools_list(req: Dict[str, Any]) -> None:
    resp = {
        "jsonrpc": "2.0",
        "id": req.get("id"),
        "result": {
            "tools": [
                {
                    "name": "http.get",
                    "description": "Mock HTTP GET",
                    "inputSchema": None,
                }
            ]
        },
    }
    send_response(resp)


def handle_tools_call(req: Dict[str, Any]) -> None:
    params = req.get("params") or {}
    name = params.get("name") if isinstance(params, dict) else None
    arguments = params.get("arguments") if isinstance(params, dict) else {}

    # Compose a simple CallToolResult-like object
    if name == "http.get":
        url = arguments.get("url") if isinstance(arguments, dict) else None
        text = f"Mocked HTTP GET response for {url or 'unknown URL'}"
        result = {
            "content": [{"text": text}],
            "structuredContent": {"type": "mock_http", "url": url, "length": len(text)},
            "isError": False,
        }
    else:
        result = {"content": [{"text": f"Called tool {name}"}], "isError": False}

    resp = {"jsonrpc": "2.0", "id": req.get("id"), "result": result}
    send_response(resp)


def main() -> None:
    # write a startup ping to a log file so parent processes can observe
    try:
        os.makedirs(os.path.join(os.getcwd(), 'logs'), exist_ok=True)
        with open(os.path.join(os.getcwd(), 'logs', 'mock_stdio.log'), 'a', encoding='utf-8') as lf:
            lf.write(f"mock_stdio starting pid={os.getpid()} ts={time.time()}\n")
            lf.flush()
    except Exception:
        pass

    # Read line-delimited JSON messages from stdin
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except Exception:
            # ignore invalid JSON
            continue

        # JSON-RPC request
        method = msg.get("method")
        if method == "initialize":
            handle_initialize(msg)
        elif method == "tools/list":
            handle_tools_list(msg)
        elif method == "tools/call":
            handle_tools_call(msg)
        else:
            # Generic success response
            resp = {"jsonrpc": "2.0", "id": msg.get("id"), "result": {"ok": True}}
            send_response(resp)


if __name__ == "__main__":
    main()
