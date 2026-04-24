"use client";

import { useHealth } from "@/lib/hooks/useHealth";
import { cn } from "@/lib/utils";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

export function HealthDot() {
  const { health, error } = useHealth();

  const color = (() => {
    if (error) return "bg-red-500";
    if (!health) return "bg-muted-foreground/40 animate-pulse";
    if (health.status === "ok") return "bg-emerald-500";
    return "bg-amber-500";
  })();

  const text = (() => {
    if (error) return "API unreachable";
    if (!health) return "Connecting to API…";
    const parts: string[] = [];
    parts.push(`Ollama: ${health.ollama.reachable ? "✓" : "✗"}`);
    parts.push(`Index: ${health.index.present ? "✓" : "✗"}`);
    parts.push(`J=${health.models.judge}`);
    return parts.join(" · ");
  })();

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <span
            className="inline-flex items-center gap-2 text-xs text-muted-foreground cursor-help"
            aria-label="API health"
          >
            <span className={cn("inline-block h-2 w-2 rounded-full", color)} />
            {error
              ? "API offline"
              : health?.status === "ok"
                ? "Ready"
                : "Degraded"}
          </span>
        </TooltipTrigger>
        <TooltipContent side="top" className="max-w-xs">
          {text}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
