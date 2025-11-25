#!/usr/bin/env python3
"""
Run an MCP stdio client in a separate process and print JSON result to stdout.
Reads a JSON payload from stdin with keys: command, args, env, timeout
"""
import sys
import os
import json
import asyncio
import time
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

async def run_payload(payload):
    # Ensure backend package importable
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

    try:
        from src.services.mcp.clients.stdio_client import StdioMcpConnection
    except Exception as e:
        return {"ok": False, "error": f"import error: {e}"}

    cmd = payload.get("command")
    args = payload.get("args") or []
    env = payload.get("env") or {}
    timeout = int(payload.get("timeout") or 30)

    conn = StdioMcpConnection(cmd, args=args, env=env)
    out = {"ok": False}
    try:
        # Retry startup a few times because stdio child startup can be
        # timing-sensitive on some platforms. This is a pragmatic
        # reliability improvement for local dev/test workflows.
        attempts = int(payload.get("attempts") or 3)
        last_exc = None
        for attempt in range(1, attempts + 1):
            try:
                await asyncio.wait_for(conn.start(), timeout=timeout)
                break
            except Exception as e:
                last_exc = e
                try:
                    import logging

                    logging.getLogger().warning("Attempt %d/%d: start failed: %s", attempt, attempts, e)
                except Exception:
                    pass
                if attempt < attempts:
                    await asyncio.sleep(0.5)
        else:
            # all attempts failed
            raise last_exc

        tools = await conn.list_tools()
        out = {"ok": True, "tools": tools}
        try:
            await conn.stop()
        except Exception:
            pass
    except Exception as e:
        tb = ""
        try:
            import traceback

            tb = traceback.format_exc()
        except Exception:
            tb = str(e)
        out = {"ok": False, "error": str(e), "traceback": tb}
        try:
            await conn.stop()
        except Exception:
            pass
    return out

def main():
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw)
    except Exception as e:
        print(json.dumps({"ok": False, "error": f"bad input: {e}"}))
        sys.exit(1)

    try:
        res = asyncio.run(run_payload(payload))
        print(json.dumps(res))
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}))


if __name__ == '__main__':
    main()
