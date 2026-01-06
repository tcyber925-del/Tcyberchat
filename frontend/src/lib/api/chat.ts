// Helper to get headers with guest session
const getHeaders = (headers: Record<string, string> = {}) => {
  const guestId = typeof window !== 'undefined' ? localStorage.getItem('guestSessionId') : null;
  const newHeaders: Record<string, string> = { ...headers };
  if (guestId) {
    newHeaders['X-Guest-Session-Id'] = guestId;
  }
  return newHeaders;
};

// sendMessageStreaming - posts a single message to the server and streams SSE
export async function sendMessageStreaming(
  message: string,
  conversationId?: string,
  model?: string,
  documentId?: string,
  enableWebSearch?: boolean,
  onChunk?: (chunk: string) => void,
  onComplete?: (
    finalMessage: {
      content: string;
      messageId?: string;
      citations?: any[];
      webSearchUsed?: boolean;
      webSearchResultsCount?: number;
      webProvider?: string;
      webImpl?: string;
    },
  ) => void,
  onError?: (err: Error) => void,
) {
  const response = await fetch('/api/chat/stream', {
    method: 'POST',
    headers: getHeaders({
      'Content-Type': 'application/json',
    }),
    body: JSON.stringify({ message, conversationId, documentId, model, enableWebSearch }),
  });

  if (!response.ok) {
    const text = await response.text().catch(() => response.statusText);
    throw new Error(text || response.statusText);
  }

  const reader = response.body?.getReader();
  if (!reader) return;

  const decoder = new TextDecoder();
  let buffer = '';
  let sawSSE = false;

  // Debug start
  // eslint-disable-next-line no-console
  console.debug('[client] started reading response stream');

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const chunkText = decoder.decode(value, { stream: true });

      // Debug chunk
      // eslint-disable-next-line no-console
      console.debug('[client] chunk read length=', chunkText.length);

      buffer += chunkText;

      // Heuristic: if we encounter 'event:' or 'data:' it's SSE
      if (!sawSSE && /(^|\n)(event:|data:)/.test(buffer)) {
        sawSSE = true;
      }

      if (sawSSE) {
        // Line-oriented SSE parser: handle cases where events arrive without a double-newline separator
        // We process complete lines and keep the last partial line in buffer.
        const lines = buffer.split(/\r?\n/);
        // If the buffer does not end with a newline, the last element is a partial line — keep it in buffer
        const endsWithNewline = /\r?\n$/.test(buffer);
        const partial = endsWithNewline ? '' : (lines.pop() ?? '');

        // State for accumulating an event block across lines
        let currentEvent = 'message';
        const currentDataLines: string[] = [];

        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed === '') {
            // blank line -> flush accumulated event
            const data = currentDataLines.join('\n').trim();
            if (currentEvent === 'chunk') {
              if (data.length <= 3) {
                for (const ch of data) onChunk?.(ch);
              } else if (/\s/.test(data)) {
                const tokens = data.split(/(\s+)/).filter(Boolean);
                for (const t of tokens) onChunk?.(t);
              } else {
                onChunk?.(data);
              }
            } else if (currentEvent === 'message') {
              if (data) {
                try {
                  const parsed = JSON.parse(data);
                  const content = parsed.content || parsed.response || '';
                  onComplete?.({
                    content,
                    messageId: parsed.messageId,
                    citations: parsed.citations,
                    webSearchUsed: parsed.webSearchUsed,
                    webSearchResultsCount: parsed.webSearchResultsCount,
                    webProvider: parsed.webProvider,
                    webImpl: parsed.webImpl,
                  });
                } catch (e) {
                  onComplete?.({ content: data });
                }
              }
            } else if (currentEvent === 'error') {
              try {
                const parsed = JSON.parse(currentDataLines.join('\n'));
                onError?.(new Error(parsed.error || parsed));
              } catch (e) {
                onError?.(new Error(currentDataLines.join('\n')));
              }
            }
            // reset state
            currentEvent = 'message';
            currentDataLines.length = 0;
            continue;
          }

          // Parse event: and data: lines
          const eventMatch = /^event:\s*(\S+)/i.exec(line);
          if (eventMatch) {
            currentEvent = eventMatch[1].trim();
            continue;
          }
          const dataMatch = /^data:\s*(.*)$/i.exec(line);
          if (dataMatch) {
            currentDataLines.push(dataMatch[1]);
            continue;
          }
          // If line doesn't match, ignore
        }

        // Restore buffer to contain the unfinished partial line
        buffer = partial;
      } else {
        // Not SSE: treat each read chunk as partial data
        // Split on line breaks to try to extract readable pieces
        const lines = buffer.split(/\r?\n/);
        // Keep last partial line in buffer
        buffer = lines.pop() ?? '';
        for (const line of lines) {
          if (!line) continue;
          // Robustness: if it looks like JSON even without SSE markers, try to parse it
          if (line.trim().startsWith('{') && line.trim().endsWith('}')) {
            try {
              const parsed = JSON.parse(line);
              const content = parsed.content || parsed.response || '';
              if (content) {
                onChunk?.(content);
                continue;
              }
            } catch (e) {
              // fall through to raw chunk
            }
          }
          onChunk?.(line);
        }
      }
    }

    // Flush any remaining buffer
    if (buffer.trim()) {
      const remaining = buffer.trim();
      try {
        if (remaining.startsWith('{') && remaining.endsWith('}')) {
          const parsed = JSON.parse(remaining);
          const content = parsed.content || parsed.response || parsed.error || '';
          if (content) {
            onChunk?.(content);
            if (onComplete) {
              onComplete({
                content,
                messageId: parsed.messageId,
                citations: parsed.citations,
                webSearchUsed: parsed.webSearchUsed,
                webSearchResultsCount: parsed.webSearchResultsCount,
                webProvider: parsed.webProvider,
                webImpl: parsed.webImpl,
              });
              return;
            }
          }
        }
      } catch (e) {
        // Not JSON, treat as raw
      }

      if (sawSSE) {
        // We already tried parsing above, if it failed or wasn't what we expected, 
        // just treat as raw chunk if not already completed
        onChunk?.(remaining);
      } else {
        onChunk?.(remaining);
      }
    }
  } catch (err) {
    onError?.(err instanceof Error ? err : new Error(String(err)));
  } finally {
    try {
      reader.releaseLock();
    } catch { }
  }
}

// getModels - fetches the list of available AI models
export async function getModels() {
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';
  const response = await fetch(`${API_BASE_URL}/api/v1/models`);
  if (!response.ok) {
    const text = await response.text().catch(() => response.statusText);
    throw new Error(text || response.statusText);
  }
  const data = await response.json();
  return data.models || [];
}

// getConversations - fetches all conversations
export async function getConversations(limit: number = 50): Promise<any[]> {
  try {
    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';
    const response = await fetch(`${API_BASE_URL}/api/v1/chat/conversations?limit=${limit}`, {
      headers: getHeaders(),
    });
    if (!response.ok) {
      const text = await response.text().catch(() => response.statusText);
      throw new Error(
        text || `Failed to fetch conversations: ${response.status} ${response.statusText}`,
      );
    }
    const data = await response.json();
    // Ensure we return an array even if API returns null/undefined
    return Array.isArray(data) ? data : [];
  } catch (error) {
    // Handle network errors
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error('Network error: Unable to connect to server. Please check your connection.');
    }
    throw error;
  }
}

// getConversationMessages - fetches messages for a specific conversation
export async function getConversationMessages(conversationId: string): Promise<any> {
  if (!conversationId || typeof conversationId !== 'string') {
    throw new Error('Invalid conversation ID');
  }

  try {
    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';
    const response = await fetch(`${API_BASE_URL}/api/v1/chat/conversations/${conversationId}`, {
      headers: getHeaders(),
    });
    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('Conversation not found');
      }
      const text = await response.text().catch(() => response.statusText);
      throw new Error(
        text || `Failed to fetch conversation: ${response.status} ${response.statusText}`,
      );
    }
    const data = await response.json();

    // Validate and normalize data
    if (!data || !data.id) {
      throw new Error('Invalid conversation data received from server');
    }

    return {
      conversation: {
        id: data.id,
        title: data.title || 'Untitled Conversation',
        startedAt: data.startedAt || new Date().toISOString(),
        lastActivity: data.lastActivity || data.startedAt || new Date().toISOString(),
        documentId: data.documentId || null,
        messageCount: data.messageCount || 0,
      },
      messages: (Array.isArray(data.messages) ? data.messages : [])
        .map((msg: any) => {
          // Validate message data
          if (!msg || !msg.id || !msg.content) {
            console.warn('Invalid message data:', msg);
            return null;
          }
          return {
            id: msg.id,
            content: msg.content || '',
            timestamp: msg.timestamp ? new Date(msg.timestamp) : new Date(),
            role:
              msg.type === 'bot'
                ? 'assistant'
                : msg.type === 'user'
                  ? 'user'
                  : msg.type || 'assistant',
            conversationId: msg.conversationId || conversationId,
            citations: Array.isArray(msg.citations) ? msg.citations : [],
            metadata: msg.metadata || {},
          };
        })
        .filter((msg: any) => msg !== null), // Remove invalid messages
    };
  } catch (error) {
    // Handle network errors
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error('Network error: Unable to connect to server. Please check your connection.');
    }
    throw error;
  }
}

// deepResearch - calls backend Deep Research API and returns full answer with citations
export async function deepResearch(
  query: string,
  model?: string,
  maxIterations: number = 2,
  signal?: AbortSignal,
) {
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';
  const res = await fetch(`${API_BASE_URL}/api/tools/web-search/deep-research`, {
    method: 'POST',
    headers: getHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ query, model, maxIterations }),
    signal,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(text || res.statusText);
  }
  return res.json();
}

// deepResearchStream - Manual SSE stream reader using POST fetch (more robust through tunnels)
export function deepResearchStream(
  query: string,
  model?: string,
  maxIterations: number = 2,
) {
  const listeners: Record<string, ((e: any) => void)[]> = {};
  
  const emit = (event: string, data: any) => {
    const list = listeners[event] || [];
    list.forEach(cb => cb({ data }));
  };

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';
  const controller = new AbortController();

  // Async IIFE to process the stream
  (async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/tools/web-search/deep-research/stream`, {
        method: 'POST',
        headers: getHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({ query, model, maxIterations }),
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${await response.text()}`);
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error('No response body');

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        let currentEvent = 'message';
        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed) continue;

          if (trimmed.startsWith('event:')) {
            currentEvent = trimmed.split('event:')[1].trim();
          } else if (trimmed.startsWith('data:')) {
            const data = trimmed.split('data:')[1].trim();
            emit(currentEvent, data);
            currentEvent = 'message'; // reset for next
          }
        }
      }
    } catch (err) {
      if ((err as any).name !== 'AbortError') {
        emit('error', JSON.stringify({ error: String(err) }));
      }
    }
  })();

  return {
    addEventListener: (event: string, callback: (e: any) => void) => {
      if (!listeners[event]) listeners[event] = [];
      listeners[event].push(callback);
    },
    close: () => controller.abort(),
  };
}

// deleteConversation - deletes a conversation
export async function deleteConversation(conversationId: string): Promise<void> {
  if (!conversationId || typeof conversationId !== 'string') {
    throw new Error('Invalid conversation ID');
  }

  try {
    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';
    const response = await fetch(`${API_BASE_URL}/api/v1/chat/conversations/${conversationId}`, {
      method: 'DELETE',
      headers: getHeaders(),
    });

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('Conversation not found');
      }
      const text = await response.text().catch(() => response.statusText);
      throw new Error(
        text || `Failed to delete conversation: ${response.status} ${response.statusText}`,
      );
    }
  } catch (error) {
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error('Network error: Unable to connect to server. Please check your connection.');
    }
    throw error;
  }
}

// updateConversation - updates a conversation (title, isPinned, isArchived)
export async function updateConversation(
  conversationId: string,
  updates: { title?: string; isPinned?: boolean; isArchived?: boolean },
): Promise<any> {
  if (!conversationId || typeof conversationId !== 'string') {
    throw new Error('Invalid conversation ID');
  }

  try {
    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';
    const response = await fetch(`${API_BASE_URL}/api/v1/chat/conversations/${conversationId}`, {
      method: 'PATCH',
      headers: getHeaders({
        'Content-Type': 'application/json',
      }),
      body: JSON.stringify(updates),
    });

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('Conversation not found');
      }
      const text = await response.text().catch(() => response.statusText);
      throw new Error(
        text || `Failed to update conversation: ${response.status} ${response.statusText}`,
      );
    }

    return await response.json();
  } catch (error) {
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error('Network error: Unable to connect to server. Please check your connection.');
    }
    throw error;
  }
}

// exportConversation - exports a conversation as JSON
export async function exportConversation(conversationId: string): Promise<any> {
  if (!conversationId || typeof conversationId !== 'string') {
    throw new Error('Invalid conversation ID');
  }

  try {
    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';
    const response = await fetch(
      `${API_BASE_URL}/api/v1/chat/conversations/${conversationId}/export`,
      {
        method: 'POST',
        headers: getHeaders(),
      },
    );

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('Conversation not found');
      }
      const text = await response.text().catch(() => response.statusText);
      throw new Error(
        text || `Failed to export conversation: ${response.status} ${response.statusText}`,
      );
    }

    return await response.json();
  } catch (error) {
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error('Network error: Unable to connect to server. Please check your connection.');
    }
    throw error;
  }
}
