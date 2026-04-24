import { Badge } from "../ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Skeleton } from "../ui/skeleton";
import { MarkdownBody } from "../common/MarkdownBody";
import { ThinkingShimmer } from "./ThinkingShimmer";

export function DraftPanel({
  draft,
  loading,
  streaming,
  thinking,
}: {
  draft: string;
  loading?: boolean;
  streaming?: boolean;
  thinking?: boolean;
}) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between gap-2 flex-wrap">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <span className="text-muted-foreground">Step 2 · </span>
            Knowledge draft
          </CardTitle>
          {thinking ? (
            <ThinkingShimmer />
          ) : streaming ? (
            <Badge variant="secondary" className="animate-pulse">
              streaming…
            </Badge>
          ) : null}
        </div>
      </CardHeader>
      <CardContent>
        {loading && !draft ? (
          <div className="space-y-2">
            <Skeleton className="h-3 w-full" />
            <Skeleton className="h-3 w-[94%]" />
            <Skeleton className="h-3 w-[88%]" />
            <Skeleton className="h-3 w-[70%]" />
          </div>
        ) : draft ? (
          <div className="relative">
            <MarkdownBody>{draft}</MarkdownBody>
            {streaming && !thinking && (
              <span
                className="inline-block w-[0.4em] h-[1em] ml-[1px] bg-primary align-[-0.1em] animate-pulse"
                aria-hidden="true"
              />
            )}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground italic">
            {thinking ? "thinking…" : "(empty)"}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
