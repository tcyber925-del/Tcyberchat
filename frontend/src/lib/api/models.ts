const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface AvailableModel {
  name: string;
  size: number;
  modified_at: string;
  provider: string;
}

export async function getAvailableModels(): Promise<AvailableModel[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/models`);
    if (!response.ok) {
      throw new Error(`Error fetching models: ${response.statusText}`);
    }
    const models = await response.json();
    // Ensure the response is an array
    if (Array.isArray(models)) {
      return models;
    }
    // Handle cases where the API might return an object with a models key
    if (models && Array.isArray(models.models)) {
      return models.models;
    }
    return [];
  } catch (error) {
    console.error('Failed to fetch available models:', error);
    return [];
  }
}
