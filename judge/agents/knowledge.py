"""Knowledge LLM — produces a factual, style-neutral draft.

The draft is intentionally plain so the Style LLM has clean content to
restyle without also having to fix errors. Runs on the shared base model
with any LoRA adapter disabled.
"""

from agents.shared_model import SharedBaseModel


KNOWLEDGE_SYSTEM = (
    "You are a neutral, information-dense assistant. "
    "Answer the user's question with accurate, well-organized facts. "
    "Do NOT adopt any particular tone, persona, or writing style. "
    "Prefer plain declarative sentences. Keep it under 180 words."
)


class KnowledgeLLM:
    def __init__(self, shared: SharedBaseModel):
        self.shared = shared

    def draft(self, query: str) -> str:
        prompt = f"{KNOWLEDGE_SYSTEM}\n\nQuestion: {query}\n\nAnswer:"
        model = self.shared.model_without_adapter()
        # If a PEFT wrapper exists, run with adapter disabled so we get base behavior.
        if hasattr(model, "disable_adapter"):
            with model.disable_adapter():
                return self.shared.generate(model, prompt, temperature=0.5)
        return self.shared.generate(model, prompt, temperature=0.5)
