'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { ChatSession } from '@/types/chat';
import { Message } from '@/types/message';
import { Document } from '@/types/document';
import { UserSettings } from '@/types/settings';
import { sendMessageStreaming, getModels, getConversations, getConversationMessages, deleteConversation, updateConversation, exportConversation } from '@/lib/api/chat';
import { uploadDocument as apiUploadDocument, getDocuments as apiGetDocuments, deleteDocument as apiDeleteDocument, updateDocument as apiUpdateDocument, exportDocument as apiExportDocument } from '@/lib/api/documents';
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
  renameDocument: (documentId: string, newFilename: string) => Promise<void>;
  shareDocument: (documentId: string) => Promise<void>;
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
  // Conversation management
  deleteSession: (sessionId: string) => Promise<void>;
  renameSession: (sessionId: string, newTitle: string) => Promise<void>;
  shareSession: (sessionId: string) => Promise<void>;
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

  // Load conversations from database on mount
  useEffect(() => {
    const loadConversations = async () => {
      try {
        setIsLoading(true);
        const conversations = await getConversations(50);
        // Validate and normalize conversation data
        const sessionsWithDates = conversations
          .filter((conv: any) => conv && conv.id) // Filter out invalid conversations
          .map((conv: any) => {
            try {
              return {
                id: conv.id,
                title: conv.title || 'Untitled Conversation',
                timestamp: conv.startedAt ? new Date(conv.startedAt) : new Date(),
                lastActivity: conv.lastActivity ? new Date(conv.lastActivity) : new Date(),
                documentId: conv.documentId || undefined,
                messageCount: conv.messageCount || 0,
              };
            } catch (dateError) {
              console.warn('Error parsing dates for conversation:', conv.id, dateError);
              // Fallback to current date if date parsing fails
              return {
                id: conv.id,
                title: conv.title || 'Untitled Conversation',
                timestamp: new Date(),
                lastActivity: new Date(),
                documentId: conv.documentId || undefined,
                messageCount: conv.messageCount || 0,
              };
            }
          });
        setSessions(sessionsWithDates);
      } catch (error) {
        console.error('Failed to load conversations from database:', error);
        const errorMessage = error instanceof Error ? error.message : 'Failed to load chat sessions';
        showToast(errorMessage, 'error');
        // Set empty array on error to prevent UI issues
        setSessions([]);
      } finally {
        setIsLoading(false);
      }
    };
    loadConversations();
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

  const addMessage = (message: Message) => {
    setMessages((prev) => [...prev, message]);
  };

  const selectSession = async (sessionId: string | null) => {
    if (sessionId === null) {
      setCurrentSession(null);
      setMessages([]);
      setSelectedDocumentId(null);
      showToast('Started a new chat.', 'info');
      return;
    }
    
    // Load conversation and messages from API
    try {
      setIsLoading(true);
      const { conversation, messages: loadedMessages } = await getConversationMessages(sessionId);
      
      const session: ChatSession = {
        id: conversation.id,
        title: conversation.title,
        timestamp: new Date(conversation.startedAt),
        lastActivity: new Date(conversation.lastActivity),
        documentId: conversation.documentId || undefined,
        messageCount: conversation.messageCount,
      };
      
      setCurrentSession(session);
      setMessages(loadedMessages);
      
      // Set selected document if conversation has one
      if (conversation.documentId) {
        setSelectedDocumentId(conversation.documentId);
      } else {
        setSelectedDocumentId(null);
      }
      
      // Refresh conversations list to update last activity (don't fail if this fails)
      try {
        const conversations = await getConversations(50);
        const updatedSessions = conversations
          .filter((conv: any) => conv && conv.id)
          .map((conv: any) => ({
            id: conv.id,
            title: conv.title || 'Untitled Conversation',
            timestamp: conv.startedAt ? new Date(conv.startedAt) : new Date(),
            lastActivity: conv.lastActivity ? new Date(conv.lastActivity) : new Date(),
            documentId: conv.documentId || undefined,
            messageCount: conv.messageCount || 0,
          }));
        setSessions(updatedSessions);
      } catch (refreshError) {
        // Don't show error for refresh failure, just log it
        console.warn('Failed to refresh conversations list:', refreshError);
      }
      
      showToast(`Loaded conversation: ${session.title}`, 'info');
    } catch (error) {
      console.error('Failed to load conversation:', error);
      showToast('Failed to load conversation.', 'error');
    } finally {
      setIsLoading(false);
    }
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

  const renameDocument = async (documentId: string, newFilename: string) => {
    if (!newFilename || newFilename.trim().length === 0) {
      showToast('Filename cannot be empty.', 'error');
      return;
    }
    
    try {
      setIsLoading(true);
      const updatedDocument = await apiUpdateDocument(documentId, newFilename.trim());
      
      // Update in documents list
      setDocuments(prev => prev.map(doc => 
        doc.id === documentId ? updatedDocument : doc
      ));
      
      showToast('Document renamed successfully.', 'success');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to rename document';
      setError(errorMessage);
      showToast(errorMessage, 'error');
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const shareDocument = async (documentId: string) => {
    try {
      setIsLoading(true);
      const documentData = await apiExportDocument(documentId);
      
      // Create a JSON blob and download it
      const jsonString = JSON.stringify(documentData, null, 2);
      const blob = new Blob([jsonString], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `document-${documentId}-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      
      // Also copy to clipboard as a fallback
      try {
        await navigator.clipboard.writeText(jsonString);
        showToast('Document exported and copied to clipboard!', 'success');
      } catch (clipboardError) {
        showToast('Document exported successfully!', 'success');
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to export document';
      setError(errorMessage);
      showToast(errorMessage, 'error');
      throw error;
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

          // Refresh conversations list to get updated last activity and any new conversations
          const refreshConversations = async () => {
            try {
              const conversations = await getConversations(50);
              const updatedSessions = conversations
                .filter((conv: any) => conv && conv.id)
                .map((conv: any) => ({
                  id: conv.id,
                  title: conv.title || 'Untitled Conversation',
                  timestamp: conv.startedAt ? new Date(conv.startedAt) : new Date(),
                  lastActivity: conv.lastActivity ? new Date(conv.lastActivity) : new Date(),
                  documentId: conv.documentId || undefined,
                  messageCount: conv.messageCount || 0,
                }));
              setSessions(updatedSessions);
              
              // If we don't have a current session but we have a conversationId, find and set it
              if (!currentSession && (conversationId || userMessage.conversationId)) {
                const convId = conversationId || userMessage.conversationId;
                const foundSession = updatedSessions.find((s: ChatSession) => s.id === convId);
                if (foundSession) {
                  setCurrentSession(foundSession);
                }
              }
            } catch (error) {
              // Don't show error toast for background refresh failures
              console.warn('Failed to refresh conversations:', error);
            }
          };
          // Don't await - let it run in background
          refreshConversations();

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

  // Conversation management functions
  const deleteSession = async (sessionId: string) => {
    try {
      setIsLoading(true);
      await deleteConversation(sessionId);
      
      // Remove from sessions list
      setSessions(prev => prev.filter(s => s.id !== sessionId));
      
      // If the deleted session was the current one, clear it
      if (currentSession?.id === sessionId) {
        setCurrentSession(null);
        setMessages([]);
        setSelectedDocumentId(null);
      }
      
      showToast('Conversation deleted successfully.', 'success');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to delete conversation';
      setError(errorMessage);
      showToast(errorMessage, 'error');
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const renameSession = async (sessionId: string, newTitle: string) => {
    if (!newTitle || newTitle.trim().length === 0) {
      showToast('Title cannot be empty.', 'error');
      return;
    }
    
    try {
      setIsLoading(true);
      await updateConversation(sessionId, { title: newTitle.trim() });
      
      // Update in sessions list
      setSessions(prev => prev.map(s => 
        s.id === sessionId ? { ...s, title: newTitle.trim() } : s
      ));
      
      // Update current session if it's the one being renamed
      if (currentSession?.id === sessionId) {
        setCurrentSession({ ...currentSession, title: newTitle.trim() });
      }
      
      showToast('Conversation renamed successfully.', 'success');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to rename conversation';
      setError(errorMessage);
      showToast(errorMessage, 'error');
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const shareSession = async (sessionId: string) => {
    try {
      setIsLoading(true);
      const conversationData = await exportConversation(sessionId);
      
      // Create a JSON blob and download it
      const jsonString = JSON.stringify(conversationData, null, 2);
      const blob = new Blob([jsonString], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `conversation-${sessionId}-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      
      // Also copy to clipboard as a fallback
      try {
        await navigator.clipboard.writeText(jsonString);
        showToast('Conversation exported and copied to clipboard!', 'success');
      } catch (clipboardError) {
        showToast('Conversation exported successfully!', 'success');
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to export conversation';
      setError(errorMessage);
      showToast(errorMessage, 'error');
      throw error;
    } finally {
      setIsLoading(false);
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
        renameDocument,
        shareDocument,
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
        // Conversation management
        deleteSession,
        renameSession,
        shareSession,
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
