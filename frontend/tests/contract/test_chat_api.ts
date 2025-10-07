import { describe, it, expect } from '@jest/globals';

describe('Chat API Contract', () => {
  it('should fail to send a message if backend is not running', async () => {
    const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001';
    const response = await fetch(`${API_URL}/chat/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message: 'Hello' }),
    });

    // Expecting a failure or a non-2xx status code as the backend is not running
    expect(response.ok).toBe(false);
    expect(response.status).toBeGreaterThanOrEqual(400);
  });

  it('should fail to fetch conversations if backend is not running', async () => {
    const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001';
    const response = await fetch(`${API_URL}/chat/conversations`);

    // Expecting a failure or a non-2xx status code as the backend is not running
    expect(response.ok).toBe(false);
    expect(response.status).toBeGreaterThanOrEqual(400);
  });
});