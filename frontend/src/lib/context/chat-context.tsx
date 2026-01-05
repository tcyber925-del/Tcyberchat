'use client';

import React, { createContext, useContext, useReducer, useEffect, ReactNode, useCallback } from 'react';
import { ChatSession } from '@/types/chat';
import { Message, TextMessage, AgenticMessage, StepOutput } from '@/types/message';
import { Document } from '@/types/document';
import {
  sendMessageStreaming,
  getModels,
  getConversations,
  getConversationMessages,
  deleteConversation,
  updateConversation,
  exportConversation,
} from '@/lib/api/chat';
import {
  uploadDocument as apiUploadDocument,
  getDocuments as apiGetDocuments,
  deleteDocument as apiDeleteDocument,
  updateDocument as apiUpdateDocument,
  exportDocument as apiExportDocument,
} from '@/lib/api/documents';
import { useToast } from './toast-context';
import { useSettings } from './settings-context';
import { useAuth } from '@/hooks/use-auth';

// --- State Definition ---

interface ChatState {
  isSidebarOpen: boolean;
  sessions: ChatSession[];
  currentSession: ChatSession | null;
  messages: Message[];
  documents: Document[];
  selectedDocumentId: string | null;
  isLoading: boolean;
  error: string | null;
  isModelMenuOpen: boolean;
  localModels: any[];
  cloudModels: any[];
  isStreaming: boolean;
  streamingMessage: Message | null;
  lastDeletedMessage: Message | null;
}

const initialState: ChatState = {
  isSidebarOpen: true,
  sessions: [],
  currentSession: null,
  messages: [],
  documents: [],
  selectedDocumentId: null,
  isLoading: false,
  error: null,
  isModelMenuOpen: false,
  localModels: [],
  cloudModels: [],
  isStreaming: false,
  streamingMessage: null,
  lastDeletedMessage: null,
};

// --- Actions ---

type ChatAction =
  | { type: 'SET_SIDEBAR_OPEN'; payload: boolean }
  | { type: 'SET_SESSIONS'; payload: ChatSession[] }
  | { type: 'SET_CURRENT_SESSION'; payload: ChatSession | null }
  | { type: 'SET_MESSAGES'; payload: Message[] }
  | { type: 'ADD_MESSAGE'; payload: Message }
  | { type: 'UPDATE_MESSAGE'; payload: { id: string; updates: Partial<Message> } }
  | { type: 'DELETE_MESSAGE'; payload: string }
  | { type: 'SET_DOCUMENTS'; payload: Document[] }
  | { type: 'SET_SELECTED_DOCUMENT_ID'; payload: string | null }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'SET_MODEL_MENU_OPEN'; payload: boolean }
  | { type: 'SET_MODELS'; payload: { local: any[]; cloud: any[] } }
  | { type: 'START_STREAMING'; payload: Message }
  | { type: 'UPDATE_STREAMING'; payload: string }
  | { type: 'STOP_STREAMING' }
  | { type: 'UNDO_DELETE_MESSAGE' }
  | { type: 'FORK_CONVERSATION'; payload: { messageId: string; newContent: string } }
  | { type: 'SWITCH_VERSION'; payload: { messageId: string; versionIndex: number } };

// --- Reducer ---

function chatReducer(state: ChatState, action: ChatAction): ChatState {
  switch (action.type) {
    case 'SET_SIDEBAR_OPEN':
      return { ...state, isSidebarOpen: action.payload };
    case 'SET_SESSIONS':
      return { ...state, sessions: action.payload };
    case 'SET_CURRENT_SESSION':
      return { ...state, currentSession: action.payload };
    case 'SET_MESSAGES':
      return { ...state, messages: action.payload };
    case 'ADD_MESSAGE':
      return { ...state, messages: [...state.messages, action.payload] };
    case 'UPDATE_MESSAGE':
      return {
        ...state,
        messages: state.messages.map((m) =>
          m.id === action.payload.id ? ({ ...m, ...action.payload.updates } as Message) : m
        ),
      };
    case 'SWITCH_VERSION':
      return {
        ...state,
        messages: state.messages.map((m) =>
          m.id === action.payload.messageId ? ({ ...m, activeVersionIndex: action.payload.versionIndex } as Message) : m
        ),
      };
    case 'FORK_CONVERSATION':
      const forkIndex = state.messages.findIndex((m) => m.id === action.payload.messageId);
      if (forkIndex === -1) return state;
      // Keep messages up to the fork point (exclusive of the message being edited/forked)
      return {
        ...state,
        messages: state.messages.slice(0, forkIndex),
      };
    case 'DELETE_MESSAGE':
      const msgToDelete = state.messages.find((m) => m.id === action.payload);
      return {
        ...state,
        messages: state.messages.filter((m) => m.id !== action.payload),
        lastDeletedMessage: msgToDelete || null,
      };
    case 'SET_DOCUMENTS':
      return { ...state, documents: action.payload };
    case 'SET_SELECTED_DOCUMENT_ID':
      return { ...state, selectedDocumentId: action.payload };
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
    case 'SET_ERROR':
      return { ...state, error: action.payload };
    case 'SET_MODEL_MENU_OPEN':
      return { ...state, isModelMenuOpen: action.payload };
    case 'SET_MODELS':
      return { ...state, localModels: action.payload.local, cloudModels: action.payload.cloud };
    case 'START_STREAMING':
      return { ...state, isStreaming: true, streamingMessage: action.payload };
    case 'UPDATE_STREAMING':
      if (!state.streamingMessage || state.streamingMessage.type !== 'text') return state;
      return {
        ...state,
        streamingMessage: {
          ...state.streamingMessage,
          content: state.streamingMessage.content === 'Assistant is typing...' 
            ? action.payload 
            : state.streamingMessage.content + action.payload,
        } as TextMessage,
      };
    case 'STOP_STREAMING':
      return { ...state, isStreaming: false, streamingMessage: null };
    case 'UNDO_DELETE_MESSAGE':
      if (!state.lastDeletedMessage) return state;
      return {
        ...state,
        messages: [...state.messages, state.lastDeletedMessage].sort(
          (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
        ),
        lastDeletedMessage: null,
      };
    default:
      return state;
  }
}

interface ChatContextType extends ChatState {
  setIsSidebarOpen: (open: boolean) => void;
  setSessions: (sessions: ChatSession[]) => void;
  setCurrentSession: (session: ChatSession | null) => void;
  setMessages: (messages: Message[]) => void;
  setDocuments: (documents: Document[]) => void;
  setSelectedDocumentId: (documentId: string | null) => void;
  addMessage: (message: Message) => void;
  selectSession: (sessionId: string | null) => void;
  selectDocument: (documentId: string) => void;
  uploadDocument: (file: File) => Promise<Document>;
  deleteDocument: (documentId: string) => Promise<void>;
  renameDocument: (documentId: string, newFilename: string) => Promise<void>;
  shareDocument: (documentId: string) => Promise<void>;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setIsModelMenuOpen: (isOpen: boolean) => void;
  sendStreamingMessage: (
    content: string,
    conversationId?: string,
    enableWebSearch?: boolean,
    documentId?: string,
  ) => Promise<void>;
  stopStreaming: () => void;
  deleteMessage: (messageId: string) => void;
  undoDeleteMessage: () => void;
  regenerateMessage: (messageId: string) => Promise<void>;
  forkConversation: (messageId: string, newContent: string) => Promise<void>;
  switchMessageVersion: (messageId: string, versionIndex: number) => void;
  deleteSession: (sessionId: string) => Promise<void>;
  renameSession: (sessionId: string, newTitle: string) => Promise<void>;
  shareSession: (sessionId: string) => Promise<void>;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export function ChatProvider({ children }: { children: ReactNode }) {
  const { settings } = useSettings();
  const [state, dispatch] = useReducer(chatReducer, initialState);
  const { showToast } = useToast();
  const { user, loading: authLoading } = useAuth();

  const setIsSidebarOpen = (payload: boolean) => dispatch({ type: 'SET_SIDEBAR_OPEN', payload });
  const setSessions = (payload: ChatSession[]) => dispatch({ type: 'SET_SESSIONS', payload });
  const setCurrentSession = (payload: ChatSession | null) => dispatch({ type: 'SET_CURRENT_SESSION', payload });
  const setMessages = (payload: Message[]) => dispatch({ type: 'SET_MESSAGES', payload });
  const setDocuments = (payload: Document[]) => dispatch({ type: 'SET_DOCUMENTS', payload });
  const setSelectedDocumentId = (payload: string | null) => dispatch({ type: 'SET_SELECTED_DOCUMENT_ID', payload });
  const setLoading = (payload: boolean) => dispatch({ type: 'SET_LOADING', payload });
  const setError = (payload: string | null) => dispatch({ type: 'SET_ERROR', payload });
  const setIsModelMenuOpen = (payload: boolean) => dispatch({ type: 'SET_MODEL_MENU_OPEN', payload });

  // Load conversations from database on mount
  useEffect(() => {
    if (authLoading || !user) {
      if (!authLoading && !user) setSessions([]);
      return;
    }
    const loadConversations = async () => {
      try {
        setLoading(true);
        const conversations = await getConversations(50);
        const sessionsWithDates = conversations
          .filter((conv: any) => conv && conv.id)
          .map((conv: any) => ({
            id: conv.id,
            title: conv.title || 'Untitled Conversation',
            timestamp: conv.startedAt ? new Date(conv.startedAt) : new Date(),
            lastActivity: conv.lastActivity ? new Date(conv.lastActivity) : new Date(),
            documentId: conv.documentId || undefined,
            messageCount: conv.messageCount || 0,
          }));
        setSessions(sessionsWithDates);
      } catch (error) {
        console.error('Failed to load conversations:', error);
        showToast('Failed to load chat sessions', 'error');
      } finally {
        setLoading(false);
      }
    };
    loadConversations();
  }, [user, authLoading]);

  // Fetch documents on mount
  useEffect(() => {
    if (authLoading || !user) {
      if (!authLoading && !user) setDocuments([]);
      return;
    }
    const fetchDocuments = async () => {
      try {
        const fetchedDocuments = await apiGetDocuments();
        setDocuments(fetchedDocuments);
      } catch (err) {
        showToast('Failed to fetch documents', 'error');
      }
    };
    fetchDocuments();
  }, [user, authLoading]);

  // Fetch models on mount
  useEffect(() => {
    const fetchModels = async () => {
      try {
        const allModels = await getModels();
        const local = (allModels || []).filter((m: any) => m.provider === 'llama.cpp');
        const cloud = (allModels || []).filter((m: any) => m.provider !== 'llama.cpp');
        dispatch({ type: 'SET_MODELS', payload: { local, cloud } });
      } catch (err) {
        showToast('Failed to fetch models', 'error');
      }
    };
    fetchModels();
  }, []);

  const addMessage = (payload: Message) => dispatch({ type: 'ADD_MESSAGE', payload });

  const selectSession = async (sessionId: string | null) => {
    if (sessionId === null) {
      setCurrentSession(null);
      setMessages([]);
      setSelectedDocumentId(null);
      showToast('Started a new chat.', 'info');
      return;
    }

    try {
      setLoading(true);
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
      setSelectedDocumentId(conversation.documentId || null);
      showToast(`Loaded conversation: ${session.title}`, 'info');
    } catch (error) {
      console.error('Failed to load conversation:', error);
      showToast('Failed to load conversation.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const selectDocument = (documentId: string) => {
    setSelectedDocumentId(documentId);
    showToast(`Selected document: ${documentId}`, 'info');
  };

  const uploadDocument = async (file: File) => {
    setLoading(true);
    setError(null);
    try {
      const newDocument = await apiUploadDocument(file);
      setDocuments([...state.documents, newDocument]);
      showToast(`Document "${newDocument.filename}" uploaded successfully!`, 'success');
      return newDocument;
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to upload document';
      setError(msg);
      showToast(msg, 'error');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const deleteDocument = async (documentId: string) => {
    setLoading(true);
    try {
      await apiDeleteDocument(documentId);
      setDocuments(state.documents.filter((doc) => doc.id !== documentId));
      if (state.selectedDocumentId === documentId) setSelectedDocumentId(null);
      showToast(`Document deleted successfully!`, 'success');
    } catch (err) {
      showToast('Failed to delete document', 'error');
    } finally {
      setLoading(false);
    }
  };

  const renameDocument = async (documentId: string, newFilename: string) => {
    if (!newFilename.trim()) return showToast('Filename cannot be empty.', 'error');
    try {
      setLoading(true);
      const updated = await apiUpdateDocument(documentId, newFilename.trim());
      setDocuments(state.documents.map((doc) => (doc.id === documentId ? updated : doc)));
      showToast('Document renamed successfully.', 'success');
    } catch (error) {
      showToast('Failed to rename document', 'error');
    } finally {
      setLoading(false);
    }
  };

  const shareDocument = async (documentId: string) => {
    try {
      setLoading(true);
      const data = await apiExportDocument(documentId);
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `document-${documentId}.json`;
      link.click();
      URL.revokeObjectURL(url);
      showToast('Document exported successfully!', 'success');
    } catch (error) {
      showToast('Failed to export document', 'error');
    } finally {
      setLoading(false);
    }
  };

  const sendStreamingMessage = async (
    content: string,
    conversationId?: string,
    enableWebSearch: boolean = false,
    documentId?: string,
  ) => {
    if (state.isStreaming) return;

    const convId = conversationId || state.currentSession?.id || 'default';
    
    // 1. Add user message
    const userMessage: TextMessage = {
      id: `user-${Date.now()}`,
      type: 'text',
      role: 'user',
      content,
      timestamp: new Date(),
      conversationId: convId,
    };
    addMessage(userMessage);

    // 2. Start streaming with placeholder
    const streamingMsg: TextMessage = {
      id: `ai-${Date.now()}`,
      type: 'text',
      role: 'assistant',
      content: 'Assistant is typing...',
      timestamp: new Date(),
      conversationId: convId,
    };
    dispatch({ type: 'START_STREAMING', payload: streamingMsg });

    try {
      await sendMessageStreaming(
        content,
        state.currentSession?.id,
        settings.selectedModel,
        documentId || state.selectedDocumentId || undefined,
        enableWebSearch,
        (chunk) => dispatch({ type: 'UPDATE_STREAMING', payload: chunk }),
        (final) => {
          dispatch({ type: 'STOP_STREAMING' });
          const aiMessage: TextMessage = {
            id: (final as any)?.messageId ?? `ai-${Date.now()}`,
            type: 'text',
            role: 'assistant',
            content: final.content || '',
            timestamp: new Date(),
            conversationId: convId,
            citations: (final as any)?.citations ?? [],
            metadata: {
              webProvider: (final as any)?.webProvider,
              webSearchUsed: (final as any)?.webSearchUsed,
            },
          };
          addMessage(aiMessage);
          showToast('AI response received!', 'success');
        },
        (err) => {
          showToast(err.message, 'error');
          dispatch({ type: 'STOP_STREAMING' });
        }
      );
    } catch (error) {
      dispatch({ type: 'STOP_STREAMING' });
    }
  };

  const stopStreaming = () => dispatch({ type: 'STOP_STREAMING' });

  const deleteMessage = (payload: string) => {
    dispatch({ type: 'DELETE_MESSAGE', payload });
    showToast('Message deleted.', 'info');
  };

  const undoDeleteMessage = () => dispatch({ type: 'UNDO_DELETE_MESSAGE' });

  const regenerateMessage = async (messageId: string) => {
    const msgIndex = state.messages.findIndex((m) => m.id === messageId);
    if (msgIndex === -1) return;
    
    // Find the last user message before this assistant message
    let lastUserPrompt = "";
    for (let i = msgIndex - 1; i >= 0; i--) {
      if (state.messages[i].role === 'user') {
        lastUserPrompt = (state.messages[i] as TextMessage).content;
        break;
      }
    }
    
    if (!lastUserPrompt) return;
    
    // Delete the current assistant message and everything after it
    const newMessages = state.messages.slice(0, msgIndex);
    dispatch({ type: 'SET_MESSAGES', payload: newMessages });
    
    // Resend the last user prompt
    await sendStreamingMessage(lastUserPrompt);
  };

  const forkConversation = async (messageId: string, newContent: string) => {
    dispatch({ type: 'FORK_CONVERSATION', payload: { messageId, newContent } });
    await sendStreamingMessage(newContent);
  };

  const switchMessageVersion = (messageId: string, versionIndex: number) => {
    dispatch({ type: 'SWITCH_VERSION', payload: { messageId, versionIndex } });
  };

  const deleteSession = async (sessionId: string) => {
    try {
      setLoading(true);
      await deleteConversation(sessionId);
      setSessions(state.sessions.filter((s) => s.id !== sessionId));
      if (state.currentSession?.id === sessionId) {
        setCurrentSession(null);
        setMessages([]);
        setSelectedDocumentId(null);
      }
      showToast('Conversation deleted successfully.', 'success');
    } catch (error) {
      showToast('Failed to delete conversation', 'error');
    } finally {
      setLoading(false);
    }
  };

  const renameSession = async (sessionId: string, newTitle: string) => {
    if (!newTitle.trim()) return showToast('Title cannot be empty.', 'error');
    try {
      setLoading(true);
      await updateConversation(sessionId, { title: newTitle.trim() });
      setSessions(state.sessions.map((s) => (s.id === sessionId ? { ...s, title: newTitle.trim() } : s)));
      if (state.currentSession?.id === sessionId) setCurrentSession({ ...state.currentSession, title: newTitle.trim() });
      showToast('Conversation renamed successfully.', 'success');
    } catch (error) {
      showToast('Failed to rename conversation', 'error');
    } finally {
      setLoading(false);
    }
  };

  const shareSession = async (sessionId: string) => {
    try {
      setLoading(true);
      const data = await exportConversation(sessionId);
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `conversation-${sessionId}.json`;
      link.click();
      URL.revokeObjectURL(url);
      showToast('Conversation exported successfully!', 'success');
    } catch (error) {
      showToast('Failed to export conversation', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <ChatContext.Provider
      value={{
        ...state,
        setIsSidebarOpen,
        setSessions,
        setCurrentSession,
        setMessages,
        setDocuments,
        setSelectedDocumentId,
        addMessage,
        selectSession,
        selectDocument,
        uploadDocument,
        deleteDocument,
        renameDocument,
        shareDocument,
        setLoading,
        setError,
        setIsModelMenuOpen,
        sendStreamingMessage,
        stopStreaming,
        deleteMessage,
        undoDeleteMessage,
        regenerateMessage,
        forkConversation,
        switchMessageVersion,
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
