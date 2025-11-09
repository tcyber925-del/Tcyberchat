'use client';

import React, { useCallback, useState } from 'react';
import { useChat } from '@/lib/context/chat-context';
import ChatHistory from './chat-history';

interface ChatHistoryDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

const ChatHistoryDrawer: React.FC<ChatHistoryDrawerProps> = ({ isOpen, onClose }) => {
  const { sessions, selectSession } = useChat();

  const handleSelectSession = useCallback((sessionId: string) => {
    selectSession(sessionId);
    onClose(); // Close drawer after selecting a session
  }, [selectSession, onClose]);

  const handleNewChat = useCallback(() => {
    selectSession(null); // Start a new chat by clearing current session
    onClose(); // Close drawer after starting new chat
  }, [selectSession, onClose]);

  return (
    <aside
      className={`fixed left-0 top-0 h-full bg-gray-100 border-r border-gray-200 transition-transform duration-300 ease-in-out z-40 ${
        isOpen ? 'translate-x-0' : '-translate-x-full'
      }`}
      style={{ width: '16rem' }}
      role="complementary"
      aria-label="Chat history sidebar"
      aria-hidden={!isOpen}
    >
      <div className="p-4">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold">Chat History</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700" aria-label="Close chat history">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <ChatHistory sessions={sessions} onSelectSession={handleSelectSession} />
        <button
          onClick={handleNewChat}
          className="mt-4 p-2 bg-blue-500 text-white rounded hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 w-full"
          aria-label="Start a new chat conversation"
        >
          New Chat
        </button>
      </div>
    </aside>
  );
};

export default ChatHistoryDrawer;
