import { Brain } from "lucide-react";

/**
 * Shown while a thinking-mode model (DeepSeek-R1 distills, Qwen3-thinking,
 * some custom Gemma variants) is emitting its internal chain-of-thought. The
 * backend strips <think>…</think> blocks before any tokens reach the UI, so
 * from the client's view the stream is silent during that phase — this
 * shimmer tells the user the model is active, not stalled.
 */
export function ThinkingShimmer() {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-md border border-primary/30 bg-primary/5 px-2 py-0.5 text-xs font-medium text-primary">
      <Brain className="h-3 w-3 animate-pulse" aria-hidden="true" />
      <span className="thinking-shimmer">thinking…</span>
    </span>
  );
}
