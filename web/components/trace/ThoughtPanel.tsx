"use client";

import { useState } from "react";
import { Brain, ChevronDown, ChevronRight } from "lucide-react";

/**
 * Renders the chain-of-thought captured from a thinking-mode model.
 *
 * Auto-expands while the model is actively thinking (so the user sees the
 * stream live), collapses to a compact toggle once thinking ends. Always
 * visually distinct from real output — italic, muted, indented.
 */
export function ThoughtPanel({
  text,
  active,
}: {
  text: string;
  active: boolean;
}) {
  const [manualExpanded, setManualExpanded] = useState<boolean | null>(null);
  if (!text) return null;

  // While actively thinking, default to expanded; afterwards default to
  // collapsed. Manual toggle wins either way.
  const expanded = manualExpanded ?? active;

  return (
    <div className="rounded-md border border-primary/25 bg-primary/[0.04]">
      <button
        type="button"
        onClick={() => setManualExpanded(!expanded)}
        className="flex w-full items-center gap-2 px-3 py-2 text-left text-xs font-medium text-primary hover:bg-primary/[0.06] transition-colors"
      >
        <Brain
          className={`h-3.5 w-3.5 ${active ? "animate-pulse" : ""}`}
          aria-hidden="true"
        />
        <span className={active ? "thinking-shimmer" : ""}>
          {active ? "thinking…" : "thought process"}
        </span>
        <span className="ml-auto flex items-center gap-1 text-muted-foreground">
          {text.length > 0 && <span>{text.length} chars</span>}
          {expanded ? (
            <ChevronDown className="h-3.5 w-3.5" />
          ) : (
            <ChevronRight className="h-3.5 w-3.5" />
          )}
        </span>
      </button>
      {expanded && (
        <pre className="max-h-64 overflow-auto whitespace-pre-wrap px-3 pb-3 pt-1 text-xs leading-5 text-muted-foreground italic font-sans">
          {text}
        </pre>
      )}
    </div>
  );
}
