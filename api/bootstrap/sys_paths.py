"""Repo-root + pipeline-path resolution."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
JUDGE_DIR = REPO_ROOT / "judge"
STYLE_BANK_DIR = REPO_ROOT / "style_bank"
STYLE_CARDS_PATH = STYLE_BANK_DIR / "style_cards.jsonl"
DATA_DIR = REPO_ROOT / "data"
FAISS_INDEX_PATH = DATA_DIR / "style_index.faiss"
ID_MAP_PATH = DATA_DIR / "id_map.json"
STYLE_CARDS_CACHE_PATH = DATA_DIR / "style_cards_cache.json"
RESULTS_DIR = REPO_ROOT / "results"
TRACES_DIR = RESULTS_DIR / "traces"
EVAL_JUDGE_PATH = RESULTS_DIR / "evaluation_results_3llm.json"
