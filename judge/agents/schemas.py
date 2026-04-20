"""Data contracts for the 3-LLM pipeline."""

from dataclasses import dataclass, field, asdict
from typing import Literal, Optional, List, Dict, Any


JudgeAction = Literal["accept", "revise_style", "content_drift", "wrong_style"]


@dataclass
class JudgeVerdict:
    """Structured output of the Judge LLM.

    The `action` field is the control signal the orchestrator acts on.
    """
    style_score: int           # 1–5, how well the styled output matches the target style card
    content_faithful: bool     # does the styled output preserve the draft's facts?
    content_cosine: float      # embedding cosine between draft and styled (0–1)
    action: JudgeAction
    rationale: str = ""
    raw: str = ""              # raw judge model output, for debugging


@dataclass
class RevisionStep:
    attempt: int
    style_id: str
    draft: str
    styled: str
    verdict: JudgeVerdict


@dataclass
class PipelineTrace:
    query: str
    preference: str
    retrieval: List[Dict[str, Any]]
    draft: str
    revisions: List[RevisionStep] = field(default_factory=list)
    final_style_id: str = ""
    final_output: str = ""
    final_verdict: Optional[JudgeVerdict] = None

    def to_dict(self):
        return asdict(self)
