const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function exportData(): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}/data-management/export`, {
    method: 'POST',
  });

  if (!response.ok) {
    throw new Error(`Error exporting data: ${response.statusText}`);
  }
  return response.blob();
}

export async function importData(file: File): Promise<void> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/data-management/import`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Error importing data: ${response.statusText}`);
  }
}
