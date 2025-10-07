'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { ChatSession } from '@/types/chat';
import { Message } from '@/types/message';
import { Document } from '@/types/document';
import { UserSettings } from '@/types/settings';
import { sendMessageStreaming } from '@/lib/api/chat';
import { uploadDocument as apiUploadDocument } from '@/lib/api/documents';
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
  userSettings: UserSettings;
  setUserSettings: (settings: UserSettings) => void;
  addMessage: (message: Message) => void;
  selectSession: (sessionId: string) => void;
  selectDocument: (documentId: string) => void;
  uploadDocument: (file: File) => Promise<void>;
  isLoading: boolean;
  error: string | null;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  // Streaming functionality
  isStreaming: boolean;
  streamingMessage: Message | null;
  sendStreamingMessage: (content: string, conversationId?: string) => Promise<void>;
  stopStreaming: () => void;
  deleteMessage: (messageId: string) => void;
  undoDeleteMessage: () => void;
  lastDeletedMessage: Message | null;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export function ChatProvider({ children }: { children: ReactNode }) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [userSettings, setUserSettings] = useState<UserSettings>({
    theme: 'system',
    selectedModel: 'Gemini',
    notifications: true,
    language: 'en',
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Streaming state
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState<Message | null>(null);

  // Undo state
  const [deletedMessages, setDeletedMessages] = useState<Message[]>([]);
  const [lastDeletedMessage, setLastDeletedMessage] = useState<Message | null>(null);

  const { showToast } = useToast(); // Use the toast hook

  // Conversation persistence
  const STORAGE_KEY = 'tcyber-chat-sessions';

  // Load conversations from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
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

  // Save sessions to localStorage whenever they change
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
    } catch (error) {
      console.warn('Failed to save sessions to localStorage:', error);
      showToast('Failed to save chat sessions.', 'error');
    }
  }, [sessions, showToast]);

  const addMessage = (message: Message) => {
    setMessages((prev) => [...prev, message]);
  };

  const selectSession = (sessionId: string) => {
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
    // TODO: Implement opening document viewer
    console.log('Selected document:', documentId);
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

  const sendStreamingMessage = async (content: string, conversationId?: string) => {
    if (isStreaming) return; // Prevent multiple simultaneous streams

    setIsStreaming(true);
    setError(null);

    // Get selected model from settings
    const selectedModel = userSettings.selectedModel;

    // Add user message immediately
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      content,
      timestamp: new Date(),
      type: 'user',
      conversationId: conversationId || currentSession?.id || 'default',
    };
    addMessage(userMessage);

    // Create placeholder streaming message
    const streamingMsg: Message = {
      id: `ai-${Date.now()}`,
      content: '',
      timestamp: new Date(),
      type: 'ai',
      conversationId: conversationId || currentSession?.id || 'default',
      citations: [],
    };
    setStreamingMessage(streamingMsg);

    try {
      await sendMessageStreaming(
        content,
        conversationId || currentSession?.id,
        selectedModel, // Pass the selected model
        // onChunk callback - update streaming message content
        (chunk: string) => {
          setStreamingMessage(prev => prev ? {
            ...prev,
            content: prev.content + chunk
          } : null);
        },
        // onComplete callback - finalize the message
        (finalMessage: Message) => {
          setStreamingMessage(null);
          addMessage(finalMessage);
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
        userSettings,
        setUserSettings,
        addMessage,
        selectSession,
        selectDocument,
        uploadDocument,
        isLoading,
        error,
        setLoading: setIsLoading,
        setError,
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
