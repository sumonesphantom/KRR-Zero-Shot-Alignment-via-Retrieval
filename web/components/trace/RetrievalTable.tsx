import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";
import type { RetrievalHit } from "@/lib/api/types";

export function RetrievalTable({
  hits,
  selectedStyleId,
}: {
  hits: RetrievalHit[];
  selectedStyleId?: string;
}) {
  if (hits.length === 0) {
    return (
      <div className="text-sm text-muted-foreground">No retrieval results yet.</div>
    );
  }
  const maxScore = Math.max(...hits.map((h) => h.score), 0.0001);
  return (
    <div className="flex flex-col gap-1.5">
      {hits.map((h) => (
        <div
          key={h.rank}
          className={cn(
            "grid grid-cols-[auto_1fr_auto] items-center gap-3 rounded-md border px-3 py-2 text-sm",
            selectedStyleId === h.styleId &&
              "border-primary/60 bg-primary/5"
          )}
        >
          <Badge variant="outline" className="w-7 justify-center tabular-nums">
            #{h.rank}
          </Badge>
          <div className="min-w-0">
            <div className="font-medium truncate">{h.styleId}</div>
            <div className="mt-1 flex items-center gap-2">
              <Progress
                value={(h.score / maxScore) * 100}
                className="h-1 w-32"
              />
              <span className="text-xs text-muted-foreground tabular-nums">
                {h.score.toFixed(3)}
              </span>
            </div>
          </div>
          <span className="text-xs text-muted-foreground tabular-nums">
            w {h.weight.toFixed(2)}
          </span>
        </div>
      ))}
    </div>
  );
}
