'use client';

import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import { MarkdownRenderer } from '@/components/ui/markdown-renderer';
import { 
  FileSearch, 
  ExternalLink, 
  ChevronRight, 
  ChevronLeft, 
  Download, 
  Copy, 
  Check,
  ShieldCheck,
  ShieldAlert,
  History,
  Maximize2,
  Minimize2,
  Pin
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Dialog, DialogContent } from '@/components/ui/dialog';

interface DeepResearchArtifactProps {
  content: string;
  citations?: any[];
  metadata?: any;
  className?: string;
  onPin?: (content: string) => void;
}

export const DeepResearchArtifact = ({ 
  content, 
  citations = [], 
  metadata, 
  className,
  onPin
}: DeepResearchArtifactProps) => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isExpanded, setIsExpanded] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const ArtifactContent = ({ expanded = false }: { expanded?: boolean }) => (
    <div className={cn(
      "flex flex-col md:flex-row w-full mx-auto rounded-xl border border-border bg-card shadow-lg overflow-hidden transition-all duration-300",
      expanded ? "h-full w-full max-w-none border-none shadow-none rounded-none" : "h-[600px] max-w-5xl relative",
      className
    )}>
      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 bg-background h-full">
        <header className="flex items-center justify-between px-4 py-2 border-b border-border bg-muted/30 flex-shrink-0">
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="bg-primary/5 text-primary border-primary/20 gap-1">
              <FileSearch className="w-3 h-3" />
              Deep Research Report
            </Badge>
            {metadata?.iterations && (
              <span className="text-[10px] text-muted-foreground flex items-center gap-1">
                <History className="w-3 h-3" />
                {metadata.iterations} iterations
              </span>
            )}
          </div>
          <div className="flex items-center gap-1">
            {onPin && (
              <Button 
                variant="ghost" 
                size="icon-sm" 
                onClick={() => onPin(content)} 
                title="Pin to Sidebar"
                aria-label="Pin to Sidebar"
              >
                <Pin className="w-4 h-4" />
              </Button>
            )}
            <Button 
              variant="ghost" 
              size="icon-sm" 
              onClick={() => setIsExpanded(!isExpanded)} 
              title={isExpanded ? "Collapse View" : "Expand to Fullscreen"}
              aria-label={isExpanded ? "Collapse View" : "Expand to Fullscreen"}
            >
              {isExpanded ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
            </Button>
            <Button 
              variant="ghost" 
              size="icon-sm" 
              onClick={handleCopy} 
              title="Copy Markdown"
              aria-label="Copy Markdown"
            >
              {copied ? <Check className="w-4 h-4 text-green-500" /> : <Copy className="w-4 h-4" />}
            </Button>
            <Button 
              variant="ghost" 
              size="icon-sm" 
              title="Download PDF (Coming Soon)" 
              aria-label="Download PDF"
              disabled
            >
              <Download className="w-4 h-4" />
            </Button>
            <Button 
              variant="ghost" 
              size="icon-sm" 
              onClick={() => setIsSidebarOpen(!isSidebarOpen)}
              className="md:flex hidden"
              title={isSidebarOpen ? "Close Sidebar" : "Open Sidebar"}
              aria-label={isSidebarOpen ? "Close Sidebar" : "Open Sidebar"}
            >
              {isSidebarOpen ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
            </Button>
          </div>
        </header>

        <ScrollArea className="flex-1 overflow-auto">
          <div className="p-6 h-full">
            <article className={cn(
              "prose prose-sm dark:prose-invert prose-headings:font-bold prose-a:text-primary mx-auto",
              expanded ? "max-w-5xl" : "max-w-3xl"
            )}>
              <MarkdownRenderer content={content} />
            </article>
          </div>
        </ScrollArea>
      </div>

      {/* Sources Sidebar */}
      {isSidebarOpen && (
        <aside className={cn(
          "w-full md:w-80 border-t md:border-t-0 md:border-l border-border bg-muted/10 flex flex-col transition-all duration-300 animate-in slide-in-from-right-5 h-full",
        )}>
          <header className="px-4 py-3 border-b border-border font-semibold text-sm flex items-center justify-between flex-shrink-0">
            Sources & Evidence
            <Badge variant="secondary" className="text-[10px]">{citations.length}</Badge>
          </header>
          
          <ScrollArea className="flex-1 overflow-auto">
            <div className="p-4 space-y-3">
              {citations.length === 0 ? (
                <div className="text-center py-10">
                  <p className="text-xs text-muted-foreground italic">No citations found in this iteration.</p>
                </div>
              ) : (
                citations.map((cite, idx) => {
                  const trust = cite.trust || 0.5;
                  const isHighTrust = trust >= 0.75;
                  
                  return (
                    <div key={idx} className="p-3 rounded-lg border border-border bg-background hover:border-primary/30 hover:shadow-sm transition-all group">
                      <div className="flex items-start justify-between gap-2 mb-1.5">
                        <span className="flex-shrink-0 flex items-center justify-center w-5 h-5 rounded bg-primary/10 text-primary text-[10px] font-bold">
                          {idx + 1}
                        </span>
                        <div className="flex-1 min-w-0">
                          <h4 className="text-[11px] font-semibold text-foreground line-clamp-1 group-hover:text-primary transition-colors">
                            {cite.title || cite.domain || 'Untitled Source'}
                          </h4>
                        </div>
                        <a href={cite.url} target="_blank" rel="noopener noreferrer" className="text-muted-foreground hover:text-primary transition-colors">
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      </div>

                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <div className="text-[10px] flex items-center gap-1 mb-2 cursor-help">
                              {isHighTrust ? (
                                <ShieldCheck className="w-3 h-3 text-green-500" />
                              ) : (
                                <ShieldAlert className="w-3 h-3 text-yellow-500" />
                              )}
                              <span className={isHighTrust ? "text-green-600 font-medium" : "text-yellow-600 font-medium"}>
                                {isHighTrust ? "Verified Source" : "Web Source"}
                              </span>
                              <span className="text-muted-foreground ml-auto opacity-70">
                                {cite.domain}
                              </span>
                            </div>
                          </TooltipTrigger>
                          <TooltipContent side="left" className="max-w-xs">
                            <p className="text-xs">Trust Score: {(trust * 100).toFixed(0)}%</p>
                            <p className="text-[10px] text-muted-foreground mt-1">Based on domain authority and content safety analysis.</p>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>

                      <div className="bg-muted/30 rounded p-2 text-[10px] text-muted-foreground line-clamp-3 italic leading-relaxed">
                        "{cite.snippet}"
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </ScrollArea>
        </aside>
      )}
    </div>
  );

  return (
    <>
      <ArtifactContent />
      
      <Dialog open={isExpanded} onOpenChange={setIsExpanded}>
        <DialogContent className="max-w-none w-screen h-screen p-0 border-none rounded-none bg-background overflow-hidden flex flex-col">
          <div className="flex-1 overflow-hidden h-full">
            <ArtifactContent expanded />
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
};
