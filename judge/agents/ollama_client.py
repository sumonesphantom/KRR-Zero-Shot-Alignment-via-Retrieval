"""Thin wrapper over Ollama's chat API with consistent generate() signature.

Every role (Knowledge, Style, Judge) talks to Ollama through this wrapper so
parameters (temperature, top_p, num_predict, stop) stay uniform and we have
one place to handle retries / errors.
"""

from ollama import Client

from config import OLLAMA_HOST, MAX_NEW_TOKENS


class OllamaClient:
    def __init__(self, model: str, host: str = OLLAMA_HOST):
        self.model = model
        self.client = Client(host=host)

    def generate(self, prompt: str, system: str | None = None,
                 temperature: float = 0.7, top_p: float = 0.9,
                 max_new_tokens: int = MAX_NEW_TOKENS,
                 stop: list[str] | None = None) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        options = {
            "temperature": temperature,
            "top_p": top_p,
            "num_predict": max_new_tokens,
            "repeat_penalty": 1.15,
        }
        if stop:
            options["stop"] = stop

        resp = self.client.chat(
            model=self.model,
            messages=messages,
            options=options,
        )
        return resp["message"]["content"].strip()
