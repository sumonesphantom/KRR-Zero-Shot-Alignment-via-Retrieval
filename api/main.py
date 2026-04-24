"""FastAPI app for the Zero-Shot Alignment via Retrieval web product.

Lifespan:
  - Bootstrap the dual-pipeline registry (applies env overrides onto the
    pipeline config modules in-place).
  - Warm the style-card cache.
  - Record initial Ollama reachability + index presence for /api/health.

Shutdown: nothing aggressive; uvicorn reaps on exit.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from api.bootstrap import registry
from api.bootstrap.sys_paths import FAISS_INDEX_PATH
from api.settings import get_settings
from api.services import styles_service
from api.routers import health as health_router
from api.routers import styles as styles_router
from api.routers import traces as traces_router
from api.routers import generate as generate_router


logger = logging.getLogger("api.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info("Bootstrapping registry...")
    registry.bootstrap()

    # Warm style cards cache (cheap, fast-fail if file is missing).
    try:
        cards = styles_service.load_cards()
        logger.info("Loaded %d style cards", len(cards))
    except FileNotFoundError as e:
        logger.warning("style cards not loaded: %s", e)

    if not FAISS_INDEX_PATH.exists():
        logger.warning(
            "FAISS index missing at %s. Run: python scripts/build_index.py",
            FAISS_INDEX_PATH,
        )

    logger.info("API ready. Models: K=%s S=%s J=%s Ollama=%s",
                settings.KNOWLEDGE_MODEL, settings.STYLE_MODEL,
                settings.JUDGE_MODEL, settings.OLLAMA_HOST)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="KRR — Zero-Shot Alignment via Retrieval",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Content-Type"],
    )

    app.include_router(health_router.router)
    app.include_router(styles_router.router)
    app.include_router(traces_router.router)
    app.include_router(generate_router.router)

    @app.exception_handler(Exception)
    async def on_unhandled(_request, exc: Exception):
        logger.exception("Unhandled exception")
        return JSONResponse(
            status_code=500,
            content={"error": "internal", "detail": str(exc), "code": "INTERNAL"},
        )

    return app


app = create_app()
