"""GET /api/health — reports Ollama + FAISS index readiness. Never 500s."""

from __future__ import annotations

import logging

from fastapi import APIRouter
from ollama import Client as OllamaClient

from api.bootstrap import registry
from api.bootstrap.sys_paths import FAISS_INDEX_PATH, STYLE_CARDS_PATH
from api.schemas.common import (
    HealthResponse,
    IndexHealth,
    ModelsInUse,
    OllamaHealth,
)
from api.settings import get_settings


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")


@router.get("/health", response_model=HealthResponse)
async def health():
    settings = get_settings()

    # Ollama reachability + pulled models.
    ollama_reachable = False
    ollama_error: str | None = None
    models_available: list[str] = []
    try:
        client = OllamaClient(host=settings.OLLAMA_HOST, timeout=1.0)
        resp = client.list()
        models_available = [m.get("name") or m.get("model") or "" for m in resp.get("models", [])]
        models_available = [m for m in models_available if m]
        ollama_reachable = True
    except Exception as e:
        ollama_error = f"{type(e).__name__}: {e}"

    index_present = FAISS_INDEX_PATH.exists()

    try:
        jcfg = registry.get_judge_config()
        max_revisions = int(getattr(jcfg, "MAX_REVISIONS", 2))
    except Exception:
        max_revisions = 2

    judge_ready = index_present and ollama_reachable and STYLE_CARDS_PATH.exists()
    status = "ok" if judge_ready else "degraded"

    return HealthResponse(
        status=status,
        ollama=OllamaHealth(
            reachable=ollama_reachable,
            host=settings.OLLAMA_HOST,
            error=ollama_error,
            models_available=models_available,
        ),
        index=IndexHealth(present=index_present, path=str(FAISS_INDEX_PATH)),
        judge_ready=judge_ready,
        max_revisions=max_revisions,
        models=ModelsInUse(
            knowledge=settings.KNOWLEDGE_MODEL,
            style=settings.STYLE_MODEL,
            judge=settings.JUDGE_MODEL,
        ),
    )
