export interface Citation {
  id: number;
  docId: string;
  page?: number;
  snippet: string;
  url?: string;
}

export interface Message {
  id: string;
  content: string;
  timestamp: Date;
  type: 'user' | 'ai';
  conversationId: string;
  citations?: Citation[];
  metadata?: object;
}