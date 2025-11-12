import { describe, it, expect } from '@jest/globals';

describe('Export/Import API Contract', () => {
  it('should fail to export data if backend is not running', async () => {
    const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001';
    const response = await fetch(`${API_URL}/data-management/export`, {
      method: 'POST',
    });

    // Expecting a failure or a non-2xx status code as the backend is not running
    expect(response.ok).toBe(false);
    expect(response.status).toBeGreaterThanOrEqual(400);
  });

  it('should fail to import data if backend is not running', async () => {
    const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001';
    const formData = new FormData();
    formData.append('file', new Blob(['{}'], { type: 'application/json' }), 'data.json');

    const response = await fetch(`${API_URL}/data-management/import`, {
      method: 'POST',
      body: formData,
    });

    // Expecting a failure or a non-2xx status code as the backend is not running
    expect(response.ok).toBe(false);
    expect(response.status).toBeGreaterThanOrEqual(400);
  });
});
