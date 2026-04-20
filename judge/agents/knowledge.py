"""Knowledge LLM — produces a factual, style-neutral draft via Ollama.

The draft is intentionally plain so the Style LLM has clean content to
restyle without also having to fix errors.
"""

from agents.ollama_client import OllamaClient
from config import KNOWLEDGE_MODEL


KNOWLEDGE_SYSTEM = (
    "You are a neutral, information-dense assistant. "
    "Answer the user's question with accurate, well-organized facts. "
    "Do NOT adopt any particular tone, persona, or writing style. "
    "Prefer plain declarative sentences. Keep it under 180 words."
)


class KnowledgeLLM:
    def __init__(self, client: OllamaClient | None = None):
        self.client = client or OllamaClient(KNOWLEDGE_MODEL)

    def draft(self, query: str) -> str:
        return self.client.generate(
            prompt=f"Question: {query}\n\nAnswer:",
            system=KNOWLEDGE_SYSTEM,
            temperature=0.5,
        )
