export interface FetchOptions extends RequestInit {
  timeoutMs?: number;
  retries?: number;
}

function sleep(ms: number) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

export async function fetchWithTimeoutAndRetry(url: string, options: FetchOptions = {}) {
  const { timeoutMs = 60000, retries = 1, signal: outerSignal, ...fetchOpts } = options;

  let attempt = 0;
  let lastError: any = null;

  while (attempt <= retries) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    // If an outer signal is provided, abort our internal controller when it fires.
    const onOuterAbort = () => controller.abort();
    if (outerSignal) {
      if (outerSignal.aborted) {
        clearTimeout(timeoutId);
        throw new DOMException('Aborted', 'AbortError');
      }
      outerSignal.addEventListener('abort', onOuterAbort);
    }

    try {
      // Use the composed signal so either outer or timeout can cancel.
      const res = await fetch(url, { ...fetchOpts, signal: controller.signal });
      clearTimeout(timeoutId);
      if (outerSignal) outerSignal.removeEventListener('abort', onOuterAbort);

      if (!res.ok) {
        const errText = await res.text().catch(() => res.statusText || '');
        throw new Error(`HTTP ${res.status}: ${errText}`);
      }
      return res;
    } catch (err) {
      lastError = err;
      // If aborted by outer signal, rethrow immediately
      if (outerSignal && (outerSignal as any).aborted) {
        throw err;
      }
      // If it's an AbortError due to timeout and we have retries, continue
      attempt += 1;
      if (attempt > retries) {
        throw err;
      }
      // Exponential backoff before retrying
      await sleep(200 * Math.pow(2, attempt - 1));
    } finally {
      try { clearTimeout(undefined as any); } catch { }
    }
  }

  throw lastError;
}

export async function fetchJsonWithRetries<T = any>(url: string, options: FetchOptions = {}): Promise<T> {
  const res = await fetchWithTimeoutAndRetry(url, options);
  return res.json() as Promise<T>;
}
