import { ChatSession } from '@/types/chat';
import { Message } from '@/types/message';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001';

export async function getConversations(): Promise<ChatSession[]> {
  const response = await fetch(`${API_BASE_URL}/chat/conversations`);
  if (!response.ok) {
    throw new Error(`Error fetching conversations: ${response.statusText}`);
  }
  const data = await response.json();
  return data.map((item: any) => ({
    ...item,
    timestamp: new Date(item.timestamp),
    lastActivity: new Date(item.lastActivity),
  }));
}

export async function sendMessage(messageContent: string, conversationId?: string, model?: string): Promise<Message> {
  const response = await fetch(`${API_BASE_URL}/chat/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ message: messageContent, conversationId, ...(model && { model }) }),
  });

  if (!response.ok) {
    throw new Error(`Error sending message: ${response.statusText}`);
  }
  const data = await response.json();
  return {
    id: data.messageId,
    content: data.response,
    timestamp: new Date(),
    type: 'ai',
    conversationId: conversationId || 'default',
    citations: data.citations || [],
  };
}

export async function sendMessageStreaming(
  messageContent: string,
  conversationId?: string,
  model?: string,
  onChunk?: (chunk: string) => void,
  onComplete?: (fullMessage: Message) => void,
  onError?: (error: Error) => void
): Promise<void> {
  try {
    const response = await fetch(`${API_BASE_URL}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message: messageContent, conversationId, ...(model && { model }) }),
    });

    if (!response.ok) {
      throw new Error(`Error streaming message: ${response.statusText}`);
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();
    let fullContent = '';
    let messageId = '';

    if (!reader) {
      throw new Error('Response body is not readable');
    }

    while (true) {
      const { done, value } = await reader.read();

      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));

            if (data.content && !data.done) {
              fullContent += data.content;
              onChunk?.(data.content);
            } else if (data.done) {
              messageId = data.messageId || '';
              const finalMessage: Message = {
                id: messageId,
                content: fullContent,
                timestamp: new Date(),
                type: 'ai',
                conversationId: conversationId || 'default',
                citations: data.citations || [],
              };
              onComplete?.(finalMessage);
              break;
            }
          } catch (e) {
            // Skip malformed JSON lines
            continue;
          }
        }
      }
    }
  } catch (error) {
    onError?.(error as Error);
  }
}
