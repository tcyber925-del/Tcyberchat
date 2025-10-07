'use client';

import React, { useRef } from 'react';
import { Document } from '@/types/document';
import { useChat } from '@/lib/context/chat-context'; // Import useChat

interface DocumentManagerProps {
  documents: Document[];
  onSelectDocument: (documentId: string) => void;
  onUploadDocument: (file: File) => void;
}

const DocumentManager: React.FC<DocumentManagerProps> = ({ documents, onSelectDocument, onUploadDocument }) => {
  const { isLoading } = useChat(); // Use isLoading from context
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
    <div className="flex flex-col">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold">Documents</h2>
        <button
          onClick={handleUploadClick}
          className="p-2 bg-blue-500 text-white rounded hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 cursor-pointer"
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
        className="mb-4 p-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
        aria-describedby="document-search-help"
        type="text"
      />
      <span id="document-search-help" className="sr-only">
        Type to filter your documents by name or content
      </span>
      <ul role="listbox" aria-label="Document list">
        {isLoading ? (
          // Loading skeleton
          Array.from({ length: 3 }).map((_, index) => (
            <li key={index} className="p-2">
              <div className="h-6 bg-gray-300 rounded animate-pulse w-full"></div>
            </li>
          ))
        ) : documents.length > 0 ? (
          documents.map((doc) => (
            <li
              key={doc.id}
              onClick={() => onSelectDocument(doc.id)}
              className="p-2 cursor-pointer hover:bg-gray-200 rounded"
              role="option"
              aria-selected="false"
            >
              {doc.filename}
            </li>
          ))
        ) : (
          <li className="p-2 text-gray-500 text-center" role="status" aria-live="polite">
            No documents uploaded yet
          </li>
        )}
      </ul>
    </div>
  );
};

export default DocumentManager;
