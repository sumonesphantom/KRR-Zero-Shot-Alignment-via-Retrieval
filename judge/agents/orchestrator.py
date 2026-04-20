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

    def run(self, query: str, preference: str, top_k: int = TOP_K) -> PipelineTrace:
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

        print(f"[orchestrator] Knowledge drafting...")
        draft = self.knowledge.draft(query)
        trace.draft = draft

        style_idx = 0
        attempt_for_style = 0
        total_revisions = 0
        best: RevisionStep | None = None

        while style_idx < len(retrieval) and total_revisions < MAX_REVISIONS + 1:
            style_card = retrieval[style_idx]["card"]
            style_id = style_card["id"]
            print(f"[orchestrator] Style '{style_id}' attempt {attempt_for_style}")

            styled = self.style.restyle(
                draft, style_card, preference, attempt=attempt_for_style
            )
            verdict = self.judge.evaluate(query, draft, styled, style_card)
            print(
                f"[orchestrator]   judge: action={verdict.action} "
                f"style={verdict.style_score}/5 content_cos={verdict.content_cosine:.2f}"
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
        return trace


def _score(step: RevisionStep) -> tuple:
    v = step.verdict
    return (int(v.content_faithful), v.style_score, v.content_cosine)
