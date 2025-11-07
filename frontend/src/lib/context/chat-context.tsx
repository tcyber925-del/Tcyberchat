'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { ChatSession } from '@/types/chat';
import { Message } from '@/types/message';
import { Document } from '@/types/document';
import { UserSettings } from '@/types/settings';
import { sendMessageStreaming, getModels } from '@/lib/api/chat';
import { uploadDocument as apiUploadDocument, getDocuments as apiGetDocuments, deleteDocument as apiDeleteDocument } from '@/lib/api/documents';
import { useToast } from './toast-context'; // Import useToast

interface ChatContextType {
  isSidebarOpen: boolean;
  setIsSidebarOpen: (open: boolean) => void;
  sessions: ChatSession[];
  setSessions: (sessions: ChatSession[]) => void;
  currentSession: ChatSession | null;
  setCurrentSession: (session: ChatSession | null) => void;
  messages: Message[];
  setMessages: (messages: Message[]) => void;
  documents: Document[];
  setDocuments: (documents: Document[]) => void;
  selectedDocumentId: string | null; // Add selectedDocumentId
  setSelectedDocumentId: (documentId: string | null) => void; // Add setSelectedDocumentId
  addMessage: (message: Message) => void;
  selectSession: (sessionId: string | null) => void;
  selectDocument: (documentId: string) => void;
  uploadDocument: (file: File) => Promise<void>;
  deleteDocument: (documentId: string) => Promise<void>; // Add deleteDocument
  isLoading: boolean;
  error: string | null;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void; // Add setError
  isModelMenuOpen: boolean; // Add isModelMenuOpen
  setIsModelMenuOpen: (isOpen: boolean) => void; // Add setIsModelMenuOpen
  localModels: any[]; // Add localModels
  cloudModels: any[]; // Add cloudModels
  // Streaming functionality
  isStreaming: boolean;
  streamingMessage: Message | null;
  sendStreamingMessage: (content: string, conversationId?: string) => Promise<void>;
  stopStreaming: () => void;
  deleteMessage: (messageId: string) => void;
  undoDeleteMessage: () => void;
  lastDeletedMessage: Message | null;
}

import { useSettings } from './settings-context';

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export function ChatProvider({ children }: { children: ReactNode }) {
  const { settings, isLoading: isSettingsLoading } = useSettings();
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocumentId, setSelectedDocumentId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isModelMenuOpen, setIsModelMenuOpen] = useState(false); // Initialize isModelMenuOpen
  const [localModels, setLocalModels] = useState<any[]>([]);
  const [cloudModels, setCloudModels] = useState<any[]>([]);

  // Streaming state
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState<Message | null>(null);

  // Undo state
  const [deletedMessages, setDeletedMessages] = useState<Message[]>([]);
  const [lastDeletedMessage, setLastDeletedMessage] = useState<Message | null>(null);

  const { showToast } = useToast(); // Use the toast hook

  // Constants for localStorage keys
  const SESSIONS_STORAGE_KEY = 'tcyber-chat-sessions';

  // Load conversations from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(SESSIONS_STORAGE_KEY);
      if (stored) {
        const parsedSessions = JSON.parse(stored);
        const sessionsWithDates = parsedSessions.map((session: any) => ({
          ...session,
          timestamp: new Date(session.timestamp),
          lastActivity: new Date(session.lastActivity),
        }));
        setSessions(sessionsWithDates);
      }
    } catch (error) {
      console.warn('Failed to load sessions from localStorage:', error);
      showToast('Failed to load chat sessions.', 'error');
    }
  }, [showToast]);

  // Fetch documents on mount
  useEffect(() => {
    const fetchDocuments = async () => {
      try {
        const fetchedDocuments = await apiGetDocuments();
        setDocuments(fetchedDocuments);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to fetch documents';
        setError(errorMessage);
        showToast(errorMessage, 'error');
      }
    };
    fetchDocuments();
  }, [showToast]);

  // Fetch models on mount
  useEffect(() => {
    const fetchModels = async () => {
      try {
        const allModels = await getModels();
        const local = (allModels || []).filter(m => m.provider === 'llama.cpp');
        const cloud = (allModels || []).filter(m => m.provider !== 'llama.cpp');
        setLocalModels(local);
        setCloudModels(cloud);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to fetch models';
        setError(errorMessage);
        showToast(errorMessage, 'error');
      }
    };
    fetchModels();
  }, [showToast]);

  // Save sessions to localStorage whenever they change
  useEffect(() => {
    try {
      localStorage.setItem(SESSIONS_STORAGE_KEY, JSON.stringify(sessions));
    }  catch (error) {
      console.warn('Failed to save sessions to localStorage:', error);
      showToast('Failed to save chat sessions.', 'error');
    }
  }, [sessions]);

  const addMessage = (message: Message) => {
    setMessages((prev) => [...prev, message]);
  };

  const selectSession = (sessionId: string | null) => {
    if (sessionId === null) {
      setCurrentSession(null);
      setMessages([]);
      showToast('Started a new chat.', 'info');
      return;
    }
    // TODO: Implement fetching session details from API
    const newSession: ChatSession = {
      id: sessionId,
      title: `Chat ${sessionId.substring(0, 4)}`,
      timestamp: new Date(),
      lastActivity: new Date(),
      messageCount: 0,
    };
    setCurrentSession(newSession);
    setMessages([]); // Clear messages for new session
    showToast(`Switched to session ${newSession.title}`, 'info');
  };

  const selectDocument = (documentId: string) => {
    setSelectedDocumentId(documentId);
    showToast(`Selected document: ${documentId}`, 'info');
  };

  const uploadDocument = async (file: File) => {
    setIsLoading(true);
    setError(null);
    try {
      const newDocument = await apiUploadDocument(file);
      setDocuments((prev) => [...prev, newDocument]);
      showToast(`Document "${newDocument.filename}" uploaded successfully!`, 'success');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to upload document';
      setError(errorMessage);
      showToast(errorMessage, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const deleteDocument = async (documentId: string) => {
    setIsLoading(true);
    setError(null);
    try {
      await apiDeleteDocument(documentId); // Call the API delete function
      setDocuments((prev) => prev.filter((doc) => doc.id !== documentId));
      if (selectedDocumentId === documentId) {
        setSelectedDocumentId(null); // Deselect if the deleted document was selected
      }
      showToast(`Document deleted successfully!`, 'success');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete document';
      setError(errorMessage);
      showToast(errorMessage, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const sendStreamingMessage = async (content: string, conversationId?: string) => {
    if (isStreaming) return; // Prevent multiple simultaneous streams

    setIsStreaming(true);
    setError(null);

    // Get selected model from settings
    const selectedModel = settings.selectedModel;

    // Add user message immediately
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      content,
      timestamp: new Date(),
      role: 'user',
      conversationId: conversationId || currentSession?.id || 'default',
    };
    addMessage(userMessage);

    // Create placeholder streaming message (visible immediately while model warms)
    const streamingMsg: Message = {
      id: `ai-${Date.now()}`,
      content: 'Assistant is typing...',
      timestamp: new Date(),
      role: 'assistant',
      conversationId: conversationId || currentSession?.id || 'default',
      citations: [],
    };
    setStreamingMessage(streamingMsg);

    try {
      await sendMessageStreaming(
        content,
        conversationId || currentSession?.id,
        selectedModel, // Pass the selected model
    selectedDocumentId ?? undefined, // Pass the selected document ID or undefined
        // onChunk callback - update streaming message content
        (chunk: string) => {
          // eslint-disable-next-line no-console
          console.debug('[chat-context] onChunk received length=', chunk?.length, 'preview=', chunk?.slice(0,50));
          setStreamingMessage(prev => {
            if (!prev) return null;
            // If placeholder is present, replace it with the first real chunk
            const placeholder = 'Assistant is typing...';
            const newContent = prev.content === placeholder ? chunk : prev.content + chunk;
            return {
              ...prev,
              content: newContent
            };
          });
        },
        // onComplete callback - finalize the message
        (finalMessage) => {
          // finalMessage is expected to be { content, messageId?, citations? }
          // eslint-disable-next-line no-console
          console.debug('[chat-context] onComplete finalMessage preview=', finalMessage?.content?.slice(0,80));
          setStreamingMessage(null);

          // Format the backend content and citations into a clear, human-readable Markdown string
          const formatFinal = (msg: { content?: string; citations?: any[] | undefined }) => {
            const parts: string[] = [];
            const main = msg?.content?.trim() ?? '';
            if (main) parts.push(main);

            const cit = msg?.citations ?? [];
            if (Array.isArray(cit) && cit.length > 0) {
              parts.push('\n---\n');
              parts.push('Citations:');
              cit.forEach((c: any, idx: number) => {
                const id = c.docId ?? c.id ?? 'unknown-doc';
                const page = c.page !== undefined && c.page !== null ? `, page ${c.page}` : '';
                parts.push(`\n${idx + 1}. ${id}${page}`);
                if (c.snippet) {
                  // indent snippet as blockquote
                  const snippet = String(c.snippet).trim();
                  parts.push(`\n> ${snippet.replace(/\r?\n/g, '\n> ')}`);
                }
              });
            }

            return parts.join('\n');
          };

          const formattedContent = formatFinal(finalMessage as any);

          const aiMessage: Message = {
            id: (finalMessage as any)?.messageId ?? `ai-${Date.now()}`,
            content: formattedContent,
            timestamp: new Date(),
            role: 'assistant',
            conversationId: conversationId || currentSession?.id || 'default',
            citations: (finalMessage as any)?.citations ?? [],
          };
          addMessage(aiMessage);
          showToast('AI response received!', 'success');

          // Update session last activity
          if (currentSession) {
            setCurrentSession({
              ...currentSession,
              lastActivity: new Date(),
              messageCount: currentSession.messageCount + 2
            });
          }
        },
        // onError callback
        (error: Error) => {
          // eslint-disable-next-line no-console
          console.error('[chat-context] onError', error);
          setError(error.message);
          setStreamingMessage(null);
          showToast(`Error: ${error.message}`, 'error');
        }
      );
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      setError(errorMessage);
      setStreamingMessage(null);
      showToast(`Error: ${errorMessage}`, 'error');
    } finally {
      setIsStreaming(false);
    }
  };

  const stopStreaming = () => {
    setIsStreaming(false);
    setStreamingMessage(null);
    showToast('Streaming stopped.', 'info');
  };

  const deleteMessage = (messageId: string) => {
    const messageToDelete = messages.find(msg => msg.id === messageId);
    if (messageToDelete) {
      setMessages(prev => prev.filter(msg => msg.id !== messageId));
      setDeletedMessages(prev => [...prev, messageToDelete]);
      setLastDeletedMessage(messageToDelete);
      showToast('Message deleted. Click "Undo" to restore.', 'info', 10000);

      // Auto-clear undo after 10 seconds
      setTimeout(() => {
        setLastDeletedMessage(null);
        setDeletedMessages(prev => prev.filter(msg => msg.id !== messageId));
      }, 10000);
    }
  };

  const undoDeleteMessage = () => {
    if (lastDeletedMessage) {
      setMessages(prev => {
        // Insert the message back in the correct position based on timestamp
        const newMessages = [...prev, lastDeletedMessage];
        return newMessages.sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime());
      });
      setDeletedMessages(prev => prev.filter(msg => msg.id !== lastDeletedMessage.id));
      setLastDeletedMessage(null);
      showToast('Message restored.', 'success');
    }
  };

  return (
    <ChatContext.Provider
      value={{
        isSidebarOpen,
        setIsSidebarOpen,
        sessions,
        setSessions,
        currentSession,
        setCurrentSession,
        messages,
        setMessages,
        documents,
        setDocuments,
        selectedDocumentId,
        setSelectedDocumentId,
        addMessage,
        selectSession,
        selectDocument,
        uploadDocument,
        deleteDocument, // Add deleteDocument
        isLoading,
        error,
        setLoading: setIsLoading,
        setError,
        isModelMenuOpen,
        setIsModelMenuOpen,
        localModels,
        cloudModels,
        // Streaming functionality
        isStreaming,
        streamingMessage,
        sendStreamingMessage,
        stopStreaming,
        // Message management
        deleteMessage,
        undoDeleteMessage,
        lastDeletedMessage,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
}

export function useChat() {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
}
