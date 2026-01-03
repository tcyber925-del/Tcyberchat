'use client';

import React from 'react';
import { useArtifact } from '@/lib/context/artifact-context';
import { 
  Artifact, 
  ArtifactHeader, 
  ArtifactTitle, 
  ArtifactClose, 
  ArtifactContent,
  ArtifactActions,
  ArtifactAction
} from './artifact';
import { MarkdownRenderer } from '@/components/ui/markdown-renderer';
import { cn } from '@/lib/utils';
import { AnimatePresence, motion } from 'framer-motion';
import { Copy, Download, Maximize2 } from 'lucide-react';
import { Button } from '@/components/ui/button';

export const ArtifactSidebar = () => {
  const { activeArtifact, isOpen, setIsOpen, setActiveArtifact } = useArtifact();

  if (!activeArtifact) return null;

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ x: '100%' }}
          animate={{ x: 0 }}
          exit={{ x: '100%' }}
          transition={{ type: 'spring', damping: 25, stiffness: 200 }}
          className="fixed right-0 top-0 bottom-0 w-full md:w-[500px] lg:w-[650px] z-40 bg-background border-l border-border shadow-2xl flex flex-col"
        >
          <Artifact className="h-full rounded-none border-none">
            <ArtifactHeader className="h-14">
              <div className="flex flex-col">
                <ArtifactTitle className="text-sm font-bold">
                  {activeArtifact.title}
                </ArtifactTitle>
                <span className="text-[10px] text-muted-foreground uppercase tracking-widest font-semibold">
                  {activeArtifact.type} Artifact
                </span>
              </div>
              
              <ArtifactActions>
                <ArtifactAction 
                  tooltip="Copy Content" 
                  onClick={() => navigator.clipboard.writeText(activeArtifact.content)}
                >
                  <Copy size={16} />
                </ArtifactAction>
                <ArtifactAction tooltip="Download">
                  <Download size={16} />
                </ArtifactAction>
                <ArtifactClose onClick={() => setIsOpen(false)} />
              </ArtifactActions>
            </ArtifactHeader>

            <ArtifactContent className="p-0">
              <div className="h-full overflow-y-auto p-6">
                {activeArtifact.type === 'report' || activeArtifact.type === 'markdown' ? (
                  <article className="prose prose-sm dark:prose-invert max-w-none">
                    <MarkdownRenderer content={activeArtifact.content} />
                  </article>
                ) : activeArtifact.type === 'code' ? (
                  <pre className="p-4 rounded-lg bg-muted font-mono text-xs overflow-x-auto">
                    <code>{activeArtifact.content}</code>
                  </pre>
                ) : (
                  <div className="flex items-center justify-center h-full text-muted-foreground italic">
                    Unsupported artifact type
                  </div>
                )}
              </div>
            </ArtifactContent>
          </Artifact>
        </motion.div>
      )}
    </AnimatePresence>
  );
};
