"""Shared schemas: CamelModel base, health, error responses."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class OllamaHealth(CamelModel):
    reachable: bool
    host: str
    error: str | None = None
    models_available: list[str] = []


class IndexHealth(CamelModel):
    present: bool
    path: str


class ModelsInUse(CamelModel):
    knowledge: str
    style: str
    judge: str


class HealthResponse(CamelModel):
    status: str  # 'ok' | 'degraded'
    ollama: OllamaHealth
    index: IndexHealth
    judge_ready: bool
    max_revisions: int
    models: ModelsInUse


class ErrorResponse(CamelModel):
    error: str
    detail: str | None = None
    code: str
