'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import { Paperclip, Globe, X, Sparkles, Zap } from 'lucide-react';
import { Button } from './button';

interface ChatInputModalProps {
  isOpen: boolean;
  onClose: () => void;
  onFileAttach: () => void;
  onWebSearchToggle: () => void;
  webSearchEnabled: boolean;
  onDeepResearchToggle?: () => void;
  deepResearchEnabled?: boolean;
}

export const ChatInputModal: React.FC<ChatInputModalProps> = ({
  isOpen,
  onClose,
  onFileAttach,
  onWebSearchToggle,
  webSearchEnabled,
  onDeepResearchToggle,
  deepResearchEnabled,
}) => {
  if (!isOpen) return null;

  return (
    <div className="absolute bottom-full left-0 right-0 mb-2 flex justify-center z-50 px-4">
      <div className="bg-card border border-border rounded-xl shadow-xl p-2 flex items-center gap-2 animate-in fade-in slide-in-from-bottom-2 duration-300">
        {/* File Attachment Button */}
        <button
          type="button"
          onClick={() => {
            onFileAttach();
            onClose();
          }}
          className={cn(
            'flex items-center gap-2 px-4 py-2 rounded-lg',
            'text-sm font-medium transition-all duration-200',
            'hover:bg-accent hover:text-accent-foreground',
            'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
          )}
          title="Add photos & files"
        >
          <Paperclip className="h-4 w-4" />
          <span>Files</span>
        </button>

        <div className="w-px h-6 bg-border mx-1" />

        {/* Web Search Toggle Button */}
        <button
          type="button"
          onClick={() => {
            onWebSearchToggle();
          }}
          className={cn(
            'flex items-center gap-2 px-4 py-2 rounded-lg',
            'text-sm font-medium transition-all duration-300',
            webSearchEnabled 
              ? 'bg-primary/15 text-primary shadow-sm border border-primary/20' 
              : 'hover:bg-accent text-muted-foreground',
            'focus:outline-none focus:ring-2 focus:ring-ring',
          )}
          title="Toggle Web Search"
        >
          <Globe className={cn('h-4 w-4', webSearchEnabled && 'animate-pulse')} />
          <span>Web Search</span>
          {webSearchEnabled && (
            <Badge variant="default" className="ml-1 px-1 h-4 text-[10px]">ON</Badge>
          )}
        </button>

        {/* Deep Research Persistent Toggle */}
        {onDeepResearchToggle && (
          <button
            type="button"
            onClick={() => {
              onDeepResearchToggle();
            }}
            className={cn(
              'group relative flex items-center gap-2 px-4 py-2 rounded-lg overflow-hidden',
              'text-sm font-medium transition-all duration-500',
              deepResearchEnabled
                ? 'bg-gradient-to-r from-violet-600 to-indigo-600 text-white shadow-lg shadow-violet-500/20'
                : 'hover:bg-accent text-muted-foreground border border-transparent',
              'focus:outline-none focus:ring-2 focus:ring-violet-500',
            )}
            title="Toggle Deep Research Mode - Agentic multi-step research"
          >
            {deepResearchEnabled && (
              <div className="absolute inset-0 bg-gradient-to-r from-violet-400/20 to-indigo-400/20 animate-pulse" />
            )}
            <Sparkles className={cn(
              'h-4 w-4 relative z-10 transition-all duration-500',
              deepResearchEnabled ? 'rotate-12 scale-110' : 'group-hover:rotate-12'
            )} />
            <span className="relative z-10 font-semibold">Deep Research</span>
            {deepResearchEnabled && (
              <span className="relative z-10 ml-1 text-[10px] bg-white/20 backdrop-blur-sm px-1.5 py-0.5 rounded-full border border-white/30">
                ACTIVE
              </span>
            )}
          </button>
        )}

        <div className="w-px h-6 bg-border mx-1" />

        {/* Close Button */}
        <button
          type="button"
          onClick={onClose}
          className={cn(
            'p-1.5 rounded-full',
            'text-muted-foreground hover:text-foreground hover:bg-accent',
            'transition-all duration-200',
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

import { Badge } from './badge';
