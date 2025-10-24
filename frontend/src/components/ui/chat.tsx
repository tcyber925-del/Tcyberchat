import * as React from 'react';
import { cn } from '@/lib/utils'; // Assuming you have a utility for class names

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
}

const ChatMessage = React.forwardRef<HTMLDivElement, ChatMessageProps>(
  ({ className, role, children, ...props }, ref) => {
    const isUser = role === 'user';
    const bubbleClasses = isUser
      ? 'bg-primary text-primary-foreground self-end'
      : 'bg-muted text-muted-foreground self-start';

    return (
      <div
        ref={ref}
        className={cn(
          'flex',
          isUser ? 'justify-end' : 'justify-start',
          'mb-4 animate-slide-up', // Assuming animate-slide-up is defined in your CSS
          className
        )}
        {...props}
      >
        <div
          className={cn(
            'group rounded-lg p-4 shadow-sm transition-all duration-200 hover:shadow-md',
            bubbleClasses
          )}
        >
          {children}
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
