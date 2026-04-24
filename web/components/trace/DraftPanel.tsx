import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export function DraftPanel({
  draft,
  loading,
  streaming,
}: {
  draft: string;
  loading?: boolean;
  streaming?: boolean;
}) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between gap-2 flex-wrap">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <span className="text-muted-foreground">Step 2 · </span>
            Knowledge draft
          </CardTitle>
          {streaming && (
            <Badge variant="secondary" className="animate-pulse">
              streaming…
            </Badge>
          )}
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
        ) : (
          <p className="whitespace-pre-wrap text-sm leading-6">
            {draft || (
              <span className="text-muted-foreground italic">(empty)</span>
            )}
            {streaming && (
              <span
                className="inline-block w-[0.4em] h-[1em] ml-[1px] bg-primary align-[-0.1em] animate-pulse"
                aria-hidden="true"
              />
            )}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
