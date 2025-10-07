'use client';

import React, { useCallback, useState } from 'react';
import { useChat } from '@/lib/context/chat-context';
import ChatHistory from './chat-history';
import DocumentManager from './document-manager';

interface SidebarProps {
  isOpen?: boolean;
  onToggle?: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ isOpen = true, onToggle }) => {
  const { selectSession, selectDocument, documents, sessions, uploadDocument } = useChat();
  const [internalIsOpen, setInternalIsOpen] = useState(isOpen);

  // Use external toggle if provided, otherwise use internal state
  const isSidebarOpen = onToggle ? isOpen : internalIsOpen;

  const handleToggle = useCallback(() => {
    if (onToggle) {
      onToggle();
    } else {
      setInternalIsOpen(prev => !prev);
    }
  }, [onToggle]);

  const handleNewChat = () => {
    // TODO: Implement new chat logic
    console.log('Starting new chat');
  };

  return (
    <>
      {/* Toggle Button */}
      <button
        onClick={handleToggle}
        className="fixed top-4 left-4 z-50 p-2 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-all duration-200"
        aria-label="Toggle Sidebar"
        aria-expanded={isSidebarOpen}
      >
        <svg
          className={`w-5 h-5 transition-transform duration-200 ${isSidebarOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </button>

      {/* Sidebar */}
      <aside
        className={`fixed left-0 top-0 h-full bg-gray-100 border-r border-gray-200 transition-transform duration-300 ease-in-out z-40 ${
          isSidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
        style={{ width: '16rem' }}
        role="complementary"
        aria-label="Chat sidebar"
        aria-hidden={!isSidebarOpen}
      >
      <nav aria-label="Chat navigation" className="mb-4">
        <h2 className="text-lg font-semibold mb-2" id="chat-history-heading">Chat History</h2>
        <ChatHistory sessions={sessions} onSelectSession={selectSession} />
      </nav>

      <div className="flex-grow"></div>

      <section aria-labelledby="documents-heading">
        <h2 id="documents-heading" className="sr-only">Document Management</h2>
        <DocumentManager documents={documents} onSelectDocument={selectDocument} onUploadDocument={uploadDocument} />
      </section>

      <button
        onClick={handleNewChat}
        className="mt-4 p-2 bg-blue-500 text-white rounded hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
        aria-label="Start a new chat conversation"
      >
        New Chat
      </button>
      </aside>
    </>
  );
};

export default Sidebar;
