"""Thin wrapper over Ollama's chat API with a consistent `generate()` signature.

Every role (Knowledge, Style, Judge) talks to Ollama through this wrapper so
parameters stay uniform and we have one place to handle retries / errors /
streaming.

Fixes for Gemma on Ollama that were needed when Style/Judge returned empty:
  1. Expand context window (num_ctx=8192). Style/Judge prompts easily exceed
     Ollama's default 2048, after which the server silently truncates and the
     generation can collapse to 0 tokens.
  2. Floor the sampling temperature at 0.01 — Gemma builds in Ollama have been
     observed to return empty strings at exactly temperature=0.
  3. Fold system messages into the user turn. Gemma's native chat template has
     no system role; Ollama's template merges them but handling has been
     inconsistent across versions. Inlining is robust.
  4. Disable the reasoning channel. Gemma 3n (shipped here as gemma4:e4b)
     runs in "thinking" mode by default under Ollama: the model produces a
     long internal chain-of-thought that goes to `message.thinking` while
     `message.content` stays empty until the reasoning finishes. On rewrite/
     JSON prompts it regularly burned the entire `num_predict` budget on
     thinking, yielding empty content. We pass `think=False` to shut it off.
  5. Fallback retry: if the first call still returns empty, retry once with a
     small temperature bump, then surface the empty to the caller if still bad.

Token-level streaming: pass `on_chunk=callback` to `generate()` and the wrapper
will open a streaming chat, call the callback per delta, and return the full
accumulated content. Used by the orchestrator to emit `draft_delta` /
`style_delta` SSE events to the web UI.
"""

from typing import Callable, Optional

from ollama import Client

from config import OLLAMA_HOST, MAX_NEW_TOKENS


NUM_CTX = 8192
MIN_TEMPERATURE = 0.01


class OllamaClient:
    def __init__(self, model: str, host: str = OLLAMA_HOST):
        self.model = model
        self.client = Client(host=host)

    def _chat(self, user_content: str, temperature: float, top_p: float,
              max_new_tokens: int, stop: list[str] | None,
              on_chunk: Optional[Callable[[str], None]] = None) -> str:
        options = {
            "temperature": max(temperature, MIN_TEMPERATURE),
            "top_p": top_p,
            "num_predict": max_new_tokens,
            "num_ctx": NUM_CTX,
            "repeat_penalty": 1.15,
        }
        if stop:
            options["stop"] = stop

        if on_chunk is None:
            # Non-streaming path — preserves the original behavior exactly.
            resp = self.client.chat(
                model=self.model,
                messages=[{"role": "user", "content": user_content}],
                options=options,
                think=False,
            )
            content = (resp["message"]["content"] or "").strip()
            if content:
                return content
            thinking = getattr(resp["message"], "thinking", None) or ""
            return thinking.strip()

        # Streaming path — yield chunks to the callback; accumulate for retries.
        acc: list[str] = []
        thinking_acc: list[str] = []
        try:
            stream = self.client.chat(
                model=self.model,
                messages=[{"role": "user", "content": user_content}],
                options=options,
                think=False,
                stream=True,
            )
            for chunk in stream:
                msg = chunk.get("message") if isinstance(chunk, dict) else chunk.message
                if msg is None:
                    continue
                delta = (msg.get("content") if isinstance(msg, dict) else getattr(msg, "content", None)) or ""
                if delta:
                    acc.append(delta)
                    try:
                        on_chunk(delta)
                    except Exception as e:
                        print(f"[ollama_client] on_chunk raised: {e!r}")
                # Some builds route early output to `thinking` even with think=False.
                th = (msg.get("thinking") if isinstance(msg, dict) else getattr(msg, "thinking", None)) or ""
                if th:
                    thinking_acc.append(th)
        except Exception as e:
            print(f"[ollama_client] stream error: {e!r}")

        content = ("".join(acc)).strip()
        if content:
            return content
        return ("".join(thinking_acc)).strip()

    def generate(self, prompt: str, system: str | None = None,
                 temperature: float = 0.7, top_p: float = 0.9,
                 max_new_tokens: int = MAX_NEW_TOKENS,
                 stop: list[str] | None = None,
                 on_chunk: Optional[Callable[[str], None]] = None) -> str:
        """Generate a completion. If `on_chunk` is provided, streams tokens
        through the callback as they arrive; returns the full text either way.
        """
        user_content = f"{system}\n\n{prompt}" if system else prompt

        out = self._chat(user_content, temperature, top_p, max_new_tokens, stop, on_chunk)
        if out:
            return out

        # Retry once with a slight temperature bump before giving up. The retry
        # is always non-streaming — if the first streamed attempt yielded
        # nothing, we don't want to re-stream an empty to the UI.
        retry_temp = max(temperature + 0.1, 0.2)
        out = self._chat(user_content, retry_temp, top_p, max_new_tokens, stop, None)
        if not out:
            print(f"[ollama_client] WARNING: empty response from model={self.model} "
                  f"after retry (prompt len={len(user_content)} chars)")
        return out
