"use client";

import Link from "next/link";
import { Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { toast } from "sonner";

import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "../../components/ui/alert-dialog";
import { EmptyState } from "../../components/common/EmptyState";
import { historyStore, type HistoryEntry } from "../../lib/stores/historyStore";
import { truncate } from "../../lib/format";

function fmtRelative(iso: string): string {
  const d = new Date(iso);
  const diff = (Date.now() - d.getTime()) / 1000;
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)} min ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)} h ago`;
  return d.toLocaleString();
}

export default function HistoryPage() {
  const [entries, setEntries] = useState<HistoryEntry[]>([]);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    setEntries(historyStore.list());
  }, []);

  const remove = (id: string) => {
    historyStore.remove(id);
    setEntries(historyStore.list());
    toast.success("Run removed from history");
  };

  const clearAll = () => {
    historyStore.clear();
    setEntries([]);
    toast.success("History cleared");
  };

  if (!mounted) {
    // Avoid SSR/CSR mismatch — localStorage only exists on the client.
    return null;
  }

  return (
    <div className="mx-auto flex min-w-0 max-w-5xl flex-col gap-4">
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div>
          <h2 className="text-xl font-semibold tracking-tight">History</h2>
          <p className="text-sm text-muted-foreground">
            {entries.length === 0
              ? "No runs yet. Every Playground run is saved here in your browser (localStorage), never on the server."
              : `${entries.length} run${entries.length === 1 ? "" : "s"} saved locally in your browser. Capped at 50 — oldest are pruned.`}
          </p>
        </div>
        {entries.length > 0 && (
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="outline" size="sm">
                <Trash2 className="h-3.5 w-3.5" /> Clear all
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Clear all history?</AlertDialogTitle>
                <AlertDialogDescription>
                  This removes {entries.length} saved run{entries.length === 1 ? "" : "s"} from this browser. The server-side traces (under <code className="font-mono text-xs">results/traces/</code>) are not affected.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction onClick={clearAll}>Clear</AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        )}
      </div>

      {entries.length === 0 ? (
        <EmptyState
          title="No saved runs yet"
          description="Run a query from the Playground. When it finishes, it'll show up here automatically."
        />
      ) : (
        <div className="flex flex-col gap-2">
          {entries.map((e) => (
            <Card
              key={e.id}
              className="hover:bg-accent/40 transition-colors group"
            >
              <CardHeader className="pb-1">
                <div className="flex items-center justify-between gap-3 flex-wrap">
                  <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <Badge variant="outline">{e.finalStyleId || "—"}</Badge>
                    <span className="text-xs text-muted-foreground font-normal">
                      {fmtRelative(e.createdAt)}
                    </span>
                  </CardTitle>
                  <div className="flex items-center gap-2">
                    <Button variant="ghost" size="sm" asChild>
                      <Link href={`/history/${e.id}`}>Open</Link>
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      aria-label="Remove from history"
                      onClick={() => remove(e.id)}
                      className="opacity-60 group-hover:opacity-100"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <Link href={`/history/${e.id}`} className="block">
                  <p className="text-sm">{truncate(e.query, 180)}</p>
                  <p className="mt-1 text-xs text-muted-foreground italic">
                    pref: {truncate(e.preference, 120)}
                  </p>
                </Link>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
