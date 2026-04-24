import type { GenerateRequest, SseEvent } from "./types";

// See lib/api/client.ts for BASE resolution — empty string means same-origin,
// which Next.js rewrites proxy to the internal api service. SSE streams pass
// through unbuffered.
const BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

/**
 * POST the request, parse SSE frames from the response body stream, yield typed events.
 *
 * Native EventSource is GET-only, so we open a POST via fetch and parse the SSE
 * framing by hand. Frames look like:
 *   event: <type>\n
 *   data: <json>\n
 *   \n
 */
export async function* streamJudge(
  req: GenerateRequest,
  signal: AbortSignal
): AsyncGenerator<SseEvent> {
  const res = await fetch(`${BASE}/api/generate/judge`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    },
    body: JSON.stringify(req),
    signal,
  });

  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`HTTP ${res.status}: ${text}`);
  }
  if (!res.body) {
    throw new Error("Response has no body");
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buf = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) return;
      buf += decoder.decode(value, { stream: true });

      let sep: number;
      while ((sep = findFrameBoundary(buf)) !== -1) {
        const frame = buf.slice(0, sep);
        buf = buf.slice(sep).replace(/^[\r\n]+/, "");
        const ev = parseFrame(frame);
        if (ev) yield ev;
      }
    }
  } finally {
    reader.releaseLock();
  }
}

function findFrameBoundary(s: string): number {
  // SSE frames are separated by \n\n. Handle \r\n\r\n too.
  const a = s.indexOf("\n\n");
  const b = s.indexOf("\r\n\r\n");
  if (a === -1) return b;
  if (b === -1) return a;
  return Math.min(a, b);
}

function parseFrame(frame: string): SseEvent | null {
  const lines = frame.split(/\r?\n/);
  let dataLines: string[] = [];
  for (const line of lines) {
    if (!line || line.startsWith(":")) continue; // comment / keepalive
    if (line.startsWith("data:")) {
      dataLines.push(line.slice(5).trimStart());
    }
    // `event:` / `id:` / `retry:` headers are not used — we rely on the `type`
    // field inside the JSON data payload.
  }
  if (dataLines.length === 0) return null;
  try {
    return JSON.parse(dataLines.join("\n")) as SseEvent;
  } catch (e) {
    console.warn("[sse] failed to parse frame", e, frame);
    return null;
  }
}
