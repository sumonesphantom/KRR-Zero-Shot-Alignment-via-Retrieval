"use client";

import { AlertCircle } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="mx-auto max-w-2xl flex flex-col gap-3">
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Something broke</AlertTitle>
        <AlertDescription>
          {error.message || "Unknown error"}
          {error.digest && (
            <span className="block text-xs mt-1 opacity-70">
              id: {error.digest}
            </span>
          )}
        </AlertDescription>
      </Alert>
      <div>
        <Button onClick={reset}>Try again</Button>
      </div>
    </div>
  );
}
