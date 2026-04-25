// Mirror of api/schemas/*.py — camelCase everywhere.

export type JudgeAction =
  | "accept"
  | "revise_style"
  | "content_drift"
  | "wrong_style";

export interface StyleExample {
  prompt: string;
  answer: string;
}

export interface StyleCard {
  id: string;
  tags: string[];
  instruction: string;
  examples: StyleExample[];
  adapterPath: string | null;
}

export interface StylesListResponse {
  styles: StyleCard[];
}

export interface JudgeVerdict {
  styleScore: number;
  contentFaithful: boolean;
  contentCosine: number;
  action: JudgeAction;
  rationale: string;
  raw: string;
}

export interface RetrievalHit {
  rank: number;
  styleId: string;
  score: number;
  weight: number;
  card?: StyleCard | null;
}

export interface RevisionStep {
  attempt: number;
  styleId: string;
  draft: string;
  styled: string;
  verdict: JudgeVerdict;
}

export interface PipelineTrace {
  query: string;
  preference: string;
  retrieval: RetrievalHit[];
  draft: string;
  revisions: RevisionStep[];
  finalStyleId: string;
  finalOutput: string;
  finalVerdict: JudgeVerdict | null;
}

export interface TraceSummary {
  id: string;
  path: string;
  query: string;
  preference: string;
  finalStyleId: string;
  nRevisions: number;
  createdAt: string | null;
}

export interface TraceListResponse {
  traces: TraceSummary[];
  evaluationsAvailable: { judge: boolean };
}

export interface GenerateRequest {
  preference: string;
  query: string;
  topK?: number;
}

export interface HealthResponse {
  status: "ok" | "degraded";
  ollama: {
    reachable: boolean;
    host: string;
    error: string | null;
    modelsAvailable: string[];
  };
  index: { present: boolean; path: string };
  judgeReady: boolean;
  maxRevisions: number;
  models: { knowledge: string; style: string; judge: string };
}

// --- SSE events ---

export type SseEvent =
  | { type: "retrieval"; retrieval: RetrievalHit[] }
  | { type: "draft_thinking"; thinking: boolean }
  | { type: "draft_thought_delta"; delta: string }
  | { type: "draft_delta"; delta: string }
  | { type: "draft"; draft: string }
  | {
      type: "style_attempt_start";
      attempt: number;
      attemptForStyle: number;
      styleId: string;
    }
  | {
      type: "style_thinking";
      attempt: number;
      styleId: string;
      thinking: boolean;
    }
  | {
      type: "style_thought_delta";
      attempt: number;
      styleId: string;
      delta: string;
    }
  | {
      type: "style_delta";
      attempt: number;
      styleId: string;
      delta: string;
    }
  | {
      type: "style_attempt";
      attempt: number;
      styleId: string;
      styled: string;
    }
  | {
      type: "judge_verdict";
      attempt: number;
      styleId: string;
      verdict: JudgeVerdict;
    }
  | {
      type: "final";
      finalStyleId: string;
      finalOutput: string;
      finalVerdict: JudgeVerdict;
    }
  | { type: "error"; code: string; message: string };
