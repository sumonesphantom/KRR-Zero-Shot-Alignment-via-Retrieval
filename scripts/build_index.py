"""Build the FAISS retrieval index from style_bank/style_cards.jsonl.

Run once, offline, after editing or adding style cards.

  python scripts/build_index.py

Outputs under data/:
  - style_index.faiss         FAISS IndexFlatIP of MiniLM embeddings
  - id_map.json               int → style_id
  - style_cards_cache.json    the full card list for fast re-read

No PyTorch, no LLM — just sentence-transformers (MiniLM) + faiss-cpu.
"""

from __future__ import annotations

import json
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


REPO_ROOT = Path(__file__).resolve().parents[1]
STYLE_CARDS_PATH = REPO_ROOT / "style_bank" / "style_cards.jsonl"
INDEX_DIR = REPO_ROOT / "data"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def load_style_cards(path: Path = STYLE_CARDS_PATH) -> list[dict]:
    cards: list[dict] = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                cards.append(json.loads(line))
    print(f"Loaded {len(cards)} style cards from {path.relative_to(REPO_ROOT)}")
    return cards


def build_style_text(card: dict) -> str:
    parts = [card["instruction"]]
    parts.append("Tags: " + ", ".join(card.get("tags", [])))
    for ex in card.get("examples", [])[:2]:
        parts.append(f"Example Q: {ex['prompt']}")
        parts.append(f"Example A: {ex['answer'][:200]}")
    return "\n".join(parts)


def build_index() -> None:
    cards = load_style_cards()
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    texts = [build_style_text(c) for c in cards]
    print("Encoding style cards with MiniLM-L6-v2...")
    embeddings = model.encode(texts, show_progress_bar=True, normalize_embeddings=True)
    embeddings = np.array(embeddings, dtype="float32")

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)
    print(f"FAISS IndexFlatIP built: {index.ntotal} vectors · dim {dim}")

    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(INDEX_DIR / "style_index.faiss"))

    id_map = {i: card["id"] for i, card in enumerate(cards)}
    with open(INDEX_DIR / "id_map.json", "w") as f:
        json.dump(id_map, f, indent=2)

    with open(INDEX_DIR / "style_cards_cache.json", "w") as f:
        json.dump(cards, f, indent=2)

    print(f"Index + metadata written to {INDEX_DIR.relative_to(REPO_ROOT)}/")


if __name__ == "__main__":
    build_index()
