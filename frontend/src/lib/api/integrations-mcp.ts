export type McpTool = {
  name: string;
  description?: string;
};

export type McpServer = {
  id: string;
  transport: 'wss' | 'stdio' | string;
  enabled: boolean;
  tags?: string[];
  connected?: boolean;
  healthy?: boolean;
  tools?: string[];
  last_error?: string | null;
  cached_capabilities?: any;
};

export type McpServerUpsert = {
  id: string;
  transport: 'wss' | 'stdio';
  enabled?: boolean;
  // wss fields
  url?: string;
  headers?: Record<string, string>;
  // stdio fields
  command?: string;
  args?: string[];
  tags?: string[];
  timeouts?: { connectMs?: number; readMs?: number };
};

export type McpFetchDocRequest = {
  url: string;
  server?: string; // 'auto' or specific id
  tool?: string; // default 'http.get'
  preferredTags?: string[];
};

export type McpFetchDocResponse = {
  url?: string;
  content?: string;
  suspicious?: boolean;
  serverId?: string;
  tool?: string;
  citation?: {
    title?: string;
    url?: string;
    snippet?: string;
    source?: string;
    source_type?: string;
  };
  error?: string;
};

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers || {}),
    },
  });
  if (!res.ok) {
    let detail = '';
    try {
      const j = await res.json();
      detail = j?.detail || j?.error || res.statusText;
    } catch {
      detail = res.statusText;
    }
    throw new Error(`HTTP ${res.status} ${detail}`);
  }
  return res.json();
}

export async function listMcpServers(): Promise<{ servers: McpServer[] }> {
  return http('/api/integrations/mcp/servers');
}

export async function upsertMcpServer(server: McpServerUpsert): Promise<{ ok: boolean }> {
  return http('/api/integrations/mcp/servers', {
    method: 'POST',
    body: JSON.stringify(server),
  });
}

export async function disableMcpServer(serverId: string): Promise<{ ok: boolean }> {
  return http(`/api/integrations/mcp/servers/${encodeURIComponent(serverId)}`, {
    method: 'DELETE',
  });
}

export async function warmConnect(): Promise<{ ok: boolean; servers: McpServer[] }> {
  return http('/api/integrations/mcp/warm-connect', { method: 'POST' });
}

export async function fetchDocViaMcp(req: McpFetchDocRequest): Promise<McpFetchDocResponse> {
  return http('/api/integrations/mcp/fetch-doc', {
    method: 'POST',
    body: JSON.stringify(req),
  });
}
