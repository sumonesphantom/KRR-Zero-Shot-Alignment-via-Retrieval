"use client";

import type { PipelineTrace } from "../api/types";

export type HistoryEntry = {
  id: string;
  createdAt: string; // ISO 8601
  query: string;
  preference: string;
  finalStyleId: string;
  trace: PipelineTrace;
};

const KEY = "krr:history:v1";
const MAX_ENTRIES = 50;

const isClient = () => typeof window !== "undefined";

function read(): HistoryEntry[] {
  if (!isClient()) return [];
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as unknown;
    return Array.isArray(parsed) ? (parsed as HistoryEntry[]) : [];
  } catch {
    return [];
  }
}

function write(entries: HistoryEntry[]) {
  if (!isClient()) return;
  try {
    localStorage.setItem(KEY, JSON.stringify(entries));
  } catch (e) {
    // Most common reason: storage quota exceeded. Trim and retry once.
    try {
      localStorage.setItem(KEY, JSON.stringify(entries.slice(0, 20)));
    } catch {
      console.warn("[history] localStorage write failed:", e);
    }
  }
}

const genId = () =>
  `r_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;

export const historyStore = {
  list(): HistoryEntry[] {
    return read();
  },

  add(trace: PipelineTrace): HistoryEntry {
    const entry: HistoryEntry = {
      id: genId(),
      createdAt: new Date().toISOString(),
      query: trace.query,
      preference: trace.preference,
      finalStyleId: trace.finalStyleId,
      trace,
    };
    const all = read();
    const next = [entry, ...all].slice(0, MAX_ENTRIES);
    write(next);
    return entry;
  },

  get(id: string): HistoryEntry | null {
    return read().find((e) => e.id === id) ?? null;
  },

  remove(id: string) {
    write(read().filter((e) => e.id !== id));
  },

  clear() {
    write([]);
  },
};
