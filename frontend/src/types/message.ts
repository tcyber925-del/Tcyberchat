export interface Citation {
  id: number;
  docId?: string; // optional for web citations
  page?: number;
  snippet: string;
  url?: string;
  title?: string;
  source?: string;
  source_type?: string;
  // Web extras
  quotes?: string[];
  trust?: number; // 0..1
  suspicious?: boolean;
  domain?: string;
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
