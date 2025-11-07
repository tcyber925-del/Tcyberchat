'use client';

import React, { useRef } from 'react';
import { Document } from '@/types/document';

interface DocumentManagerProps {
  documents: Document[];
  onSelectDocument: (documentId: string) => void;
  onUploadDocument: (file: File) => void;
  onDeleteDocument: (documentId: string) => void;
  isLoading: boolean;
}

const DocumentManager: React.FC<DocumentManagerProps> = ({ documents, onSelectDocument, onUploadDocument, onDeleteDocument, isLoading }) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      onUploadDocument(file);
    }
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="flex flex-col text-sm">
      <div className="flex justify-between items-center mb-2">
        <h2 className="text-md font-semibold">Documents</h2>
        <button
          onClick={handleUploadClick}
          className="p-2 bg-primary text-primary-foreground rounded hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 cursor-pointer text-xs"
        >
          Upload
        </button>
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          onChange={handleFileChange}
        />
      </div>
      <input
        id="document-search"
        placeholder="Search documents..."
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
        ) : documents.length > 0 ? (
          documents.map((doc, index) => (
            <li
              key={`${doc.id}-${index}`}
              className="p-2 flex justify-between items-center hover:bg-accent hover:text-accent-foreground rounded"
              role="option"
              aria-selected="false"
              title={doc.filename}
            >
              <span
                onClick={() => onSelectDocument(doc.id)}
                className="cursor-pointer flex-grow truncate"
              >
                {doc.filename}
              </span>
              <div className="flex gap-2 pl-2">
                <button
                  onClick={() => onDeleteDocument(doc.id)}
                  className="p-1 bg-red-600 text-white rounded hover:bg-red-700 text-xs"
                >
                  Delete
                </button>
              </div>
            </li>
          ))
        ) : (
          <li className="p-2 text-muted-foreground text-center" role="status" aria-live="polite">
            No documents uploaded yet
          </li>
        )}
      </ul>
    </div>
  );
};

export default DocumentManager;
