# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository purpose

Zero-shot preference alignment via retrieval: given a natural-language preference ("be formal and academic"), retrieve a pre-authored style card from a FAISS index and run a three-LLM **Knowledge / Style / Judge** control loop to generate a style-aligned response. All LLM calls go through Ollama. There is no TinyLlama, no PyTorch, no LoRA training — style is represented as data (JSONL style cards), retrieval is embedding + FAISS, and the pipeline never mutates model weights.

## Commands

All commands run from the repo root. No Makefile, no test suite.

```bash
# one-time — install deps, pull models, build the FAISS index
pip install -r requirements.txt
pip install -r api/requirements-api.txt
pnpm -C web install
ollama pull gemma4:latest && ollama pull rnj-1:latest    # or whatever models you'll use
python scripts/build_index.py                            # writes data/style_index.faiss + id_map.json + style_cards_cache.json

# CLI pipeline
python judge/run_pipeline.py --step evaluate     # 20-prompt eval; writes results/evaluation_results_3llm.json + traces/
python judge/run_pipeline.py --step demo         # interactive REPL

# Web stack (3 shells)
ollama serve
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
pnpm -C web dev                                  # http://localhost:3000

# or all-in-one
docker compose up
```

No test suite or linter. Sanity-check backend changes with:

```bash
python -m api.scripts.smoke_registry             # registry isolation + on_event kwarg
python -m api.scripts.smoke_orchestrator "be formal" "Explain how a computer stores data."
```

## Architecture

### The KSJ loop (`judge/agents/orchestrator.py`)

The core algorithm. `Orchestrator.run(query, preference, top_k, on_event=None) -> PipelineTrace`:

1. `StyleRetriever.retrieve(preference, top_k)` — FAISS top-K over MiniLM-embedded style cards.
2. `KnowledgeLLM.draft(query)` — neutral factual answer, no style.
3. Loop over retrieved cards:
   - `StyleLLM.restyle(draft, card, preference, attempt)` — rewrites draft using the card (instruction + few-shot examples inline in prompt).
   - `JudgeLLM.evaluate(query, draft, styled, card)` — returns a `JudgeVerdict` with `action ∈ {accept, revise_style, content_drift, wrong_style}`. Content-preservation cosine is computed **locally** via sentence-transformers — independent of the judge's LLM call.
4. Action routing (line 70+):
   - `accept` → break, return best.
   - `revise_style` / `content_drift` → same card, `attempt_for_style++`, stronger hint + lower temperature.
   - `wrong_style` → advance `style_idx`, reset attempt.
5. Bounded by `MAX_REVISIONS=2`. A best-so-far `RevisionStep` (scored by `(content_faithful, style_score, content_cosine)`) is always emitted.

Every step is persisted by `judge/evaluate.py` to `results/traces/trace_NN.json` via `PipelineTrace.to_dict()` (dataclass in `judge/agents/schemas.py`).

### Streaming hook

`Orchestrator.run` accepts an optional `on_event: Callable[[dict], None]`. When provided, it emits events at each step boundary — `retrieval`, `draft`, `style_attempt_start`, `style_attempt`, `judge_verdict`, `final` — each a plain dict. The FastAPI `POST /api/generate/judge` endpoint uses this to fan out Server-Sent Events to the web playground.

### Env-driven config

`judge/config.py` holds defaults (`MAX_REVISIONS`, `CONTENT_PRESERVATION_MIN`, `TOP_K`, `OLLAMA_HOST`, `KNOWLEDGE_MODEL`, `STYLE_MODEL`, `JUDGE_MODEL`, etc.). These get overridden at runtime by the env: `api/bootstrap/registry.py:bootstrap()` reads from `os.environ` and patches the already-imported `judge.config` module in place **before** any `OllamaClient` / `Orchestrator` is constructed. This means you can change models or thresholds via `.env` without editing `judge/`.

The current default routes the Judge to a **different model family** (`rnj-1:latest`) than Knowledge/Style (`gemma4:latest`), to break self-preference bias (Zheng 2023).

### Registry — why so much machinery for two imports

`judge/` uses bare imports: `from config import ...`, `from retrieve import ...`, `from agents.orchestrator import ...`. Resolving these means putting `judge/` on `sys.path`, which pollutes the top-level module namespace (`sys.modules["config"]`, `sys.modules["retrieve"]`). If anything else in the process ever imports a module called `config` or `retrieve`, it'll silently collide. `api/bootstrap/registry.py` does a controlled import: inserts `judge/` on `sys.path`, imports each module, rebinds the object to a `krr_judge.*` alias in `sys.modules`, then strips the bare name. After bootstrap, `"config" not in sys.modules` is asserted — any future stray import will break loudly.

Historical note: the repo used to have a second pipeline (TinyLlama + LoRA, in `previous/`) that needed this isolation to coexist. That pipeline was removed; the isolation pattern is kept because it's cheap and defensive.

### Ollama client (`judge/agents/ollama_client.py`)

Contains Gemma-on-Ollama workarounds documented in the module docstring. Preserve them when modifying:

- `num_ctx=8192` — Style/Judge prompts exceed Ollama's 2048 default and the server silently truncates otherwise, collapsing generation to empty output.
- Temperature floored at `0.01` — Gemma builds return empty at exactly `0`.
- System message inlined into the user turn — Gemma's chat template has no system role; Ollama handling is inconsistent across versions.
- `think=False` — Gemma 3n runs "thinking" mode by default, which burns the `num_predict` budget on CoT that gets routed to `message.thinking` instead of `message.content`.
- Two-pass retry with a slight temperature bump if the first call returns empty.

If you swap in a non-Gemma model (e.g. `rnj-1`), most of these become unnecessary but harmless.

### Retrieval

`scripts/build_index.py` concatenates `instruction + tags + up to 2 example Q/A pairs` per card, encodes with `sentence-transformers/all-MiniLM-L6-v2` (normalized), and writes a FAISS `IndexFlatIP` to `data/style_index.faiss`. The same MiniLM model is reused by the `StyleRetriever` at query time **and** by `JudgeLLM` for the content-preservation cosine — one SentenceTransformer load per Orchestrator.

### Web app (`web/`)

Next.js 15 App Router + Tailwind v4 + hand-written shadcn/ui primitives. Three pages:

- `/` — Playground. `useGenerationStream` hook consumes the SSE stream from the API and accumulates a `PipelineTraceOut`-shaped object via `useReducer`. The same `<TraceViewer>` renders both the live stream and static historical traces.
- `/styles` — grid of the 10 cards with a detail drawer.
- `/traces` + `/traces/[id]` — browses `results/traces/*.json`.

SSE over POST: native `EventSource` is GET-only, so `lib/api/sse.ts` opens a POST via `fetch`, reads `res.body` as a ReadableStream, splits on `\n\n`, and yields typed events.

## Things that will bite you

- **FAISS index missing.** `StyleRetriever.__init__` raises `FileNotFoundError` if `data/style_index.faiss` is absent. `/api/health` reports this; the web HealthBanner prints the exact fix (`python scripts/build_index.py`).
- **Ollama not running / wrong model.** `OllamaClient.generate` will return empty strings. `/api/health` pings Ollama at startup and lists pulled models so mismatches are visible in the web UI.
- **Env overrides only apply at bootstrap.** If you change `.env` while uvicorn is running, restart the process — the registry patches config modules **once** at startup.
- **`judge/config.py` has a leftover `STYLE_MODE` flag** with values `{"prompt", "lora"}`. Only `"prompt"` is supported; the LoRA path was from the deleted `previous/` pipeline and `StyleLLM.__init__` raises `NotImplementedError` for any other value. Leave as `"prompt"`.
- **SSE behind a proxy.** Set `X-Accel-Buffering: no`, `Cache-Control: no-cache`, `Connection: keep-alive` on the stream response (already done in `routers/generate.py`). `sse-starlette` emits keepalive comments every 15 s.
- **Team project.** Any presentation-facing changes (README, `PPT.md`, the HTML deck, `/about` page) should credit the team, not a single author.
