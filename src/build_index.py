"""Build a FAISS index from style cards for fast retrieval."""

import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from config import (
    STYLE_CARDS_PATH, INDEX_DIR, EMBEDDING_MODEL_NAME
)


def load_style_cards(path=STYLE_CARDS_PATH):
    """Load style cards from JSONL file."""
    cards = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                cards.append(json.loads(line))
    print(f"Loaded {len(cards)} style cards.")
    return cards


def build_style_text(card):
    """Build a searchable text representation from a style card."""
    parts = [card["instruction"]]
    parts.append("Tags: " + ", ".join(card["tags"]))
    for ex in card.get("examples", [])[:2]:
        parts.append(f"Example Q: {ex['prompt']}")
        parts.append(f"Example A: {ex['answer'][:200]}")
    return "\n".join(parts)


def build_index():
    """Build and save the FAISS index + metadata."""
    cards = load_style_cards()
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    # Build text representations
    texts = [build_style_text(c) for c in cards]

    # Encode
    print("Encoding style cards...")
    embeddings = model.encode(texts, show_progress_bar=True, normalize_embeddings=True)
    embeddings = np.array(embeddings, dtype="float32")

    # Build FAISS index (inner product = cosine sim when normalized)
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)
    print(f"FAISS index built with {index.ntotal} vectors of dim {dim}.")

    # Save
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(INDEX_DIR / "style_index.faiss"))

    id_map = {i: card["id"] for i, card in enumerate(cards)}
    with open(INDEX_DIR / "id_map.json", "w") as f:
        json.dump(id_map, f, indent=2)

    with open(INDEX_DIR / "style_cards_cache.json", "w") as f:
        json.dump(cards, f, indent=2)

    print(f"Index and metadata saved to {INDEX_DIR}")
    return index, id_map, cards


if __name__ == "__main__":
    build_index()
