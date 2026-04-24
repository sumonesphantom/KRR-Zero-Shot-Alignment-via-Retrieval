# API

FastAPI wrapper over the `judge/` (Knowledge / Style / Judge) pipeline.

## Run

```bash
pip install -r requirements.txt
pip install -r api/requirements-api.txt
cp api/.env.example .env            # adjust OLLAMA_HOST, model names, etc.

# one-time — build the FAISS index from style_bank/style_cards.jsonl
python scripts/build_index.py

# dev
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000/docs` for OpenAPI.

## Env

See `api/.env.example`. The `OLLAMA_HOST` / `KNOWLEDGE_MODEL` / `STYLE_MODEL` /
`JUDGE_MODEL` values in `.env` override the defaults in `judge/config.py`
without editing the pipeline source. Overrides are applied at
`registry.bootstrap()` time, before any OllamaClient instantiation.

## Sanity scripts

```bash
python -m api.scripts.smoke_registry          # bootstrap + isolation checks
python -m api.scripts.smoke_orchestrator \    # end-to-end run with on_event
    "be formal" "Explain how a computer stores data."
```

## Key files

- `bootstrap/registry.py` — the only place that touches `sys.path` / `sys.modules`. Loads `judge/` under `krr_judge.*` aliases so the pipeline's bare `from config import …` imports don't leak into the app.
- `streaming/bus.py` — thread→async bridge. The orchestrator's `run()` is synchronous; we run it in a worker thread and marshall events back to the event loop.
- `routers/generate.py` — the SSE endpoint. Wraps `Orchestrator.run(on_event=…)` in `sse-starlette`.
- `schemas/*.py` — Pydantic schemas with camelCase aliases for the TS client.

## camelCase drift

Any new field on a backend schema must be added both to `api/schemas/*.py` AND to `web/lib/api/types.ts`. The TS types are hand-maintained (not OpenAPI-generated) for v1.
