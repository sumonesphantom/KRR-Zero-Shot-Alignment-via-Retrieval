"use client";

import { DraftPanel } from "@/components/trace/DraftPanel";
import { FinalOutputPanel } from "@/components/trace/FinalOutputPanel";
import { RetrievalPanel } from "@/components/trace/RetrievalPanel";
import { RevisionsList } from "@/components/trace/RevisionsList";
import type { PipelineTrace } from "@/lib/api/types";

export interface TraceViewerProps {
  trace: PipelineTrace;
  mode: "live" | "static";
  activeAttempt?: {
    attempt: number;
    attemptForStyle: number;
    styleId: string;
  } | null;
}

/**
 * Single-column trace renderer used by the /traces/[id] detail page.
 * The Playground page composes these same primitives into a 2-column layout.
 */
export function TraceViewer({ trace, mode, activeAttempt }: TraceViewerProps) {
  const hasDraft = trace.draft.length > 0;
  const selectedId = trace.finalStyleId || trace.revisions[0]?.styleId;

  return (
    <div className="flex flex-col gap-4">
      <RetrievalPanel
        hits={trace.retrieval}
        selectedStyleId={selectedId}
        live={mode === "live"}
      />

      {(hasDraft || mode === "live") && (
        <DraftPanel
          draft={trace.draft}
          loading={mode === "live" && !hasDraft}
          streaming={
            mode === "live" && hasDraft && trace.revisions.length === 0
          }
        />
      )}

      <RevisionsList
        revisions={trace.revisions}
        mode={mode}
        activeAttempt={activeAttempt ?? null}
      />

      {trace.finalOutput && trace.finalVerdict && (
        <FinalOutputPanel
          styleId={trace.finalStyleId}
          output={trace.finalOutput}
          verdict={trace.finalVerdict}
        />
      )}
    </div>
  );
}
