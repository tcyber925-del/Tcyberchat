import * as React from 'react';
import { cn } from '@/lib/utils';
import { Bot, User, Pencil, Copy, Check, RefreshCcw, ThumbsUp, ThumbsDown, GitBranch, Volume2 } from 'lucide-react';
import { Button } from './button';

import { useSettings } from '@/lib/context/settings-context';
import { DeepResearchArtifact } from '@/components/ai-elements/deep-research-artifact';
import { Message, MessageContent, MessageAvatar } from '@/components/ai-elements/message';
import { Branch, BranchSelector, BranchPrevious, BranchNext, BranchPage } from '@/components/ai-elements/branch';
import { Actions, Action } from '@/components/ai-elements/actions';
import { StepMonitor } from '@/components/ai-elements/step-monitor';
import { PlanRenderer } from '@/components/ai-elements/plan-renderer';

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
  type?: 'text' | 'agentic' | 'deep-research' | 'tool' | 'error';
  variant?: 'contained' | 'flat'; // New: support different visual styles
  content?: string; // Raw content for copying
  onCopy?: any; // Optional copy callback (typed as any to avoid DOM prop conflict)
  onEdit?: (content: string) => void; // Optional edit callback (for user messages)
  onRegenerate?: () => void; // New: handle regeneration
  onBranch?: () => void; // New: handle branching
  onVote?: (score: number) => void; // New: handle feedback
  timestamp?: Date; // Optional timestamp for the message
  isStreaming?: boolean; // Whether this message is currently streaming
  messageId?: string; // Optional message ID for editing
  meta?: any; // Optional metadata (e.g., web provider info)
  citations?: any[]; // Optional citations to render as source cards
  versionIndex?: number; // New: current version index
  totalVersions?: number; // New: total versions available
  onVersionChange?: (index: number) => void; // New: handle version switching
  // Agentic UI
  steps?: any[];
  plan?: string[];
  onPin?: (content: string) => void;
}

const ChatMessage = React.forwardRef<HTMLDivElement, ChatMessageProps>(
  (
    {
      className,
      role,
      type = 'text',
      variant = 'contained',
      children,
      content,
      onCopy,
      onEdit,
      onRegenerate,
      onBranch,
      onVote,
      timestamp,
      isStreaming = false,
      messageId,
      meta,
      citations,
      versionIndex = 0,
      totalVersions = 1,
      onVersionChange,
      steps,
      plan,
      onPin,
      ...props
    },
    ref,
  ) => {
    const isUser = role === 'user';
    const [copied, setCopied] = React.useState(false);
    const { settings } = useSettings();

    // If it's a deep research result, render the artifact view
    if (meta?.deepResearch || type === 'deep-research') {
      if (!isUser) {
        return (
          <div 
            ref={ref} 
            className={cn('flex flex-col gap-2 mb-8 w-full max-w-none animate-in fade-in slide-in-from-bottom-4 duration-500', className)}
            {...props}
          >
            <div className="flex items-center gap-2 px-1 mb-1">
              <div className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center">
                <Bot className="h-3.5 w-3.5 text-primary" />
              </div>
              <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Deep Research Engine</span>
            </div>
            <DeepResearchArtifact 
              content={content || ''} 
              citations={citations} 
              metadata={meta} 
              onPin={onPin}
            />
            {timestamp && (
              <span className="text-[10px] text-muted-foreground px-1 self-start">
                {new Intl.DateTimeFormat('en-US', { hour: 'numeric', minute: '2-digit', hour12: true }).format(timestamp)}
              </span>
            )}
          </div>
        );
      }
    }

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
        .replace(/!\[([^\]]+)\]\([^)]+\)/g, '$1') // Remove links, keep text
        .replace(/!\[([^\]]*)\]\([^)]+\)/g, '') // Remove images
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
            if (React.isValidElement(child) && (child as any).props?.children) {
              // Recursively extract text from nested children
              const extractText = (node: any): string => {
                if (typeof node === 'string') return node;
                if (typeof node === 'number') return String(node);
                if (Array.isArray(node)) {
                  return node.map(extractText).join('');
                }
                if (React.isValidElement(node) && (node as any).props?.children) {
                  return extractText((node as any).props.children);
                }
                return '';
              };
              return extractText((child as any).props.children);
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
      <Message 
        ref={ref} 
        from={role as any} 
        className={cn('mb-6 animate-slide-up group', className)}
        {...props}
      >
        <div className={cn(
          'flex flex-col w-full',
          isUser ? 'items-end' : 'items-start'
        )}>
          <div className={cn(
            "flex items-start gap-3 w-full",
            isUser ? "flex-row-reverse" : "flex-row"
          )}>
            <MessageAvatar src="" name={isUser ? "ME" : "AI"} className="mt-1 flex-shrink-0" />
            
            <div className={cn(
              "relative flex flex-col gap-3 min-w-0",
              (type === 'agentic' || type === 'deep-research') ? "w-full max-w-4xl" : "max-w-[85%] md:max-w-[75%]"
            )}>
              {/* Agentic Plan */}
              {type === 'agentic' && plan && plan.length > 0 && (
                <PlanRenderer plan={plan} className="animate-in fade-in slide-in-from-top-2 duration-500" />
              )}

              {/* Agentic Steps */}
              {type === 'agentic' && steps && steps.length > 0 && (
                <StepMonitor steps={steps} className="animate-in fade-in slide-in-from-top-4 duration-700" />
              )}

              {/* Main Content Bubble */}
              {(content || children) && (
                <MessageContent 
                  variant={variant}
                  className={cn(
                    isStreaming && 'animate-pulse-subtle',
                    isUser ? 'rounded-tr-none' : 'rounded-tl-none',
                    "shadow-sm border border-border/50"
                  )}
                >
                  <div className="prose prose-sm dark:prose-invert max-w-none break-anywhere w-full whitespace-normal leading-relaxed">
                    {children}
                  </div>
                </MessageContent>
              )}

              {/* Version/Branching Controls */}
              {totalVersions > 1 && (
                <Branch 
                  defaultBranch={versionIndex} 
                  onBranchChange={onVersionChange}
                  className="mt-1"
                >
                  <BranchSelector from={role as any} className="px-0">
                    <BranchPrevious className="size-5" />
                    <BranchPage className="text-[10px]" />
                    <BranchNext className="size-5" />
                  </BranchSelector>
                </Branch>
              )}

              {/* Action buttons - appears on hover */}
              <div
                className={cn(
                  'absolute top-0 opacity-0 group-hover:opacity-100 transition-all duration-200 flex items-center',
                  isUser ? '-left-12' : '-right-12',
                )}
              >
                <Actions className={cn(
                  "flex-col bg-background/80 backdrop-blur-sm border border-border rounded-lg p-1 shadow-md",
                  isUser ? "mr-2" : "ml-2"
                )}>
                  {isUser && onEdit && (
                    <Action tooltip="Edit Prompt" onClick={() => content && onEdit(content)}>
                      <Pencil size={14} />
                    </Action>
                  )}
                  
                  {!isUser && onRegenerate && (
                    <Action tooltip="Regenerate" onClick={onRegenerate}>
                      <RefreshCcw size={14} />
                    </Action>
                  )}

                  <Action tooltip="Copy to Clipboard" onClick={handleCopy}>
                    {copied ? <Check size={14} className="text-green-500" /> : <Copy size={14} />}
                  </Action>

                  {!isUser && (
                    <>
                      <Action tooltip="Branch from here" onClick={onBranch}>
                        <GitBranch size={14} />
                      </Action>
                      <Action tooltip="Read Aloud" onClick={() => {}}>
                        <Volume2 size={14} />
                      </Action>
                      <div className="h-px w-full bg-border my-1" />
                      <Action tooltip="Helpful" onClick={() => onVote?.(1)}>
                        <ThumbsUp size={14} />
                      </Action>
                      <Action tooltip="Not Helpful" onClick={() => onVote?.(-1)}>
                        <ThumbsDown size={14} />
                      </Action>
                    </>
                  )}
                </Actions>
              </div>
            </div>
          </div>

          {/* Dev-only web badge under assistant messages */}
          {!isUser &&
            meta &&
            process.env.NODE_ENV !== 'production' &&
            settings?.showWebDebugBadges && (
              <div className="mt-1 ml-11 flex items-center gap-1 text-[10px] text-muted-foreground">
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
              <div className="mt-2 ml-11 grid grid-cols-1 md:grid-cols-2 gap-2 w-full max-w-2xl">
                {citations.slice(0, 4).map((c: any, idx: number) => {
                  const url: string = c.url || '';
                  let host = '';
                  try {
                    host = url ? new URL(url).hostname.replace('www.', '') : '';
                  } catch { }
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
                      {/* Trust and domain badges */}
                      {typeof c.trust === 'number' || host ? (
                        <div className="mt-1 flex items-center gap-1">
                          {typeof c.trust === 'number' && (
                            <span
                              className={cn(
                                'text-[10px] px-1 py-0.5 rounded',
                                c.trust >= 0.75
                                  ? 'bg-green-100 text-green-700'
                                  : c.trust >= 0.5
                                    ? 'bg-yellow-100 text-yellow-700'
                                    : 'bg-red-100 text-red-700',
                              )}
                              title={`Trust score: ${(c.trust * 100).toFixed(0)}%`}
                            >
                              {c.trust >= 0.75 ? 'High' : c.trust >= 0.5 ? 'Med' : 'Low'} trust
                            </span>
                          )}
                          {host && (
                            <span className="text-[10px] px-1 py-0.5 rounded bg-accent/40 text-muted-foreground">
                              {host}
                            </span>
                          )}
                        </div>
                      ) : null}
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
                'text-[10px] text-muted-foreground mt-1',
                isUser ? 'mr-11' : 'ml-11'
              )}
            >
              {formatTime(timestamp)}
            </span>
          )}
        </div>
      </Message>
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