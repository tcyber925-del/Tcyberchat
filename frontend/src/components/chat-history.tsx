'use client';

import React from 'react';
import { ChatSession } from '@/types/chat';

interface ChatHistoryProps {
  sessions: ChatSession[];
  onSelectSession: (sessionId: string) => void;
  isLoading: boolean;
}

const ChatHistory: React.FC<ChatHistoryProps> = ({ sessions, onSelectSession, isLoading }) => {

  return (
    <div className="flex flex-col text-sm">
      <input
        id="chat-search"
        placeholder="Search chats..."
        className="mb-2 p-2 border border-border bg-background text-foreground rounded focus:outline-none focus:ring-2 focus:ring-ring"
        aria-describedby="chat-search-help"
        type="text"
      />
      <span id="chat-search-help" className="sr-only">
        Type to filter your chat history by title or content
      </span>
      <ul role="listbox" aria-label="Chat sessions" className="space-y-1">
        {isLoading ? (
          // Loading skeleton
          Array.from({ length: 5 }).map((_, index) => (
            <li key={index} className="p-2">
              <div className="h-5 bg-muted rounded animate-pulse w-3/4"></div>
            </li>
          ))
        ) : sessions.length > 0 ? (
          sessions.map((session) => (
            <li
              key={session.id}
              onClick={() => onSelectSession(session.id)}
              className="p-2 cursor-pointer hover:bg-accent hover:text-accent-foreground rounded truncate"
              role="option"
              aria-selected="false"
              title={session.title}
            >
              {session.title}
            </li>
          ))
        ) : (
          <li className="p-2 text-muted-foreground text-center" role="status" aria-live="polite">
            No chat history yet
          </li>
        )}
      </ul>
    </div>
  );
};

export default ChatHistory;
