"""Generate responses using retrieved style adapters."""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
from retrieve import StyleRetriever
from config import (
    BASE_MODEL_NAME, DEVICE, MAX_NEW_TOKENS, MAX_SEQ_LENGTH, PROJECT_ROOT
)


class StyledGenerator:
    """Generates responses using retrieved style LoRA adapters."""

    def __init__(self):
        print(f"Loading base model: {BASE_MODEL_NAME} on {DEVICE}")
        self.tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_NAME)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        self.base_model = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL_NAME,
            torch_dtype=torch.float32,
            device_map={"": DEVICE} if DEVICE != "mps" else None,
        )
        if DEVICE == "mps":
            self.base_model = self.base_model.to("mps")

        self.retriever = StyleRetriever()
        self._current_adapter = None
        self._adapted_model = None

    def _load_adapter(self, adapter_path: str):
        """Load a LoRA adapter onto the base model."""
        full_path = str(PROJECT_ROOT / adapter_path)
        if self._current_adapter == full_path:
            return  # Already loaded

        # Reset to base model if we had a different adapter
        if self._adapted_model is not None:
            del self._adapted_model
            if DEVICE == "mps":
                torch.mps.empty_cache()

        self._adapted_model = PeftModel.from_pretrained(
            self.base_model, full_path
        )
        self._adapted_model.eval()
        self._current_adapter = full_path
        print(f"  Loaded adapter: {adapter_path}")

    def _generate(self, model, prompt: str, max_new_tokens=MAX_NEW_TOKENS):
        """Generate text from a model."""
        chat_prompt = f"<|user|>\n{prompt}\n<|assistant|>\n"
        inputs = self.tokenizer(
            chat_prompt,
            return_tensors="pt",
            truncation=True,
            max_length=MAX_SEQ_LENGTH,
        ).to(model.device)

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=0.7,
                do_sample=True,
                top_p=0.9,
                pad_token_id=self.tokenizer.eos_token_id,
            )

        generated = self.tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[1]:],
            skip_special_tokens=True,
        ).strip()
        return generated

    def generate_base(self, prompt: str):
        """Generate using the base model (no adapter)."""
        return self._generate(self.base_model, prompt)

    def generate_with_style(self, prompt: str, style_id: str = None,
                            preference_query: str = None, top_k: int = 1):
        """
        Generate using a style adapter.

        Either specify style_id directly, or provide preference_query
        to retrieve the best matching style.

        Args:
            prompt: The actual question/prompt to answer
            style_id: Explicit style adapter ID (skip retrieval)
            preference_query: Natural language preference description
            top_k: Number of styles to consider (1 = top-1 retrieval)

        Returns:
            dict with generated text, style info, and retrieval results
        """
        if preference_query:
            retrieval_results = self.retriever.retrieve(preference_query, top_k)
            best = retrieval_results[0]
            style_id = best["style_id"]
            adapter_path = best["card"]["adapter_path"]
        else:
            # Direct style specification
            retrieval_results = None
            card = self.retriever.cards[style_id]
            adapter_path = card["adapter_path"]

        # Load and generate with adapter
        self._load_adapter(adapter_path)
        styled_response = self._generate(self._adapted_model, prompt)

        return {
            "prompt": prompt,
            "style_id": style_id,
            "response": styled_response,
            "retrieval_results": retrieval_results,
        }

    def generate_comparison(self, prompt: str, preference_query: str, top_k: int = 3):
        """
        Generate a full comparison: base model vs retrieved style vs random style.

        Returns dict with all outputs for evaluation.
        """
        import random

        # Base model output
        base_output = self.generate_base(prompt)

        # Retrieved style output
        retrieval_results = self.retriever.retrieve(preference_query, top_k)
        best = retrieval_results[0]
        self._load_adapter(best["card"]["adapter_path"])
        retrieved_output = self._generate(self._adapted_model, prompt)

        # Random style output (different from retrieved)
        all_style_ids = list(self.retriever.cards.keys())
        random_style_id = random.choice(
            [s for s in all_style_ids if s != best["style_id"]]
        )
        random_card = self.retriever.cards[random_style_id]
        self._load_adapter(random_card["adapter_path"])
        random_output = self._generate(self._adapted_model, prompt)

        return {
            "prompt": prompt,
            "preference_query": preference_query,
            "base_output": base_output,
            "retrieved_style_id": best["style_id"],
            "retrieved_output": retrieved_output,
            "random_style_id": random_style_id,
            "random_output": random_output,
            "retrieval_results": retrieval_results,
        }


def demo_generation():
    """Demo the generation system."""
    gen = StyledGenerator()

    test_cases = [
        {
            "prompt": "Explain how machine learning works.",
            "preference": "I want a formal, academic explanation with proper terminology",
        },
        {
            "prompt": "What is climate change?",
            "preference": "explain it simply like I'm 5, use fun analogies",
        },
        {
            "prompt": "How does the internet work?",
            "preference": "be concise, use bullet points, no fluff",
        },
    ]

    for tc in test_cases:
        print(f"\n{'='*70}")
        print(f"Prompt: {tc['prompt']}")
        print(f"Preference: {tc['preference']}")
        print(f"{'='*70}")

        result = gen.generate_comparison(tc["prompt"], tc["preference"])

        print(f"\n--- Base Model ---")
        print(result["base_output"][:300])
        print(f"\n--- Retrieved Style: {result['retrieved_style_id']} ---")
        print(result["retrieved_output"][:300])
        print(f"\n--- Random Style: {result['random_style_id']} ---")
        print(result["random_output"][:300])


if __name__ == "__main__":
    demo_generation()
