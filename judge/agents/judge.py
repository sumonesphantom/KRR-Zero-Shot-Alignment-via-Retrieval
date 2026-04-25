"""Judge LLM — evaluates the styled output and returns a control signal.

Runs on Ollama with a different model family from the generator (Mistral 7B
by default vs Llama 3.1 8B for Knowledge/Style) to reduce self-preference bias.
Content-preservation cosine is computed locally via sentence-transformers.
"""

import json
import re
import numpy as np

from agents.ollama_client import OllamaClient
from agents.schemas import JudgeVerdict
from config import (
    JUDGE_MODEL,
    JUDGE_STYLE_PASS_THRESHOLD,
    CONTENT_PRESERVATION_MIN,
)


JUDGE_SYSTEM = (
    "You are an impartial judge of style adherence. You read a DRAFT "
    "(content-only answer), a STYLED answer that was supposed to rewrite the "
    "draft in a target STYLE, and the STYLE CARD with its instruction, tags, "
    "and exemplars. Reply with JSON only — no prose before or after.\n\n"
    'Schema: {"style_score": <int 1-5>, "content_faithful": <true|false>, '
    '"rationale": "<one sentence naming the specific style markers present or absent>"}\n\n'
    "Style score rubric:\n"
    "- 5 — Excellent. Distinctive style markers from the card (vocabulary, "
    "rhythm, punctuation, register) are present throughout. Reads cleanly in "
    "the target voice.\n"
    "- 4 — Good. The style is clearly committed to and lands; one or two "
    "characteristic markers are softer than the exemplars but a reader hits "
    "the right voice immediately. This is the normal accept score for a "
    "competent rewrite.\n"
    "- 3 — Surface only. A few markers swapped in but the default neutral "
    "voice still dominates; the reader couldn't confidently name the style.\n"
    "- 2 — Style hinted at but effectively ignored.\n"
    "- 1 — Not in style at all.\n\n"
    "Calibration: 4 is the target for a competent first attempt that lands "
    "the voice, even if not perfectly. Reserve 5 for rewrites that are "
    "delightfully on-style. Drop to 3 only if the rewrite is essentially "
    "the neutral draft with cosmetic substitutions.\n\n"
    "content_faithful: true iff the styled answer preserves the facts of the "
    "draft (no added claims, no dropped key facts, no contradictions). "
    "Rewording or compression is fine as long as no fact is invented or lost."
)


def _parse_verdict_json(text: str) -> dict:
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
    def __init__(self, embedder, client: OllamaClient | None = None):
        """
        embedder: object with .embed(text)->np.ndarray (the StyleRetriever)
        client:   OllamaClient for the judge model
        """
        self.embedder = embedder
        self.client = client or OllamaClient(JUDGE_MODEL)

    def evaluate(self, query: str, draft: str, styled: str,
                 style_card: dict) -> JudgeVerdict:
        # Step 1 — deterministic content cosine.
        content_cos = _cosine(self.embedder.embed(draft), self.embedder.embed(styled))

        # Step 2 — judge LLM call.
        user_prompt = (
            f"USER QUESTION: {query}\n\n"
            f"STYLE CARD:\n"
            f"  id: {style_card.get('id','')}\n"
            f"  instruction: {style_card.get('instruction','')}\n"
            f"  tags: {', '.join(style_card.get('tags', []))}\n\n"
            f"DRAFT:\n{draft}\n\n"
            f"STYLED:\n{styled}\n\n"
            "JSON:"
        )
        raw = self.client.generate(
            prompt=user_prompt,
            system=JUDGE_SYSTEM,
            temperature=0.0,
            top_p=1.0,
            max_new_tokens=150,
        )

        parsed = _parse_verdict_json(raw)
        style_score = int(parsed.get("style_score", 3))
        content_faithful_llm = bool(parsed.get("content_faithful", True))
        rationale = str(parsed.get("rationale", "")).strip()

        content_faithful = content_faithful_llm and (content_cos >= CONTENT_PRESERVATION_MIN)

        # Step 3 — action from signals.
        if not content_faithful:
            action = "content_drift"
        elif style_score < 2:
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
