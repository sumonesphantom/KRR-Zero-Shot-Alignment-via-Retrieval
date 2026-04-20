"""Shared configuration for the 3-LLM (Knowledge / Style / Judge) pipeline.

Paths point to the repo root so style_bank/, data/, and results/ are shared
with the single-LLM pipeline in previous/.
"""

import torch
from pathlib import Path

# Repo root — one level above judge/
PROJECT_ROOT = Path(__file__).parent.parent

# Shared paths
STYLE_BANK_DIR = PROJECT_ROOT / "style_bank"
STYLE_CARDS_PATH = STYLE_BANK_DIR / "style_cards.jsonl"
ADAPTERS_DIR = STYLE_BANK_DIR / "adapters"
INDEX_DIR = PROJECT_ROOT / "data"
TRAINING_DATA_DIR = PROJECT_ROOT / "data" / "training"
RESULTS_DIR = PROJECT_ROOT / "results"
TRACES_DIR = RESULTS_DIR / "traces"

# Models
BASE_MODEL_NAME = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
# If set, judge uses a separate, stronger model. None = reuse BASE_MODEL_NAME.
JUDGE_MODEL_NAME = None


def get_device():
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


DEVICE = get_device()

# Retrieval
TOP_K = 5
TEMPERATURE = 0.1

# Generation
MAX_NEW_TOKENS = 256
MAX_SEQ_LENGTH = 512

# Orchestrator control loop
MAX_REVISIONS = 2
JUDGE_STYLE_PASS_THRESHOLD = 4  # 1–5 scale, judge must rate ≥ this to accept
CONTENT_PRESERVATION_MIN = 0.70  # cosine(draft, styled) ≥ this or flag drift
