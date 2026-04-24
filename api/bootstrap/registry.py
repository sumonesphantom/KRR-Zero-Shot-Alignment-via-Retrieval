"""Isolated import of the judge pipeline.

`judge/` uses bare imports (`from config import ...`, `from retrieve import ...`,
`from agents.orchestrator import ...`). This registry:

  1. Inserts `judge/` on sys.path, imports each module, and applies env overrides
     to the config module IN PLACE before any OllamaClient / Orchestrator is
     constructed.
  2. Re-binds the imported module objects to unique `krr_judge.*` sys.modules
     aliases so the bare names don't leak into the rest of the application.
  3. Asserts that no bare names (`config`, `retrieve`) are left in sys.modules
     after bootstrap — guards against future pipelines colliding on the same
     top-level names.
"""

from __future__ import annotations

import importlib
import sys
from types import ModuleType
from typing import Any

from api.bootstrap.sys_paths import JUDGE_DIR
from api.settings import get_settings


_state: dict[str, Any] = {
    "bootstrapped": False,
    "judge_loaded": False,
    "judge_config": None,
    "judge_retrieve": None,
    "judge_schemas": None,
    "judge_orchestrator_cls": None,
}


def _pop(names: list[str]) -> None:
    for n in names:
        sys.modules.pop(n, None)


def _apply_judge_env_overrides(cfg: ModuleType) -> None:
    """Rebind env-provided values onto the judge config module in place.

    Reads from the `Settings` object (which loads `.env` via an absolute path),
    so the override always matches what `/api/health` reports — no divergence
    between "what Settings says" and "what the OllamaClient was constructed with".
    """
    s = get_settings()

    # Always-set (these have hard defaults in Settings).
    cfg.OLLAMA_HOST = s.OLLAMA_HOST
    cfg.KNOWLEDGE_MODEL = s.KNOWLEDGE_MODEL
    cfg.STYLE_MODEL = s.STYLE_MODEL
    cfg.JUDGE_MODEL = s.JUDGE_MODEL

    # Optional tuning — only apply if the user explicitly set it in .env.
    if s.MAX_REVISIONS is not None:
        cfg.MAX_REVISIONS = s.MAX_REVISIONS
    if s.JUDGE_STYLE_PASS_THRESHOLD is not None:
        cfg.JUDGE_STYLE_PASS_THRESHOLD = s.JUDGE_STYLE_PASS_THRESHOLD
    if s.CONTENT_PRESERVATION_MIN is not None:
        cfg.CONTENT_PRESERVATION_MIN = s.CONTENT_PRESERVATION_MIN
    if s.TOP_K is not None:
        cfg.TOP_K = s.TOP_K
    if s.MAX_NEW_TOKENS is not None:
        cfg.MAX_NEW_TOKENS = s.MAX_NEW_TOKENS


def _load_judge() -> None:
    if _state["judge_loaded"]:
        return

    judge_path = str(JUDGE_DIR)
    sys.path.insert(0, judge_path)

    _pop([
        "config", "retrieve",
        "agents", "agents.orchestrator", "agents.judge", "agents.style",
        "agents.knowledge", "agents.ollama_client", "agents.schemas",
    ])

    try:
        cfg = importlib.import_module("config")
        _apply_judge_env_overrides(cfg)

        retrieve_mod = importlib.import_module("retrieve")
        schemas_mod = importlib.import_module("agents.schemas")
        _ = importlib.import_module("agents.ollama_client")
        _ = importlib.import_module("agents.knowledge")
        _ = importlib.import_module("agents.style")
        _ = importlib.import_module("agents.judge")
        orch_mod = importlib.import_module("agents.orchestrator")

        sys.modules["krr_judge.config"] = cfg
        sys.modules["krr_judge.retrieve"] = retrieve_mod
        sys.modules["krr_judge.schemas"] = schemas_mod
        sys.modules["krr_judge.orchestrator"] = orch_mod

        _state["judge_config"] = cfg
        _state["judge_retrieve"] = retrieve_mod
        _state["judge_schemas"] = schemas_mod
        _state["judge_orchestrator_cls"] = getattr(orch_mod, "Orchestrator")
        _state["judge_loaded"] = True
    finally:
        try:
            sys.path.remove(judge_path)
        except ValueError:
            pass
        _pop([
            "config", "retrieve",
            "agents", "agents.orchestrator", "agents.judge", "agents.style",
            "agents.knowledge", "agents.ollama_client", "agents.schemas",
        ])


def bootstrap() -> None:
    """Load the judge pipeline under namespaced sys.modules aliases. Idempotent."""
    if _state["bootstrapped"]:
        return
    _load_judge()

    stray = [n for n in ("config", "retrieve") if n in sys.modules]
    if stray:
        raise RuntimeError(
            f"[registry] bootstrap left stray bare module names in sys.modules: {stray}."
        )
    _state["bootstrapped"] = True


def _require_judge() -> None:
    if not _state["judge_loaded"]:
        raise RuntimeError("registry.bootstrap() must be called before accessing the judge pipeline")


def get_judge_orchestrator_cls():
    _require_judge()
    return _state["judge_orchestrator_cls"]


def get_judge_schemas() -> ModuleType:
    _require_judge()
    return _state["judge_schemas"]


def get_judge_retrieve() -> ModuleType:
    _require_judge()
    return _state["judge_retrieve"]


def get_judge_config() -> ModuleType:
    _require_judge()
    return _state["judge_config"]


def debug_state() -> dict[str, Any]:
    return {
        "bootstrapped": _state["bootstrapped"],
        "judge_loaded": _state["judge_loaded"],
    }
