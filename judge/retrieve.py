"""Retrieve top-k style modules for a given user preference query.

Identical algorithm to previous/src/retrieve.py but imports the judge/ config.
"""

import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from config import INDEX_DIR, EMBEDDING_MODEL_NAME, TOP_K, TEMPERATURE


class StyleRetriever:
    def __init__(self):
        self.model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        self.index = faiss.read_index(str(INDEX_DIR / "style_index.faiss"))
        with open(INDEX_DIR / "id_map.json", "r") as f:
            self.id_map = json.load(f)
        with open(INDEX_DIR / "style_cards_cache.json", "r") as f:
            self.cards = {c["id"]: c for c in json.load(f)}

    def retrieve(self, query: str, top_k: int = TOP_K):
        query_emb = self.model.encode(
            [query], normalize_embeddings=True
        ).astype("float32")
        scores, indices = self.index.search(query_emb, top_k)
        scores, indices = scores[0], indices[0]

        weights = np.exp(scores / TEMPERATURE)
        weights = weights / weights.sum()

        return [
            {
                "rank": i + 1,
                "style_id": self.id_map[str(idx)],
                "score": float(score),
                "weight": float(weight),
                "card": self.cards[self.id_map[str(idx)]],
            }
            for i, (idx, score, weight) in enumerate(zip(indices, scores, weights))
        ]

    def embed(self, text: str) -> np.ndarray:
        """Expose the sentence embedder for content-preservation scoring."""
        return self.model.encode([text], normalize_embeddings=True).astype("float32")[0]
