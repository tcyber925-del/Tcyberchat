export interface Document {
  id: string;
  filename: string;
  size: number;
  mimeType: string;
  uploadedAt: Date;
  status: 'uploading' | 'processing' | 'analyzing' | 'transcribing' | 'embedding' | 'ready' | 'error';
  hasContent: boolean;
  hasTranscription: boolean;
  hasImageAnalysis: boolean;
  previewImage?: string;
}