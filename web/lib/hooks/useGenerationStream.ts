"use client";

import { useCallback, useEffect, useReducer, useRef } from "react";

import { streamJudge } from "../api/sse";
import { historyStore } from "../stores/historyStore";
import type {
  GenerateRequest,
  PipelineTrace,
  RevisionStep,
  SseEvent,
} from "../api/types";

export type StreamStatus = "idle" | "streaming" | "done" | "error";

interface State {
  status: StreamStatus;
  trace: PipelineTrace | null;
  // The attempt the Style LLM is actively producing (set by style_attempt_start,
  // cleared by matching style_attempt).
  activeAttempt: {
    attempt: number;
    attemptForStyle: number;
    styleId: string;
  } | null;
  // Thinking-mode shimmer flags. Thinking models emit <think>…</think> blocks
  // that the backend strips before streaming real tokens; these flags tell the
  // UI to show a shimmer while the model is in that gated phase.
  draftThinking: boolean;
  styleThinking: Record<number, boolean>;
  error: string | null;
  errorCode: string | null;
  request: GenerateRequest | null;
}

type Action =
  | { type: "start"; req: GenerateRequest }
  | { type: "event"; ev: SseEvent }
  | { type: "error"; error: Error }
  | { type: "cancel" }
  | { type: "reset" };

const initial: State = {
  status: "idle",
  trace: null,
  activeAttempt: null,
  draftThinking: false,
  styleThinking: {},
  error: null,
  errorCode: null,
  request: null,
};

function emptyTrace(req: GenerateRequest): PipelineTrace {
  return {
    query: req.query,
    preference: req.preference,
    retrieval: [],
    draft: "",
    revisions: [],
    finalStyleId: "",
    finalOutput: "",
    finalVerdict: null,
  };
}

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case "start":
      return {
        status: "streaming",
        trace: emptyTrace(action.req),
        activeAttempt: null,
        draftThinking: false,
        styleThinking: {},
        error: null,
        errorCode: null,
        request: action.req,
      };
    case "reset":
      return initial;
    case "cancel":
      return {
        ...state,
        status: "idle",
        activeAttempt: null,
        draftThinking: false,
        styleThinking: {},
      };
    case "error":
      return {
        ...state,
        status: "error",
        error: action.error.message,
        errorCode: null,
        activeAttempt: null,
        draftThinking: false,
        styleThinking: {},
      };
    case "event": {
      if (!state.trace) return state;
      const t = { ...state.trace };
      const ev = action.ev;
      const placeholderVerdict = {
        styleScore: 0,
        contentFaithful: true,
        contentCosine: 0,
        action: "revise_style" as const,
        rationale: "",
        raw: "",
      };
      switch (ev.type) {
        case "retrieval":
          t.retrieval = ev.retrieval;
          return { ...state, trace: t };
        case "draft_thinking":
          return { ...state, draftThinking: ev.thinking };
        case "draft_delta":
          // Append streaming token to the draft being composed.
          t.draft = (t.draft ?? "") + ev.delta;
          return { ...state, trace: t };
        case "draft":
          // Terminal event for the Knowledge step — authoritative value.
          t.draft = ev.draft;
          return { ...state, trace: t, draftThinking: false };
        case "style_attempt_start":
          // Create an empty revision slot so incoming `style_delta` chunks
          // have somewhere to land without waiting for `style_attempt`.
          if (!t.revisions.find((r) => r.attempt === ev.attempt)) {
            t.revisions = [
              ...t.revisions,
              {
                attempt: ev.attempt,
                styleId: ev.styleId,
                draft: t.draft,
                styled: "",
                verdict: placeholderVerdict,
              },
            ];
          }
          return {
            ...state,
            trace: { ...t },
            activeAttempt: {
              attempt: ev.attempt,
              attemptForStyle: ev.attemptForStyle,
              styleId: ev.styleId,
            },
          };
        case "style_thinking":
          return {
            ...state,
            styleThinking: { ...state.styleThinking, [ev.attempt]: ev.thinking },
          };
        case "style_delta": {
          // Immutable update — never mutate the existing revision object, or
          // React strict-mode's double-invoke of the reducer in dev applies
          // the delta twice and every word appears doubled on screen.
          const idx = t.revisions.findIndex((r) => r.attempt === ev.attempt);
          if (idx === -1) {
            t.revisions = [
              ...t.revisions,
              {
                attempt: ev.attempt,
                styleId: ev.styleId,
                draft: t.draft,
                styled: ev.delta,
                verdict: placeholderVerdict,
              },
            ];
          } else {
            t.revisions = t.revisions.map((r, i) =>
              i === idx ? { ...r, styled: (r.styled ?? "") + ev.delta } : r
            );
          }
          return { ...state, trace: { ...t } };
        }
        case "style_attempt": {
          // Terminal event for this style attempt — authoritative value.
          const idx = t.revisions.findIndex((r) => r.attempt === ev.attempt);
          if (idx === -1) {
            t.revisions = [
              ...t.revisions,
              {
                attempt: ev.attempt,
                styleId: ev.styleId,
                draft: t.draft,
                styled: ev.styled,
                verdict: placeholderVerdict,
              },
            ];
          } else {
            t.revisions = t.revisions.map((r, i) =>
              i === idx ? { ...r, styled: ev.styled } : r
            );
          }
          const nextStyleThinking = { ...state.styleThinking };
          delete nextStyleThinking[ev.attempt];
          return {
            ...state,
            trace: { ...t },
            activeAttempt: null,
            styleThinking: nextStyleThinking,
          };
        }
        case "judge_verdict": {
          const idx = t.revisions.findIndex((r) => r.attempt === ev.attempt);
          if (idx === -1) return { ...state, trace: { ...t } };
          t.revisions = t.revisions.map((r, i) =>
            i === idx ? { ...r, verdict: ev.verdict } : r
          );
          return { ...state, trace: { ...t } };
        }
        case "final":
          t.finalStyleId = ev.finalStyleId;
          t.finalOutput = ev.finalOutput;
          t.finalVerdict = ev.finalVerdict;
          return {
            ...state,
            trace: t,
            status: "done",
            activeAttempt: null,
            draftThinking: false,
            styleThinking: {},
          };
        case "error":
          return {
            ...state,
            status: "error",
            error: ev.message,
            errorCode: ev.code,
            activeAttempt: null,
          };
      }
    }
  }
}

export function useGenerationStream() {
  const [state, dispatch] = useReducer(reducer, initial);
  const abortRef = useRef<AbortController | null>(null);
  // Tracks which trace has already been archived to browser history, so
  // React strict-mode's double-invoke of effects in dev doesn't save twice.
  const savedRef = useRef<PipelineTrace | null>(null);

  // Archive every completed run into localStorage-backed history.
  useEffect(() => {
    if (state.status === "streaming") {
      savedRef.current = null;
      return;
    }
    if (
      state.status === "done" &&
      state.trace &&
      state.trace.finalOutput &&
      savedRef.current !== state.trace
    ) {
      savedRef.current = state.trace;
      historyStore.add(state.trace);
    }
  }, [state.status, state.trace]);

  const start = useCallback(async (req: GenerateRequest) => {
    abortRef.current?.abort();
    const ctl = new AbortController();
    abortRef.current = ctl;
    dispatch({ type: "start", req });
    try {
      for await (const ev of streamJudge(req, ctl.signal)) {
        dispatch({ type: "event", ev });
      }
    } catch (e) {
      if ((e as Error).name === "AbortError") return;
      dispatch({ type: "error", error: e instanceof Error ? e : new Error(String(e)) });
    }
  }, []);

  const cancel = useCallback(() => {
    abortRef.current?.abort();
    dispatch({ type: "cancel" });
  }, []);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    dispatch({ type: "reset" });
  }, []);

  return {
    status: state.status,
    trace: state.trace,
    activeAttempt: state.activeAttempt,
    draftThinking: state.draftThinking,
    styleThinking: state.styleThinking,
    error: state.error,
    errorCode: state.errorCode,
    start,
    cancel,
    reset,
  };
}
