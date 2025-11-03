'use client';

import React, { Suspense, lazy, useState, useCallback, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { useSettings } from '@/lib/context/settings-context';
import SettingsPanel from '@/components/settings-panel';
import { useChat } from '@/lib/context/chat-context';
import { Message as ChatMessageType } from '@/types/message';
import '@/lib/styles/markdown.css';
import { Button } from '@/components/ui/button';
import { Chat, ChatInput, ChatMessage } from '@/components/ui/chat';

// Lazy load components for performance optimization
const TopBar = lazy(() => import('@/components/top-bar'));
const ChatHistoryDrawer = lazy(() => import('@/components/chat-history-drawer'));
const DocumentManagerDrawer = lazy(() => import('@/components/document-manager-drawer'));
const SettingsDrawer = lazy(() => import('@/components/settings-drawer'));

// Loading fallback component
const LoadingFallback = () => (
  <div className="flex items-center justify-center p-4">
    <div className="animate-spin rounded-full h-6 w-6 border-2 border-primary border-t-transparent"></div>
  </div>
);

export default function Home() {
  const { messages, setMessages, isLoading, isStreaming, streamingMessage, sendStreamingMessage, stopStreaming } = useChat();
  const { isSettingsOpen, toggleSettingsPanel } = useSettings();
  const [input, setInput] = useState('');
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

  const handleNewChat = useCallback(() => {
    setMessages([]); // Clear the chat messages
    setIsChatHistoryOpen(false);
    setIsDocumentManagerOpen(false);
  }, [setMessages]);

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
  }, []);

  const handleSubmitLocal = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    // If already streaming, stop the stream
    if (isStreaming) {
      stopStreaming();
      return;
    }
    const text = input?.trim();
    if (!text) return;
    try {
      await sendStreamingMessage(text);
      setInput('');
    } catch (err) {
      // swallow - context handles error state and toasts
      console.error('send error', err);
    }
  }, [input, sendStreamingMessage, isStreaming, stopStreaming]);

  const chatRef = useRef<HTMLDivElement | null>(null);

  // Auto-scroll when messages or streamingMessage change
  useEffect(() => {
    const el = chatRef.current;
    if (!el) return;
    // Scroll to bottom smoothly
    try {
      el.scrollTop = el.scrollHeight;
    } catch {}
  }, [messages, streamingMessage]);

  // Only render certain debug UI on the client to avoid hydration mismatches
  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <div data-testid="main-layout" className="flex h-screen bg-background">
      <Suspense fallback={<LoadingFallback />}>
        <ChatHistoryDrawer isOpen={isChatHistoryOpen} onClose={() => setIsChatHistoryOpen(false)} />
      </Suspense>

      <Suspense fallback={<LoadingFallback />}>
        <SettingsDrawer isOpen={isSettingsOpen} onClose={toggleSettingsPanel} />
      </Suspense>

      <div className="flex flex-col flex-grow">
        <Suspense fallback={<LoadingFallback />}>
          <TopBar
            onToggleChatHistory={toggleChatHistory}
            onToggleDocumentManager={toggleDocumentManager}
            isChatHistoryOpen={isChatHistoryOpen}
            isDocumentManagerOpen={isDocumentManagerOpen}
            onNewChat={handleNewChat} // Pass handleNewChat to TopBar
          />
        </Suspense>
  <main ref={chatRef} className="flex-grow p-4 overflow-y-auto">
          <div>
            <div>
              {messages.length === 0 && !isLoading && !streamingMessage ? (
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
                <Chat>
                  {messages.map((m: ChatMessageType) => {
                    // Normalize role: some messages may use `type` or `role`, and older code used 'ai'
                    const rawRole = (m as any).role ?? (m as any).type ?? 'assistant';
                    const role = rawRole === 'ai' ? 'assistant' : rawRole;
                    return (
                      <ChatMessage key={m.id} role={role as any}>
                        <ReactMarkdown>{m.content}</ReactMarkdown>
                      </ChatMessage>
                    );
                  })}
                  {/* Render in-progress streaming message */}
                  {streamingMessage && (
                    <ChatMessage key={streamingMessage.id} role="assistant">
                      <ReactMarkdown>{streamingMessage.content}</ReactMarkdown>
                    </ChatMessage>
                  )}
                </Chat>
              )}
            </div>
          </div>
        </main>

        {/* Undo notification - Removed as it's not directly supported by AI SDK's useChat */}
        {/* {lastDeletedMessage && (
          <div className="fixed bottom-20 left-1/2 transform -translate-x-1/2 bg-card text-card-foreground border border-border px-4 py-3 rounded-lg shadow-xl z-50 flex items-center gap-3 animate-slide-up">
            <span className="text-sm font-medium">Message deleted</span>
            <button
              onClick={undoDeleteMessage}
              className="text-primary hover:text-primary/80 underline text-sm font-medium transition-colors duration-200"
            >
              Undo
            </button>
          </div>
        )} */}

        <form onSubmit={handleSubmitLocal} className="p-4 border-t bg-background flex items-center space-x-2">
          <ChatInput value={input} onChange={handleInputChange} placeholder="Type your message here..." className="flex-grow" />
          <Button type="submit" disabled={isLoading || isStreaming || !input.trim()}>
            {isStreaming ? 'Stop' : 'Send'}
          </Button>
        </form>
      </div>
      <Suspense fallback={<LoadingFallback />}>
        <DocumentManagerDrawer isOpen={isDocumentManagerOpen} onClose={() => setIsDocumentManagerOpen(false)} />
      </Suspense>

      {/* Debug overlay (client-only to avoid hydration mismatches) */}
      {/* debug overlay removed */}
    </div>
  );
}
