'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import { CheckCircle2, Loader2, Search, FileText, Brain, MessageSquareQuote, Check } from 'lucide-react';

export type ResearchStep = 'plan' | 'investigate' | 'synthesize' | 'critique' | 'complete';

interface DeepResearchProgressProps {
  currentStep: ResearchStep | string | null;
  className?: string;
}

const steps = [
  { id: 'plan', label: 'Planning', icon: Search, description: 'Decomposing your request into research goals...' },
  { id: 'investigate', label: 'Investigating', icon: FileText, description: 'Crawling the web and extracting deep content...' },
  { id: 'synthesize', label: 'Synthesizing', icon: Brain, description: 'Analyzing findings and drafting the comprehensive report...' },
  { id: 'critique', label: 'Critiquing', icon: MessageSquareQuote, description: 'Verifying completeness and identifying potential gaps...' },
];

export const DeepResearchProgress = ({ currentStep, className }: DeepResearchProgressProps) => {
  if (!currentStep) return null;

  const getStepStatus = (stepId: string) => {
    const stepOrder = ['plan', 'investigate', 'synthesize', 'critique', 'complete'];
    const currentIndex = stepOrder.indexOf(currentStep as string);
    const stepIndex = stepOrder.indexOf(stepId);

    if (currentStep === 'complete') return 'complete';
    if (currentIndex === -1 || stepIndex > currentIndex) return 'pending';
    if (stepIndex === currentIndex) return 'active';
    return 'complete';
  };

  const activeStepObj = steps.find(s => s.id === currentStep) || steps[0];

  return (
    <div className={cn('w-full py-6 px-4 space-y-8 animate-in fade-in zoom-in-95 duration-500', className)}>
      <div className="flex items-center justify-between max-w-xl mx-auto relative px-2">
        {/* Progress Bar Background */}
        <div className="absolute top-5 left-0 w-full h-0.5 bg-muted z-0" />
        
        {/* Active Progress Bar Fill */}
        <div 
          className="absolute top-5 left-0 h-0.5 bg-primary transition-all duration-500 ease-in-out z-0" 
          style={{ 
            width: currentStep === 'complete' ? '100%' : 
                   currentStep === 'plan' ? '0%' : 
                   currentStep === 'investigate' ? '33%' : 
                   currentStep === 'synthesize' ? '66%' : '100%' 
          }}
        />
        
        {steps.map((step) => {
          const status = getStepStatus(step.id);
          const Icon = step.icon;
          
          return (
            <div key={step.id} className="relative z-10 flex flex-col items-center">
              <div
                className={cn(
                  'w-10 h-10 rounded-full flex items-center justify-center border-2 transition-all duration-500 shadow-md',
                  status === 'complete' ? 'bg-primary border-primary text-primary-foreground' : 
                  status === 'active' ? 'bg-background border-primary text-primary ring-4 ring-primary/20 scale-110' : 
                  'bg-background border-muted text-muted-foreground'
                )}
              >
                {status === 'complete' ? (
                  <Check className="w-5 h-5 stroke-[3px]" />
                ) : status === 'active' ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Icon className="w-5 h-5" />
                )}
              </div>
              <span 
                className={cn(
                  'absolute -bottom-7 text-[11px] font-bold uppercase tracking-tight transition-colors duration-500 whitespace-nowrap',
                  status === 'active' ? 'text-primary' : status === 'complete' ? 'text-foreground' : 'text-muted-foreground'
                )}
              >
                {step.label}
              </span>
            </div>
          );
        })}
      </div>
      
      <div className="text-center space-y-1 pt-2">
        <h3 className="text-sm font-semibold text-foreground animate-in slide-in-from-bottom-1">
          {currentStep === 'complete' ? 'Research Finalized' : `Step: ${activeStepObj.label}`}
        </h3>
        <p className="text-xs text-muted-foreground max-w-xs mx-auto leading-relaxed">
          {currentStep === 'complete' ? 'The comprehensive report is ready below.' : activeStepObj.description}
        </p>
      </div>
    </div>
  );
};