import { Badge } from "../ui/badge";
import type { JudgeAction } from "../../lib/api/types";

const copy: Record<JudgeAction, { label: string; variant: "default" | "success" | "warn" | "destructive" }> = {
  accept: { label: "accept", variant: "success" },
  revise_style: { label: "revise style", variant: "warn" },
  content_drift: { label: "content drift", variant: "destructive" },
  wrong_style: { label: "wrong style", variant: "destructive" },
};

export function ActionBadge({ action }: { action: JudgeAction }) {
  const c = copy[action] ?? { label: action, variant: "default" as const };
  return <Badge variant={c.variant}>{c.label}</Badge>;
}
