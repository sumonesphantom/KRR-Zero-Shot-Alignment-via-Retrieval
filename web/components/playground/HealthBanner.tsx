"use client";

import { AlertCircle } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useHealth } from "@/lib/hooks/useHealth";

export function HealthBanner() {
  const { health, error } = useHealth();

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>API unreachable</AlertTitle>
        <AlertDescription>
          Could not reach {process.env.NEXT_PUBLIC_API_BASE ?? "the API"}. Start
          the backend:{" "}
          <code className="font-mono text-xs">uvicorn api.main:app --reload</code>
        </AlertDescription>
      </Alert>
    );
  }

  if (!health) return null;

  const problems: string[] = [];
  if (!health.ollama.reachable)
    problems.push(
      `Ollama not reachable at ${health.ollama.host}. Run: ollama serve`
    );
  if (!health.index.present)
    problems.push("FAISS index missing. Run: python scripts/build_index.py");

  if (problems.length === 0) return null;

  return (
    <Alert variant="warn">
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>Some features unavailable</AlertTitle>
      <AlertDescription>
        <ul className="list-disc pl-4 space-y-0.5">
          {problems.map((p) => (
            <li key={p}>{p}</li>
          ))}
        </ul>
      </AlertDescription>
    </Alert>
  );
}
