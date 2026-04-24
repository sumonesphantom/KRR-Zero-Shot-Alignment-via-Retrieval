import { Badge } from "@/components/ui/badge";

export function StyleScoreBadge({ score }: { score: number }) {
  const variant = score >= 4 ? "success" : score >= 3 ? "warn" : "destructive";
  return (
    <Badge variant={variant as "success" | "warn" | "destructive"}>
      {score}/5
    </Badge>
  );
}

export function CosineBadge({ cosine }: { cosine: number }) {
  const variant =
    cosine >= 0.8 ? "success" : cosine >= 0.7 ? "warn" : "destructive";
  return (
    <Badge variant={variant as "success" | "warn" | "destructive"}>
      cos {cosine.toFixed(2)}
    </Badge>
  );
}
