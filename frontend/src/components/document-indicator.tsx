'use client';

import React from 'react';
import { XIcon, FileTextIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface DocumentIndicatorProps {
  documentId: string;
  documentName: string;
  onRemove: () => void;
  className?: string;
}

export function DocumentIndicator({ 
  documentId, 
  documentName, 
  onRemove,
  className 
}: DocumentIndicatorProps) {
  return (
    <div
      className={cn(
        'flex items-center gap-2 px-3 py-2 bg-primary/10 border border-primary/20 rounded-md text-sm',
        'transition-all duration-200',
        className
      )}
      role="status"
      aria-label={`Selected document: ${documentName}`}
    >
      <FileTextIcon className="w-4 h-4 text-primary flex-shrink-0" aria-hidden="true" />
      <span className="flex-1 truncate text-foreground" title={documentName}>
        {documentName}
      </span>
      <Button
        type="button"
        variant="ghost"
        size="sm"
        onClick={onRemove}
        className="h-6 w-6 p-0 hover:bg-primary/20 flex-shrink-0"
        aria-label={`Deselect document: ${documentName}`}
        title="Deselect document"
      >
        <XIcon className="w-3 h-3" aria-hidden="true" />
      </Button>
    </div>
  );
}

