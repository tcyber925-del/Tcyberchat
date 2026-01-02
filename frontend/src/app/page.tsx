'use client';

import React, { Suspense, lazy, useState, useCallback, useRef, useEffect } from 'react';
import { Virtuoso } from 'react-virtuoso';
import { useSettings } from '@/lib/context/settings-context';
import { deepResearch, deepResearchStream } from '@/lib/api/chat';
import SettingsPanel from '@/components/settings-panel';
import { useChat } from '@/lib/context/chat-context';
import { Message } from '@/types/message';
import '@/lib/styles/markdown.css';
import { Button } from '@/components/ui/button';
import { Chat, ChatInput, ChatMessage } from '@/components/ui/chat';
import { MarkdownRenderer } from '@/components/ui/markdown-renderer';
import { TypingIndicator } from '@/components/ui/typing-indicator';
import { cn } from '@/lib/utils';
import { useToast } from '@/lib/context/toast-context';
import { Plus, Globe, Sparkles } from 'lucide-react';

import Sidebar from '@/components/sidebar';
import { DocumentIndicator } from '@/components/document-indicator';
import { DeepResearchProgress } from '@/components/ai-elements/deep-research-progress';
import { ConversationEmptyState } from '@/components/ai-elements/conversation';
import { Suggestions, Suggestion } from '@/components/ai-elements/suggestion';
import { ArtifactSidebar } from '@/components/ai-elements/artifact-sidebar';
import { useArtifact } from '@/lib/context/artifact-context';
import { 
  PromptInput, 
  PromptInputTextarea, 
  PromptInputToolbar, 
  PromptInputTools, 
  PromptInputSubmit,
  PromptInputProvider,
  PromptInputAttachments,
  PromptInputAttachment,
  PromptInputActionMenu,
  PromptInputActionMenuTrigger,
  PromptInputActionMenuContent,
  PromptInputActionMenuItem,
  PromptInputActionAddAttachments,
  PromptInputSpeechButton,
  usePromptInputController,
  type PromptInputMessage
} from '@/components/ai-elements/prompt-input';

// Lazy load components for performance optimization
const SettingsDrawer = lazy(() => import('@/components/settings-drawer'));

// Loading fallback component
const LoadingFallback = () => (
  <div className="flex items-center justify-center p-4">
    <div className="animate-spin rounded-full h-6 w-6 border-2 border-primary border-t-transparent"></div>
  </div>
);

function ChatInterface() {
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
    regenerateMessage,
    forkConversation,
    switchMessageVersion,
  } = useChat();
  const { settings, isSettingsOpen, toggleSettingsPanel } = useSettings();
  const { showToast } = useToast();
  const { setActiveArtifact } = useArtifact();
  const { textInput } = usePromptInputController();
  const input = textInput.value;
  const setInput = textInput.setInput;
  
  const [isDragging, setIsDragging] = useState(false);
  const [webSearchEnabled, setWebSearchEnabled] = useState(false);
  const [deepResearchEnabled, setDeepResearchEnabled] = useState(false);
  const [editingMessageId, setEditingMessageId] = useState<string | null>(null);
  const [isDeepRunning, setIsDeepRunning] = useState(false);
  const deepAbortRef = useRef<AbortController | null>(null);
  const deepStreamRef = useRef<any>(null);
  const [deepStep, setDeepStep] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
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

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);

      // Check if dropped item is a file
      const items = Array.from(e.dataTransfer.items);
      const hasFiles = items.some((item) => item.kind === 'file');

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
            showToast(
              `Only the first file was uploaded. ${files.length - 1} other file(s) were ignored.`,
              'info',
            );
          }
        } catch (error) {
          console.error('Error uploading file:', error);
          showToast('Failed to upload file. Please try again.', 'error');
        }
      }
    },
    [uploadDocument, showToast],
  );

  const handleNewChat = useCallback(() => {
    selectSession(null); // Proper reset: clears messages AND conversationId
  }, [selectSession]);

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
  }, [setInput]);

  // Auto-detect if query needs web search
  const shouldUseWebSearch = useCallback((query: string): boolean => {
    const timeSensitiveKeywords = [
      'latest',
      'recent',
      'news',
      'today',
      'current',
      'now',
      'this week',
      'this month',
      '2024',
      '2025',
      'update',
      'what is',
      'what are',
      'who is',
      'when did',
    ];
    const lowerQuery = query.toLowerCase();
    return timeSensitiveKeywords.some((keyword) => lowerQuery.includes(keyword));
  }, []);

  const handleDeepResearch = useCallback(async (text: string) => {
    if (!text) {
      showToast('Enter a question to run Deep Research.', 'warning');
      return;
    }
    if (isDeepRunning) {
      deepAbortRef.current?.abort();
      return;
    }
    try {
      setIsDeepRunning(true);
      setDeepStep('plan');
      showToast('Running deep research...', 'info');
      
      // Append the user message
      const userMsg: Message = {
        id: 'u-' + Date.now().toString(36),
        type: 'text',
        content: text,
        timestamp: new Date(),
        role: 'user',
        conversationId: '',
      };
      setMessages([...messages, userMsg]);

      const iterations = settings.deepResearchDefaultIterations ?? 2;
      const model = settings.selectedModel;
      
      // Use ref-based cleanup
      const es = deepResearchStream(text, model, iterations);
      deepStreamRef.current = es;
      
      es.addEventListener('step', (e: any) => {
        try {
          const payload = typeof e.data === 'string' ? JSON.parse(e.data) : e.data;
          if (payload?.step) setDeepStep(payload.step);
        } catch { }
      });
      
      es.addEventListener('final', (e: any) => {
        try {
          const payload = typeof e.data === 'string' ? JSON.parse(e.data) : e.data;
          const assistantMsg: Message = {
            id: 'a-' + (Date.now() + 1).toString(36),
            type: 'deep-research',
            content: payload.answer || 'No answer generated.',
            timestamp: new Date(),
            role: 'assistant',
            conversationId: '',
            citations: Array.isArray(payload.citations) ? payload.citations : [],
            iterations: payload.metadata?.iterations || 1,
            satisfied: payload.metadata?.satisfied ?? true,
            metadata: { ...payload.metadata, deepResearch: true },
          };
          // We need to use the functional update pattern if possible, or get fresh messages
          // Since our new context setMessages is a simple setter, we use the current messages
          setMessages([...messages, userMsg, assistantMsg]);
          setInput('');
          setDeepResearchEnabled(false);
          setDeepStep('complete');
        } catch (err) {
          console.error('Failed to parse final research result:', err);
        } finally {
          setIsDeepRunning(false);
          deepStreamRef.current = null;
        }
      });
      
      es.addEventListener('error', (e: any) => {
        console.error('Deep research error:', e);
        setIsDeepRunning(false);
        setDeepStep(null);
        deepStreamRef.current = null;
        showToast('Research stream interrupted or failed.', 'error');
      });
    } catch (e) {
      console.error('Deep research launch error:', e);
      setIsDeepRunning(false);
      showToast('Could not start deep research.', 'error');
    }
  }, [setMessages, settings, showToast, isDeepRunning, setInput]);

  const handleSubmitLocal = useCallback(
    async (message: PromptInputMessage) => {
      if (isStreaming) {
        stopStreaming();
        return;
      }
      const text = message.text?.trim();
      if (!text && (!message.files || message.files.length === 0)) return;

      if (deepResearchEnabled) {
        await handleDeepResearch(text || '');
        return;
      }

      const useWebSearch = webSearchEnabled || (text ? shouldUseWebSearch(text) : false);

      try {
        let attachedDocumentId = undefined;

        // Handle direct attachments from the prompt input
        if (message.files && message.files.length > 0) {
          const firstFile = message.files[0];
          if (firstFile.originalFile) {
            try {
              showToast('Uploading attachment...', 'info');
              const uploadedDoc = await uploadDocument(firstFile.originalFile);
              attachedDocumentId = uploadedDoc.id;
              // Clear attachments from input after successful "send" start
            } catch (err) {
              console.error('Failed to upload direct attachment:', err);
              // Continue without attachment if it fails? Or stop? 
              // For safety, let's stop and let the user know.
              return; 
            }
          }
        }

        // If editing a message, update it instead of sending a new one
        if (editingMessageId) {
          // Find the message and update it
          const messageToEdit = messages.find((m) => m.id === editingMessageId);
          if (messageToEdit) {
            // Update the message content
            const updatedMessages: Message[] = messages.map((m) =>
              m.id === editingMessageId ? ({ ...m, content: text, timestamp: new Date() } as Message) : m,
            );
            setMessages(updatedMessages);

            // Resend the edited message
            await sendStreamingMessage(text || '', undefined, useWebSearch);

            // Clear editing state
            setEditingMessageId(null);
            setWebSearchEnabled(false);
            if (useWebSearch && !webSearchEnabled) {
              showToast('Message updated and resent with web search!', 'success');
            } else {
              showToast('Message updated and resent!', 'success');
            }
          }
        } else {
          // Normal send
          // If we have an attachedDocumentId, use it. Otherwise use the globally selected one.
          const docIdToUse = attachedDocumentId || selectedDocumentId || undefined;
          
          await sendStreamingMessage(text || '', undefined, useWebSearch, docIdToUse);
          setWebSearchEnabled(false); // Reset web search after sending
          if (useWebSearch && !webSearchEnabled) {
            showToast('Web search enabled automatically for this query', 'info');
          }
        }
      } catch (err) {
        // swallow - context handles error state and toasts
        console.error('send error', err);
      }
    },
    [
      sendStreamingMessage,
      isStreaming,
      stopStreaming,
      webSearchEnabled,
      deepResearchEnabled,
      handleDeepResearch,
      editingMessageId,
      messages,
      setMessages,
      showToast,
      shouldUseWebSearch,
    ],
  );

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
  }, [setInput]);

  const handleSuggestionClick = useCallback((suggestion: string) => {
    setInput(suggestion);
    // Submit after a short delay to ensure state update is processed
    setTimeout(() => {
      handleSubmitLocal({ text: suggestion, files: [] });
    }, 10);
  }, [setInput, handleSubmitLocal]);

  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return <div className="flex h-screen items-center justify-center bg-background"><LoadingFallback /></div>;

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

      <div className="flex flex-col flex-grow overflow-x-hidden relative">
        <ArtifactSidebar />
        <header className="flex items-center p-4 border-b border-border">
          <h1 className="text-xl font-bold">TcyberChatbot</h1>
        </header>
        
        <div className="flex-grow overflow-hidden relative flex flex-col">
          {messages.length === 0 && !streamingMessage ? (
            <div className="flex-grow overflow-y-auto p-4">
              <ConversationEmptyState
                title="Welcome to TcyberChatbot"
                description="Your local-first AI assistant. Upload documents, ask questions, and get intelligent responses with citations."
                className="min-h-[60vh]"
              >
                <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center animate-bounce-subtle mb-4">
                  <span className="text-3xl">🤖</span>
                </div>
                
                <div className="w-full max-w-2xl mt-8">
                  <p className="text-xs font-semibold text-muted-foreground uppercase tracking-widest mb-4">Suggested Starters</p>
                  <Suggestions>
                    <Suggestion 
                      suggestion="What can you do?" 
                      onClick={handleSuggestionClick} 
                    />
                    <Suggestion 
                      suggestion="Analyze my uploaded documents" 
                      onClick={handleSuggestionClick} 
                    />
                    <Suggestion 
                      suggestion="Search for latest AI news" 
                      onClick={handleSuggestionClick} 
                    />
                    <Suggestion 
                      suggestion="Explain deep research mode" 
                      onClick={handleSuggestionClick} 
                    />
                  </Suggestions>
                </div>

                <div
                  className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-2xl w-full mt-12 animate-slide-up"
                  style={{ animationDelay: '0.2s' }}
                >
                  <div className="p-4 bg-card border border-border rounded-lg hover:shadow-md transition-shadow duration-200 text-left">
                    <div className="text-2xl mb-2">📄</div>
                    <h3 className="font-semibold mb-1">Document Upload</h3>
                    <p className="text-xs text-muted-foreground">
                      Upload PDFs, images, and text files for analysis
                    </p>
                  </div>
                  <div className="p-4 bg-card border border-border rounded-lg hover:shadow-md transition-shadow duration-200 text-left">
                    <div className="text-2xl mb-2">🎤</div>
                    <h3 className="font-semibold mb-1">Voice Input</h3>
                    <p className="text-xs text-muted-foreground">
                      Record voice messages for hands-free interaction
                    </p>
                  </div>
                  <div className="p-4 bg-card border border-border rounded-lg hover:shadow-md transition-shadow duration-200 text-left">
                    <div className="text-2xl mb-2">🔍</div>
                    <h3 className="font-semibold mb-1">Smart Search</h3>
                    <p className="text-xs text-muted-foreground">
                      Get answers with document citations and web search
                    </p>
                  </div>
                </div>
              </ConversationEmptyState>
            </div>
          ) : (
            <div className="flex-grow relative h-full w-full">
              <Chat className="h-full w-full overflow-hidden">
                <Virtuoso
                  style={{ height: '100%', width: '100%' }}
                  data={messages}
                  followOutput="auto"
                  initialTopMostItemIndex={messages.length - 1}
                  components={{
                    Footer: () => streamingMessage ? (
                      <div className="pt-4 pb-4">
                        <ChatMessage
                          key={streamingMessage.id}
                          role="assistant"
                          content={(streamingMessage as any).content || ""}
                          timestamp={streamingMessage.timestamp}
                          isStreaming={isStreaming}
                          onCopy={(text: string) => {
                            showToast('Message copied to clipboard!', 'success');
                          }}
                        >
                          {(streamingMessage as any).content === 'Assistant is typing...' ? (
                            <TypingIndicator />
                          ) : (
                            <MarkdownRenderer content={(streamingMessage as any).content || ""} />
                          )}
                        </ChatMessage>
                      </div>
                    ) : null
                  }}
                  itemContent={(index, m) => {
                    const rawRole = (m as any).role ?? (m as any).type ?? 'assistant';
                    const role = rawRole === 'ai' ? 'assistant' : rawRole;
                    const isUserMessage = role === 'user';
                    const mContent = (m as any).content || "";
                    
                    return (
                      <div className="pb-4 px-4">
                        <ChatMessage
                          key={m.id}
                          role={role as any}
                          type={m.type}
                          content={mContent}
                          timestamp={m.timestamp}
                          messageId={m.id}
                          meta={(m as any).metadata}
                          citations={(m as any).citations}
                          versionIndex={m.activeVersionIndex}
                          totalVersions={m.versions?.length || 1}
                          onVersionChange={(idx) => switchMessageVersion(m.id, idx)}
                          onRegenerate={!isUserMessage ? () => regenerateMessage(m.id) : undefined}
                          onBranch={!isUserMessage ? () => forkConversation(m.id, mContent) : undefined}
                          onCopy={(text: string) => {
                            showToast('Message copied to clipboard!', 'success');
                          }}
                          onEdit={
                            isUserMessage
                              ? (content) => {
                                handleEditMessage(m.id, content);
                              }
                              : undefined
                          }
                          onPin={(content) => {
                            setActiveArtifact({
                              id: m.id,
                              type: 'report',
                              title: 'Research Report',
                              content: content,
                            });
                            showToast('Pinned to workspace!', 'success');
                          }}
                        >
                          {isUserMessage ? (
                            <div className="whitespace-pre-wrap">{mContent}</div>
                          ) : (
                            <MarkdownRenderer content={mContent} />
                          )}
                        </ChatMessage>
                      </div>
                    );
                  }}
                />
              </Chat>
            </div>
          )}
        </div>

        <div
          className={cn(
            'border-t bg-background transition-colors duration-200',
            isDragging && 'border-primary border-2 bg-primary/5',
          )}
          onDragEnter={handleDragEnter}
          onDragLeave={handleDragLeave}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
        >
          {selectedDocumentId &&
            (() => {
              const selectedDoc = documents.find((doc) => doc.id === selectedDocumentId);
              if (!selectedDoc) {
                setTimeout(() => setSelectedDocumentId(null), 0);
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

          {isDragging && (
            <div className="px-4 py-12 text-center border-2 border-dashed border-primary rounded-lg mx-4 my-2 bg-primary/10">
              <p className="text-primary font-medium text-lg">Drop file here to upload</p>
              <p className="text-primary/70 text-sm mt-1">Release to upload your document</p>
            </div>
          )}

          {!isDragging && (
            <div className="relative">
              <PromptInput
                onSubmit={handleSubmitLocal}
                className="p-4"
                inputGroupClassName={cn(
                  "max-w-4xl mx-auto shadow-sm transition-all duration-300 bg-card border-border",
                  deepResearchEnabled && "border-violet-500/50 ring-violet-500/20 ring-2"
                )}
              >
                <PromptInputAttachments>
                  {(file) => <PromptInputAttachment data={file} />}
                </PromptInputAttachments>
                
                <PromptInputTextarea
                  placeholder={
                    editingMessageId ? 'Edit your message...' : 
                    deepResearchEnabled ? 'Ask a deep research question...' : 
                    'Type your message here...'
                  }
                  className="max-h-[200px]"
                />
                
                <PromptInputToolbar>
                  <PromptInputTools>
                    <PromptInputActionMenu>
                      <PromptInputActionMenuTrigger />
                      <PromptInputActionMenuContent>
                                              <PromptInputActionAddAttachments />
                                              <PromptInputActionMenuItem 
                                                onClick={() => setWebSearchEnabled(!webSearchEnabled)}
                                                textValue={`Web Search ${webSearchEnabled ? "Enabled" : "Disabled"}`}
                                              >
                                                <Globe className={cn("mr-2 size-4", webSearchEnabled && "text-primary")} />
                                                Web Search {webSearchEnabled ? "(Enabled)" : "(Disabled)"}
                                              </PromptInputActionMenuItem>
                                              <PromptInputActionMenuItem 
                                                onClick={() => setDeepResearchEnabled(!deepResearchEnabled)}
                                                textValue={`Deep Research ${deepResearchEnabled ? "Enabled" : "Disabled"}`}
                                              >
                                                <Sparkles className={cn("mr-2 size-4", deepResearchEnabled && "text-violet-500")} />
                                                Deep Research {deepResearchEnabled ? "(Enabled)" : "(Disabled)"}
                                              </PromptInputActionMenuItem>
                        
                      </PromptInputActionMenuContent>
                    </PromptInputActionMenu>
                    
                    <PromptInputSpeechButton />
                    
                    {deepResearchEnabled && (
                      <div className="flex items-center gap-1 px-2 py-1 bg-violet-600 text-white rounded-md text-[10px] font-bold shadow-sm animate-in zoom-in-90">
                        <Sparkles className="h-3 w-3" />
                        <span>DEEP</span>
                      </div>
                    )}
                    {(webSearchEnabled || (!deepResearchEnabled && input.trim() && shouldUseWebSearch(input))) && (
                      <div className="flex items-center gap-1 px-2 py-1 bg-primary/10 text-primary rounded-md text-[10px] font-bold">
                        <Globe className="h-3 w-3" />
                        <span>WEB</span>
                      </div>
                    )}
                  </PromptInputTools>
                  
                  <PromptInputSubmit 
                    status={isStreaming ? 'streaming' : isLoading ? 'submitted' : undefined}
                  >
                    {editingMessageId ? 'Resend' : undefined}
                  </PromptInputSubmit>
                </PromptInputToolbar>
              </PromptInput>

              {isDeepRunning && (
                <div className="px-4 pb-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
                  <div className="bg-card border border-border rounded-xl p-4 shadow-sm relative">
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon-sm"
                      className="absolute top-2 right-2 text-muted-foreground hover:text-destructive transition-colors"
                      onClick={() => {
                        try { deepStreamRef.current?.close(); } catch { }
                        deepStreamRef.current = null;
                        deepAbortRef.current?.abort();
                      }}
                      title="Cancel Research"
                    >
                      <Plus className="h-4 w-4 rotate-45" />
                    </Button>
                    <DeepResearchProgress currentStep={deepStep} />
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function Home() {
  return (
    <PromptInputProvider>
      <ChatInterface />
    </PromptInputProvider>
  );
}