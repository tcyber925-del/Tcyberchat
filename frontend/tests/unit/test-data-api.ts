import { exportData, importData } from '../../src/lib/api/data';

// Mock fetch globally
const mockFetch = jest.fn();
global.fetch = mockFetch;

describe('Data Management API', () => {
  const API_URL = 'http://localhost:3001';

  beforeEach(() => {
    jest.clearAllMocks();
    process.env.NEXT_PUBLIC_API_URL = API_URL;
  });

  afterEach(() => {
    delete process.env.NEXT_PUBLIC_API_URL;
  });

  describe('exportData', () => {
    it('should successfully export data and return blob', async () => {
      const mockBlob = new Blob(['test data'], { type: 'application/zip' });
      mockFetch.mockResolvedValueOnce({
        ok: true,
        blob: jest.fn().mockResolvedValue(mockBlob),
      });

      const result = await exportData();

      expect(mockFetch).toHaveBeenCalledWith(`${API_URL}/data-management/export`, {
        method: 'POST',
      });
      expect(result).toBe(mockBlob);
    });

    it('should throw error when export fails', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        statusText: 'Internal Server Error',
      });

      await expect(exportData()).rejects.toThrow('Error exporting data: Internal Server Error');
    });

    it('should use default API URL when NEXT_PUBLIC_API_URL is not set', async () => {
      delete process.env.NEXT_PUBLIC_API_URL;

      const mockBlob = new Blob(['test data'], { type: 'application/zip' });
      mockFetch.mockResolvedValueOnce({
        ok: true,
        blob: jest.fn().mockResolvedValue(mockBlob),
      });

      await exportData();

      expect(mockFetch).toHaveBeenCalledWith('http://localhost:3001/data-management/export', {
        method: 'POST',
      });
    });
  });

  describe('importData', () => {
    const mockFile = new File(['test content'], 'test.zip', { type: 'application/zip' });

    it('should successfully import data', async () => {
      const mockResponse = { message: 'Import completed successfully' };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue(mockResponse),
      });

      await importData(mockFile);

      expect(mockFetch).toHaveBeenCalledWith(`${API_URL}/data-management/import`, {
        method: 'POST',
        body: expect.any(FormData),
      });
    });

    it('should create FormData with file', async () => {
      const mockResponse = { message: 'Import completed successfully' };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue(mockResponse),
      });

      await importData(mockFile);

      const callArgs = mockFetch.mock.calls[0];
      const formData = callArgs[1].body as FormData;

      // Check that FormData contains the file
      expect(formData.get('file')).toBe(mockFile);
    });

    it('should throw error when import fails', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        statusText: 'Bad Request',
      });

      await expect(importData(mockFile)).rejects.toThrow('Error importing data: Bad Request');
    });

    it('should handle files with special characters in name', async () => {
      const specialFile = new File(['content'], 'test file with spaces.zip', { type: 'application/zip' });
      const mockResponse = { message: 'Import completed successfully' };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue(mockResponse),
      });

      await importData(specialFile);

      const callArgs = mockFetch.mock.calls[0];
      const formData = callArgs[1].body as FormData;
      expect(formData.get('file')).toBe(specialFile);
    });
  });
});