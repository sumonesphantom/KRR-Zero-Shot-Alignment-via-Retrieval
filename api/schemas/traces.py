"""Trace schemas mirroring judge/agents/schemas dataclasses (camelCased)."""

from __future__ import annotations

from typing import Literal

from api.schemas.common import CamelModel
from api.schemas.styles import StyleCardOut


JudgeAction = Literal["accept", "revise_style", "content_drift", "wrong_style"]


class JudgeVerdictOut(CamelModel):
    style_score: int
    content_faithful: bool
    content_cosine: float
    action: JudgeAction
    rationale: str = ""
    raw: str = ""


class RetrievalHitOut(CamelModel):
    rank: int
    style_id: str
    score: float
    weight: float
    card: StyleCardOut | None = None


class RevisionStepOut(CamelModel):
    attempt: int
    style_id: str
    draft: str
    styled: str
    verdict: JudgeVerdictOut


class PipelineTraceOut(CamelModel):
    query: str
    preference: str
    retrieval: list[RetrievalHitOut]
    draft: str
    revisions: list[RevisionStepOut] = []
    final_style_id: str = ""
    final_output: str = ""
    final_verdict: JudgeVerdictOut | None = None


class TraceSummary(CamelModel):
    id: str
    path: str
    query: str
    preference: str
    final_style_id: str
    n_revisions: int
    created_at: str | None = None


class EvaluationsAvailable(CamelModel):
    judge: bool


class TraceListResponse(CamelModel):
    traces: list[TraceSummary]
    evaluations_available: EvaluationsAvailable
