import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CopyButton } from "@/components/common/CopyButton";
import { ActionBadge } from "@/components/trace/ActionBadge";
import {
  CosineBadge,
  StyleScoreBadge,
} from "@/components/trace/VerdictBadge";
import type { JudgeVerdict } from "@/lib/api/types";

export function FinalOutputPanel({
  styleId,
  output,
  verdict,
}: {
  styleId: string;
  output: string;
  verdict: JudgeVerdict;
}) {
  return (
    <Card className="border-primary/60 bg-primary/5">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <span className="text-muted-foreground">Final · </span>
            <Badge variant="outline">{styleId}</Badge>
          </CardTitle>
          <div className="flex items-center gap-2 flex-wrap">
            <StyleScoreBadge score={verdict.styleScore} />
            <CosineBadge cosine={verdict.contentCosine} />
            <ActionBadge action={verdict.action} />
            <CopyButton text={output} />
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <p className="whitespace-pre-wrap text-sm leading-6">{output}</p>
      </CardContent>
    </Card>
  );
}
