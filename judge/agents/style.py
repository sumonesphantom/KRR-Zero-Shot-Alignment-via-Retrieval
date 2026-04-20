"""Style LLM — rewrites the Knowledge draft in the target style.

Uses the shared base model with the retrieved LoRA adapter attached.
Following ZeroStylus (2025), rewriting an existing draft is an easier
task than cold styled generation and preserves content better.
"""

from agents.shared_model import SharedBaseModel


def _rewrite_prompt(draft: str, style_card: dict, preference: str,
                    strength_hint: str = "") -> str:
    examples = style_card.get("examples", [])[:2]
    example_block = ""
    for ex in examples:
        example_block += f"\nExample prompt: {ex.get('prompt','')}\n"
        example_block += f"Example styled answer: {ex.get('answer','')}\n"

    tags = ", ".join(style_card.get("tags", []))
    return (
        "You are a rewriter. Rewrite the DRAFT below in the requested STYLE.\n"
        "Rules:\n"
        " 1. Preserve every fact in the DRAFT — do not add new claims or drop facts.\n"
        " 2. Change only tone, vocabulary, and structure to match the style.\n"
        " 3. Produce ONLY the rewritten answer — no preamble, no meta commentary.\n"
        f"{strength_hint}\n\n"
        f"USER PREFERENCE: {preference}\n"
        f"STYLE INSTRUCTION: {style_card['instruction']}\n"
        f"STYLE TAGS: {tags}\n"
        f"{example_block}\n"
        f"DRAFT:\n{draft}\n\n"
        "REWRITTEN ANSWER:"
    )


class StyleLLM:
    def __init__(self, shared: SharedBaseModel):
        self.shared = shared

    def restyle(self, draft: str, style_card: dict, preference: str,
                attempt: int = 0) -> str:
        # On retries, tighten the rewrite directive.
        hint = ""
        temperature = 0.7
        if attempt == 1:
            hint = " 4. The previous attempt did not match the style clearly enough. Commit harder to the style markers (vocabulary, structure, punctuation) from the examples."
            temperature = 0.5
        elif attempt >= 2:
            hint = " 4. Match the style in the examples almost literally. Mirror their sentence structure and characteristic phrases."
            temperature = 0.35

        prompt = _rewrite_prompt(draft, style_card, preference, hint)
        self.shared.ensure_adapter(style_card["adapter_path"])
        model = self.shared.model_with_adapter()
        return self.shared.generate(model, prompt, temperature=temperature)
