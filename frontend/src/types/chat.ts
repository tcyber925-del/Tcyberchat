export interface ChatSession {
  id: string;
  title: string;
  summary?: string;
  timestamp: Date;
  lastActivity: Date;
  messageCount: number;
  documentId?: string;
}