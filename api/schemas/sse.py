"""Event payloads for SSE stream. Documentation-only; the router serializes dicts
directly into frames. Kept here so the TS client can mirror them.
"""

from __future__ import annotations

from typing import Literal

from api.schemas.common import CamelModel
from api.schemas.traces import JudgeVerdictOut, RetrievalHitOut


class RetrievalEvent(CamelModel):
    type: Literal["retrieval"]
    retrieval: list[RetrievalHitOut]


class DraftEvent(CamelModel):
    type: Literal["draft"]
    draft: str


class StyleAttemptStartEvent(CamelModel):
    type: Literal["style_attempt_start"]
    attempt: int
    attempt_for_style: int
    style_id: str


class StyleAttemptEvent(CamelModel):
    type: Literal["style_attempt"]
    attempt: int
    style_id: str
    styled: str


class JudgeVerdictEvent(CamelModel):
    type: Literal["judge_verdict"]
    attempt: int
    style_id: str
    verdict: JudgeVerdictOut


class FinalEvent(CamelModel):
    type: Literal["final"]
    final_style_id: str
    final_output: str
    final_verdict: JudgeVerdictOut


class ErrorEvent(CamelModel):
    type: Literal["error"]
    code: str
    message: str
