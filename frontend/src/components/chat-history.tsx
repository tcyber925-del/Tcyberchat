'use client';

import React, { useState, useCallback, useEffect, useRef } from 'react';
import { ChatSession } from '@/types/chat';
import { useChat } from '@/lib/context/chat-context';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import { Trash2, Edit2, Share2, MoreVertical } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ChatHistoryProps {
  sessions: ChatSession[];
  onSelectSession: (sessionId: string) => void;
  isLoading: boolean;
}

const ChatHistory: React.FC<ChatHistoryProps> = ({ sessions, onSelectSession, isLoading }) => {
  const { deleteSession, renameSession, shareSession } = useChat();
  const [searchQuery, setSearchQuery] = useState('');
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [renameDialogOpen, setRenameDialogOpen] = useState(false);
  const [selectedSession, setSelectedSession] = useState<ChatSession | null>(null);
  const [renameValue, setRenameValue] = useState('');
  const [hoveredSessionId, setHoveredSessionId] = useState<string | null>(null);
  const [expandedMenuId, setExpandedMenuId] = useState<string | null>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  const filteredSessions = sessions.filter(session =>
    session.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Close dropdown menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setExpandedMenuId(null);
      }
    };

    if (expandedMenuId) {
      // Use a small delay to avoid closing immediately when opening
      setTimeout(() => {
        document.addEventListener('mousedown', handleClickOutside);
      }, 0);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [expandedMenuId]);

  const handleDeleteClick = useCallback((e: React.MouseEvent, session: ChatSession) => {
    e.stopPropagation();
    setSelectedSession(session);
    setDeleteDialogOpen(true);
    setExpandedMenuId(null);
  }, []);

  const handleRenameClick = useCallback((e: React.MouseEvent, session: ChatSession) => {
    e.stopPropagation();
    setSelectedSession(session);
    setRenameValue(session.title);
    setRenameDialogOpen(true);
    setExpandedMenuId(null);
  }, []);

  const handleShareClick = useCallback(async (e: React.MouseEvent, session: ChatSession) => {
    e.stopPropagation();
    try {
      await shareSession(session.id);
    } catch (error) {
      // Error is handled by the context
    }
    setExpandedMenuId(null);
  }, [shareSession]);

  const handleDeleteConfirm = useCallback(async () => {
    if (selectedSession) {
      try {
        await deleteSession(selectedSession.id);
        setDeleteDialogOpen(false);
        setSelectedSession(null);
      } catch (error) {
        // Error is handled by the context
      }
    }
  }, [selectedSession, deleteSession]);

  const handleRenameConfirm = useCallback(async () => {
    if (selectedSession && renameValue.trim()) {
      try {
        await renameSession(selectedSession.id, renameValue.trim());
        setRenameDialogOpen(false);
        setSelectedSession(null);
        setRenameValue('');
      } catch (error) {
        // Error is handled by the context
      }
    }
  }, [selectedSession, renameValue, renameSession]);

  return (
    <>
      <div className="flex flex-col text-sm">
        <input
          id="chat-search"
          placeholder="Search chats..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="mb-2 p-2 border border-border bg-background text-foreground rounded focus:outline-none focus:ring-2 focus:ring-ring"
          aria-describedby="chat-search-help"
          type="text"
        />
        <span id="chat-search-help" className="sr-only">
          Type to filter your chat history by title or content
        </span>
        <ul role="listbox" aria-label="Chat sessions" className="space-y-1">
          {isLoading ? (
            // Loading skeleton
            Array.from({ length: 5 }).map((_, index) => (
              <li key={index} className="p-2">
                <div className="h-5 bg-muted rounded animate-pulse w-3/4"></div>
              </li>
            ))
          ) : filteredSessions.length > 0 ? (
            filteredSessions.map((session) => (
              <li
                key={session.id}
                className={cn(
                  "group relative flex items-center gap-2 p-2 rounded",
                  "hover:bg-accent hover:text-accent-foreground",
                  "transition-colors"
                )}
                onMouseEnter={() => setHoveredSessionId(session.id)}
                onMouseLeave={() => {
                  setHoveredSessionId(null);
                  setExpandedMenuId(null);
                }}
              >
                <div
                  onClick={() => onSelectSession(session.id)}
                  className="flex-1 cursor-pointer truncate min-w-0"
                  role="option"
                  aria-selected="false"
                  title={session.title}
                >
                  {session.title}
                </div>
                {(hoveredSessionId === session.id || expandedMenuId === session.id) && (
                  <div className="flex items-center gap-1 flex-shrink-0">
                    <div className="relative">
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          setExpandedMenuId(expandedMenuId === session.id ? null : session.id);
                        }}
                        className="h-6 w-6 p-0"
                        aria-label="More options"
                      >
                        <MoreVertical className="h-3 w-3" />
                      </Button>
                      {expandedMenuId === session.id && (
                        <div ref={menuRef} className="absolute right-0 top-8 z-10 bg-background border border-border rounded-md shadow-lg p-1 min-w-[120px]">
                          <button
                            onClick={(e) => handleRenameClick(e, session)}
                            className="w-full flex items-center gap-2 px-2 py-1.5 text-sm hover:bg-accent rounded text-left"
                          >
                            <Edit2 className="h-3 w-3" />
                            Rename
                          </button>
                          <button
                            onClick={(e) => handleShareClick(e, session)}
                            className="w-full flex items-center gap-2 px-2 py-1.5 text-sm hover:bg-accent rounded text-left"
                          >
                            <Share2 className="h-3 w-3" />
                            Share
                          </button>
                          <button
                            onClick={(e) => handleDeleteClick(e, session)}
                            className="w-full flex items-center gap-2 px-2 py-1.5 text-sm hover:bg-destructive/10 hover:text-destructive rounded text-left"
                          >
                            <Trash2 className="h-3 w-3" />
                            Delete
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </li>
            ))
          ) : (
            <li className="p-2 text-muted-foreground text-center" role="status" aria-live="polite">
              {searchQuery ? 'No conversations found' : 'No chat history yet'}
            </li>
          )}
        </ul>
      </div>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Conversation</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete "{selectedSession?.title}"? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setDeleteDialogOpen(false);
                setSelectedSession(null);
              }}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleDeleteConfirm}
            >
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Rename Dialog */}
      <Dialog open={renameDialogOpen} onOpenChange={setRenameDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Rename Conversation</DialogTitle>
            <DialogDescription>
              Enter a new name for this conversation.
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <Input
              value={renameValue}
              onChange={(e) => setRenameValue(e.target.value)}
              placeholder="Conversation title"
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  handleRenameConfirm();
                } else if (e.key === 'Escape') {
                  setRenameDialogOpen(false);
                }
              }}
              autoFocus
            />
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setRenameDialogOpen(false);
                setSelectedSession(null);
                setRenameValue('');
              }}
            >
              Cancel
            </Button>
            <Button
              onClick={handleRenameConfirm}
              disabled={!renameValue.trim()}
            >
              Save
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default ChatHistory;
