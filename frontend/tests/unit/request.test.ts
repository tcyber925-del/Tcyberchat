import { fetchJsonWithRetries } from '@/lib/api/request';

describe('fetchWithTimeoutAndRetry / fetchJsonWithRetries', () => {
  const originalFetch = global.fetch;

  afterEach(() => {
    global.fetch = originalFetch;
    jest.restoreAllMocks();
  });

  test('retries on transient failure and returns JSON', async () => {
    const mockJson = { hello: 'world' };

    // First call rejects, second call resolves
    let call = 0;
    global.fetch = jest.fn().mockImplementation(() => {
      call += 1;
      if (call === 1) {
        return Promise.reject(new Error('network error'));
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve(mockJson) } as any);
    });

    const res = await fetchJsonWithRetries('http://example.test/foo', { timeoutMs: 1000, retries: 1 });
    expect(res).toEqual(mockJson);
    expect((global.fetch as jest.Mock).mock.calls.length).toBeGreaterThanOrEqual(2);
  });

  test('throws when retries exhausted', async () => {
    global.fetch = jest.fn().mockImplementation(() => Promise.reject(new Error('network still down')));

    await expect(fetchJsonWithRetries('http://example.test/bar', { timeoutMs: 200, retries: 1 })).rejects.toThrow();
  });
});
