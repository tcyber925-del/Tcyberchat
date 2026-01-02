'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import { ListTodo, ArrowRight, Circle } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface PlanRendererProps {
  plan: string[];
  className?: string;
}

export const PlanRenderer = ({ plan, className }: PlanRendererProps) => {
  if (!plan || plan.length === 0) return null;

  return (
    <div className={cn("bg-muted/30 rounded-xl border border-border/50 p-4 space-y-4", className)}>
      <div className="flex items-center gap-2">
        <div className="bg-primary/10 p-1.5 rounded-lg text-primary">
          <ListTodo size={16} />
        </div>
        <div className="flex flex-col">
          <span className="text-xs font-bold uppercase tracking-wider text-foreground">Strategic Roadmap</span>
          <span className="text-[10px] text-muted-foreground">Orchestrator planned {plan.length} phases</span>
        </div>
      </div>

      <div className="space-y-3 pl-2">
        {plan.map((item, idx) => (
          <div key={idx} className="flex gap-3 relative group">
            {/* Connector Line */}
            {idx !== plan.length - 1 && (
              <div className="absolute left-[7px] top-[18px] bottom-[-12px] w-[1px] bg-border group-hover:bg-primary/30 transition-colors" />
            )}
            
            <div className="mt-1 relative z-10">
              <div className="w-3.5 h-3.5 rounded-full border-2 border-primary bg-background flex items-center justify-center">
                <div className="w-1 h-1 rounded-full bg-primary" />
              </div>
            </div>
            
            <div className="flex flex-col gap-1">
              <span className="text-sm font-medium text-foreground leading-none">
                Phase {idx + 1}
              </span>
              <p className="text-xs text-muted-foreground leading-relaxed">
                {item}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
