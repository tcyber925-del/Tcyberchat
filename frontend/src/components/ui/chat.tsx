import * as React from 'react';
import { cn } from '@/lib/utils';
import { Copy, Check, User, Bot, Pencil } from 'lucide-react';
import { Button } from './button';

interface ChatProps extends React.ComponentPropsWithoutRef<'div'> {
  // Add any specific props for the Chat container if needed
}

const Chat = React.forwardRef<HTMLDivElement, ChatProps>(
  ({ className, children, ...props }, ref) => (
    <div
      ref={ref}
      className={cn('flex flex-col space-y-4 max-h-full overflow-y-auto', className)}
      {...props}
    >
      {children}
    </div>
  ),
);
Chat.displayName = 'Chat';

interface ChatMessageProps extends React.ComponentPropsWithoutRef<'div'> {
  role: 'user' | 'assistant' | 'system' | 'function' | 'tool';
  content?: string; // Raw content for copying
  onCopy?: (content: string) => void; // Optional copy callback
  onEdit?: (content: string) => void; // Optional edit callback (for user messages)
  timestamp?: Date; // Optional timestamp for the message
  isStreaming?: boolean; // Whether this message is currently streaming
  messageId?: string; // Optional message ID for editing
  meta?: any; // Optional metadata (e.g., web provider info)
  citations?: any[]; // Optional citations to render as source cards
}

import { useSettings } from '@/lib/context/settings-context';

const ChatMessage = React.forwardRef<HTMLDivElement, ChatMessageProps>(
  (
    {
      className,
      role,
      children,
      content,
      onCopy,
      onEdit,
      timestamp,
      isStreaming = false,
      messageId,
      meta,
      citations,
      ...props
    },
    ref,
  ) => {
    const isUser = role === 'user';
    const [copied, setCopied] = React.useState(false);
    const { settings } = useSettings();

    // Enhanced bubble classes with better visual distinction
    const bubbleClasses = isUser
      ? 'bg-primary text-primary-foreground'
      : 'bg-card border border-border text-foreground';

    // Format timestamp
    const formatTime = React.useCallback((date?: Date) => {
      if (!date) return '';
      return new Intl.DateTimeFormat('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true,
      }).format(date);
    }, []);

    // Extract plain text from markdown content for copying
    const extractPlainText = React.useCallback((text: string): string => {
      if (!text) return '';
      // Remove markdown syntax patterns while preserving content
      return text
        .replace(/```[\s\S]*?```/g, (match) => {
          // Extract code from code blocks, preserving it
          const codeMatch = match.match(/```[\w]*\n?([\s\S]*?)```/);
          return codeMatch ? codeMatch[1] : '';
        })
        .replace(/`([^`]+)`/g, '$1') // Remove inline code markers, keep content
        .replace(/#{1,6}\s+/g, '') // Remove headers
        .replace(/\*\*([^*]+)\*\*/g, '$1') // Remove bold markers
        .replace(/\*([^*]+)\*/g, '$1') // Remove italic markers
        .replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1') // Remove links, keep text
        .replace(/!\[([^\]]*)\]\([^\)]+\)/g, '') // Remove images
        .replace(/^\s*[-*+]\s+/gm, '') // Remove list markers
        .replace(/^\s*\d+\.\s+/gm, '') // Remove numbered list markers
        .replace(/^>\s+/gm, '') // Remove blockquote markers
        .replace(/\n{3,}/g, '\n\n') // Normalize multiple newlines
        .trim();
    }, []);

    const handleCopy = React.useCallback(async () => {
      // Use content prop if available, otherwise try to extract from children
      let textToCopy = content;

      if (!textToCopy && children) {
        // Try to extract text from React children
        const childrenArray = React.Children.toArray(children);
        const textFromChildren = childrenArray
          .map((child) => {
            if (typeof child === 'string') return child;
            if (React.isValidElement(child) && child.props?.children) {
              // Recursively extract text from nested children
              const extractText = (node: any): string => {
                if (typeof node === 'string') return node;
                if (typeof node === 'number') return String(node);
                if (Array.isArray(node)) {
                  return node.map(extractText).join('');
                }
                if (React.isValidElement(node) && node.props?.children) {
                  return extractText(node.props.children);
                }
                return '';
              };
              return extractText(child.props.children);
            }
            return '';
          })
          .join('');
        textToCopy = extractPlainText(textFromChildren);
      } else if (textToCopy) {
        textToCopy = extractPlainText(textToCopy);
      }

      if (!textToCopy) return;

      try {
        await navigator.clipboard.writeText(textToCopy);
        setCopied(true);
        if (onCopy) {
          onCopy(textToCopy);
        }
        // Reset copied state after 2 seconds
        setTimeout(() => setCopied(false), 2000);
      } catch (error) {
        console.error('Failed to copy text:', error);
        // Fallback: try using the Clipboard API with a temporary textarea
        try {
          const textarea = document.createElement('textarea');
          textarea.value = textToCopy;
          textarea.style.position = 'fixed';
          textarea.style.opacity = '0';
          document.body.appendChild(textarea);
          textarea.select();
          document.execCommand('copy');
          document.body.removeChild(textarea);
          setCopied(true);
          if (onCopy) {
            onCopy(textToCopy);
          }
          setTimeout(() => setCopied(false), 2000);
        } catch (fallbackError) {
          console.error('Fallback copy also failed:', fallbackError);
        }
      }
    }, [content, children, extractPlainText, onCopy]);

    return (
      <div
        ref={ref}
        className={cn(
          'flex gap-3 mb-6 animate-slide-up group',
          isUser ? 'justify-end' : 'justify-start',
          className,
        )}
        {...props}
      >
        {/* Avatar - only show for assistant messages */}
        {!isUser && (
          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center mt-1">
            <Bot className="h-4 w-4 text-primary" />
          </div>
        )}

        <div
          className={cn(
            'flex flex-col',
            isUser
              ? 'items-end max-w-[80%] md:max-w-[70%]'
              : 'items-start max-w-[80%] md:max-w-[70%]',
          )}
        >
          {/* Message bubble */}
          <div
            className={cn(
              'relative rounded-2xl px-4 py-3 shadow-sm transition-all duration-200',
              'hover:shadow-md',
              isStreaming && 'animate-pulse-subtle',
              bubbleClasses,
              isUser ? 'rounded-br-md' : 'rounded-bl-md',
            )}
          >
            <div className="prose prose-sm dark:prose-invert max-w-none">{children}</div>

            {/* Action buttons - appears on hover */}
            <div
              className={cn(
                'absolute top-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex gap-1',
                isUser ? 'right-2' : 'right-2',
              )}
            >
              {/* Edit button - only for user messages */}
              {isUser && onEdit && (
                <Button
                  variant="ghost"
                  size="icon-sm"
                  onClick={() => {
                    if (content) {
                      onEdit(content);
                    }
                  }}
                  className={cn(
                    'text-primary-foreground/70 hover:text-primary-foreground hover:bg-primary-foreground/20',
                    'h-7 w-7 p-0',
                  )}
                  aria-label="Edit message"
                  title="Edit message"
                >
                  <Pencil className="h-3.5 w-3.5" />
                </Button>
              )}

              {/* Copy button */}
              <Button
                variant="ghost"
                size="icon-sm"
                onClick={handleCopy}
                className={cn(
                  isUser
                    ? 'text-primary-foreground/70 hover:text-primary-foreground hover:bg-primary-foreground/20'
                    : 'text-muted-foreground/70 hover:text-foreground hover:bg-accent',
                  'h-7 w-7 p-0',
                )}
                aria-label={copied ? 'Copied!' : 'Copy message'}
                title={copied ? 'Copied!' : 'Copy message'}
              >
                {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
              </Button>
            </div>
          </div>

          {/* Dev-only web badge under assistant messages */}
          {!isUser &&
            meta &&
            process.env.NODE_ENV !== 'production' &&
            settings?.showWebDebugBadges && (
              <div className="mt-1 flex items-center gap-1 text-[10px] text-muted-foreground">
                <span className="px-1.5 py-0.5 rounded bg-primary/10 text-primary font-medium">
                  Web
                </span>
                <span className="px-1 py-0.5 rounded bg-accent/60">
                  {meta?.webProvider ?? 'n/a'}
                </span>
                <span className="px-1 py-0.5 rounded bg-accent/40">
                  {meta?.webImpl ?? 'custom'}
                </span>
                <span className="px-1 py-0.5 rounded bg-accent/20">
                  {typeof meta?.webSearchResultsCount === 'number'
                    ? `#${meta.webSearchResultsCount}`
                    : '#0'}
                </span>
              </div>
            )}

          {/* Source cards */}
          {!isUser &&
            settings?.showSourcesPanel &&
            Array.isArray(citations) &&
            citations.length > 0 && (
              <div className="mt-2 grid grid-cols-1 md:grid-cols-2 gap-2 w-full">
                {citations.slice(0, 4).map((c: any, idx: number) => {
                  const url: string = c.url || '';
                  let host = '';
                  try {
                    host = url ? new URL(url).hostname.replace('www.', '') : '';
                  } catch {}
                  const title = c.title || host || 'Source';
                  const snippet = (c.snippet || '').slice(0, 140);
                  return (
                    <a
                      key={idx}
                      href={url || '#'}
                      target="_blank"
                      rel="noreferrer"
                      className="block border border-border rounded-md p-2 hover:bg-accent transition-colors"
                    >
                      <div className="text-xs font-medium text-foreground line-clamp-1">
                        {title}
                      </div>
                      {host && <div className="text-[10px] text-muted-foreground">{host}</div>}
                      {snippet && (
                        <div className="text-[11px] text-muted-foreground mt-1 line-clamp-2">
                          {snippet}
                        </div>
                      )}
                    </a>
                  );
                })}
              </div>
            )}

          {/* Timestamp */}
          {timestamp && (
            <span
              className={cn(
                'text-xs text-muted-foreground mt-1 px-1',
                isUser ? 'text-right' : 'text-left',
              )}
            >
              {formatTime(timestamp)}
            </span>
          )}
        </div>

        {/* Avatar - only show for user messages */}
        {isUser && (
          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary flex items-center justify-center mt-1">
            <User className="h-4 w-4 text-primary-foreground" />
          </div>
        )}
      </div>
    );
  },
);
ChatMessage.displayName = 'ChatMessage';

interface ChatInputProps extends React.ComponentPropsWithoutRef<'textarea'> {
  // Add any specific props for the ChatInput if needed
}

const ChatInput = React.forwardRef<HTMLTextAreaElement, ChatInputProps>(
  ({ className, ...props }, ref) => (
    <textarea
      ref={ref}
      className={cn(
        'flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
        className,
      )}
      {...props}
    />
  ),
);
ChatInput.displayName = 'ChatInput';

export { Chat, ChatMessage, ChatInput };
