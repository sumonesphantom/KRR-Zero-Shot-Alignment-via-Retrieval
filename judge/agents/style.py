"""Style LLM — rewrites the Knowledge draft in the target style via Ollama.

Current implementation: STYLE_MODE="prompt". The *retrieval* mechanism is still
central — FAISS picks the best Style Card for the user's preference — but the
retrieved card is injected into the prompt (instruction + few-shot examples)
rather than loaded as a LoRA adapter. This is because:

  1. The existing LoRA adapters were trained on TinyLlama-1.1B; their weights
     do not transfer to Llama 3.1 8B or Mistral 7B.
  2. Ollama applies LoRA via GGUF-format adapters (Modelfile `ADAPTER`
     directive), not HF/PEFT format.

To restore the LoRA-retrieval path ("lora" mode), adapters must be retrained
on the new base model and converted to GGUF. Tracked in TODO.md.
"""

from agents.ollama_client import OllamaClient
from config import STYLE_MODEL, STYLE_MODE


STYLE_SYSTEM = (
    "Rewrite the DRAFT in the target STYLE. Preserve every fact. "
    "Output only the rewritten answer."
)


def _user_prompt(draft: str, style_card: dict, preference: str,
                 strength_hint: str = "") -> str:
    examples = style_card.get("examples", [])[:2]
    example_block = ""
    for ex in examples:
        example_block += f"\nExample prompt: {ex.get('prompt','')}\n"
        example_block += f"Example styled answer: {ex.get('answer','')}\n"

    tags = ", ".join(style_card.get("tags", []))
    return (
        f"USER PREFERENCE: {preference}\n"
        f"STYLE INSTRUCTION: {style_card['instruction']}\n"
        f"STYLE TAGS: {tags}\n"
        f"{example_block}\n"
        f"{strength_hint}\n"
        f"DRAFT:\n{draft}\n\n"
        "REWRITTEN ANSWER:"
    )


class StyleLLM:
    def __init__(self, client: OllamaClient | None = None):
        if STYLE_MODE != "prompt":
            raise NotImplementedError(
                f"STYLE_MODE={STYLE_MODE!r} not supported. "
                "Ollama LoRA support requires GGUF-converted adapters; see TODO.md."
            )
        self.client = client or OllamaClient(STYLE_MODEL)

    def restyle(self, draft: str, style_card: dict, preference: str,
                attempt: int = 0, on_chunk=None, on_thinking=None,
                on_thought=None) -> str:
        if attempt == 0:
            hint, temperature = "", 0.7
        elif attempt == 1:
            hint = (
                "NOTE: The previous attempt did not match the style clearly enough. "
                "Commit harder to the style markers (vocabulary, structure, "
                "punctuation) seen in the examples."
            )
            temperature = 0.5
        else:
            hint = (
                "NOTE: Match the style of the examples almost literally. "
                "Mirror their sentence structure and characteristic phrases."
            )
            temperature = 0.35

        return self.client.generate(
            prompt=_user_prompt(draft, style_card, preference, hint),
            system=STYLE_SYSTEM,
            temperature=temperature,
            on_chunk=on_chunk,
            on_thinking=on_thinking,
            on_thought=on_thought,
        )
