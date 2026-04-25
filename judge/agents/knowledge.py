"""Knowledge LLM — produces a factual, style-neutral draft via Ollama.

The draft is intentionally plain so the Style LLM has clean content to
restyle without also having to fix errors.
"""

from agents.ollama_client import OllamaClient
from config import KNOWLEDGE_MODEL


KNOWLEDGE_SYSTEM = (
    "You are a neutral, information-dense reference writer. "
    "Your output is a DRAFT that a separate style model will rewrite afterwards, "
    "so focus only on factual substance — not tone, persona, or formatting flair. "
    "Produce a thorough, self-contained explanation that covers: "
    "(a) what the thing is, (b) how it works / the mechanism, "
    "(c) the key components or steps involved, and (d) a concrete example "
    "or canonical use case when it helps clarity. "
    "Aim for roughly 150–300 words of substantive content — do not pad with "
    "throat-clearing or restatements, but do not under-answer either. "
    "Use plain declarative sentences. Markdown is allowed (short paragraphs, "
    "bullet lists where genuinely list-like, inline code for identifiers). "
    "Do not add headings, emojis, or style-specific vocabulary."
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
