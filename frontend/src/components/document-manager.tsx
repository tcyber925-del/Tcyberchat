'use client';

import React, { useRef, useState, useCallback, useEffect } from 'react';
import { Document } from '@/types/document';
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

interface DocumentManagerProps {
  documents: Document[];
  onSelectDocument: (documentId: string) => void;
  onUploadDocument: (file: File) => void;
  onDeleteDocument: (documentId: string) => void;
  isLoading: boolean;
}

const DocumentManager: React.FC<DocumentManagerProps> = ({
  documents,
  onSelectDocument,
  onUploadDocument,
  onDeleteDocument,
  isLoading,
}) => {
  const { renameDocument, shareDocument } = useChat();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [renameDialogOpen, setRenameDialogOpen] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [renameValue, setRenameValue] = useState('');
  const [hoveredDocumentId, setHoveredDocumentId] = useState<string | null>(null);
  const [expandedMenuId, setExpandedMenuId] = useState<string | null>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  const filteredDocuments = documents.filter((doc) =>
    doc.filename.toLowerCase().includes(searchQuery.toLowerCase()),
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

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      onUploadDocument(file);
    }
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleDeleteClick = useCallback((e: React.MouseEvent, doc: Document) => {
    e.stopPropagation();
    setSelectedDocument(doc);
    setDeleteDialogOpen(true);
    setExpandedMenuId(null);
  }, []);

  const handleRenameClick = useCallback((e: React.MouseEvent, doc: Document) => {
    e.stopPropagation();
    setSelectedDocument(doc);
    setRenameValue(doc.filename);
    setRenameDialogOpen(true);
    setExpandedMenuId(null);
  }, []);

  const handleShareClick = useCallback(
    async (e: React.MouseEvent, doc: Document) => {
      e.stopPropagation();
      try {
        await shareDocument(doc.id);
      } catch (error) {
        // Error is handled by the context
      }
      setExpandedMenuId(null);
    },
    [shareDocument],
  );

  const handleDeleteConfirm = useCallback(async () => {
    if (selectedDocument) {
      try {
        await onDeleteDocument(selectedDocument.id);
        setDeleteDialogOpen(false);
        setSelectedDocument(null);
      } catch (error) {
        // Error is handled by the context
      }
    }
  }, [selectedDocument, onDeleteDocument]);

  const handleRenameConfirm = useCallback(async () => {
    if (selectedDocument && renameValue.trim()) {
      try {
        await renameDocument(selectedDocument.id, renameValue.trim());
        setRenameDialogOpen(false);
        setSelectedDocument(null);
        setRenameValue('');
      } catch (error) {
        // Error is handled by the context
      }
    }
  }, [selectedDocument, renameValue, renameDocument]);

  return (
    <>
      <div className="flex flex-col text-sm">
        <div className="flex justify-between items-center mb-2">
          <h2 className="text-md font-semibold">Documents</h2>
          <button
            onClick={handleUploadClick}
            className="p-2 bg-primary text-primary-foreground rounded hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 cursor-pointer text-xs"
          >
            Upload
          </button>
          <input ref={fileInputRef} type="file" className="hidden" onChange={handleFileChange} />
        </div>
        <input
          id="document-search"
          placeholder="Search documents..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="mb-2 p-2 border border-border bg-background text-foreground rounded focus:outline-none focus:ring-2 focus:ring-ring"
          aria-describedby="document-search-help"
          type="text"
        />
        <span id="document-search-help" className="sr-only">
          Type to filter your documents by name or content
        </span>
        <ul role="listbox" aria-label="Document list" className="space-y-1">
          {isLoading ? (
            // Loading skeleton
            Array.from({ length: 3 }).map((_, index) => (
              <li key={index} className="p-2">
                <div className="h-5 bg-muted rounded animate-pulse w-full"></div>
              </li>
            ))
          ) : filteredDocuments.length > 0 ? (
            filteredDocuments.map((doc, index) => (
              <li
                key={`${doc.id}-${index}`}
                className={cn(
                  'group relative flex items-center gap-2 p-2 rounded',
                  'hover:bg-accent hover:text-accent-foreground',
                  'transition-colors',
                )}
                onMouseEnter={() => setHoveredDocumentId(doc.id)}
                onMouseLeave={() => {
                  setHoveredDocumentId(null);
                  setExpandedMenuId(null);
                }}
              >
                <div
                  onClick={() => onSelectDocument(doc.id)}
                  className="flex-1 cursor-pointer truncate min-w-0"
                  role="option"
                  aria-selected="false"
                  title={doc.filename}
                >
                  {doc.filename}
                </div>
                {(hoveredDocumentId === doc.id || expandedMenuId === doc.id) && (
                  <div className="flex items-center gap-1 flex-shrink-0">
                    <div className="relative">
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          setExpandedMenuId(expandedMenuId === doc.id ? null : doc.id);
                        }}
                        className="h-6 w-6 p-0"
                        aria-label="More options"
                      >
                        <MoreVertical className="h-3 w-3" />
                      </Button>
                      {expandedMenuId === doc.id && (
                        <div
                          ref={menuRef}
                          className="absolute right-0 top-8 z-10 bg-background border border-border rounded-md shadow-lg p-1 min-w-[120px]"
                        >
                          <button
                            onClick={(e) => handleRenameClick(e, doc)}
                            className="w-full flex items-center gap-2 px-2 py-1.5 text-sm hover:bg-accent rounded text-left"
                          >
                            <Edit2 className="h-3 w-3" />
                            Rename
                          </button>
                          <button
                            onClick={(e) => handleShareClick(e, doc)}
                            className="w-full flex items-center gap-2 px-2 py-1.5 text-sm hover:bg-accent rounded text-left"
                          >
                            <Share2 className="h-3 w-3" />
                            Share
                          </button>
                          <button
                            onClick={(e) => handleDeleteClick(e, doc)}
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
              {searchQuery ? 'No documents found' : 'No documents uploaded yet'}
            </li>
          )}
        </ul>
      </div>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Document</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete "{selectedDocument?.filename}"? This action cannot be
              undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setDeleteDialogOpen(false);
                setSelectedDocument(null);
              }}
            >
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleDeleteConfirm}>
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Rename Dialog */}
      <Dialog open={renameDialogOpen} onOpenChange={setRenameDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Rename Document</DialogTitle>
            <DialogDescription>Enter a new name for this document.</DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <Input
              value={renameValue}
              onChange={(e) => setRenameValue(e.target.value)}
              placeholder="Document filename"
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
                setSelectedDocument(null);
                setRenameValue('');
              }}
            >
              Cancel
            </Button>
            <Button onClick={handleRenameConfirm} disabled={!renameValue.trim()}>
              Save
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default DocumentManager;
