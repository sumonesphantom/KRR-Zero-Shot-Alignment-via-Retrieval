"""Orchestrator — runs the Knowledge → Style → Judge control loop (Ollama).

All three roles call Ollama. The StyleRetriever (FAISS + sentence-transformers)
still runs locally and is also used as the embedder for the judge's
content-preservation cosine.

Loop per request:
  1. Retrieve top-K styles.
  2. Knowledge LLM drafts from the query alone.
  3. Style LLM rewrites the draft in the top-1 retrieved style.
  4. Judge evaluates. Action determines next step:
       accept          -> return
       revise_style    -> Style LLM retries (attempt++) with stronger prompt
       content_drift   -> Style LLM retries with re-emphasis on DRAFT
       wrong_style     -> advance to the next style in top-K, reset attempt
  5. Cap at MAX_REVISIONS total Style/Judge rounds; emit best candidate.
"""

from dataclasses import asdict
from typing import Callable, Optional

from retrieve import StyleRetriever
from agents.ollama_client import OllamaClient
from agents.knowledge import KnowledgeLLM
from agents.style import StyleLLM
from agents.judge import JudgeLLM
from agents.schemas import PipelineTrace, RevisionStep
from config import (
    MAX_REVISIONS, TOP_K,
    KNOWLEDGE_MODEL, STYLE_MODEL, JUDGE_MODEL,
)


class Orchestrator:
    def __init__(self):
        print(f"[orchestrator] Knowledge={KNOWLEDGE_MODEL}  "
              f"Style={STYLE_MODEL}  Judge={JUDGE_MODEL}")
        self.retriever = StyleRetriever()
        self.knowledge = KnowledgeLLM(OllamaClient(KNOWLEDGE_MODEL))
        self.style = StyleLLM(OllamaClient(STYLE_MODEL))
        self.judge = JudgeLLM(
            embedder=self.retriever,
            client=OllamaClient(JUDGE_MODEL),
        )

    def run(
        self,
        query: str,
        preference: str,
        top_k: int = TOP_K,
        on_event: Optional[Callable[[dict], None]] = None,
    ) -> PipelineTrace:
        def _to_camel(s: str) -> str:
            parts = s.split("_")
            return parts[0] + "".join(p.title() for p in parts[1:])

        def _camel_dict(d):
            """Recursively convert dict keys from snake_case → camelCase.
            Non-dict values pass through; lists are mapped element-wise."""
            if isinstance(d, dict):
                return {_to_camel(k): _camel_dict(v) for k, v in d.items()}
            if isinstance(d, list):
                return [_camel_dict(x) for x in d]
            return d

        def _emit(type_: str, **payload):
            if on_event is None:
                return
            try:
                on_event({"type": type_, **_camel_dict(payload)})
            except Exception as e:
                print(f"[orchestrator] on_event callback raised: {e!r}")

        retrieval = self.retriever.retrieve(preference, top_k=top_k)
        trace = PipelineTrace(
            query=query,
            preference=preference,
            retrieval=[
                {"rank": r["rank"], "style_id": r["style_id"],
                 "score": r["score"], "weight": r["weight"]}
                for r in retrieval
            ],
            draft="",
        )
        _emit("retrieval", retrieval=trace.retrieval)

        print(f"[orchestrator] Knowledge drafting...")
        draft = self.knowledge.draft(
            query,
            on_chunk=(lambda delta: _emit("draft_delta", delta=delta)) if on_event else None,
        )
        trace.draft = draft
        _emit("draft", draft=draft)

        style_idx = 0
        attempt_for_style = 0
        total_revisions = 0
        best: RevisionStep | None = None

        while style_idx < len(retrieval) and total_revisions < MAX_REVISIONS + 1:
            style_card = retrieval[style_idx]["card"]
            style_id = style_card["id"]
            print(f"[orchestrator] Style '{style_id}' attempt {attempt_for_style}")
            _emit(
                "style_attempt_start",
                attempt=total_revisions,
                attemptForStyle=attempt_for_style,
                styleId=style_id,
            )

            _attempt_captured = total_revisions
            _style_id_captured = style_id
            styled = self.style.restyle(
                draft, style_card, preference, attempt=attempt_for_style,
                on_chunk=(
                    lambda delta, a=_attempt_captured, sid=_style_id_captured:
                        _emit("style_delta", attempt=a, styleId=sid, delta=delta)
                ) if on_event else None,
            )
            _emit(
                "style_attempt",
                attempt=total_revisions,
                styleId=style_id,
                styled=styled,
            )
            verdict = self.judge.evaluate(query, draft, styled, style_card)
            print(
                f"[orchestrator]   judge: action={verdict.action} "
                f"style={verdict.style_score}/5 content_cos={verdict.content_cosine:.2f}"
            )
            _emit(
                "judge_verdict",
                attempt=total_revisions,
                styleId=style_id,
                verdict=asdict(verdict),
            )

            step = RevisionStep(
                attempt=total_revisions,
                style_id=style_id,
                draft=draft,
                styled=styled,
                verdict=verdict,
            )
            trace.revisions.append(step)

            if best is None or _score(step) > _score(best):
                best = step

            if verdict.action == "accept":
                break

            total_revisions += 1
            if total_revisions > MAX_REVISIONS:
                break

            if verdict.action == "wrong_style":
                style_idx += 1
                attempt_for_style = 0
            elif verdict.action in ("revise_style", "content_drift"):
                attempt_for_style += 1
            else:
                break

        assert best is not None
        trace.final_style_id = best.style_id
        trace.final_output = best.styled
        trace.final_verdict = best.verdict
        _emit(
            "final",
            finalStyleId=trace.final_style_id,
            finalOutput=trace.final_output,
            finalVerdict=asdict(trace.final_verdict),
        )
        return trace


def _score(step: RevisionStep) -> tuple:
    v = step.verdict
    return (int(v.content_faithful), v.style_score, v.content_cosine)
