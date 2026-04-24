# Zero-Shot Alignment via Retrieval

Align LLM outputs to user preferences by retrieving pre-authored style modules at inference time, instead of fine-tuning per user. Given a natural-language preference ("be formal and academic"), the system retrieves the best-matching style card from a FAISS index and runs a three-LLM **Knowledge / Style / Judge** control loop to produce a style-aligned response — all on top of Ollama, no LLM training required.

## Why not fine-tune?

Fine-tuning per user is expensive, slow, risks catastrophic forgetting on the base, and doesn't scale — every new tenant needs labelled data and a training loop. With retrieval:

- Styles are **data**, not weights. Add a new style with one line in `style_bank/style_cards.jsonl`.
- The base model is **frozen**. It never drifts.
- Alignment is **auditable**. Every output ties to a `(card_id, content_cosine, judge_verdict)` triple persisted to `results/traces/`.

## Architecture

```
preference ─► MiniLM ─► FAISS ─► top-K style cards
query      ─► Knowledge LLM ─► neutral draft
draft + card ─► Style LLM ─► styled rewrite
draft, styled, card ─► Judge LLM ─► {accept | revise_style | content_drift | wrong_style}
                  └─► local cosine(draft, styled)   (catches hallucination the judge misses)
```

Loop capped at `MAX_REVISIONS`. Best-seen candidate always emitted. Every step persisted.

| Role | Default model | Purpose |
|---|---|---|
| Knowledge | `gemma4:latest` | Neutral factual draft (no style) |
| Style | `gemma4:latest` + retrieved style card in prompt | Rewrites the draft in the target style |
| Judge | `rnj-1:latest` (different family from Knowledge/Style) | JSON verdict + local embedding cosine; routes the control loop |

All three roles call Ollama. The only local compute is the `sentence-transformers/all-MiniLM-L6-v2` embedder used for FAISS retrieval and the judge's content-preservation cosine. **No PyTorch, no adapter training.**

## Project layout

```
├── judge/                       # the 3-LLM pipeline
│   ├── run_pipeline.py          #   entry: --step {evaluate, demo}
│   ├── config.py                #   defaults (env overrides applied at runtime)
│   ├── retrieve.py              #   FAISS retriever + .embed() for content cosine
│   ├── eval_data.py             #   20-prompt eval set + heuristic scorer
│   ├── evaluate.py              #   full eval, writes results + per-request traces
│   └── agents/
│       ├── schemas.py           #   JudgeVerdict, RevisionStep, PipelineTrace
│       ├── knowledge.py         #   Knowledge LLM (neutral draft)
│       ├── style.py             #   Style LLM (rewrite using retrieved card)
│       ├── judge.py             #   Judge LLM (JSON verdict + cosine)
│       ├── ollama_client.py     #   Gemma-on-Ollama workarounds (num_ctx, think=False, retry)
│       └── orchestrator.py      #   the accept / revise_style / content_drift / wrong_style loop
│
├── api/                         # FastAPI wrapper over judge/
├── web/                         # Next.js playground + traces + styles browser
├── scripts/
│   └── build_index.py           # one-time: build FAISS index from style_bank
├── style_bank/
│   └── style_cards.jsonl        # 10 styles — id, tags, instruction, 2 examples each
├── data/                        # FAISS index + cached cards (built by scripts/build_index.py)
├── results/                     # evaluation_results_3llm.json + traces/trace_NN.json
├── docker-compose.yml           # ollama + api + web
└── Zero-Shot Alignment via Retrieval.html   # presentation deck (6 slides, 1920×1080)
```

## Setup

### Requirements

- Python 3.10+
- Ollama running locally (`ollama serve`) with at least two models pulled
- Node 20+ for the web app

### Install

```bash
# Python deps — tiny footprint, no torch / transformers / peft
pip install -r requirements.txt
pip install -r api/requirements-api.txt

# Web deps
pnpm -C web install

# Pull the models referenced in .env
ollama pull gemma4:latest
ollama pull rnj-1:latest

# One-time: build the FAISS index
python scripts/build_index.py
```

### Configure

Copy `api/.env.example` to `.env` (at repo root) and adjust if needed. Key env vars:

- `OLLAMA_HOST` — where your Ollama is listening (default `http://localhost:11434`)
- `KNOWLEDGE_MODEL`, `STYLE_MODEL`, `JUDGE_MODEL` — any models you've pulled via `ollama list`
- `MAX_REVISIONS`, `JUDGE_STYLE_PASS_THRESHOLD`, `CONTENT_PRESERVATION_MIN`, `TOP_K`, `MAX_NEW_TOKENS` — orchestrator tunables (optional; absent = use `judge/config.py` defaults)

## Usage

### Web app (recommended)

```bash
# three shells
ollama serve
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
pnpm -C web dev                                # http://localhost:3000
```

Or the whole stack in Docker:

```bash
docker compose up
docker compose exec ollama ollama pull gemma4:latest
docker compose exec ollama ollama pull rnj-1:latest
docker compose run --rm api python scripts/build_index.py
# open http://localhost:3000
```

The playground streams every step of the KSJ loop over SSE — retrieval, knowledge draft, each style attempt, each judge verdict, final — as they happen. `/styles` browses the bank. `/traces` browses past eval runs.

### CLI evaluation

```bash
python judge/run_pipeline.py --step evaluate   # 20-prompt eval, writes results/traces/
python judge/run_pipeline.py --step demo       # interactive demo
```

Outputs:
- `results/evaluation_results_3llm.json` — summary (win rate vs base, mean judge score, mean content cosine, mean revisions)
- `results/traces/trace_NN.json` — full per-request trace (retrieval, draft, every style attempt, every judge verdict)

## Style cards

Each style in `style_bank/style_cards.jsonl`:

```json
{
  "id": "formal_academic",
  "tags": ["formal", "academic", "detailed", "structured"],
  "instruction": "Answer in a formal academic tone. Use precise terminology…",
  "examples": [
    { "prompt": "Explain gradient descent.",
      "answer": "Gradient descent is a first-order iterative optimization…" }
  ]
}
```

The 10 bundled styles: `formal_academic`, `business_executive`, `technical_precise`, `storytelling_narrative`, `eli5_playful`, `hype_bro`, `gen_z_online`, `keywords_only`, `dad_joke_pun`, `shakespeare_iambic`.

Add a new style: append one JSONL line, rerun `python scripts/build_index.py`. That's it.

## Evaluation

Three metrics per item, 20 items total:

- **Pairwise win vs base** — the heuristic scorer compares the 3-LLM output to a direct-query baseline (same Ollama model, no retrieval). The 3-LLM wins in 13 of 20 items on the last run.
- **Judge style score** (1–5) — the Judge LLM rates style adherence; mean 4.9/5 on the last run.
- **Content cosine** — `cos(embed(draft), embed(styled))`, computed locally. Mean 0.80, and every item passes the 0.70 drift threshold.

### Honest caveats (from the last run)

1. **Self-preference bias.** The reported run had Knowledge, Style, *and* Judge on the same model (`gemma4`), so the judge rubber-stamped at 4.9/5 and the revision loop barely fired. The default `.env` now routes Judge to `rnj-1:latest` — a different model family — to break this bias. Re-run the eval to see the loop actually fire.
2. **Retrieval ceiling.** 5 of 20 items retrieve the wrong style (MiniLM top-1 = 75%). When retrieval misses, the heuristic scores against a style the pipeline never tried to produce. Fixing retrieval (larger bank, harder exemplars, or judge-in-the-loop rerank from top-K) is the next lever.

## Design decisions

**Why retrieval instead of per-user fine-tuning?** Fine-tuning per user doesn't scale (labels, VRAM, iteration time), mutates the shared base, and bakes alignment into weights where you can't audit it. Retrieval turns alignment into a discrete, inspectable decision: every output points to one style card, one content cosine, one judge verdict.

**Why three LLMs instead of one?** A single LLM doing content, style, and quality gating at once conflates them — it hallucinates facts to appear more stylistic. Decoupling draft from restyle gives the Style LLM a clean input to rewrite, and the independent Judge (on a different model family) scores the result without self-preference.

**Why compute content cosine outside the judge?** The judge's LLM call can miss subtle hallucinations. A sentence-embedding cosine between the draft and the styled output is independent of the judge's weights — two signals instead of one.

**Why cap revisions?** Pathological prompts can loop forever under adversarial input. `MAX_REVISIONS` gives a hard cost ceiling, and we always emit the best-seen candidate.

## Presentation

The 6-slide deck is at `Zero-Shot Alignment via Retrieval.html`. Open it in a browser; keyboard ←/→/Space navigate. ⌘/Ctrl-P → Save as PDF produces a clean 1920×1080 per-page PDF.

## References

- *LoRA: Low-Rank Adaptation of Large Language Models* (Hu et al., 2021)
- *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena* (Zheng et al., 2023) — the self-preference bias we design around
- Sentence-Transformers · https://www.sbert.net/
- FAISS · https://github.com/facebookresearch/faiss
- Ollama · https://ollama.com
