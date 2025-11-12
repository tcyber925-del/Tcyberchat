export interface Citation {
  id: number;
  docId: string;
  page?: number;
  snippet: string;
  url?: string;
  title?: string;
  source?: string;
  source_type?: string;
}

export interface Message {
  id: string;
  content: string;
  timestamp: Date;
  role: 'user' | 'assistant' | 'system' | 'function' | 'tool';
  conversationId: string;
  citations?: Citation[];
  metadata?: object;
}
