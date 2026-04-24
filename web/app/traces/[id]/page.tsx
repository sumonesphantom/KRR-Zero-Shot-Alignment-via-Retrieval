import Link from "next/link";

import { api, ApiError } from "@/lib/api/client";
import { EmptyState } from "@/components/common/EmptyState";
import { TraceViewer } from "@/components/trace/TraceViewer";
import { Button } from "@/components/ui/button";

export const dynamic = "force-dynamic";

export default async function TraceDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  try {
    const trace = await api.getTrace(id);
    return (
      <div className="mx-auto flex min-w-0 max-w-5xl flex-col gap-4">
        <div className="flex items-start justify-between gap-3 flex-wrap">
          <div>
            <h2 className="text-xl font-semibold tracking-tight">{id}</h2>
            <p className="text-sm text-muted-foreground">
              pref: {trace.preference}
            </p>
          </div>
          <Button variant="outline" size="sm" asChild>
            <Link href="/traces">← Back to all traces</Link>
          </Button>
        </div>
        <div className="rounded-md border bg-muted/30 p-3">
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">
            Query
          </p>
          <p className="text-sm">{trace.query}</p>
        </div>
        <TraceViewer trace={trace} mode="static" />
      </div>
    );
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) {
      return (
        <EmptyState
          title={`Trace "${id}" not found`}
          description="Trace files live in results/traces/. Make sure the file exists."
        />
      );
    }
    return (
      <EmptyState
        title="Could not load trace"
        description={e instanceof Error ? e.message : String(e)}
      />
    );
  }
}
