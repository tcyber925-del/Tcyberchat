export interface Citation {
  id: number;
  docId?: string; // optional for web citations
  page?: number;
  snippet: string;
  url?: string;
  title?: string;
  source?: string;
  source_type?: string;
  // Web extras
  quotes?: string[];
  trust?: number; // 0..1
  suspicious?: boolean;
  domain?: string;
}

export interface StepOutput {
  step_number: number;
  step_name: string;
  status: 'running' | 'success' | 'failed' | 'retried';
  content?: string;
  duration?: number;
  is_step_repeated?: boolean;
  error?: string;
}

export type MessageRole = 'user' | 'assistant' | 'system' | 'function' | 'tool';

export interface BaseMessage {
  id: string;
  timestamp: Date;
  role: MessageRole;
  conversationId: string;
  metadata?: Record<string, any>;
  // Branching & Versioning
  parentId?: string; // ID of the previous message
  versions?: Message[]; // Alternative versions of this message
  activeVersionIndex?: number; // Currently displayed version
}

export interface TextMessage extends BaseMessage {
  type: 'text';
  content: string;
  citations?: Citation[];
}

export interface AgenticMessage extends BaseMessage {
  type: 'agentic';
  content: string; // The overall final or interim response
  steps: StepOutput[];
  plan?: string[];
  citations?: Citation[];
}

export interface DeepResearchMessage extends BaseMessage {
  type: 'deep-research';
  content: string; // Final markdown report
  citations: Citation[];
  iterations: number;
  satisfied: boolean;
}

export interface ToolMessage extends BaseMessage {
  type: 'tool';
  tool_name: string;
  tool_input: any;
  tool_output: any;
}

export interface ErrorMessage extends BaseMessage {
  type: 'error';
  error: string;
  code?: string;
}

export type Message = TextMessage | AgenticMessage | DeepResearchMessage | ToolMessage | ErrorMessage;