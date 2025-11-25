const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://0.0.0.0:8000';
import { fetchJsonWithRetries } from '@/lib/api/request';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface AvailableModel {
  name: string;
  size: number;
  modified_at: string;
  provider: string;
}

// Simple in-memory cache with TTL
let cachedModels: AvailableModel[] | null = null;
let cacheTimestamp = 0;
const CACHE_TTL_MS = 2 * 60 * 1000; // 2 minutes

// Reuse an in-progress promise so multiple callers share the same request
let inProgressPromise: Promise<AvailableModel[]> | null = null;

export async function getAvailableModels(opts?: { forceRefresh?: boolean; signal?: AbortSignal }): Promise<AvailableModel[]> {
  try {
    const now = Date.now();
    if (!opts?.forceRefresh && cachedModels && now - cacheTimestamp < CACHE_TTL_MS) {
      return cachedModels;
    }

    if (inProgressPromise && !opts?.forceRefresh) {
      return inProgressPromise;
    }

    const url = `${API_BASE_URL}/api/v1/models`;
    inProgressPromise = (async () => {
      try {
        const models = await fetchJsonWithRetries<AvailableModel[] | { models: AvailableModel[] }>(url, { timeoutMs: 8000, retries: 1, signal: opts?.signal });
        const resolved = Array.isArray(models) ? models : (models && Array.isArray((models as any).models) ? (models as any).models : []);
        cachedModels = resolved;
        cacheTimestamp = Date.now();
        return resolved;
      } finally {
        inProgressPromise = null;
      }
    })();

    return inProgressPromise;
  } catch (error) {
    console.error('Failed to fetch available models:', error);
    // On error, return cached models if available to avoid breaking UI
    if (cachedModels) return cachedModels;
    return [];
  }
}
