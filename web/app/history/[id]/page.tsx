"use client";

import Link from "next/link";
import { use, useEffect, useState } from "react";

import { Button } from "../../../components/ui/button";
import { EmptyState } from "../../../components/common/EmptyState";
import { TraceViewer } from "../../../components/trace/TraceViewer";
import { historyStore, type HistoryEntry } from "../../../lib/stores/historyStore";

export default function HistoryDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [entry, setEntry] = useState<HistoryEntry | null | undefined>(undefined);

  useEffect(() => {
    setEntry(historyStore.get(id));
  }, [id]);

  if (entry === undefined) {
    // Initial render before the localStorage read fires — avoid SSR/CSR mismatch.
    return null;
  }

  if (entry === null) {
    return (
      <div className="mx-auto flex min-w-0 max-w-5xl flex-col gap-4">
        <div className="flex items-start justify-between gap-3 flex-wrap">
          <div>
            <h2 className="text-xl font-semibold tracking-tight">
              Run not found
            </h2>
            <p className="text-sm text-muted-foreground">
              This run may have been cleared, or the link is from a different browser.
            </p>
          </div>
          <Button variant="outline" size="sm" asChild>
            <Link href="/history">← Back to history</Link>
          </Button>
        </div>
        <EmptyState
          title={`No saved run with id "${id}"`}
          description="History lives in this browser's localStorage. Clearing site data or using a different browser will make old runs unavailable."
        />
      </div>
    );
  }

  return (
    <div className="mx-auto flex min-w-0 max-w-5xl flex-col gap-4">
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div>
          <h2 className="text-xl font-semibold tracking-tight">
            {entry.finalStyleId || "Run"}
          </h2>
          <p className="text-sm text-muted-foreground">
            pref: {entry.preference}
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            {new Date(entry.createdAt).toLocaleString()}
          </p>
        </div>
        <Button variant="outline" size="sm" asChild>
          <Link href="/history">← Back to history</Link>
        </Button>
      </div>
      <div className="rounded-md border bg-muted/30 p-3">
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">
          Query
        </p>
        <p className="text-sm">{entry.query}</p>
      </div>
      <TraceViewer trace={entry.trace} mode="static" />
    </div>
  );
}
