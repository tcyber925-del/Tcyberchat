import { Document } from '@/types/document';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001';

export async function uploadDocument(file: File): Promise<Document> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/documents/upload`, {
    method: 'POST',
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
  const response = await fetch(`${API_BASE_URL}/documents/`);
  if (!response.ok) {
    throw new Error(`Error fetching documents: ${response.statusText}`);
  }
  const data = await response.json();
  return data.map((item: any) => ({
    ...item,
    uploadedAt: new Date(item.uploadedAt),
  }));
}
