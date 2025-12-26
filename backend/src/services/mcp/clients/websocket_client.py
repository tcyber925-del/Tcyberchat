"""
Minimal WebSocket client transport for MCP when the SDK doesn't provide one.

This adapter uses the `websockets` library to connect to a WebSocket MCP server
and bridges JSON RPC messages to AnyIO memory streams expected by `mcp.client.session.ClientSession`.
"""
from __future__ import annotations

import json
from contextlib import asynccontextmanager
from typing import Any, Dict

import anyio
from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream

try:
    import websockets
except Exception:  # pragma: no cover - runtime dependency may be missing in some dev envs
    websockets = None

import mcp.types as types  # rely on installed mcp package for message parsing


@asynccontextmanager
async def websocket_client(url: str, headers: Dict[str, Any] | None = None, timeout: float = 5):
    if websockets is None:
        raise RuntimeError("'websockets' library is not installed; cannot create websocket client")

    read_stream: MemoryObjectReceiveStream[types.JSONRPCMessage | Exception]
    read_stream_writer: MemoryObjectSendStream[types.JSONRPCMessage | Exception]

    write_stream: MemoryObjectSendStream[types.JSONRPCMessage]
    write_stream_reader: MemoryObjectReceiveStream[types.JSONRPCMessage]

    read_stream_writer, read_stream = anyio.create_memory_object_stream(0)
    write_stream, write_stream_reader = anyio.create_memory_object_stream(0)

    # Connect using websockets (text frames containing JSON)
    conn = await websockets.connect(url, extra_headers=headers or {}, subprotocols=["mcp"])

    async def ws_reader():
        try:
            async with read_stream_writer:
                async for raw in conn:
                    try:
                        # Parse JSON into MCP JSONRPCMessage
                        msg = types.JSONRPCMessage.model_validate_json(raw)
                    except Exception as exc:
                        await read_stream_writer.send(exc)
                        continue
                    await read_stream_writer.send(msg)
        except Exception as exc:
            try:
                await read_stream_writer.send(exc)
            except Exception:
                pass

    async def ws_writer():
        try:
            async with write_stream_reader:
                async for message in write_stream_reader:
                    # message is a pydantic model; send its JSON representation
                    payload = message.model_dump_json(by_alias=True, exclude_none=True)
                    await conn.send(payload)
        except Exception:
            pass

    async with anyio.create_task_group() as tg:
        tg.start_soon(ws_reader)
        tg.start_soon(ws_writer)
        try:
            yield read_stream, write_stream
        finally:
            try:
                await conn.close()
            except Exception:
                pass
