"""Shared configuration for the 3-LLM (Knowledge / Style / Judge) pipeline.

Inference runs through Ollama. Make sure the models below are pulled:

    ollama pull llama3.1:8b-instruct-q4_K_M
    ollama pull mistral:7b-instruct-q4_K_M

The sentence-transformers embedder still runs locally for FAISS retrieval and
for the judge's content-preservation cosine.
"""

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

# Ollama
OLLAMA_HOST = "http://localhost:11434"

# Per-role models (Ollama tags).
# Knowledge and Style use Llama 3.1 8B — strong instruction following, good at
# faithful rewriting. Judge uses Mistral 7B — different family from the
# generator, which reduces self-preference bias (Zheng et al. 2023).
KNOWLEDGE_MODEL = "llama3.1:8b-instruct-q4_K_M"
STYLE_MODEL = "llama3.1:8b-instruct-q4_K_M"
JUDGE_MODEL = "mistral:7b-instruct-q4_K_M"

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

# Style-role mode. Current implementation uses "prompt" (retrieved style card
# injected into the Ollama prompt). "lora" will require retraining adapters on
# the new base model and converting them to GGUF for Ollama's ADAPTER directive.
STYLE_MODE = "prompt"  # one of {"prompt", "lora"} — "lora" not yet implemented for Ollama
