"""Judge LLM — evaluates the styled output and returns a control signal.

Outputs a structured JudgeVerdict the orchestrator acts on:
  accept          — styled output is good, emit it
  revise_style    — content is fine, style is weak → Style LLM retries harder
  content_drift   — style is fine but facts drifted from the draft
  wrong_style     — retrieved style itself looks like a mismatch, try next top-K

Runs on the shared base model with adapter disabled (or on a separate,
stronger judge model if JUDGE_MODEL_NAME is set).
"""

import json
import re
import numpy as np

from agents.shared_model import SharedBaseModel
from agents.schemas import JudgeVerdict
from config import (
    JUDGE_MODEL_NAME,
    JUDGE_STYLE_PASS_THRESHOLD,
    CONTENT_PRESERVATION_MIN,
)


JUDGE_RUBRIC = """You are an impartial judge. You will read a DRAFT (content-only answer),
a STYLED answer that was supposed to rewrite the draft in a target STYLE, and the
STYLE CARD describing that target style. Rate the STYLED answer on two axes and
reply with JSON only — no prose before or after.

Schema:
{"style_score": <int 1-5>, "content_faithful": <true|false>, "rationale": "<one sentence>"}

Rubric:
- style_score: 5 = clearly matches all style markers; 3 = partial; 1 = not in style.
- content_faithful: true iff the styled answer preserves the facts of the draft
  (no added claims, no dropped key facts, no contradictions). Rewording is fine.
"""


def _parse_verdict_json(text: str) -> dict:
    # Try to extract the first {...} JSON object in the output.
    match = re.search(r"\{.*?\}", text, re.DOTALL)
    if not match:
        return {}
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return {}


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


class JudgeLLM:
    def __init__(self, shared: SharedBaseModel, embedder):
        """
        shared: SharedBaseModel for the judge's LLM call
        embedder: object with .embed(text)->np.ndarray for content cosine
        """
        self.shared = shared
        self.embedder = embedder
        self.separate_model = JUDGE_MODEL_NAME is not None
        if self.separate_model:
            self.judge_shared = SharedBaseModel(JUDGE_MODEL_NAME)
        else:
            self.judge_shared = shared

    def evaluate(self, query: str, draft: str, styled: str,
                 style_card: dict) -> JudgeVerdict:
        # Step 1 — content-preservation cosine (deterministic).
        d_emb = self.embedder.embed(draft)
        s_emb = self.embedder.embed(styled)
        content_cos = _cosine(d_emb, s_emb)

        # Step 2 — ask the judge LLM for style & faithfulness.
        prompt = (
            f"{JUDGE_RUBRIC}\n\n"
            f"USER QUESTION: {query}\n\n"
            f"STYLE CARD:\n"
            f"  id: {style_card.get('id','')}\n"
            f"  instruction: {style_card.get('instruction','')}\n"
            f"  tags: {', '.join(style_card.get('tags',[]))}\n\n"
            f"DRAFT:\n{draft}\n\n"
            f"STYLED:\n{styled}\n\n"
            f"JSON:"
        )

        model = self.judge_shared.model_without_adapter()
        if hasattr(model, "disable_adapter"):
            with model.disable_adapter():
                raw = self.judge_shared.generate(
                    model, prompt, temperature=0.0, do_sample=False, max_new_tokens=150
                )
        else:
            raw = self.judge_shared.generate(
                model, prompt, temperature=0.0, do_sample=False, max_new_tokens=150
            )

        parsed = _parse_verdict_json(raw)
        style_score = int(parsed.get("style_score", 3))
        content_faithful_llm = bool(parsed.get("content_faithful", True))
        rationale = str(parsed.get("rationale", "")).strip()

        # Combine LLM faithfulness with cosine floor.
        content_faithful = content_faithful_llm and (content_cos >= CONTENT_PRESERVATION_MIN)

        # Step 3 — derive action from the two signals.
        if not content_faithful:
            action = "content_drift"
        elif style_score < 2:
            # Style is so weak it suggests the retrieved style was wrong for the query.
            action = "wrong_style"
        elif style_score < JUDGE_STYLE_PASS_THRESHOLD:
            action = "revise_style"
        else:
            action = "accept"

        return JudgeVerdict(
            style_score=style_score,
            content_faithful=content_faithful,
            content_cosine=content_cos,
            action=action,
            rationale=rationale,
            raw=raw,
        )
