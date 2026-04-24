"""Single source of truth for API runtime configuration.

All env vars in api/.env.example flow through this class. registry.bootstrap()
pulls values from this Settings object (not raw os.environ) so `.env` is
loaded via pydantic-settings regardless of the process CWD.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


# Absolute path to the repo-root `.env`, so pydantic-settings finds it
# regardless of the uvicorn process CWD.
_REPO_ROOT = Path(__file__).resolve().parent.parent
_ENV_FILE = _REPO_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # --- API runtime ---
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    ALLOWED_ORIGINS: str = "http://localhost:3000"
    MAX_CONCURRENT_JUDGE_RUNS: int = 2

    # --- Ollama ---
    # Defaults match local pulls; override with .env per machine.
    # Judge routed to a different model family → no self-preference bias.
    OLLAMA_HOST: str = "http://localhost:11434"
    KNOWLEDGE_MODEL: str = "gemma4:latest"
    STYLE_MODEL: str = "gemma4:latest"
    JUDGE_MODEL: str = "rnj-1:latest"

    # --- Judge orchestrator tuning (None = use judge/config.py defaults) ---
    MAX_REVISIONS: int | None = None
    JUDGE_STYLE_PASS_THRESHOLD: int | None = None
    CONTENT_PRESERVATION_MIN: float | None = None
    TOP_K: int | None = None
    MAX_NEW_TOKENS: int | None = None

    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
