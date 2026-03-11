"""Retrieve top-k style modules for a given user preference query."""

import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from config import INDEX_DIR, EMBEDDING_MODEL_NAME, TOP_K, TEMPERATURE


class StyleRetriever:
    """Retrieves the best matching style adapters for a preference query."""

    def __init__(self):
        self.model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        self.index = faiss.read_index(str(INDEX_DIR / "style_index.faiss"))

        with open(INDEX_DIR / "id_map.json", "r") as f:
            self.id_map = json.load(f)

        with open(INDEX_DIR / "style_cards_cache.json", "r") as f:
            self.cards = {c["id"]: c for c in json.load(f)}

    def retrieve(self, query: str, top_k: int = TOP_K):
        """
        Retrieve top-k style cards matching the query.

        Args:
            query: Natural language preference description
                   e.g. "I want formal, academic explanations"
            top_k: Number of results to return

        Returns:
            List of (style_card, similarity_score, weight) tuples
        """
        query_emb = self.model.encode(
            [query], normalize_embeddings=True
        ).astype("float32")

        scores, indices = self.index.search(query_emb, top_k)
        scores = scores[0]
        indices = indices[0]

        # Compute softmax weights
        weights = np.exp(scores / TEMPERATURE)
        weights = weights / weights.sum()

        results = []
        for i, (idx, score, weight) in enumerate(zip(indices, scores, weights)):
            style_id = self.id_map[str(idx)]
            card = self.cards[style_id]
            results.append({
                "rank": i + 1,
                "style_id": style_id,
                "score": float(score),
                "weight": float(weight),
                "card": card,
            })

        return results


def demo_retrieval():
    """Demo the retrieval system."""
    retriever = StyleRetriever()

    queries = [
        "I want clear, formal, academic explanations with proper terminology",
        "explain things simply like I'm a beginner, use fun analogies",
        "be concise and use bullet points, no fluff",
        "answer like a supportive teacher who encourages questions",
        "I want technical, precise answers with code and formulas",
        "give me a balanced critical analysis with multiple perspectives",
    ]

    for query in queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}")
        results = retriever.retrieve(query, top_k=3)
        for r in results:
            print(f"  #{r['rank']} {r['style_id']:30s} "
                  f"score={r['score']:.4f}  weight={r['weight']:.4f}")


if __name__ == "__main__":
    demo_retrieval()
