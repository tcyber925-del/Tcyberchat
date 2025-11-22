'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import { Paperclip, Globe, X } from 'lucide-react';
import { Button } from './button';

interface ChatInputModalProps {
  isOpen: boolean;
  onClose: () => void;
  onFileAttach: () => void;
  onWebSearchToggle: () => void;
  webSearchEnabled: boolean;
  onDeepResearch?: () => void; // New: trigger deep research
}

export const ChatInputModal: React.FC<ChatInputModalProps> = ({
  isOpen,
  onClose,
  onFileAttach,
  onWebSearchToggle,
  webSearchEnabled,
  onDeepResearch,
}) => {
  if (!isOpen) return null;

  return (
    <div className="absolute bottom-full left-0 right-0 mb-2 flex justify-center z-50">
      <div className="bg-card border border-border rounded-lg shadow-lg p-2 flex items-center gap-2 animate-in fade-in slide-in-from-bottom-2 duration-200">
        {/* File Attachment Button */}
        <button
          type="button"
          onClick={() => {
            onFileAttach();
            onClose();
          }}
          className={cn(
            'flex items-center gap-2 px-4 py-2 rounded-md',
            'text-sm font-medium transition-colors',
            'hover:bg-accent hover:text-accent-foreground',
            'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
          )}
          title="Add photos & files"
        >
          <Paperclip className="h-4 w-4" />
          <span>Add photos & files</span>
        </button>

        {/* Web Search Toggle Button */}
        <button
          type="button"
          onClick={() => {
            onWebSearchToggle();
            onClose();
          }}
          className={cn(
            'flex items-center gap-2 px-4 py-2 rounded-md',
            'text-sm font-medium transition-colors',
            'hover:bg-accent hover:text-accent-foreground',
            'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
            webSearchEnabled && 'bg-primary/10 text-primary',
          )}
          title="Web search"
        >
          <Globe className={cn('h-4 w-4', webSearchEnabled && 'text-primary')} />
          <span>Web search</span>
          {webSearchEnabled && (
            <span className="ml-1 text-xs bg-primary text-primary-foreground px-1.5 py-0.5 rounded">
              ON
            </span>
          )}
        </button>

        {/* Deep Research Button */}
        {onDeepResearch && (
          <button
            type="button"
            onClick={() => {
              onDeepResearch?.();
              onClose();
            }}
            className={cn(
              'flex items-center gap-2 px-4 py-2 rounded-md',
              'text-sm font-medium transition-colors',
              'bg-primary text-primary-foreground hover:bg-primary/90',
              'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
            )}
            title="Run Deep Research"
          >
            <span>Deep Research</span>
          </button>
        )}

        {/* Close Button */}
        <button
          type="button"
          onClick={onClose}
          className={cn(
            'ml-2 p-1.5 rounded-md',
            'text-muted-foreground hover:text-foreground hover:bg-accent',
            'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
            'transition-colors',
          )}
          title="Close"
          aria-label="Close modal"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
};
