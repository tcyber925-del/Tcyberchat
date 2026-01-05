import { Document } from '@/types/document';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';

// Helper to get headers with guest session
const getHeaders = (headers: Record<string, string> = {}) => {
  const guestId = typeof window !== 'undefined' ? localStorage.getItem('guestSessionId') : null;
  const newHeaders: Record<string, string> = { ...headers };
  if (guestId) {
    newHeaders['X-Guest-Session-Id'] = guestId;
  }
  return newHeaders;
};

export async function uploadDocument(file: File): Promise<Document> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/documents/upload`, {
    method: 'POST',
    headers: getHeaders(),
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Error uploading document: ${response.statusText}`);
  }
  const data = await response.json();
  return {
    id: data.documentId,
    filename: data.filename,
    size: data.size,
    mimeType: data.mimeType,
    uploadedAt: new Date(data.uploadedAt),
    status: data.status,
    hasContent: data.hasContent,
    hasTranscription: data.hasTranscription,
    hasImageAnalysis: data.hasImageAnalysis,
    previewImage: data.previewImage,
  };
}

export async function getDocuments(): Promise<Document[]> {
  const response = await fetch(`${API_BASE_URL}/documents`, {
    headers: getHeaders(),
  });
  if (!response.ok) {
    throw new Error(`Error fetching documents: ${response.statusText}`);
  }
  const data = await response.json();
  return data.map((item: any) => ({
    ...item,
    uploadedAt: new Date(item.uploadedAt),
  }));
}

export async function deleteDocument(documentId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/documents/${documentId}`, {
    method: 'DELETE',
    headers: getHeaders(),
  });

  if (!response.ok) {
    throw new Error(`Error deleting document: ${response.statusText}`);
  }
}

export async function updateDocument(documentId: string, filename: string): Promise<Document> {
  const response = await fetch(`${API_BASE_URL}/documents/${documentId}`, {
    method: 'PATCH',
    headers: getHeaders({
      'Content-Type': 'application/json',
    }),
    body: JSON.stringify({ filename }),
  });

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('Document not found');
    }
    const text = await response.text().catch(() => response.statusText);
    throw new Error(text || `Failed to update document: ${response.status} ${response.statusText}`);
  }

  const data = await response.json();
  return {
    id: data.id,
    filename: data.filename,
    size: data.size,
    mimeType: data.mimeType,
    uploadedAt: new Date(data.uploadedAt),
    status: data.status,
    hasContent: data.hasContent,
    hasTranscription: data.hasTranscription,
    hasImageAnalysis: data.hasImageAnalysis,
    previewImage: data.previewImage,
  };
}

export async function exportDocument(documentId: string): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/documents/${documentId}/export`, {
    method: 'POST',
    headers: getHeaders(),
  });

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('Document not found');
    }
    const text = await response.text().catch(() => response.statusText);
    throw new Error(text || `Failed to export document: ${response.status} ${response.statusText}`);
  }

  return await response.json();
}
