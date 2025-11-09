'use client';

import React, { Suspense, lazy, useState, useCallback, useRef, useEffect } from 'react';
import { useSettings } from '@/lib/context/settings-context';
import SettingsPanel from '@/components/settings-panel';
import { useChat } from '@/lib/context/chat-context';
import { Message as ChatMessageType } from '@/types/message';
import '@/lib/styles/markdown.css';
import { Button } from '@/components/ui/button';
import { Chat, ChatInput, ChatMessage } from '@/components/ui/chat';
import { MarkdownRenderer } from '@/components/ui/markdown-renderer';
import { TypingIndicator } from '@/components/ui/typing-indicator';
import { ChatInputModal } from '@/components/ui/chat-input-modal';
import { cn } from '@/lib/utils';
import { useToast } from '@/lib/context/toast-context';
import { Plus, Globe } from 'lucide-react';

import Sidebar from '@/components/sidebar';
import { DocumentIndicator } from '@/components/document-indicator';

// Lazy load components for performance optimization
const SettingsDrawer = lazy(() => import('@/components/settings-drawer'));

// Loading fallback component
const LoadingFallback = () => (
  <div className="flex items-center justify-center p-4">
    <div className="animate-spin rounded-full h-6 w-6 border-2 border-primary border-t-transparent"></div>
  </div>
);

export default function Home() {
  const { 
    messages, 
    setMessages, 
    isLoading, 
    isStreaming, 
    streamingMessage, 
    sendStreamingMessage, 
    stopStreaming,
    sessions,
    documents,
    selectSession,
    selectDocument,
    uploadDocument,
    deleteDocument,
    selectedDocumentId,
    setSelectedDocumentId,
  } = useChat();
  const { isSettingsOpen, toggleSettingsPanel } = useSettings();
  const { showToast } = useToast();
  const [input, setInput] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [webSearchEnabled, setWebSearchEnabled] = useState(false);
  const [editingMessageId, setEditingMessageId] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const inputContainerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const handleAttachmentClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      uploadDocument(file);
    }
    // Clear the input value so that selecting the same file twice still triggers the onChange event
    event.target.value = '';
  };

  // Drag and drop handlers
  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    // Only show drag state if dragging files (not text/links)
    const hasFiles = Array.from(e.dataTransfer.types).includes('Files');
    if (hasFiles) {
      setIsDragging(true);
    }
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    // Only set dragging to false if we're leaving the drop zone (not just a child element)
    const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
    const x = e.clientX;
    const y = e.clientY;
    if (x < rect.left || x > rect.right || y < rect.top || y > rect.bottom) {
      setIsDragging(false);
    }
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    // Check if dropped item is a file
    const items = Array.from(e.dataTransfer.items);
    const hasFiles = items.some(item => item.kind === 'file');
    
    if (!hasFiles) {
      showToast('Please drop a file to upload.', 'warning');
      return;
    }

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      const file = files[0];
      
      // Basic file validation
      if (file.size === 0) {
        showToast('Cannot upload empty file.', 'error');
        return;
      }
      
      // Check file size (e.g., 100MB limit)
      const maxSize = 100 * 1024 * 1024; // 100MB
      if (file.size > maxSize) {
        showToast(`File is too large. Maximum size is ${maxSize / (1024 * 1024)}MB.`, 'error');
        return;
      }
      
      try {
        // Only upload the first file
        uploadDocument(file);
        if (files.length > 1) {
          showToast(`Only the first file was uploaded. ${files.length - 1} other file(s) were ignored.`, 'info');
        }
      } catch (error) {
        console.error('Error uploading file:', error);
        showToast('Failed to upload file. Please try again.', 'error');
      }
    }
  }, [uploadDocument, showToast]);

  const handleNewChat = useCallback(() => {
    setMessages([]); // Clear the chat messages
  }, [setMessages]);

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
  }, []);

  const handleEditMessage = useCallback((messageId: string, content: string) => {
    setEditingMessageId(messageId);
    setInput(content);
    // Focus the input field after a short delay to ensure it's rendered
    setTimeout(() => {
      inputRef.current?.focus();
      // Move cursor to end of text
      if (inputRef.current) {
        const length = inputRef.current.value.length;
        inputRef.current.setSelectionRange(length, length);
      }
    }, 100);
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
      // If editing a message, update it instead of sending a new one
      if (editingMessageId) {
        // Find the message and update it
        const messageToEdit = messages.find(m => m.id === editingMessageId);
        if (messageToEdit) {
          // Update the message content
          setMessages(prev => prev.map(m => 
            m.id === editingMessageId 
              ? { ...m, content: text, timestamp: new Date() }
              : m
          ));
          
          // Resend the edited message
          await sendStreamingMessage(text, undefined, webSearchEnabled);
          
          // Clear editing state
          setEditingMessageId(null);
          setInput('');
          setWebSearchEnabled(false);
          showToast('Message updated and resent!', 'success');
        }
      } else {
        // Normal send
        await sendStreamingMessage(text, undefined, webSearchEnabled);
        setInput('');
        setWebSearchEnabled(false); // Reset web search after sending
      }
    } catch (err) {
      // swallow - context handles error state and toasts
      console.error('send error', err);
    }
  }, [input, sendStreamingMessage, isStreaming, stopStreaming, webSearchEnabled, editingMessageId, messages, setMessages, showToast]);

  const chatRef = useRef<HTMLDivElement | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  // Smooth auto-scroll when messages or streamingMessage change
  useEffect(() => {
    const scrollToBottom = () => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
    };
    
    // Small delay to ensure DOM is updated
    const timeoutId = setTimeout(scrollToBottom, 100);
    return () => clearTimeout(timeoutId);
  }, [messages, streamingMessage]);

  // Only render certain debug UI on the client to avoid hydration mismatches
  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    setMounted(true);
  }, []);

  // Close modal when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (inputContainerRef.current && !inputContainerRef.current.contains(event.target as Node)) {
        setIsModalOpen(false);
      }
    };

    if (isModalOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => {
        document.removeEventListener('mousedown', handleClickOutside);
      };
    }
  }, [isModalOpen]);

  return (
    <div data-testid="main-layout" className="flex h-screen bg-background text-foreground">
      <Sidebar 
        sessions={sessions}
        documents={documents}
        onNewChat={handleNewChat}
        onSelectSession={selectSession}
        onSelectDocument={selectDocument}
        onUploadDocument={uploadDocument}
        onDeleteDocument={deleteDocument}
        onToggleSettings={toggleSettingsPanel}
        isLoading={isLoading}
      />

      <Suspense fallback={<LoadingFallback />}>
        <SettingsDrawer isOpen={isSettingsOpen} onClose={toggleSettingsPanel} />
      </Suspense>

      <div className="flex flex-col flex-grow">
        <header className="flex items-center p-4 border-b border-border">
          <h1 className="text-xl font-bold">TcyberChatbot</h1>
        </header>
        <main ref={chatRef} className="flex-grow p-4 overflow-y-auto scroll-smooth">
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
                    const isUserMessage = role === 'user';
                    return (
                      <ChatMessage 
                        key={m.id} 
                        role={role as any}
                        content={m.content}
                        timestamp={m.timestamp}
                        messageId={m.id}
                        onCopy={(text) => {
                          showToast('Message copied to clipboard!', 'success');
                        }}
                        onEdit={isUserMessage ? (content) => {
                          handleEditMessage(m.id, content);
                        } : undefined}
                      >
                        {isUserMessage ? (
                          <div className="whitespace-pre-wrap">{m.content}</div>
                        ) : (
                          <MarkdownRenderer content={m.content} />
                        )}
                      </ChatMessage>
                    );
                  })}
                  {/* Render in-progress streaming message */}
                  {streamingMessage && (
                    <ChatMessage 
                      key={streamingMessage.id} 
                      role="assistant"
                      content={streamingMessage.content}
                      timestamp={streamingMessage.timestamp}
                      isStreaming={isStreaming}
                      onCopy={(text) => {
                        showToast('Message copied to clipboard!', 'success');
                      }}
                    >
                      {streamingMessage.content === 'Assistant is typing...' ? (
                        <TypingIndicator />
                      ) : (
                        <MarkdownRenderer content={streamingMessage.content} />
                      )}
                    </ChatMessage>
                  )}
                  {/* Invisible element to scroll to */}
                  <div ref={messagesEndRef} />
                </Chat>
              )}
            </div>
          </div>
        </main>

        <div 
          className={cn(
            "border-t bg-background transition-colors duration-200",
            isDragging && "border-primary border-2 bg-primary/5"
          )}
          onDragEnter={handleDragEnter}
          onDragLeave={handleDragLeave}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
        >
          {/* Document indicator - shown when a document is selected */}
          {selectedDocumentId && (() => {
            const selectedDoc = documents.find(doc => doc.id === selectedDocumentId);
            // Only show indicator if document exists in the list
            // If document was deleted, it will be cleared when documents list updates
            if (!selectedDoc) {
              // Document not found - might have been deleted, clear selection
              if (selectedDocumentId) {
                // Use setTimeout to avoid state update during render
                setTimeout(() => setSelectedDocumentId(null), 0);
              }
              return null;
            }
            return (
              <div className="px-4 pt-3 pb-2">
                <DocumentIndicator
                  documentId={selectedDoc.id}
                  documentName={selectedDoc.filename}
                  onRemove={() => setSelectedDocumentId(null)}
                />
              </div>
            );
          })()}
          
          {/* Drag overlay hint */}
          {isDragging && (
            <div className="px-4 py-12 text-center border-2 border-dashed border-primary rounded-lg mx-4 my-2 bg-primary/10">
              <p className="text-primary font-medium text-lg">Drop file here to upload</p>
              <p className="text-primary/70 text-sm mt-1">Release to upload your document</p>
            </div>
          )}
          
          {/* Hide form when dragging to show drop zone clearly */}
          {!isDragging && (
            <div ref={inputContainerRef} className="relative">
              {/* Modal Overlay */}
              <ChatInputModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                onFileAttach={handleAttachmentClick}
                onWebSearchToggle={() => setWebSearchEnabled(!webSearchEnabled)}
                webSearchEnabled={webSearchEnabled}
              />
              
              <form onSubmit={handleSubmitLocal} className="p-4 flex items-center space-x-2">
                <input
                  type="file"
                  ref={fileInputRef}
                  className="hidden"
                  onChange={handleFileChange}
                />
                {/* Plus button to open modal */}
                <button
                  type="button"
                  onClick={() => setIsModalOpen(!isModalOpen)}
                  className={cn(
                    "p-2 text-muted-foreground hover:text-foreground rounded-full hover:bg-accent transition-colors",
                    isModalOpen && "bg-accent text-foreground"
                  )}
                  title="More options"
                  aria-label="More options"
                >
                  <Plus className="h-6 w-6" />
                </button>
                <ChatInput 
                  ref={inputRef}
                  value={input} 
                  onChange={handleInputChange} 
                  placeholder={editingMessageId ? "Edit your message..." : "Type your message here..."}
                  className="flex-grow"
                  onFocus={() => setIsModalOpen(false)}
                />
                {/* Web search indicator */}
                {webSearchEnabled && (
                  <div className="flex items-center gap-1 px-2 py-1 bg-primary/10 text-primary rounded-md text-xs font-medium">
                    <Globe className="h-3 w-3" />
                    <span>Web</span>
                  </div>
                )}
                {editingMessageId && (
                  <Button
                    type="button"
                    variant="ghost"
                    onClick={() => {
                      setEditingMessageId(null);
                      setInput('');
                    }}
                    className="text-muted-foreground hover:text-foreground"
                  >
                    Cancel
                  </Button>
                )}
                <Button type="submit" disabled={isLoading || isStreaming || !input.trim()}>
                  {isStreaming ? 'Stop' : editingMessageId ? 'Resend' : 'Send'}
                </Button>
              </form>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
