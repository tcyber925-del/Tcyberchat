# MCP integration (preview)

This project integrates the Model Context Protocol (MCP) in two roles:

- MultiMcpClient (consumer): connect to multiple MCP servers (local stdio and remote WSS) to fetch docs/tools/resources.
- MCP Server (producer): expose the chatbot’s tools (web_search, deep_research, fetch_url) to MCP clients. (SDK-wired)

## Configuration

Set `MCP_MULTI` to a JSON object listing servers. Example (PowerShell JSON):

```
{
  "servers": [
    {
      "id": "context7",
      "transport": "wss",
      "url": "wss://context7.example.com/mcp",
      "headers": {"Authorization": "Bearer {{CONTEXT7_MCP_TOKEN}}"},
      "tags": ["docs", "official"],
      "enabled": true,
      "timeouts": {"connectMs": 3000, "readMs": 15000}
    },
    {
      "id": "local-stdio-tools",
      "transport": "stdio",
      "command": "tools/mcp-local.exe",
      "args": [],
      "tags": ["local"],
      "enabled": true
    }
  ]
}
```

Redis keys (optional):
- `mcp:server:capabilities:{id}`: cached tools/resources summary (planned)
- `mcpdoc:{serverId}:{url}`: cached fetched content (TTL 24h)

Rate limits / circuit breaker (env):
- `MCP_CB_THRESHOLD` (default 3), `MCP_CB_COOLDOWN` (default 60)
- `MCP_DOC_TTL` (default 86400 seconds)

## API

- `GET /api/integrations/mcp/servers` — list configured servers and discovery state
- `POST /api/integrations/mcp/servers` — upsert one server config (JSON body)
- `DELETE /api/integrations/mcp/servers/{server_id}` — disable server
- `POST /api/integrations/mcp/warm-connect` — connect and discover tools (scaffold)
- `POST /api/integrations/mcp/fetch-doc` — fetch a doc via MCP (uses SDK when a server with `http.get` is connected; falls back to direct HTTP if none)

Body example for fetch-doc:
```
{
  "url": "https://modelcontextprotocol.io/docs/develop/build-client",
  "server": "auto",
  "preferredTags": ["docs"]
}
```

Response includes sanitized `content` and a normalized `citation` object compatible with the UI’s Sources panel.

## Server

A minimal MCP server is provided at `backend/src/mcp/server.py` and uses the official SDK (FastMCP). Tools exposed: `web_search`, `deep_research`. JSON Schemas are included.

### Running the server

- Stdio mode:
  - python -m scripts.mcp_server --mode stdio
- WebSocket mode:
  - python -m scripts.mcp_server --mode ws --host 0.0.0.0 --port 8765 --token "${TOKEN}"

### Validating with MCP Inspector

1) Install the official MCP packages and Inspector.
2) Run the server in stdio or ws mode (see env below).
3) Open MCP Inspector and connect to the server.
4) Verify `list_tools` shows `web_search` and `deep_research` with the schemas.
5) Invoke tools and ensure responses match the schemas.

### Env / running

- Stdio mode (example):
  - Ensure SDK is installed
  - Run a small launcher (custom) that calls `backend.src.mcp.server.run_stdio()`
- WS mode:
  - Set a token and call `run_ws(host, port, token)` via a launcher

When wiring the SDK, validate with MCP Inspector and add JSON Schemas to any additional tools.

## Notes

- SDK-backed list_tools and call_tool are wired for ws/stdio clients; http.get has a safe HTTP fallback when no server is available.
- Security: store tokens server-side only; never expose to frontend. Enforce SSRF protection when incorporating fetched content.
- Use MCP Inspector to validate your own MCP server.
