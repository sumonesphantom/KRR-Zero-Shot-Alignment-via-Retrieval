"""Request schema for the /api/generate/judge SSE endpoint."""

from __future__ import annotations

from pydantic import Field

from api.schemas.common import CamelModel


class GenerateRequest(CamelModel):
    preference: str = Field(..., min_length=1, max_length=1000)
    query: str = Field(..., min_length=1, max_length=2000)
    top_k: int = Field(default=3, ge=1, le=5)
