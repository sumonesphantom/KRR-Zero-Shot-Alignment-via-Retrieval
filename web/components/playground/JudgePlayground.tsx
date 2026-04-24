"use client";

import { AlertCircle } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "../ui/alert";
import { Progress } from "../ui/progress";
import { PlaygroundForm } from "./PlaygroundForm";
import { DraftPanel } from "../trace/DraftPanel";
import { FinalOutputPanel } from "../trace/FinalOutputPanel";
import { RetrievalPanel } from "../trace/RetrievalPanel";
import { RevisionsList } from "../trace/RevisionsList";
import { EmptyState } from "../common/EmptyState";

import { useGenerationStream } from "../../lib/hooks/useGenerationStream";
import { useHealth } from "../../lib/hooks/useHealth";

export function JudgePlayground() {
  const { health } = useHealth();
  const judge = useGenerationStream();

  const judgeReady = health?.judgeReady ?? false;
  const maxRevisions = health?.maxRevisions ?? 2;

  const trace = judge.trace;
  const hasDraft = (trace?.draft.length ?? 0) > 0;
  const selectedStyleId =
    trace?.finalStyleId || trace?.revisions[0]?.styleId;

  const progressValue = trace
    ? Math.min(
        100,
        (trace.revisions.length / (maxRevisions + 1)) * 100 +
          (judge.status === "streaming" ? 5 : 0)
      )
    : 0;

  return (
    <div className="grid gap-5 lg:grid-cols-[360px_420px_1fr] items-start">
      {/* COL 1 — question card + progress + errors */}
      <aside className="flex flex-col gap-3">
        <PlaygroundForm
          running={judge.status === "streaming"}
          submitDisabled={!judgeReady}
          onSubmit={(req) => judge.start(req)}
          onCancel={judge.cancel}
          submitLabel="Run"
        />

        {judge.status === "streaming" && (
          <div className="flex flex-col gap-1">
            <Progress value={progressValue} />
            <span className="text-xs text-muted-foreground">
              attempt {trace?.revisions.length ?? 0} / {maxRevisions + 1}
              {judge.activeAttempt
                ? ` · ${judge.activeAttempt.styleId}`
                : ""}
            </span>
          </div>
        )}

        {judge.status === "error" && judge.error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>
              Stream error{judge.errorCode ? ` · ${judge.errorCode}` : ""}
            </AlertTitle>
            <AlertDescription>{judge.error}</AlertDescription>
          </Alert>
        )}
      </aside>

      {/* COL 2 — Step 1 retrieval + Step 2 knowledge draft */}
      <section className="flex flex-col gap-3 min-w-0">
        {!trace ? (
          <EmptyState
            title="Step 1 & 2 · retrieval + draft"
            description="Top-K style cards from the FAISS index and the Knowledge LLM's neutral draft appear here once a run starts."
          />
        ) : (
          <>
            <RetrievalPanel
              hits={trace.retrieval}
              selectedStyleId={selectedStyleId}
              live={judge.status === "streaming"}
            />
            {(hasDraft || judge.status === "streaming") && (
              <DraftPanel
                draft={trace.draft}
                loading={judge.status === "streaming" && !hasDraft}
                streaming={
                  judge.status === "streaming" &&
                  hasDraft &&
                  trace.revisions.length === 0
                }
                thinking={judge.status === "streaming" && judge.draftThinking}
              />
            )}
          </>
        )}
      </section>

      {/* COL 3 — style attempts + judge verdicts + final output */}
      <section className="flex flex-col gap-3 min-w-0">
        {!trace ? (
          <EmptyState
            title="Attempts & final"
            description="Each Style LLM attempt and matching Judge verdict streams here. The best-scoring candidate is highlighted at the bottom."
          />
        ) : (
          <>
            <RevisionsList
              revisions={trace.revisions}
              mode={judge.status === "done" ? "static" : "live"}
              activeAttempt={judge.activeAttempt}
              styleThinking={judge.styleThinking}
              emptyPlaceholder={
                judge.status === "streaming" ? (
                  <EmptyState
                    title="Waiting for the first style attempt…"
                    description="Style LLM starts once the Knowledge draft finishes."
                  />
                ) : null
              }
            />
            {trace.finalOutput && trace.finalVerdict && (
              <FinalOutputPanel
                styleId={trace.finalStyleId}
                output={trace.finalOutput}
                verdict={trace.finalVerdict}
              />
            )}
          </>
        )}
      </section>
    </div>
  );
}
