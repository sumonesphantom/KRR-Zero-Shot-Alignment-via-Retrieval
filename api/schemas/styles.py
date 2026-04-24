"""Style card schemas."""

from __future__ import annotations

from api.schemas.common import CamelModel


class StyleExampleOut(CamelModel):
    prompt: str
    answer: str


class StyleCardOut(CamelModel):
    id: str
    tags: list[str]
    instruction: str
    examples: list[StyleExampleOut] = []
    adapter_path: str | None = None


class StylesListResponse(CamelModel):
    styles: list[StyleCardOut]
