import type {
  HealthResponse,
  PipelineTrace,
  StyleCard,
  StylesListResponse,
  TraceListResponse,
} from "./types";

/**
 * Base URL for API fetches.
 *
 * - Empty string (production / Docker): browser uses same-origin relative paths
 *   like `/api/health`, which Next.js rewrites to the internal api service.
 * - Absolute URL (local dev): browser hits the uvicorn server directly, e.g.
 *   http://localhost:8000. Set NEXT_PUBLIC_API_BASE in .env.local.
 *
 * `??` (nullish coalesce) only fires for undefined — an explicitly empty string
 * from the build env is preserved.
 */
const BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  code?: string;
  detail?: unknown;
  constructor(status: number, message: string, code?: string, detail?: unknown) {
    super(message);
    this.status = status;
    this.code = code;
    this.detail = detail;
  }
}

async function parseErr(res: Response): Promise<ApiError> {
  let body: unknown;
  try {
    body = await res.json();
  } catch {
    return new ApiError(res.status, res.statusText);
  }
  const detail = (body as { detail?: unknown })?.detail;
  const d = detail && typeof detail === "object" ? detail as Record<string, unknown> : null;
  return new ApiError(
    res.status,
    (d?.error as string) || (d?.message as string) || res.statusText,
    (d?.code as string) || undefined,
    detail
  );
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { cache: "no-store" });
  if (!res.ok) throw await parseErr(res);
  return res.json() as Promise<T>;
}

export const api = {
  base: BASE,
  getHealth: () => get<HealthResponse>("/api/health"),
  getStyles: () => get<StylesListResponse>("/api/styles"),
  getStyle: (id: string) => get<StyleCard>(`/api/styles/${encodeURIComponent(id)}`),
  listTraces: () => get<TraceListResponse>("/api/traces"),
  getTrace: (id: string) => get<PipelineTrace>(`/api/traces/${encodeURIComponent(id)}`),
  getJudgeEvaluation: () =>
    get<Record<string, unknown>>(`/api/traces/evaluation/judge`),
};
