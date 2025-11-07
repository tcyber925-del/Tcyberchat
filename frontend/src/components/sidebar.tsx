'use client';

import React, { useState } from 'react';
import { ChatSession } from '@/types/chat';
import { Document } from '@/types/document';
import ChatHistory from './chat-history';
import DocumentManager from './document-manager';

// Define SVG icons as React components for reusability
const NewChatIcon = () => (
  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
  </svg>
);

const DocumentIcon = () => (
  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
  </svg>
);

const HistoryIcon = () => (
  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const CollapseIcon = () => (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
    </svg>
);

const SettingsIcon = () => (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
);

interface SidebarProps {
  sessions: ChatSession[];
  documents: Document[];
  onNewChat: () => void;
  onSelectSession: (sessionId: string) => void;
  onSelectDocument: (documentId: string) => void;
  onUploadDocument: (file: File) => void;
  onDeleteDocument: (documentId: string) => void;
  onToggleSettings: () => void;
  isLoading: boolean;
}

const Sidebar: React.FC<SidebarProps> = ({
    sessions,
    documents,
    onNewChat,
    onSelectSession,
    onSelectDocument,
    onUploadDocument,
    onDeleteDocument,
    onToggleSettings,
    isLoading,
}) => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isDocumentsOpen, setIsDocumentsOpen] = useState(true);
  const [isHistoryOpen, setIsHistoryOpen] = useState(true);

  return (
    <div className={`bg-muted/50 text-foreground flex flex-col transition-width duration-300 ${isCollapsed ? 'w-20' : 'w-80'}`}>
      <div className="flex items-center justify-end p-4 border-b border-border">
        <button onClick={() => setIsCollapsed(!isCollapsed)} className="text-muted-foreground hover:text-foreground">
          <CollapseIcon />
        </button>
      </div>

      <div className="flex-grow p-2 space-y-2 overflow-y-auto">
        <button onClick={onNewChat} className="w-full flex items-center justify-center bg-primary hover:bg-primary/90 text-primary-foreground font-bold py-2 px-4 rounded">
          <NewChatIcon />
          {!isCollapsed && <span className="ml-2">New Chat</span>}
        </button>

        <nav className="space-y-2">
            <div>
                <button onClick={() => setIsDocumentsOpen(!isDocumentsOpen)} className="w-full flex items-center py-2 px-4 text-muted-foreground hover:bg-accent hover:text-accent-foreground rounded">
                    <DocumentIcon />
                    {!isCollapsed && <span className="ml-3 font-bold">Documents</span>}
                </button>
                {isDocumentsOpen && !isCollapsed && (
                    <div className="p-2">
                        <DocumentManager 
                            documents={documents} 
                            onSelectDocument={onSelectDocument} 
                            onUploadDocument={onUploadDocument} 
                            onDeleteDocument={onDeleteDocument} 
                            isLoading={isLoading}
                        />
                    </div>
                )}
            </div>
            <div>
                <button onClick={() => setIsHistoryOpen(!isHistoryOpen)} className="w-full flex items-center py-2 px-4 text-muted-foreground hover:bg-accent hover:text-accent-foreground rounded">
                    <HistoryIcon />
                    {!isCollapsed && <span className="ml-3 font-bold">Chat History</span>}
                </button>
                {isHistoryOpen && !isCollapsed && (
                    <div className="p-2">
                        <ChatHistory sessions={sessions} onSelectSession={onSelectSession} isLoading={isLoading} />
                    </div>
                )}
            </div>
        </nav>
      </div>

      <div className="p-4 border-t border-border">
        <button onClick={onToggleSettings} className="w-full flex items-center py-2 px-4 text-muted-foreground hover:bg-accent hover:text-accent-foreground rounded">
            <SettingsIcon />
            {!isCollapsed && <span className="ml-3">Settings</span>}
        </button>
      </div>
    </div>
  );
};

export default Sidebar;