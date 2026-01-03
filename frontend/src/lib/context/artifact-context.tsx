'use client';

import React, { createContext, useContext, useState, ReactNode } from 'react';

export interface ArtifactData {
  id: string;
  type: 'code' | 'markdown' | 'report' | 'image';
  title: string;
  content: string;
  metadata?: any;
}

interface ArtifactContextType {
  activeArtifact: ArtifactData | null;
  setActiveArtifact: (artifact: ArtifactData | null) => void;
  isOpen: boolean;
  setIsOpen: (open: boolean) => void;
  toggleArtifact: () => void;
}

const ArtifactContext = createContext<ArtifactContextType | undefined>(undefined);

export function ArtifactProvider({ children }: { children: ReactNode }) {
  const [activeArtifact, setActiveArtifact] = useState<ArtifactData | null>(null);
  const [isOpen, setIsOpen] = useState(false);

  const toggleArtifact = () => setIsOpen((prev) => !prev);

  // Auto-open when an artifact is set
  const handleSetActiveArtifact = (artifact: ArtifactData | null) => {
    setActiveArtifact(artifact);
    if (artifact) {
      setIsOpen(true);
    }
  };

  return (
    <ArtifactContext.Provider
      value={{
        activeArtifact,
        setActiveArtifact: handleSetActiveArtifact,
        isOpen,
        setIsOpen,
        toggleArtifact,
      }}
    >
      {children}
    </ArtifactContext.Provider>
  );
}

export function useArtifact() {
  const context = useContext(ArtifactContext);
  if (context === undefined) {
    throw new Error('useArtifact must be used within an ArtifactProvider');
  }
  return context;
}
