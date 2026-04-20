"""Shared base-model container.

All three roles (Knowledge, Style, Judge) share one loaded copy of the base
model to keep memory manageable. The Style role attaches a LoRA via PEFT;
Knowledge/Judge run with the adapter disabled (PEFT `disable_adapter()`),
so we avoid reloading weights on every role switch.
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

from config import BASE_MODEL_NAME, DEVICE, MAX_NEW_TOKENS, MAX_SEQ_LENGTH, PROJECT_ROOT


class SharedBaseModel:
    def __init__(self, model_name: str = BASE_MODEL_NAME):
        print(f"[shared_model] loading {model_name} on {DEVICE}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        self.base_model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float32,
            device_map={"": DEVICE} if DEVICE != "mps" else None,
        )
        if DEVICE == "mps":
            self.base_model = self.base_model.to("mps")
        self.base_model.eval()

        self._peft_model: PeftModel | None = None
        self._current_adapter: str | None = None

    def ensure_adapter(self, adapter_rel_path: str):
        """Load a LoRA adapter from a repo-relative path. Idempotent."""
        full = str(PROJECT_ROOT / adapter_rel_path)
        if self._current_adapter == full and self._peft_model is not None:
            return
        if self._peft_model is not None:
            del self._peft_model
            if DEVICE == "mps":
                torch.mps.empty_cache()
        self._peft_model = PeftModel.from_pretrained(self.base_model, full)
        self._peft_model.eval()
        self._current_adapter = full

    def model_with_adapter(self):
        assert self._peft_model is not None, "call ensure_adapter first"
        return self._peft_model

    def model_without_adapter(self):
        """Return a model handle that behaves like the base model.

        If a PEFT wrapper exists, use it with the adapter disabled via a
        context manager on the caller's side; we return the wrapper and
        the caller is responsible for using `with model.disable_adapter():`.
        If no adapter has ever been loaded, return the raw base model.
        """
        return self._peft_model if self._peft_model is not None else self.base_model

    def generate(self, model, prompt: str, max_new_tokens: int = MAX_NEW_TOKENS,
                 temperature: float = 0.7, top_p: float = 0.9,
                 do_sample: bool = True) -> str:
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
                temperature=temperature,
                do_sample=do_sample,
                top_p=top_p,
                repetition_penalty=1.15,
                pad_token_id=self.tokenizer.eos_token_id,
            )
        return self.tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[1]:],
            skip_special_tokens=True,
        ).strip()
