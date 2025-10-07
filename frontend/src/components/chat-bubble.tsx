'use client';

import React, { useState } from 'react';
import { Message } from '@/types/message';
import Citation from './citation';

interface ChatBubbleProps {
  message: Message;
  onRegenerate?: () => void;
  onDelete?: (messageId: string) => void;
  isStreaming?: boolean;
}

const ChatBubble: React.FC<ChatBubbleProps> = ({ message, onRegenerate, onDelete, isStreaming = false }) => {
  const [copied, setCopied] = useState(false);
  const isUser = message.type === 'user';
  const bubbleClasses = isUser
    ? 'bg-primary text-primary-foreground self-end'
    : 'bg-muted text-muted-foreground self-start';

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  };

  const handleCitationClick = (docId: string, page?: number) => {
    // TODO: Implement citation navigation
    console.log('Navigate to citation:', docId, page);
  };

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4 animate-slide-up`}>
      <div className={`group rounded-lg p-4 max-w-2xl shadow-sm transition-all duration-200 hover:shadow-md ${bubbleClasses}`}>
        <p className="whitespace-pre-wrap">{message.content}</p>
        {isStreaming && (
          <span className="inline-block w-2 h-4 bg-current animate-pulse ml-1" aria-label="AI is typing"></span>
        )}
        {message.citations && message.citations.length > 0 && (
          <div className="text-xs mt-2 flex flex-wrap gap-1">
            {message.citations.map((citation, index) => (
              <Citation
                key={citation.id}
                citation={citation}
                onClick={handleCitationClick}
              />
            ))}
          </div>
        )}
        {!isUser && !isStreaming && (
          <div className="flex gap-2 mt-3 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
            <button
              onClick={handleCopy}
              className="text-xs px-2 py-1 bg-secondary text-secondary-foreground rounded hover:bg-secondary/80 transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-ring"
              title="Copy message"
              aria-label="Copy message to clipboard"
            >
              {copied ? '✅ Copied!' : '📋 Copy'}
            </button>
            {onDelete && (
              <button
                onClick={() => onDelete(message.id)}
                className="text-xs px-2 py-1 bg-destructive text-destructive-foreground rounded hover:bg-destructive/80 transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-ring"
                title="Delete message"
                aria-label="Delete message"
              >
                🗑️ Delete
              </button>
            )}
            {onRegenerate && (
              <button
                onClick={onRegenerate}
                className="text-xs px-2 py-1 bg-secondary text-secondary-foreground rounded hover:bg-secondary/80 transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-ring"
                title="Regenerate response"
                aria-label="Regenerate AI response"
              >
                🔄 Regenerate
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatBubble;