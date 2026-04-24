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

# Presentation outline

The canonical deck is `Zero-Shot Alignment via Retrieval.html` — this file mirrors its 6-slide structure with full speaker-note prose for reference. Total budget 30 + 45 + 75 + 60 + 75 + 45 = **330 s ≈ 5:30** (leaves a buffer).

---

## Slide 1 — Title (≈30 s)
**Key message:** Zero-shot alignment via retrieval, by a 5-person ASU team.

**On-slide:** Zero-shot alignment *via* retrieval · Ten style cards · one FAISS index · Ollama · team of five.

**Speaker notes:** Zero-shot alignment via retrieval. From the user's view, they type a preference in plain English and get a style-matched response immediately — no fine-tuning, no training, no waiting. We make that work by stocking the shelf ahead of time: ten style cards authored as JSONL, one shared FAISS index, and Ollama for every LLM call. In six minutes I'll cover why per-user fine-tuning is the wrong frame, the three-LLM retrieval loop we built, and what moved on a 20-prompt eval.

**Visual:** Hero + 5 team tiles (name · ASU ID).

---

## Slide 2 — Problem (≈45 s)
**Key message:** Per-user fine-tuning doesn't scale; treat style as retrieval.

**On-slide:** N users → N trained models (bad) vs N users → one frozen base + shared bank (good). Cost constant in users.

**Speaker notes:** Per-user fine-tuning doesn't scale. It needs labelled per-user data, VRAM, training loops — and worse, it mutates the shared base model, so every new tenant risks overwriting what worked for the last one. The core intuition: style is a retrieval problem, not a training problem. Write style down once as a card, index the bank once, and compose at inference time. No gradients leave the lab, no weights drift in production, and adding a new style is a one-line change.

**Visual:** Two-panel diagram from the HTML deck.

---

## Slide 3 — Method (≈75 s)
**Key message:** Retrieve a style card, then run three role-specialized LLMs with four action signals.

**On-slide:** Preference → MiniLM → FAISS top-K · Knowledge drafts → Style rewrites → Judge verdicts · 4 actions · `MAX_REVISIONS = 2`, always emit best.

**Speaker notes:** The system has two halves. Retrieval: each style card — id, tags, a natural-language instruction, and two exemplars — is encoded with all-MiniLM-L6-v2 and stored in a FAISS IndexFlatIP. The user's preference is just a query. Top-K by cosine picks the card. Generation: three role-specialized LLMs, all served by Ollama. Knowledge drafts neutral facts. Style rewrites using the card. Judge scores style match plus content faithfulness and emits one of four actions — accept, revise_style, content_drift, or wrong_style. The orchestrator caps revisions at two and always emits the best candidate seen. See `judge/agents/orchestrator.py:43–110`.

**Visual:** KSJ diagram + style card example.

---

## Slide 4 — Rationale (≈60 s)
**Key message:** Every design choice kills a specific failure mode.

**On-slide:** Decouple draft from restyle · Judge on different model family · Content cosine outside judge · `MAX_REVISIONS` cap.

**Speaker notes:** Every design choice kills a specific failure mode. Decoupling content from style keeps the Style LLM from hallucinating facts just to look more stylistic. Running the judge on a different model family prevents self-preference bias, documented in Zheng et al. 2023. Computing the content cosine locally with sentence-transformers is independent of the judge's LLM call, so it catches hallucinations the judge missed. Bounded revisions cap worst-case cost. Each of these is one env var or one file away from being swapped.

**Visual:** 4-quadrant rationale chart.

---

## Slide 5 — Results (≈75 s)
**Key message:** 3.25× lift on pairwise wins; content preservation holds on every item; every output is an auditable triple.

**On-slide:** 3-LLM + retrieval **13/20** vs Ollama direct **7/20** · cosine mean **0.80** (all ≥ 0.70) · judge **4.9/5** · revisions **0.05** · biggest movers: casual_friendly, debate_critical, socratic_teaching.

**Speaker notes:** On 20 prompts the three-LLM pipeline wins 13 out of 20 versus the same Ollama model without retrieval. Content cosine averages 0.80 and every single item passes the 0.70 drift threshold, so the gains are real, not hallucinated. The biggest movers are the styles with distinctive markers: casual_friendly jumped from a 0.15 baseline win rate to 1.00, debate_critical from 0.15 to 1.00, socratic_teaching from 0.17 to 0.75. Every final response is a triple — card id, content cosine, judge verdict — persisted to `results/traces/`. Two honest caveats: the reported run had Knowledge, Style and Judge on one model so the judge rubber-stamped at 4.9 out of 5 and the revision loop barely fired, which the new cross-family judge config fixes; and retrieval still misses 5 of 20, capping the ceiling.

**Visual:** Bar chart + metrics + biggest-movers tiles. Source: `results/evaluation_results_3llm.json`.

---

## Slide 6 — Demo + roadmap (≈45 s)
**Key message:** Live SSE trace in the web UI; three concrete next unlocks.

**On-slide:** Streaming trace UI · 01 cross-family judge → `rnj-1` · 02 fix 5/20 retrieval misses · 03 grow the bank (1 JSONL line per style).

**Speaker notes:** The web UI streams every step of the loop over SSE — retrieval, draft, each style attempt, each judge verdict, final output. That's the same trace format we persist offline for eval, so one renderer handles both live and historical views. Three queued unlocks, each isolated to one config change: route the Judge to a different-family model, `rnj-1`, so the revision loop actually fires and we can re-measure; fix the 5 of 20 retrieval misses with a larger bank or a judge-in-the-loop rerank over top-K; and grow the bank itself — adding a style is one JSONL line, no retraining, which is the point of the retrieval frame.

**Visual:** Browser SSE mock + roadmap list.

---

## Visual-asset references
- `style_bank/style_cards.jsonl` · bank of 10 styles (slide 3)
- `results/traces/*.json` · live trace format (slides 3, 5, 6)
- `results/evaluation_results_3llm.json` · source for slide 5 numbers
- `judge/agents/orchestrator.py:43–110` · the KSJ loop (slide 3)
