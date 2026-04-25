"""Knowledge LLM — produces a factual, style-neutral draft via Ollama.

The draft is intentionally plain so the Style LLM has clean content to
restyle without also having to fix errors.
"""

from agents.ollama_client import OllamaClient
from config import KNOWLEDGE_MODEL


KNOWLEDGE_SYSTEM = (
    "Answer the question accurately and thoroughly in plain neutral prose. "
    "No tone or persona — a separate model will style it afterwards."
)


class KnowledgeLLM:
    def __init__(self, client: OllamaClient | None = None):
        self.client = client or OllamaClient(KNOWLEDGE_MODEL)

    def draft(self, query: str, on_chunk=None, on_thinking=None,
              on_thought=None) -> str:
        return self.client.generate(
            prompt=f"Question: {query}\n\nAnswer:",
            system=KNOWLEDGE_SYSTEM,
            temperature=0.5,
            on_chunk=on_chunk,
            on_thinking=on_thinking,
            on_thought=on_thought,
        )
