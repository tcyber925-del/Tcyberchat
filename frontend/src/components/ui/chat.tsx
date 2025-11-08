import * as React from 'react';
import { cn } from '@/lib/utils'; // Assuming you have a utility for class names
import { Copy, Check } from 'lucide-react';
import { Button } from './button';

interface ChatProps extends React.ComponentPropsWithoutRef<'div'> {
  // Add any specific props for the Chat container if needed
}

const Chat = React.forwardRef<HTMLDivElement, ChatProps>(
  ({ className, children, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        'flex flex-col space-y-4 max-h-full overflow-y-auto',
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
);
Chat.displayName = 'Chat';

interface ChatMessageProps extends React.ComponentPropsWithoutRef<'div'> {
  role: 'user' | 'assistant' | 'system' | 'function' | 'tool';
  content?: string; // Raw content for copying
  onCopy?: (content: string) => void; // Optional copy callback
}

const ChatMessage = React.forwardRef<HTMLDivElement, ChatMessageProps>(
  ({ className, role, children, content, onCopy, ...props }, ref) => {
    const isUser = role === 'user';
    const [copied, setCopied] = React.useState(false);
    const bubbleClasses = isUser
      ? 'bg-primary text-primary-foreground self-end'
      : 'bg-muted text-muted-foreground self-start';

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
          'flex',
          isUser ? 'justify-end' : 'justify-start',
          'mb-4 animate-slide-up group', // Added group for hover effects
          className
        )}
        {...props}
      >
        <div
          className={cn(
            'relative rounded-lg p-4 shadow-sm transition-all duration-200 hover:shadow-md',
            bubbleClasses
          )}
        >
          {children}
          {/* Copy button - appears on hover */}
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={handleCopy}
            className={cn(
              'absolute top-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200',
              isUser 
                ? 'right-2 text-primary-foreground/70 hover:text-primary-foreground hover:bg-primary-foreground/20' 
                : 'right-2 text-muted-foreground/70 hover:text-foreground hover:bg-accent',
              'h-7 w-7 p-0'
            )}
            aria-label={copied ? 'Copied!' : 'Copy message'}
            title={copied ? 'Copied!' : 'Copy message'}
          >
            {copied ? (
              <Check className="h-3.5 w-3.5" />
            ) : (
              <Copy className="h-3.5 w-3.5" />
            )}
          </Button>
        </div>
      </div>
    );
  }
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
        className
      )}
      {...props}
    />
  )
);
ChatInput.displayName = 'ChatInput';

export { Chat, ChatMessage, ChatInput };
