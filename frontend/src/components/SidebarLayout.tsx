import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import { Document, Message } from '../services/api';

interface Conversation {
  id: string;
  title: string;
  lastActivity: string;
  documentId?: string;
  messageCount: number;
}

interface SidebarLayoutProps {
  children: React.ReactNode;
}

const SidebarLayout: React.FC<SidebarLayoutProps> = ({ children }) => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedConversation, setSelectedConversation] = useState<string | null>(null);
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isRightDrawerOpen, setIsRightDrawerOpen] = useState(false);

  useEffect(() => {
    loadConversations();
    loadDocuments();
  }, []);

  const loadConversations = async () => {
    try {
      const convs = await apiService.getConversations();
      setConversations(convs);
    } catch (error) {
      console.error('Failed to load conversations:', error);
    }
  };

  const loadDocuments = async () => {
    try {
      const docs = await apiService.getDocuments();
      setDocuments(docs);
    } catch (error) {
      console.error('Failed to load documents:', error);
    }
  };

  const handleNewChat = () => {
    setSelectedConversation(null);
    // Trigger chat interface to start new conversation
    // This will be handled by the chat interface component
  };

  const handleSelectConversation = (conversationId: string) => {
    setSelectedConversation(conversationId);
    setIsSidebarOpen(false); // Close sidebar on mobile
  };

  const handleSelectDocument = (document: Document) => {
    setSelectedDocument(document);
    setIsRightDrawerOpen(true);
  };

  const handleDeleteConversation = async (conversationId: string) => {
    try {
      await apiService.deleteConversation(conversationId);
      setConversations(prev => prev.filter(c => c.id !== conversationId));
      if (selectedConversation === conversationId) {
        setSelectedConversation(null);
      }
    } catch (error) {
      console.error('Failed to delete conversation:', error);
    }
  };

  const handleDeleteDocument = async (documentId: string) => {
    try {
      await apiService.deleteDocument(documentId);
      setDocuments(prev => prev.filter(d => d.id !== documentId));
      if (selectedDocument?.id === documentId) {
        setSelectedDocument(null);
        setIsRightDrawerOpen(false);
      }
    } catch (error) {
      console.error('Failed to delete document:', error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ready': return 'text-green-500';
      case 'error': return 'text-red-500';
      default: return 'text-yellow-500';
    }
  };

  return (
    <div className="flex h-screen bg-[#343541] font-inter">
      {/* Left Sidebar */}
      <div
        className={`fixed inset-y-0 left-0 z-50 w-[260px] bg-[#202123] transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0 ${
          isSidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex flex-col h-full">
          {/* New Chat Button */}
          <div className="p-2 border-b border-gray-700">
            <button
              onClick={handleNewChat}
              className="w-full bg-transparent text-white px-3 py-2 rounded-md border border-gray-700 hover:bg-gray-700 transition-colors flex items-center justify-start gap-2"
            >
              <svg stroke="currentColor" fill="none" strokeWidth="1.5" viewBox="0 0 24 24" className="h-6 w-6" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path></svg>
              New Chat
            </button>
          </div>

          {/* Chat History */}
          <div className="flex-1 overflow-y-auto">
            <div className="p-2">
              <div className="space-y-1 text-gray-300 text-sm">
                {conversations.map((conversation) => (
                  <a
                    key={conversation.id}
                    href="#"
                    className={`group flex items-center px-3 py-2 rounded-md hover:bg-gray-700 transition-colors ${
                      selectedConversation === conversation.id ? 'bg-gray-800' : ''
                    }`}
                    onClick={() => handleSelectConversation(conversation.id)}
                  >
                    <svg stroke="currentColor" fill="none" strokeWidth="2" viewBox="0 0 24 24" className="h-4 w-4 -mt-px" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V5a2 2 0 012-2h14a2 2 0 012 2v10a2 2 0 01-2 2h-3l-4 4z"></path></svg>
                    <div className="flex-1 min-w-0 ml-3">
                      <p className="truncate">
                        {conversation.title || `Chat ${conversation.messageCount} messages`}
                      </p>
                    </div>
                    <div className="flex items-center">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteConversation(conversation.id);
                        }}
                        className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-400 transition-opacity ml-2 p-1"
                      >
                        <svg stroke="currentColor" fill="none" strokeWidth="2" viewBox="0 0 24 24" className="h-4 w-4" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                      </button>
                    </div>
                  </a>
                ))}
                {conversations.length === 0 && (
                  <p className="text-sm text-gray-500 text-center py-4">No conversations yet</p>
                )}
              </div>
            </div>

            {/* Documents Section */}
            <div className="p-2 border-t border-gray-700">
              <h3 className="text-xs font-medium text-gray-400 uppercase tracking-wider px-3 py-2">
                Documents
              </h3>
              <div className="space-y-1 text-gray-300 text-sm">
                {documents.map((document) => (
                  <a
                    key={document.id}
                    href="#"
                    className={`group flex items-center px-3 py-2 rounded-md hover:bg-gray-700 transition-colors ${
                      selectedDocument?.id === document.id ? 'bg-gray-800' : ''
                    }`}
                    onClick={() => handleSelectDocument(document)}
                  >
                    <svg stroke="currentColor" fill="none" strokeWidth="2" viewBox="0 0 24 24" className="h-4 w-4 -mt-px" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
                    <div className="flex-1 min-w-0 ml-3">
                      <p className="truncate">{document.filename}</p>
                      <div className="flex items-center space-x-2 text-xs text-gray-500">
                        <span
                          className={getStatusColor(document.status)}
                        >
                          {document.status}
                        </span>
                        <span>
                          {(document.size / 1024).toFixed(1)} KB
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteDocument(document.id);
                        }}
                        className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-400 transition-opacity ml-2 p-1"
                      >
                        <svg stroke="currentColor" fill="none" strokeWidth="2" viewBox="0 0 24 24" className="h-4 w-4" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                      </button>
                    </div>
                  </a>
                ))}
                {documents.length === 0 && (
                  <p className="text-sm text-gray-500 text-center py-4">No documents uploaded</p>
                )}
              </div>
            </div>

            {/* Settings/User Section */}
            <div className="p-2 border-t border-gray-700">
              <div className="flex items-center px-3 py-2 rounded-md text-white">
                <div className="flex-1 min-w-0">
                  <p className="text-sm truncate">Nathan Do</p>
                  <p className="text-xs text-gray-400">Free</p>
                </div>
                <button className="bg-[#10a37f] text-white px-3 py-1 rounded-md text-xs hover:bg-[#0f906e] transition-colors">
                  Upgrade
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Sidebar Backdrop for Mobile */}
      {isSidebarOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col relative bg-[#343541]">
        {/* Header */}
        <header className="bg-[#343541] border-b border-gray-700 px-4 py-3 flex items-center justify-between text-white">
            <div className="flex items-center">
                <button
                    onClick={() => setIsSidebarOpen(true)}
                    className="text-gray-400 hover:text-gray-200 lg:hidden mr-4"
                >
                    ☰
                </button>
                <h1 className="text-lg font-semibold">ChatGPT</h1>
            </div>
            <button className="bg-[#8e50e4] text-white px-3 py-1 rounded-md text-sm hover:bg-[#7a3dc2] transition-colors flex items-center gap-2">
                <svg stroke="currentColor" fill="none" strokeWidth="2" viewBox="0 0 24 24" className="h-4 w-4" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                Upgrade your plan
            </button>
        </header>

        {/* Chat Interface */}
        <main className="flex-1 overflow-y-auto flex flex-col items-center justify-center text-white">
          {children}
        </main>
      </div>

      {/* Right Panel - Document Viewer */}
      <div
        className={`fixed inset-y-0 right-0 z-50 w-96 bg-[#202123] shadow-lg transform transition-transform duration-300 ease-in-out ${
          isRightDrawerOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        <div className="flex flex-col h-full">
          <div className="flex items-center justify-between p-4 border-b border-gray-700 bg-[#202123] text-white">
            <h2 className="text-lg font-semibold">Document Viewer</h2>
            <button
              onClick={() => setIsRightDrawerOpen(false)}
              className="text-gray-400 hover:text-gray-200"
            >
              ✕
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-4 text-gray-300">
            {selectedDocument ? (
              <div className="space-y-4">
                <div className="bg-gray-700 rounded-md p-4 shadow-sm">
                  <h3 className="font-medium text-white mb-2">{selectedDocument.filename}</h3>
                  <div className="space-y-1 text-sm text-gray-400">
                    <p>
                      Status: <span className={getStatusColor(selectedDocument.status)}>{selectedDocument.status}</span>
                    </p>
                    <p>Size: {(selectedDocument.size / 1024).toFixed(1)} KB</p>
                    <p>Uploaded: {new Date(selectedDocument.uploadedAt).toLocaleDateString()}</p>
                  </div>
                </div>

                {/* Document content would be rendered here */}
                <div className="bg-gray-700 rounded-md p-4 shadow-sm">
                  <p className="text-sm text-gray-400">
                    Document viewer functionality will be implemented here.
                    This will show the document content with highlighting capabilities.
                  </p>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center h-full">
                <p className="text-gray-500">Select a document to view</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Right Drawer Backdrop */}
      {isRightDrawerOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40"
          onClick={() => setIsRightDrawerOpen(false)}
        />
      )}
    </div>
  );
};

export default SidebarLayout;

            {/* Documents Section */}
            <div className="p-2 border-t border-gray-600">
              <h3 className="text-xs font-medium text-gray-400 uppercase tracking-wider px-3 py-2">
                Documents
              </h3>
              <div className="space-y-1">
                {documents.map((document) => (
                  <div
                    key={document.id}
                    className={`group flex items-center px-3 py-2 rounded-md cursor-pointer text-white hover:bg-gray-700 transition-colors ${
                      selectedDocument?.id === document.id ? 'bg-gray-700' : ''
                    }`}
                    onClick={() => handleSelectDocument(document)}
                  >
                    <div className="flex-1 min-w-0">
                      <p className="text-sm truncate">{document.filename}</p>
                      <div className="flex items-center space-x-2">
                        <span
                          className="text-xs"
                          style={{ color: getStatusColor(document.status) }}
                        >
                          {document.status}
                        </span>
                        <span className="text-xs text-gray-500">
                          {(document.size / 1024).toFixed(1)} KB
                        </span>
                      </div>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteDocument(document.id);
                      }}
                      className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-400 transition-opacity ml-2"
                    >
                      ×
                    </button>
                  </div>
                ))}
                {documents.length === 0 && (
                  <p className="text-sm text-gray-500 text-center py-4">No documents uploaded</p>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Sidebar Backdrop for Mobile */}
      {isSidebarOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col relative">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
            <div className="flex items-center">
                <button
                    onClick={() => setIsSidebarOpen(true)}
                    className="text-gray-600 hover:text-gray-800 lg:hidden mr-4"
                >
                    ☰
                </button>
                <h1 className="text-lg font-semibold text-gray-900">Local Chatbot</h1>
            </div>
        </header>

        {/* Chat Interface */}
        <main className="flex-1 overflow-y-auto">
          {children}
        </main>
      </div>

      {/* Right Panel - Document Viewer */}
      <div
        className={`fixed inset-y-0 right-0 z-50 w-96 bg-[#f4f4f4] shadow-lg transform transition-transform duration-300 ease-in-out ${
          isRightDrawerOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        <div className="flex flex-col h-full">
          <div className="flex items-center justify-between p-4 border-b border-gray-300 bg-white">
            <h2 className="text-lg font-semibold text-gray-900">Document Viewer</h2>
            <button
              onClick={() => setIsRightDrawerOpen(false)}
              className="text-gray-500 hover:text-gray-700"
            >
              ✕
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-4">
            {selectedDocument ? (
              <div className="space-y-4">
                <div className="bg-white rounded-md p-4 shadow-sm">
                  <h3 className="font-medium text-gray-900 mb-2">{selectedDocument.filename}</h3>
                  <div className="space-y-1 text-sm text-gray-600">
                    <p>
                      Status: <span style={{ color: getStatusColor(selectedDocument.status) }}>{selectedDocument.status}</span>
                    </p>
                    <p>Size: {(selectedDocument.size / 1024).toFixed(1)} KB</p>
                    <p>Uploaded: {new Date(selectedDocument.uploadedAt).toLocaleDateString()}</p>
                  </div>
                </div>

                {/* Document content would be rendered here */}
                <div className="bg-white rounded-md p-4 shadow-sm">
                  <p className="text-sm text-gray-600">
                    Document viewer functionality will be implemented here.
                    This will show the document content with highlighting capabilities.
                  </p>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center h-full">
                <p className="text-gray-500">Select a document to view</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Right Drawer Backdrop */}
      {isRightDrawerOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40"
          onClick={() => setIsRightDrawerOpen(false)}
        />
      )}
    </div>
  );
};

export default SidebarLayout;