import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { RetrievalTable } from "@/components/trace/RetrievalTable";
import type { RetrievalHit } from "@/lib/api/types";

export function RetrievalPanel({
  hits,
  selectedStyleId,
  live,
}: {
  hits: RetrievalHit[];
  selectedStyleId?: string;
  live?: boolean;
}) {
  const hasHits = hits.length > 0;
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <span className="text-muted-foreground">Step 1 · </span>
          Retrieval (top-{hits.length || "k"})
        </CardTitle>
      </CardHeader>
      <CardContent>
        {hasHits ? (
          <RetrievalTable hits={hits} selectedStyleId={selectedStyleId} />
        ) : live ? (
          <div className="text-sm text-muted-foreground animate-pulse">
            Querying FAISS…
          </div>
        ) : (
          <div className="text-sm text-muted-foreground">
            No retrieval data.
          </div>
        )}
      </CardContent>
    </Card>
  );
}
