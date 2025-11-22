import { getAvailableModels } from '@/lib/api/models';

describe('models API caching and in-progress reuse', () => {
  const originalFetch = global.fetch;

  afterEach(() => {
    global.fetch = originalFetch;
    jest.restoreAllMocks();
  });

  test('concurrent callers share one in-flight request', async () => {
    // Make a fetch that resolves after a short delay
    let calls = 0;
    global.fetch = jest.fn().mockImplementation(() => {
      calls += 1;
      return new Promise(resolve => setTimeout(() => resolve({ ok: true, json: () => Promise.resolve([{ name: 'm1', provider: 'ollama', size: 0, modified_at: 'now' }]) } as any), 50));
    });

    const [a, b] = await Promise.all([getAvailableModels(), getAvailableModels()]);
    expect(a).toEqual(b);
    expect(calls).toBe(1);
  });

  test('cached result is used for subsequent calls', async () => {
    let calls = 0;
    global.fetch = jest.fn().mockImplementation(() => {
      calls += 1;
      return Promise.resolve({ ok: true, json: () => Promise.resolve([{ name: 'm2', provider: 'openrouter', size: 0, modified_at: 'now' }]) } as any);
    });

    const first = await getAvailableModels({ forceRefresh: true });
    const second = await getAvailableModels();
    expect(first).toEqual(second);
    expect(calls).toBe(1);
  });
});
