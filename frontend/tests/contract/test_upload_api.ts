import { describe, it, expect } from '@jest/globals';

describe('Upload API Contract', () => {
  it('should successfully upload a document when backend is running', async () => {
    const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001';
    const formData = new FormData();
    const file = new File(['test content'], 'test.txt', { type: 'text/plain' });
    formData.append('file', file);

    const response = await fetch(`${API_URL}/documents/upload`, {
      method: 'POST',
      body: formData,
    });

    // Expecting success as the backend is running
    expect(response.ok).toBe(true);
    const data = await response.json();
    expect(data).toHaveProperty('documentId');
    expect(data).toHaveProperty('filename', 'test.txt');
  });

  it('should successfully list documents when backend is running', async () => {
    const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001';
    const response = await fetch(`${API_URL}/documents/`);

    // Expecting success as the backend is running
    expect(response.ok).toBe(true);
    const data = await response.json();
    expect(Array.isArray(data)).toBe(true);
  });
});