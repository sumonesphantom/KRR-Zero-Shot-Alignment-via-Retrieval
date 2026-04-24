"""Shared configuration for the Knowledge / Style / Judge pipeline.

All LLM inference runs through Ollama. Sentence-transformers (MiniLM) runs
locally for FAISS retrieval and for the judge's content-preservation cosine.

Values here are defaults — api/bootstrap/registry.py patches them in-place
from api/settings.py (which loads .env at an absolute path) before any
OllamaClient / Orchestrator is constructed. So override via .env, not here.
"""

from pathlib import Path

# Repo root — one level above judge/
PROJECT_ROOT = Path(__file__).parent.parent

# Shared paths
STYLE_BANK_DIR = PROJECT_ROOT / "style_bank"
STYLE_CARDS_PATH = STYLE_BANK_DIR / "style_cards.jsonl"
INDEX_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"
TRACES_DIR = RESULTS_DIR / "traces"

# Ollama
OLLAMA_HOST = "http://localhost:11434"

# Per-role models. Knowledge and Style use the same model; Judge uses a
# different family so it doesn't self-prefer its own outputs (Zheng et al.
# 2023). Override per-machine via .env.
KNOWLEDGE_MODEL = "gemma4:latest"
STYLE_MODEL = "gemma4:latest"
JUDGE_MODEL = "rnj-1:latest"

# Embedding model for FAISS retrieval + judge content cosine.
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Retrieval
TOP_K = 5
TEMPERATURE = 0.1

# Generation
MAX_NEW_TOKENS = 256

# Orchestrator control loop
MAX_REVISIONS = 2
JUDGE_STYLE_PASS_THRESHOLD = 4     # judge must rate styled ≥ this (1–5) to accept
CONTENT_PRESERVATION_MIN = 0.70    # cosine(draft, styled) ≥ this or flag drift

# The retrieved style card is injected into the Style LLM's prompt (instruction
# + few-shot examples). There is no LoRA / adapter path — style is data.
STYLE_MODE = "prompt"
