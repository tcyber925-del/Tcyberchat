'use client';

import React, { Suspense, lazy, useState, useCallback } from 'react';
import { useChat } from '@/lib/context/chat-context';

// Lazy load components for performance optimization
const TopBar = lazy(() => import('@/components/top-bar'));
const MessageInput = lazy(() => import('@/components/message-input'));
const ChatBubble = lazy(() => import('@/components/chat-bubble'));
const ChatHistoryDrawer = lazy(() => import('@/components/chat-history-drawer'));
const DocumentManagerDrawer = lazy(() => import('@/components/document-manager-drawer'));

// Loading fallback component
const LoadingFallback = () => (
  <div className="flex items-center justify-center p-4">
    <div className="animate-spin rounded-full h-6 w-6 border-2 border-primary border-t-transparent"></div>
  </div>
);

export default function Home() {
  const { messages, streamingMessage, isStreaming, deleteMessage, undoDeleteMessage, lastDeletedMessage } = useChat();
  const [isChatHistoryOpen, setIsChatHistoryOpen] = useState(false);
  const [isDocumentManagerOpen, setIsDocumentManagerOpen] = useState(false);

  const toggleChatHistory = useCallback(() => {
    setIsChatHistoryOpen(prev => !prev);
    setIsDocumentManagerOpen(false); // Close document manager if open
  }, []);

  const toggleDocumentManager = useCallback(() => {
    setIsDocumentManagerOpen(prev => !prev);
    setIsChatHistoryOpen(false); // Close chat history if open
  }, []);

  return (
    <div data-testid="main-layout" className="flex h-screen bg-background">
      <Suspense fallback={<LoadingFallback />}>
        <ChatHistoryDrawer isOpen={isChatHistoryOpen} onClose={() => setIsChatHistoryOpen(false)} />
      </Suspense>

      <div className="flex flex-col flex-grow">
        <Suspense fallback={<LoadingFallback />}>
          <TopBar
            onToggleChatHistory={toggleChatHistory}
            onToggleDocumentManager={toggleDocumentManager}
            isChatHistoryOpen={isChatHistoryOpen}
            isDocumentManagerOpen={isDocumentManagerOpen}
          />
        </Suspense>
        <main className="flex-grow p-4 overflow-y-auto">
          <div className="flex flex-col space-y-4">
            {messages.length === 0 && !streamingMessage ? (
              <div className="flex flex-col items-center justify-center min-h-[60vh] text-center space-y-6 animate-fade-in">
                <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center animate-bounce-subtle">
                  <span className="text-3xl">🤖</span>
                </div>
                <div className="space-y-2 max-w-md animate-slide-up">
                  <h2 className="text-2xl font-bold text-foreground">Welcome to TcyberChatbot</h2>
                  <p className="text-muted-foreground">
                    Your local-first AI assistant. Upload documents, ask questions, and get intelligent responses with citations.
                  </p>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-2xl w-full animate-slide-up" style={{ animationDelay: '0.2s' }}>
                  <div className="p-4 bg-card border border-border rounded-lg hover:shadow-md transition-shadow duration-200">
                    <div className="text-2xl mb-2">📄</div>
                    <h3 className="font-semibold mb-1">Document Upload</h3>
                    <p className="text-sm text-muted-foreground">Upload PDFs, images, and text files for analysis</p>
                  </div>
                  <div className="p-4 bg-card border border-border rounded-lg hover:shadow-md transition-shadow duration-200">
                    <div className="text-2xl mb-2">🎤</div>
                    <h3 className="font-semibold mb-1">Voice Input</h3>
                    <p className="text-sm text-muted-foreground">Record voice messages for hands-free interaction</p>
                  </div>
                  <div className="p-4 bg-card border border-border rounded-lg hover:shadow-md transition-shadow duration-200">
                    <div className="text-2xl mb-2">🔍</div>
                    <h3 className="font-semibold mb-1">Smart Search</h3>
                    <p className="text-sm text-muted-foreground">Get answers with document citations and web search</p>
                  </div>
                </div>
                <div className="text-sm text-muted-foreground max-w-md animate-slide-up" style={{ animationDelay: '0.4s' }}>
                  <p>Start by uploading a document or asking a question below.</p>
                </div>
              </div>
            ) : (
              <>
                {messages.map((msg) => (
                  <Suspense key={msg.id} fallback={<LoadingFallback />}>
                    <ChatBubble message={msg} onDelete={deleteMessage} />
                  </Suspense>
                ))}
                {streamingMessage && (
                  <Suspense fallback={<LoadingFallback />}>
                    <ChatBubble message={streamingMessage} isStreaming={isStreaming} />
                  </Suspense>
                )}
              </>
            )}
          </div>
        </main>

        {/* Undo notification */}
        {lastDeletedMessage && (
          <div className="fixed bottom-20 left-1/2 transform -translate-x-1/2 bg-card text-card-foreground border border-border px-4 py-3 rounded-lg shadow-xl z-50 flex items-center gap-3 animate-slide-up">
            <span className="text-sm font-medium">Message deleted</span>
            <button
              onClick={undoDeleteMessage}
              className="text-primary hover:text-primary/80 underline text-sm font-medium transition-colors duration-200"
            >
              Undo
            </button>
          </div>
        )}

        <Suspense fallback={<LoadingFallback />}>
          <MessageInput />
        </Suspense>
      </div>
      <Suspense fallback={<LoadingFallback />}>
        <DocumentManagerDrawer isOpen={isDocumentManagerOpen} onClose={() => setIsDocumentManagerOpen(false)} />
      </Suspense>
    </div>
  );
}
