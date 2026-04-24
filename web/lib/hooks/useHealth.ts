"use client";

import { useEffect, useState } from "react";

import { api } from "../api/client";
import type { HealthResponse } from "../api/types";

/**
 * Shared health poller.
 *
 * Multiple components (sidebar health dot, playground banner, judge playground)
 * all want to know the API health. Each `useHealth()` used to spin its own
 * setInterval, and React 19 strict-mode double-invokes effects in dev, so six
 * concurrent pollers was common. This module-level singleton keeps exactly ONE
 * fetch-loop running while any subscriber is mounted, and tears it down when
 * the last one unmounts.
 */

type State = { health: HealthResponse | null; error: Error | null };
type Subscriber = (s: State) => void;

const POLL_INTERVAL_MS = 10_000;

let lastHealth: HealthResponse | null = null;
let lastError: Error | null = null;
let timer: ReturnType<typeof setInterval> | null = null;
const subscribers = new Set<Subscriber>();

function notify() {
  const snapshot: State = { health: lastHealth, error: lastError };
  for (const fn of subscribers) fn(snapshot);
}

async function tick() {
  try {
    lastHealth = await api.getHealth();
    lastError = null;
  } catch (e) {
    lastError = e instanceof Error ? e : new Error(String(e));
  }
  notify();
}

function ensureLoop() {
  if (timer !== null) return;
  void tick(); // initial fetch
  timer = setInterval(tick, POLL_INTERVAL_MS);
}

function maybeStopLoop() {
  if (subscribers.size > 0 || timer === null) return;
  clearInterval(timer);
  timer = null;
  lastHealth = null;
  lastError = null;
}

export function useHealth(): State {
  const [state, setState] = useState<State>({ health: lastHealth, error: lastError });

  useEffect(() => {
    subscribers.add(setState);
    ensureLoop();
    // Deliver cached value immediately on subscribe.
    if (lastHealth !== null || lastError !== null) {
      setState({ health: lastHealth, error: lastError });
    }
    return () => {
      subscribers.delete(setState);
      maybeStopLoop();
    };
  }, []);

  return state;
}
