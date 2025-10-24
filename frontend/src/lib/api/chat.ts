// sendMessageStreaming - posts a single message to the server and streams SSE
export async function sendMessageStreaming(
  message: string,
  conversationId?: string,
  model?: string,
  documentId?: string,
  onChunk?: (chunk: string) => void,
  onComplete?: (finalMessage: { content: string; messageId?: string; citations?: any[] }) => void,
  onError?: (err: Error) => void
) {
  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ message, conversationId, documentId, model }),
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
        const partial = endsWithNewline ? '' : lines.pop() ?? '';

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
                  onComplete?.({ content: parsed.content, messageId: parsed.messageId, citations: parsed.citations });
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
          onChunk?.(line);
        }
      }
    }

    // Flush any remaining buffer
    if (buffer.trim()) {
      const remaining = buffer.trim();
      if (sawSSE) {
        try {
          const parsed = JSON.parse(remaining);
          onComplete?.({ content: parsed.content, messageId: parsed.messageId, citations: parsed.citations });
        } catch (e) {
          // If not JSON, call onChunk with remaining
          onChunk?.(remaining);
        }
      } else {
        onChunk?.(remaining);
      }
    }
  } catch (err) {
    onError?.(err instanceof Error ? err : new Error(String(err)));
  } finally {
    try {
      reader.releaseLock();
    } catch {}
  }
}
