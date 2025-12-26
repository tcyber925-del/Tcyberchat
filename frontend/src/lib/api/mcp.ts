import { fetchJsonWithRetries } from '@/lib/api/request';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface McpHealthResponse {
  ok: boolean;
  ai?: {
    available_models: number;
    models?: Array<any>;
  };
  error?: string;
}

export async function getMcpHealth(signal?: AbortSignal): Promise<McpHealthResponse> {
  try {
    const res = await fetchJsonWithRetries<McpHealthResponse>(`${API_BASE_URL}/api/integrations/mcp/health`, { timeoutMs: 15000, retries: 0, signal });
    return res;
  } catch (err) {
    console.error('Failed to fetch MCP health:', err);
    return { ok: false, error: (err as any)?.message || 'failed' };
  }
}

export async function initMcpModel(model?: string): Promise<{ ok: boolean; started?: boolean; error?: string }> {
  try {
    const body = model ? { model } : {};
    const res = await fetchJsonWithRetries<{ ok: boolean; started?: boolean; error?: string }>(`${API_BASE_URL}/api/integrations/mcp/init-model`, { timeoutMs: 3000, retries: 0, method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    return res;
  } catch (err) {
    console.error('Failed to init MCP model:', err);
    return { ok: false, error: (err as any)?.message || 'failed' };
  }
}
