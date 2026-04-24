---
title: "Zero-Shot Alignment via Retrieval"
subtitle: "Knowledge / Style / Judge control loop"
total_minutes: 6
slide_count: 6
audience: "ML research / applied NLP"
team:
  - { name: "Venkat Tummala",         asu_id: "1236842219" }
  - { name: "Anish Paul Singareddy",  asu_id: "1237522730" }
  - { name: "Manan Santoki",          asu_id: "1237462072" }
  - { name: "Tanmay Godse",           asu_id: "1234028005" }
  - { name: "Charith Reddy Bandi",    asu_id: "1236775152" }
---

# How to read this file

This file is **standalone**. A downstream deck-building agent should be able to produce a complete 6-slide presentation from this file alone — no access to the codebase, no access to the README. Everything the agent needs is below: project context, architecture, numerical results, slide-by-slide briefs with full speaker-note prose, and assets.

**Constraints for the deck-building agent:**
- **Exactly 6 slides** (including the title). Do not split or merge.
- Slides map 1:1 to the four things this talk must communicate: problem, KRR approach, reasoning, insight + contribution + results — plus title and demo.
- Use only the numbers quoted in this file. Do not fabricate. If a number isn't here, don't invent one; drop the bullet instead.
- On-slide bullets are tight (≤ 5, ≤ 8 words each). Speaker notes are full prose paragraphs (60–90 words), meant to be read aloud at ~140 wpm.
- Visual captions are descriptions, not commands — the deck-builder picks the render.
- Team tiles on slide 1 use the names + ASU IDs from the front-matter.

Total budget: 30 + 50 + 50 + 80 + 70 + 50 = **330 s ≈ 5:30**, which leaves ~30 s buffer in a 6-minute slot.

---

# Project context (for the agent — not for slides directly)

## What the project is
Zero-shot preference alignment via retrieval. The user types a natural-language preference (e.g. "be formal and academic", "genz style", "executive summary"); the system retrieves the best-matching pre-authored style card from a FAISS index and runs a three-LLM **Knowledge / Style / Judge** control loop to produce a style-aligned response. All LLM calls go through Ollama. There is no fine-tuning, no LoRA, no PyTorch training — style is represented as **data** (JSONL style cards), retrieval is embedding + FAISS, and the pipeline never mutates model weights.

## Why not fine-tune (problem framing)
Per-user fine-tuning doesn't scale:
- Every new user needs labelled data, VRAM, a training loop.
- Updates mutate the shared base model → catastrophic forgetting and tenant drift.
- Alignment is baked into opaque weights → no audit trail.

With retrieval:
- Styles are data. A new style is one JSONL line.
- The base is frozen. It never drifts.
- Every output ties to a `(card_id, content_cosine, judge_verdict)` triple, persisted.

## Architecture (ASCII)

```
preference ─► MiniLM ─► FAISS ─► top-K style cards
query      ─► Knowledge LLM ─► neutral draft
draft + card ─► Style LLM ─► styled rewrite
draft, styled, card ─► Judge LLM ─► { accept | revise_style | content_drift | wrong_style }
                  └─► local cosine(draft, styled)   (catches hallucination the judge misses)
```

The loop is capped at `MAX_REVISIONS`. The best-seen candidate is always emitted. Every step is persisted to `results/traces/trace_NN.json`.

## Role → model mapping

| Role | Default model | Purpose |
|---|---|---|
| Knowledge | `gemma4:latest` | Neutral factual draft (no style pressure) |
| Style | `gemma4:latest` + retrieved style card in prompt | Rewrites the draft in the target style |
| Judge | `rnj-1:latest` (different family from Knowledge/Style) | JSON verdict + local content cosine; routes the control loop |

All three call Ollama. The only other local compute is `sentence-transformers/all-MiniLM-L6-v2` for FAISS retrieval and the judge's content-preservation cosine.

## The Knowledge/Style/Judge loop (mechanics)

`Orchestrator.run(query, preference, top_k, on_event=None) -> PipelineTrace`:

1. **Retrieve.** `StyleRetriever.retrieve(preference, top_k)` — FAISS top-K over MiniLM-embedded style cards.
2. **Draft.** `KnowledgeLLM.draft(query)` — neutral factual answer, no style.
3. **Loop over retrieved cards:**
   - `StyleLLM.restyle(draft, card, preference, attempt)` — rewrites draft using the card (instruction + 2 exemplars inline in the prompt).
   - `JudgeLLM.evaluate(query, draft, styled, card)` — returns a `JudgeVerdict` with `action ∈ {accept, revise_style, content_drift, wrong_style}`. The content-preservation cosine is computed **locally** via sentence-transformers — independent of the judge's LLM call.
4. **Action routing:**
   - `accept` → break, return best candidate.
   - `revise_style` or `content_drift` → same card, `attempt_for_style++`, stronger hint + lower temperature.
   - `wrong_style` → advance `style_idx`, reset attempt counter.
5. **Cap:** `MAX_REVISIONS = 2`. Best-so-far `RevisionStep` (scored by `(content_faithful, style_score, content_cosine)`) is always emitted.

## Config defaults (overridable via `.env`)
- `MAX_REVISIONS = 2` — hard cost ceiling on the revision loop.
- `TOP_K = 5` — retrieval fan-out. (UI uses 3.)
- `JUDGE_STYLE_PASS_THRESHOLD = 4` — judge's 1–5 rubric; must score ≥ 4 to `accept`.
- `CONTENT_PRESERVATION_MIN = 0.70` — cosine(draft, styled) must clear this or the action becomes `content_drift`.
- `MAX_NEW_TOKENS = 256` (defaults; production raises to 768).
- `EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"`.

## The style bank (8 cards)
All in `style_bank/style_cards.jsonl`. Each card = `{ id, tags, instruction, 2 exemplars }`.

| id | flavour |
|---|---|
| `formal_academic`          | Latinate vocab, subordinate clauses, hedged claims |
| `business_executive`       | Bottom-line-first, 3–5 KPIs, business idiom |
| `technical_precise`        | Precise terminology, numbers, units, complexity classes |
| `storytelling_narrative`   | Scene + character + tension; concrete sensory detail |
| `eli5_playful`             | Only common words; toys / animals / food analogies |
| `hype_bro`                 | Hype-bro slang ("bro", "no cap", "W move", "fire") |
| `gen_z_online`             | Lowercase, chronically-online Gen Z slang ("bestie", "it's giving") |
| `keywords_only`            | Maximum density, noun-phrase driven, drop articles |

Example raw card:
```json
{
  "id": "formal_academic",
  "tags": ["formal", "academic", "scholarly"],
  "instruction": "Use formal academic register. Prefer Latinate vocabulary, subordinate clauses, and hedged claims ('it may be argued that…').",
  "examples": [
    { "prompt": "Explain gradient descent.",
      "answer": "Gradient descent is a first-order iterative optimisation procedure…" }
  ]
}
```

Add a new style: append one JSONL line, rerun `python scripts/build_index.py`. No retraining.

## Evaluation (last recorded run)

On a 20-prompt eval against the same Ollama model without retrieval:
- **Pairwise wins:** 3-LLM + retrieval **13 / 20** vs Ollama direct **7 / 20** (≈ **1.85×** lift).
- **Judge style score (1–5):** mean **4.9 / 5**.
- **Content cosine:** mean **0.80**; every item clears the **0.70** drift gate.
- **Mean revisions:** **0.05** — the loop rarely fired in this run (caveat below).
- **Biggest movers** (baseline pairwise win → 3-LLM pairwise win):
  - `casual_friendly`: 0.15 → 1.00
  - `debate_critical`: 0.15 → 1.00
  - `socratic_teaching`: 0.17 → 0.75
  (Note: these style ids come from an earlier bank; the current bank is the 8-card set above. Keep the wording "biggest movers" generic unless you have a fresh eval.)

### Honest caveats (cite these out loud)

1. **Self-preference bias in the recorded run.** That run had Knowledge, Style *and* Judge on the same model (`gemma4`), so the judge rubber-stamped at 4.9 / 5 and the revision loop barely fired. The production `.env` now routes Judge to `rnj-1:latest` — a different model family — following Zheng et al. 2023 to break self-preference. A fresh eval under cross-family judging is pending.
2. **Retrieval ceiling.** 5 of 20 items retrieve the wrong style (top-1 ≈ 75%). When retrieval misses, the pipeline is scored against a style it never tried to produce. First lever to fix: bigger bank, harder exemplars, or judge-in-the-loop rerank over top-K.

## Streaming + UI (for the demo slide)

The orchestrator's `on_event` callback emits events at each step boundary. The FastAPI endpoint `POST /api/generate/judge` fans these out as Server-Sent Events to the web UI. Event types in order: `retrieval` · `draft_delta` · `draft` · `style_attempt_start` · `style_delta` · `style_attempt` · `judge_verdict` · `final`.

Web app (Next.js 16 + Tailwind + shadcn):
- **Playground `/`** — three-column layout: (1) query + preference form, (2) retrieval hits + live Knowledge draft, (3) per-attempt style + judge verdicts + final output. Live SSE token streaming.
- **Styles `/styles`** — the 8-card bank, with a detail drawer showing instruction + exemplars.
- **History `/history`** — localStorage-backed replay of the user's past runs.
- **Traces `/traces`** — browses persisted `results/traces/*.json` eval runs.

## Deployment

Docker Compose: `ollama` + `api` + `web`. Runs behind Traefik on Dokploy:
- Inter-service traffic on a private `krr-internal` network (isolates service DNS from the shared `dokploy-network`).
- `web` also joins `dokploy-network` so Traefik can route the public domain → `web:3000`.
- `api` also joins `dokploy-network` so a second Traefik rule routes `krr.msantoki.com/api/*` directly to `api:8000`, bypassing Next.js response buffering on SSE streams.

## Key design decisions (for the reasoning slide)

- **Why retrieval over per-user fine-tuning?** Fine-tuning doesn't scale (labels, VRAM, iteration), mutates the shared base, and bakes alignment into weights you can't audit. Retrieval turns alignment into a discrete, inspectable decision: one card, one cosine, one verdict.
- **Why three LLMs, not one prompt?** A single LLM doing content + style + quality gating conflates them — it hallucinates facts to appear more stylistic. Decoupling draft from restyle gives Style a clean input. An independent Judge scores the pair without self-preference.
- **Why compute content cosine outside the judge?** The judge's LLM can miss subtle hallucinations. A sentence-embedding cosine between draft and styled is independent of the judge's weights — two signals instead of one.
- **Why cap revisions?** Adversarial input can loop forever. `MAX_REVISIONS` gives a hard ceiling; we always emit the best-seen candidate.

## Stack (for slide context)
- **Backend:** Python 3.11, FastAPI, Uvicorn, `sse-starlette`, pydantic-settings.
- **Retrieval:** FAISS `IndexFlatIP` over normalised MiniLM embeddings.
- **Models:** Ollama (local / containerised), `gemma4:latest` for Knowledge + Style, `rnj-1:latest` for Judge.
- **Frontend:** Next.js 16 (App Router, Turbopack), Tailwind v4, shadcn/ui primitives, Zustand, SSE reader over `fetch` + `ReadableStream`.
- **Deploy:** Docker Compose + Traefik via Dokploy.

## Reference
- *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*, Zheng et al., 2023 — the self-preference bias the cross-family Judge is designed around.
- Sentence-Transformers · https://www.sbert.net/ — the `all-MiniLM-L6-v2` embedder.
- FAISS · https://github.com/facebookresearch/faiss — the retrieval index.
- Ollama · https://ollama.com — the LLM runtime.

---

# Slide 1 — Title (≈30 s)

**Key message:** Zero-shot alignment via retrieval, by a 5-person ASU team.

**On-slide:**
- Zero-shot alignment *via* retrieval
- Eight style cards · one FAISS index · Ollama
- Team of five (ASU)

**Speaker notes (read aloud, ~70 words):** Zero-shot alignment via retrieval. From the user's view, they type a preference in plain English and get a style-matched answer immediately — no fine-tuning, no training, no wait. We make that work by stocking the shelf ahead of time: eight style cards authored as JSONL, one shared FAISS index, and Ollama for every LLM call. In six minutes: why per-user fine-tuning is the wrong frame, the three-LLM retrieval loop, why it works, and the results.

**Visual:** Presentation title at top · subtitle "Knowledge / Style / Judge control loop" · five team member tiles (one per person) showing `name` and `ASU ID` from the front-matter.

---

# Slide 2 — Problem (≈50 s)

**Key message:** Per-user fine-tuning doesn't scale; alignment should be retrieval, not training.

**On-slide:**
- N users → N trained models (doesn't scale)
- N users → one frozen base + shared bank (scales)
- Cost constant in users · new style = one JSONL line

**Speaker notes (~80 words):** Personalising a model per user via fine-tuning doesn't scale. Each new user needs labelled data, VRAM, a training loop — and worse, updates mutate the shared base, so every tenant risks overwriting what worked for the last. Worse still, the alignment is baked into opaque weights you can't audit. The reframe: style is a retrieval problem, not a training problem. Author the style once as a card, index the bank once, compose at inference. No gradients leave the lab, the base never drifts, and adding a new style is one JSONL line.

**Visual:** Two-panel diagram, left and right.
- Left panel ("fine-tune per user") — one base model with N trainer arrows pointing in, each labelled "user 1 data", "user 2 data"…, and a caption "costs grow with users · weights drift".
- Right panel ("retrieve per user") — one frozen base model + a shelf of style cards + a retriever arrow from a preference-bubble. Caption: "bank once · infer N times · cost constant".

---

# Slide 3 — KRR approach (≈50 s)

**Key message:** Styles are symbolic modules in a bank; alignment = retrieve + compose.

**On-slide:**
- Each style = `{ id, tags, instruction, 2 exemplars }`
- MiniLM → FAISS `IndexFlatIP` (cosine on unit vectors)
- Retrieval is the *only* personalisation signal
- Eight styles today · scales by one line

**Speaker notes (~80 words):** The KRR framing. Each style is a small symbolic knowledge module — an id, tags, a natural-language instruction, and two exemplars. The library of modules is the bank; the user's preference is a query over that bank. Every card is encoded with all-MiniLM-L6-v2 and stored in a FAISS IndexFlatIP — cosine similarity as inner product on unit-normalised embeddings. At query time we retrieve top-K and compose. Because style lives in data, not weights, the knowledge base is inspectable, editable, and extensible — the three properties you want from a symbolic representation, and none fine-tuning gives you.

**Visual:** Left side: a grid of 8 style-card tiles (one per id from the bank), each showing the id and a one-line flavour. Right side: an arrow-flow `preference → MiniLM embed → FAISS top-K → selected card`. Bottom-right: a small JSON excerpt of one card (use the `formal_academic` example above).

---

# Slide 4 — Reasoning: the Knowledge/Style/Judge loop (≈80 s)

**Key message:** Three role-specialised LLMs + four judge actions turn alignment into a bounded, auditable control loop.

**On-slide:**
- Knowledge drafts facts · Style rewrites · Judge evaluates
- 4 judge actions: `accept` · `revise_style` · `content_drift` · `wrong_style`
- Judge runs a *different* model family (breaks self-preference bias)
- Content cosine computed locally — independent of the judge's LLM
- `MAX_REVISIONS = 2` · always emit best-so-far

**Speaker notes (~120 words):** Why three LLMs and not one prompt. Knowledge drafts neutral facts — no style pressure. Style rewrites that draft using the retrieved card — no factual pressure. Judge evaluates the pair along two axes: is the style right on a 1-to-5 rubric, and is the content faithful — measured by a local sentence-transformers cosine, not the judge's own LLM call. The judge emits one of four actions. Accept exits. Revise_style re-tries the same card with a stronger hint and lower temperature. Content_drift does the same because the draft is still the source of truth. Wrong_style advances to the next retrieved card. Two design choices kill specific failure modes: running the judge on a different model family than Knowledge and Style prevents self-preference bias documented in Zheng et al. 2023, and computing the content cosine outside the judge's LLM catches hallucinations the judge missed. Revisions are capped at two; the best candidate is always emitted.

**Visual:** Horizontal KSJ flow diagram.
- Nodes left-to-right: `Preference` → `FAISS top-K` → `Knowledge LLM (draft)` → `Style LLM (rewrite)` → `Judge LLM (verdict)` → `Final`.
- Under Judge, four coloured return-arrows labelled with the four actions, looping back appropriately (`accept` → Final; `revise_style`, `content_drift` → Style LLM; `wrong_style` → back to retrieval, next card).
- Under the top edge: a small dashed side-arrow from `Style` through `cosine(draft, styled)` feeding into the Judge box — labelled "local, not LLM".
- Bottom caption strip: "`MAX_REVISIONS = 2` · best-so-far always emitted".

---

# Slide 5 — Insight + contribution + results (≈70 s)

**Key message:** Every output is an auditable triple — card, cosine, verdict — and it moved the numbers.

**On-slide:**
- **Insight:** retrieval makes alignment a discrete, auditable decision
- **Contribution:** every response = `(card_id, content_cosine, judge_verdict)` triple
- 3-LLM + retrieval **13 / 20** vs Ollama direct **7 / 20** (≈ **1.85×**)
- Content cosine mean **0.80** · every item clears the **0.70** drift gate
- Judge score mean **4.9 / 5** · mean revisions **0.05**

**Speaker notes (~110 words):** The main insight and our contribution. Retrieval turns alignment into an auditable discrete decision: every response traces back to a specific card, a specific content cosine, and a specific judge verdict. That triple is the contribution — a stakeholder can see exactly why an output looks the way it does, and exactly where to intervene when it's wrong. Contrast that with RLHF, where bias flows through opaque weight updates. On a 20-prompt eval against the same Ollama model without retrieval, the pipeline wins 13 of 20 — roughly a 1.85× lift. Content cosine averages 0.80, every item clears the 0.70 drift gate. Two honest caveats: that run used the same model family for all three roles, so the judge rated generously and the revision loop barely fired; production now routes the Judge to `rnj-1` to exercise the loop. And retrieval still misses 5 of 20 — that caps the ceiling and is the first thing to fix.

**Visual:** Left: grouped bar chart "3-LLM + retrieval vs Ollama direct", values 13 and 7 out of 20, y-axis "pairwise wins (n=20)". Right: three stat cards — "cosine 0.80" (with a small dashed line at 0.70 labelled "drift gate"), "judge 4.9 / 5", "revisions 0.05". Below the chart, a thin caption strip: "source: `results/evaluation_results_3llm.json` · pre-`rnj-1` Judge; cross-family re-run pending".

---

# Slide 6 — Demo + next (≈50 s)

**Key message:** Live SSE trace in the web UI; three concrete unlocks.

**On-slide:**
- Three-column Playground — query · retrieval + draft · attempts + verdicts
- Live SSE token streaming · per-attempt judge scores · `/history` replay
- Shipped: Docker Compose · deployed on Dokploy (Traefik)
- **Next:** (1) grow the bank beyond 8 styles, (2) judge-in-loop rerank on top-K to fix the 5/20 misses, (3) content preservation beyond cosine (NLI / fact-level)

**Speaker notes (~100 words):** The web UI streams every step of the loop over Server-Sent Events — retrieval hits, draft tokens, each style attempt's tokens, each judge verdict, and the final output. Same trace format we persist offline, so one renderer works for both live streams and the history view. The full stack ships as Docker Compose and runs behind Traefik on a Dokploy deployment; the public UI is same-origin, SSE bypasses Next.js directly to the API so streams don't buffer. Three queued unlocks, each a one-config-knob change thanks to the retrieval frame: grow the style bank — one JSONL line per style, no retraining; fix the five retrieval misses with a larger bank or a judge-in-the-loop rerank over top-K; and extend content preservation beyond cosine with NLI or fact-level checks.

**Visual:** Large screenshot placeholder of the three-column Playground mid-stream (columns: form · retrieval + draft · attempts + verdicts; a `Running…` button and a progress bar visible). To the right or bottom: a compact "Next" checklist with three items.

---

# Appendix — raw assets the deck-builder can draw from

## A. Sample trace structure (schema)
Every run persisted to `results/traces/trace_NN.json` has this shape:
```json
{
  "query": "...",
  "preference": "...",
  "retrieval": [{ "rank": 0, "styleId": "...", "score": 0.72, "weight": 1.0 }],
  "draft": "...",
  "revisions": [{
    "attempt": 0,
    "styleId": "...",
    "draft": "...",
    "styled": "...",
    "verdict": {
      "styleScore": 4,
      "contentFaithful": true,
      "contentCosine": 0.86,
      "action": "accept",
      "rationale": "..."
    }
  }],
  "finalStyleId": "...",
  "finalOutput": "...",
  "finalVerdict": { ... }
}
```

## B. SSE event sequence (for demo-slide visual if needed)
```
event: retrieval          data: { rank:0, styleId, score, weight } × K
event: draft_delta        data: { delta: "tok " }     (repeated)
event: draft              data: { draft: "<full draft>" }
event: style_attempt_start data: { attempt, styleId }
event: style_delta        data: { attempt, delta: "tok " } (repeated)
event: style_attempt      data: { attempt, styleId, styled: "<full>" }
event: judge_verdict      data: { attempt, styleId, verdict: { action, ... } }
...loop until accept / MAX_REVISIONS...
event: final              data: { finalStyleId, finalOutput, finalVerdict }
```

## C. Slide → section map (for the agent's sanity check)
| Slide | The "four things" this slide lands | Section of this file it draws from |
|---|---|---|
| 1 | — (title + team) | Front-matter `team` |
| 2 | **Problem** | "Why not fine-tune" |
| 3 | **KRR-based approach** | "The style bank" + "Architecture" |
| 4 | **Reasoning process behind the method** | "The Knowledge/Style/Judge loop" + "Key design decisions" |
| 5 | **Main insight, contribution, and results** | "Evaluation (last recorded run)" + "Honest caveats" |
| 6 | — (demo + roadmap) | "Streaming + UI" + "Deployment" |

## D. Visual-asset references (if the deck-builder wants to inline concrete snippets)
- `style_bank/style_cards.jsonl` — 8 styles; one JSON line each. Use any card from §"The style bank" as an on-slide excerpt.
- `results/traces/*.json` — per-request trace example, shape as in Appendix A. Good material for slide 5 "auditable triple".
- `results/evaluation_results_3llm.json` — source for slide 5 numbers (pre-`rnj-1` Judge run).
- `judge/agents/orchestrator.py:43–110` — the KSJ loop; use as a small code-snippet caption on slide 4 if the deck needs one.
- Web UI screenshot (three-column Playground mid-stream) — slide 6.
- HTML deck `Zero-Shot Alignment via Retrieval.html` — existing hand-coded deck; source for the two-panel problem diagram on slide 2.
