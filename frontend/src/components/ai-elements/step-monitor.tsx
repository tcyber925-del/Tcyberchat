'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import { 
  CheckCircle2, 
  Loader2, 
  AlertCircle, 
  RefreshCcw, 
  ChevronDown, 
  Clock,
  Search,
  Brain,
  FileText,
  Zap
} from 'lucide-react';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { Badge } from '@/components/ui/badge';
import { StepOutput } from '@/types/message';

interface StepMonitorProps {
  steps: StepOutput[];
  className?: string;
}

const getStatusIcon = (status: StepOutput['status']) => {
  switch (status) {
    case 'success': return <CheckCircle2 className="w-4 h-4 text-green-500" />;
    case 'failed': return <AlertCircle className="w-4 h-4 text-destructive" />;
    case 'retried': return <RefreshCcw className="w-4 h-4 text-yellow-500 animate-spin-slow" />;
    case 'running': return <Loader2 className="w-4 h-4 text-primary animate-spin" />;
    default: return null;
  }
};

const getStepIcon = (name: string) => {
  const n = name.toLowerCase();
  if (n.includes('plan')) return <Zap className="w-3.5 h-3.5" />;
  if (n.includes('search') || n.includes('investigate')) return <Search className="w-3.5 h-3.5" />;
  if (n.includes('extract') || n.includes('read')) return <FileText className="w-3.5 h-3.5" />;
  if (n.includes('synth') || n.includes('think')) return <Brain className="w-3.5 h-3.5" />;
  return <Clock className="w-3.5 h-3.5" />;
};

export const StepMonitor = ({ steps, className }: StepMonitorProps) => {
  return (
    <div className={cn("space-y-3 w-full max-w-2xl", className)}>
      <div className="flex items-center gap-2 mb-4">
        <Badge variant="secondary" className="bg-primary/5 text-primary border-primary/10 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider">
          Agent Execution Logs
        </Badge>
        <div className="h-px flex-1 bg-border/50" />
      </div>

      {steps.map((step, idx) => {
        const isLast = idx === steps.length - 1;
        const isActive = step.status === 'running';
        
        return (
          <Collapsible
            key={`${step.step_number}-${idx}`}
            defaultOpen={isActive || step.status === 'failed'}
            className={cn(
              "group rounded-lg border border-border/50 bg-card/50 transition-all",
              isActive && "border-primary/30 bg-primary/5 shadow-sm ring-1 ring-primary/10",
              step.status === 'failed' && "border-destructive/30 bg-destructive/5"
            )}
          >
            <CollapsibleTrigger className="w-full text-left px-3 py-2.5 flex items-center justify-between group">
              <div className="flex items-center gap-3 min-w-0">
                <div className="flex-shrink-0">
                  {getStatusIcon(step.status)}
                </div>
                <div className="flex flex-col min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold text-foreground truncate">
                      {step.step_number}. {step.step_name}
                    </span>
                    {step.is_step_repeated && (
                      <Badge variant="outline" className="text-[9px] h-4 px-1.5 border-yellow-500/30 text-yellow-600 bg-yellow-500/5">
                        RETRY
                      </Badge>
                    )}
                  </div>
                  {step.duration && (
                    <span className="text-[10px] text-muted-foreground flex items-center gap-1">
                      <Clock className="w-2.5 h-2.5" />
                      {step.duration}s
                    </span>
                  )}
                </div>
              </div>
              <ChevronDown className={cn(
                "w-4 h-4 text-muted-foreground transition-transform duration-200 group-data-[state=open]:rotate-180",
                isActive && "text-primary"
              )} />
            </CollapsibleTrigger>
            
            <CollapsibleContent className="px-3 pb-3 pt-0">
              <div className="pl-7 space-y-2">
                {step.content && (
                  <div className="text-xs text-muted-foreground leading-relaxed bg-muted/30 rounded p-2 border border-border/30 whitespace-pre-wrap font-mono italic">
                    {step.content}
                  </div>
                )}
                {step.error && (
                  <div className="text-xs text-destructive bg-destructive/10 rounded p-2 border border-destructive/20 flex items-start gap-2">
                    <AlertCircle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
                    <span>{step.error}</span>
                  </div>
                )}
              </div>
            </CollapsibleContent>
          </Collapsible>
        );
      })}
    </div>
  );
};
