"""Singleton wrapper around the judge Orchestrator.

Lazy-constructed on first use (behind a lock) because Orchestrator.__init__
builds the StyleRetriever, which loads SentenceTransformer (~300MB) + FAISS
index — ~3–5 s cold start.
"""

from __future__ import annotations

import asyncio
from typing import Callable, Optional

from api.bootstrap import registry


_instance = None
_lock = asyncio.Lock()


async def get_orchestrator():
    global _instance
    if _instance is not None:
        return _instance
    async with _lock:
        if _instance is not None:
            return _instance
        # Running in the default executor keeps the event loop responsive while
        # SentenceTransformer and FAISS initialize.
        _instance = await asyncio.to_thread(_build)
        return _instance


def _build():
    cls = registry.get_judge_orchestrator_cls()
    return cls()


def is_ready() -> bool:
    return _instance is not None
