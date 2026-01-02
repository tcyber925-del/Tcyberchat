/**
 * Unified Stream Controller for handling Server-Sent Events (SSE)
 * Provides robust error handling, reconnection logic, and smooth rendering.
 */

export interface StreamHandlers {
  onChunk: (chunk: string) => void;
  onStep?: (step: any) => void;
  onFinal?: (data: any) => void;
  onError: (error: Error) => void;
  onComplete: () => void;
}

export interface StreamOptions {
  method?: 'GET' | 'POST';
  body?: any;
  headers?: Record<string, string>;
  reconnect?: boolean;
  maxRetries?: number;
}

export class StreamController {
  private abortController: AbortController | null = null;
  private retries = 0;
  private maxRetries = 3;

  constructor(private url: string, private handlers: StreamHandlers, private options: StreamOptions = {}) {
    this.maxRetries = options.maxRetries ?? 3;
  }

  async start() {
    this.abortController = new AbortController();
    
    try {
      const response = await fetch(this.url, {
        method: this.options.method ?? 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...this.options.headers,
        },
        body: this.options.body ? JSON.stringify(this.options.body) : undefined,
        signal: this.abortController.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      if (!response.body) {
        throw new Error('ReadableStream not supported');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        
        // Process SSE format (data: ...)
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.trim() === '') continue;
          
          // Basic SSE parsing
          const eventMatch = line.match(/^event: (.*)$/m);
          const dataMatch = line.match(/^data: (.*)$/m);
          
          const eventType = eventMatch ? eventMatch[1] : 'message';
          const dataStr = dataMatch ? dataMatch[1] : '';

          try {
            if (eventType === 'step') {
              const stepData = JSON.parse(dataStr);
              this.handlers.onStep?.(stepData);
            } else if (eventType === 'final') {
              const finalData = JSON.parse(dataStr);
              this.handlers.onFinal?.(finalData);
            } else if (eventType === 'chunk' || eventType === 'message') {
              // Some endpoints send raw text in data, some send JSON
              try {
                const json = JSON.parse(dataStr);
                if (typeof json === 'object' && json.content) {
                  this.handlers.onChunk(json.content);
                } else if (typeof json === 'string') {
                  this.handlers.onChunk(json);
                }
              } catch {
                this.handlers.onChunk(dataStr);
              }
            } else if (eventType === 'error') {
              const err = JSON.parse(dataStr);
              throw new Error(err.error || 'Unknown stream error');
            }
          } catch (e) {
            console.error('Error parsing SSE data:', e, 'Line:', line);
          }
        }
      }

      this.handlers.onComplete();
      this.retries = 0; // Reset retries on successful completion
    } catch (error: any) {
      if (error.name === 'AbortError') {
        return;
      }

      if (this.options.reconnect && this.retries < this.maxRetries) {
        this.retries++;
        const delay = Math.pow(2, this.retries) * 1000;
        console.warn(`Stream disconnected. Retrying in ${delay}ms... (${this.retries}/${this.maxRetries})`);
        setTimeout(() => this.start(), delay);
      } else {
        this.handlers.onError(error);
      }
    }
  }

  stop() {
    if (this.abortController) {
      this.abortController.abort();
      this.abortController = null;
    }
  }
}
