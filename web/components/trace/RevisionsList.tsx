"use client";

import { RevisionCard } from "./RevisionCard";
import { EmptyState } from "../common/EmptyState";
import type { PipelineTrace, RevisionStep } from "../../lib/api/types";

export function RevisionsList({
  revisions,
  mode,
  activeAttempt,
  styleThinking,
  styleThought,
  emptyPlaceholder,
}: {
  revisions: RevisionStep[];
  mode: "live" | "static";
  activeAttempt: {
    attempt: number;
    attemptForStyle: number;
    styleId: string;
  } | null;
  styleThinking?: Record<number, boolean>;
  styleThought?: Record<number, string>;
  emptyPlaceholder?: React.ReactNode;
}) {
  if (revisions.length === 0) {
    if (emptyPlaceholder !== undefined) return <>{emptyPlaceholder}</>;
    return mode === "live" ? (
      <EmptyState
        title="Waiting for the first style attempt…"
        description="The Style LLM will start once the Knowledge draft finishes."
      />
    ) : null;
  }

  return (
    <div className="flex flex-col gap-3">
      {revisions.map((step) => {
        const isActive =
          mode === "live" && activeAttempt?.attempt === step.attempt;
        const awaitingStyled = isActive && !step.styled;
        const awaitingVerdict =
          mode === "live" &&
          step.verdict.styleScore === 0 &&
          !step.verdict.rationale;
        const thinking = !!styleThinking?.[step.attempt];
        const thought = styleThought?.[step.attempt];
        return (
          <RevisionCard
            key={step.attempt}
            step={step}
            awaitingVerdict={awaitingVerdict}
            awaitingStyled={awaitingStyled}
            streaming={isActive && step.styled.length > 0}
            thinking={thinking}
            thought={thought}
          />
        );
      })}
    </div>
  );
}

export type { PipelineTrace };
