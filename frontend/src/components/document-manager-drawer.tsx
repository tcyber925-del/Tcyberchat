'use client';

import React, { useCallback } from 'react';
import { useChat } from '@/lib/context/chat-context';
import DocumentManager from './document-manager';

interface DocumentManagerDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

const DocumentManagerDrawer: React.FC<DocumentManagerDrawerProps> = ({ isOpen, onClose }) => {
  const { documents, selectDocument, uploadDocument } = useChat();

  const handleSelectDocument = useCallback((documentId: string) => {
    selectDocument(documentId);
    onClose(); // Close drawer after selecting a document
  }, [selectDocument, onClose]);

  const handleUploadDocument = useCallback(async (file: File) => {
    await uploadDocument(file);
    // Optionally, keep the drawer open or close it after upload
  }, [uploadDocument]);

  return (
    <aside
      className={`fixed right-0 top-0 h-full bg-gray-100 border-l border-gray-200 transition-transform duration-300 ease-in-out z-40 ${
        isOpen ? 'translate-x-0' : 'translate-x-full'
      }`}
      style={{ width: '16rem' }}
      role="complementary"
      aria-label="Document management sidebar"
      aria-hidden={!isOpen}
    >
      <div className="p-4">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold">Document Management</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700" aria-label="Close document management">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <DocumentManager
          documents={documents}
          onSelectDocument={handleSelectDocument}
          onUploadDocument={handleUploadDocument}
        />
      </div>
    </aside>
  );
};

export default DocumentManagerDrawer;
