import Link from "next/link";

import { api } from "../../lib/api/client";
import { EmptyState } from "../../components/common/EmptyState";
import { Badge } from "../../components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { truncate } from "../../lib/utils/format";

export const dynamic = "force-dynamic";

export default async function TracesPage() {
  try {
    const { traces, evaluationsAvailable } = await api.listTraces();

    return (
      <div className="mx-auto flex min-w-0 max-w-5xl flex-col gap-4">
        <div className="flex items-start justify-between gap-3 flex-wrap">
          <div>
            <h2 className="text-xl font-semibold tracking-tight">
              Evaluation traces
            </h2>
            <p className="text-sm text-muted-foreground max-w-2xl">
              Server-side traces from the offline eval harness. For your own{" "}
              <Link
                href="/history"
                className="underline underline-offset-2 hover:text-foreground"
              >
                Playground runs, see History
              </Link>
              .{" "}
              {traces.length === 0
                ? "No eval runs yet — generate with: "
                : `${traces.length} trace${traces.length === 1 ? "" : "s"} in results/traces/.`}
              {traces.length === 0 && (
                <code className="font-mono text-xs bg-muted/60 px-1.5 py-0.5 rounded">
                  python judge/run_pipeline.py --step evaluate
                </code>
              )}
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" asChild disabled={!evaluationsAvailable.judge}>
              <Link
                href={`${api.base}/api/traces/evaluation/judge`}
                aria-disabled={!evaluationsAvailable.judge}
                className={!evaluationsAvailable.judge ? "pointer-events-none opacity-50" : ""}
              >
                Judge eval report
              </Link>
            </Button>
          </div>
        </div>

        {traces.length === 0 ? (
          <EmptyState
            title="No traces yet"
            description="Each call to the judge/ evaluator writes a trace_NN.json file. Run the evaluation first."
          />
        ) : (
          <div className="flex flex-col gap-2">
            {traces.map((t) => (
              <Link key={t.id} href={`/traces/${t.id}`}>
                <Card className="hover:bg-accent/50 transition-colors">
                  <CardHeader className="pb-1">
                    <div className="flex items-center justify-between gap-3 flex-wrap">
                      <CardTitle className="text-sm font-medium">
                        {t.id}
                      </CardTitle>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">{t.finalStyleId}</Badge>
                        <Badge variant="secondary">{t.nRevisions} revs</Badge>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm">{truncate(t.query, 160)}</p>
                    <p className="mt-1 text-xs text-muted-foreground italic">
                      pref: {truncate(t.preference, 120)}
                    </p>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </div>
    );
  } catch (e) {
    return (
      <EmptyState
        title="Could not load traces"
        description={e instanceof Error ? e.message : String(e)}
      />
    );
  }
}
