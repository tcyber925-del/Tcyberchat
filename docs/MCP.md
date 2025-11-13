# MCP integration (preview)

This project integrates the Model Context Protocol (MCP) in two roles:

- MultiMcpClient (consumer): connect to multiple MCP servers (local stdio and remote WSS) to fetch docs/tools/resources.
- MCP Server (producer): expose the chatbot’s tools (web_search, deep_research, fetch_url) to MCP clients. (coming next)

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
- `POST /api/integrations/mcp/fetch-doc` — fetch a doc via MCP (scaffold; placeholder direct HTTP until SDK wired)

Body example for fetch-doc:
```
{
  "url": "https://modelcontextprotocol.io/docs/develop/build-client",
  "server": "auto",
  "preferredTags": ["docs"]
}
```

Response includes sanitized `content` and a normalized `citation` object compatible with the UI’s Sources panel.

## Server (skeleton)

A minimal MCP server skeleton is provided at `backend/src/mcp/server.py` with stubs for:
- `tool_web_search`
- `tool_deep_research`
- `run_stdio()` / `run_ws()`

Hook these up using the official MCP SDK to expose tools with JSON Schemas and streaming.

## Notes

- This is a scaffold. Actual MCP SDK calls (handshake, list_tools, call_tool with streaming) will replace the HTTP placeholder soon.
- Security: store tokens server-side only; never expose to frontend. Enforce SSRF protection when incorporating fetched content.
- Use MCP Inspector to validate your own MCP server once implemented.
