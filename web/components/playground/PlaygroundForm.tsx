"use client";

import { Play, Square } from "lucide-react";
import { useState } from "react";

import { Button } from "../ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Label } from "../ui/label";
import { Textarea } from "../ui/textarea";
import type { GenerateRequest } from "../../lib/api/types";

const TOP_K = 3;

export interface PlaygroundFormProps {
  onSubmit: (req: GenerateRequest) => void;
  onCancel?: () => void;
  running: boolean;
  submitDisabled?: boolean;
  submitLabel?: string;
  initialPreference?: string;
  initialQuery?: string;
}

export function PlaygroundForm({
  onSubmit,
  onCancel,
  running,
  submitDisabled,
  submitLabel = "Run",
  initialPreference = "",
  initialQuery = "",
}: PlaygroundFormProps) {
  const [preference, setPreference] = useState(initialPreference);
  const [query, setQuery] = useState(initialQuery);

  const canSubmit =
    !submitDisabled &&
    !running &&
    preference.trim().length > 0 &&
    query.trim().length > 0;

  const submit = () => {
    if (canSubmit) onSubmit({ preference, query, topK: TOP_K });
  };

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">Your question, your style</CardTitle>
      </CardHeader>
      <CardContent>
        <form
          className="flex flex-col gap-3"
          onSubmit={(e) => {
            e.preventDefault();
            submit();
          }}
          onKeyDown={(e) => {
            if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
              e.preventDefault();
              submit();
            }
          }}
        >
          <div className="flex flex-col gap-1">
            <Label htmlFor="preference">Preference</Label>
            <Textarea
              id="preference"
              placeholder="e.g. be formal and academic, use precise terminology"
              value={preference}
              onChange={(e) => setPreference(e.target.value)}
              maxLength={1000}
              rows={2}
            />
          </div>

          <div className="flex flex-col gap-1">
            <Label htmlFor="query">Question</Label>
            <Textarea
              id="query"
              placeholder="Explain how a computer stores data."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              maxLength={2000}
              rows={3}
            />
          </div>

          <div className="flex items-center gap-2 justify-end">
            {running && onCancel && (
              <Button type="button" variant="outline" onClick={onCancel}>
                <Square className="h-4 w-4" /> Cancel
              </Button>
            )}
            <Button type="submit" disabled={!canSubmit}>
              <Play className="h-4 w-4" />
              {running ? "Running…" : submitLabel}
            </Button>
          </div>

          <p className="text-xs text-muted-foreground">
            Retrieves top-{TOP_K} style cards · ⌘⏎ / Ctrl+⏎ to submit.
          </p>
        </form>
      </CardContent>
    </Card>
  );
}
