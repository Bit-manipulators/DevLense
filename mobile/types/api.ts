export type Language = "python" | "cpp" | "javascript" | "java";
export type Severity = "low" | "medium" | "high" | "critical";

export interface AnalyzeRequest {
  language: Language;
  code: string;
  error_message?: string;
  question?: string;
}

export interface AnalysisResponse {
  session_id: string;
  summary: string;
  severity: Severity;
  root_cause: string;
  explanation: string;
  affected_lines: number[];
  suggested_fix: string;
  corrected_code: string;
  debugging_steps: string[];
  confidence: number;
}

export interface ExecuteRequest {
  language: Language;
  code: string;
  stdin?: string;
  session_id?: string;
}

export interface ExecuteResponse {
  success: boolean;
  stdout: string;
  stderr: string;
  exit_code: number;
  execution_time_ms: number;
}

export interface SessionListItem {
  id: string;
  language: Language;
  summary: string;
  severity: Severity;
  confidence: number;
  execution_count: number;
  created_at: string;
}

export interface SessionExecutionItem {
  id: string;
  success: boolean;
  stdout: string;
  stderr: string;
  exit_code: number;
  execution_time_ms: number;
  created_at: string;
}

export interface DebugSession extends SessionListItem {
  code: string;
  error_message: string;
  question: string;
  root_cause: string;
  explanation: string;
  affected_lines: number[];
  suggested_fix: string;
  corrected_code: string;
  debugging_steps: string[];
  execution_history?: SessionExecutionItem[];
}

export interface HealthResponse {
  status: "ok";
  environment: string;
  execution_sandbox_available: boolean;
  sandbox_mode?: string;
}

export interface OcrRequest {
  image_base64: string;
  hint_language?: Language;
}

export interface OcrResponse {
  code: string;
  detected_language: Language;
  confidence: number;
  provider: string;
  error_message?: string;
}

export interface ChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
}

export interface AgentChatRequest {
  session_id?: string;
  code: string;
  language: Language;
  error_message?: string;
  question?: string;
  finding_summary?: string;
  user_message: string;
  history?: ChatMessage[];
}

export interface AgentChatResponse {
  reply: string;
  code_snippet?: string;
  model: string;
}
