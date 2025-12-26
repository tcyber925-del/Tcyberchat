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
  onDeepResearch?: () => void;
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

        {/* Enhanced Deep Research Button */}
        {onDeepResearch && (
          <button
            type="button"
            onClick={() => {
              onDeepResearch?.();
              onClose();
            }}
            className={cn(
              'group relative flex items-center gap-2 px-4 py-2 rounded-md overflow-hidden',
              'text-sm font-medium transition-all duration-300',
              'bg-gradient-to-r from-violet-600 to-indigo-600 text-white',
              'hover:from-violet-700 hover:to-indigo-700',
              'hover:shadow-lg hover:scale-105',
              'focus:outline-none focus:ring-2 focus:ring-violet-500 focus:ring-offset-2',
              'active:scale-95',
            )}
            title="Run Deep Research - AI-powered multi-step research with citations"
          >
            {/* Animated background gradient */}
            <div className="absolute inset-0 bg-gradient-to-r from-violet-400/20 to-indigo-400/20 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

            {/* Icon with animation */}
            <Sparkles className="h-4 w-4 relative z-10 group-hover:rotate-12 transition-transform duration-300" />

            {/* Text */}
            <span className="relative z-10 font-semibold">Deep Research</span>

            {/* Badge */}
            <span className="relative z-10 ml-1 text-[10px] bg-white/20 backdrop-blur-sm px-1.5 py-0.5 rounded-full border border-white/30">
              AI
            </span>

            {/* Subtle shine effect */}
            <div className="absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-1000 bg-gradient-to-r from-transparent via-white/10 to-transparent" />
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
