---
title: "Zero-Shot Alignment via Retrieval"
subtitle: "Knowledge / Style / Judge control loop"
course: "ASU · KRR · Spring 2026"
total_minutes: 6
slide_count: 6
aspect_ratio: "16:9"
canvas_px: "1920×1080"
audience: "ML research / applied NLP, graded class presentation"
team:
  - { name: "Venkat Tummala",         asu_id: "1236842219" }
  - { name: "Anish Paul Singareddy",  asu_id: "1237522730" }
  - { name: "Manan Santoki",          asu_id: "1237462072" }
  - { name: "Tanmay Godse",           asu_id: "1234028005" }
  - { name: "Charith Reddy Bandi",    asu_id: "1236775152" }
---

# Deck build spec

This is a **build spec**, not an outline. A deck-builder (human or agent) should be able to produce the final slide file directly from this document — every color, font size, and word of body copy is specified below. If it isn't here, don't invent it; drop the element.

## Agent contract

1. **Produce exactly 6 slides at 1920×1080.** Not 5, not 7. Every slide number below is canonical.
2. **Use only the copy in "On-slide content" — verbatim.** Speaker notes are separate; never print them on the slide.
3. **Respect the visual system in §1 globally.** Do not introduce new colors, fonts, or decorative shapes.
4. **Use only numbers that appear in §2 "Project facts".** If you can't find a number here, omit the bullet rather than inventing one.
5. **Render all diagrams and charts with the color tokens in §1.4** — never default to the presentation tool's accent palette.
6. **Deliver as**: a `.pptx` file, a Google-Slides-importable `.pptx`, OR a PDF. Whichever, it must be pixel-faithful to the layout specs in §3.

Total speaker-note budget: 30 + 50 + 50 + 80 + 70 + 50 = **330 s ≈ 5:30**, leaving ~30 s buffer in a 6-minute graded slot. Speaker notes are written to be read aloud at ~140 wpm.

---

# §1 Visual system

## 1.1 Canvas
- Aspect ratio **16:9**, canvas **1920×1080 px**.
- Outer margin **96 px** on all sides (= safe area 1728×888).
- Underlying 12-column grid, **48 px gutter**, column width **(1728 − 11·48)/12 = 100 px**.
- Baseline grid: **8 px**. Every vertical offset rounds to a multiple of 8.

## 1.2 Color tokens (hex; use exactly these)

| token | hex | usage |
|---|---|---|
| `--bg`        | `#0F0F10` | Slide background. Flat fill, no gradient. |
| `--surface`   | `#17171A` | Card / panel fill on top of `--bg`. |
| `--border`    | `#262628` | 1 px borders on cards, dividers. |
| `--text`      | `#ECECEC` | Body text. |
| `--muted`     | `#8A8A90` | Captions, labels, secondary text. |
| `--primary`   | `#F5822E` | Titles, headline numbers, accent fills, chart "our" bars. |
| `--primary-2` | `#FFC14D` | Secondary accent — use *sparingly*, only on Slide 5 for the insight pull-quote. |
| `--good`      | `#3FB950` | "accept" / positive verdict badges. |
| `--warn`      | `#D29922` | "revise_style" / "content_drift" badges. |
| `--bad`       | `#F85149` | "wrong_style" badge. |
| `--ref-bar`   | `#484850` | Chart "baseline" bar fill (neutral grey so `--primary` pops). |

**Dark-on-dark rule**: do not layer `--surface` cards on anything but `--bg`. Never white backgrounds anywhere.

## 1.3 Typography

- **Family**: Inter or Geist Sans (whichever the tool supports natively). Monospace: JetBrains Mono or Geist Mono — used for style ids and file paths.
- **Scale**:
  | role | size | weight | line-height |
  |---|---|---|---|
  | Slide title             | 64 px | 700 | 1.1 |
  | Slide sub-title         | 28 px | 500 | 1.3 |
  | Headline on content slide | 44 px | 700 | 1.15 |
  | Body copy               | 26 px | 400 | 1.45 |
  | Bullet                  | 24 px | 500 | 1.45 |
  | Caption                 | 18 px | 400 | 1.35 |
  | Micro (footer)          | 14 px | 500 | 1.2 |
  | Display number (stats)  | 112 px | 700 | 1.0 |
  | Code / mono             | 20 px | 500 | 1.4 |

- **Color rules**: titles use `--primary`. Body uses `--text`. Captions and labels use `--muted`. Never color body text `--primary`.

## 1.4 Chrome (repeats on every content slide, not on title)

- **Top-left**: slide number like `02 / 06` in 14 px Micro, color `--muted`.
- **Top-right**: project title lockup `Zero-Shot Alignment via Retrieval` in 14 px Micro, `--muted`.
- **Bottom-left**: team names comma-separated in 14 px Micro, `--muted`. E.g. `Tummala · Singareddy · Santoki · Godse · Bandi`.
- **Bottom-right**: `ASU · KRR · Spring 2026` in 14 px Micro, `--muted`.
- All four chrome items sit **32 px inside** the outer margin.
- Title slide (Slide 1) has **no chrome** — unobstructed hero.

## 1.5 Iconography
- Use outline icons only, 2 px stroke, color `--muted` unless indicated.
- Source: Lucide (same set the web UI uses).

---

# §2 Project facts (the only source the agent may quote from)

## 2.1 Problem statement
Personalising an LLM per user via fine-tuning doesn't scale. Each new user needs labelled data, GPU time, and a training loop. Updates mutate the shared base model, risking catastrophic forgetting and tenant drift. And the alignment lives in opaque weights — no audit trail.

**The reframe**: author each "style" once as a small symbolic module, index the bank once, and compose at inference. No gradients leave the lab, no weights drift in production, and adding a new style is one JSONL line.

## 2.2 Architecture (one-glance)

```
preference ─► MiniLM ─► FAISS ─► top-K style cards
query      ─► Knowledge LLM ─► neutral draft
draft + card ─► Style LLM ─► styled rewrite
draft, styled, card ─► Judge LLM ─► { accept | revise_style | content_drift | wrong_style }
                  └─► local cosine(draft, styled)   (catches hallucination the Judge misses)
```

## 2.3 The style bank — 10 cards today

All live in `style_bank/style_cards.jsonl`. Each card = `{ id, tags, instruction, 2 exemplars }`.

| id | one-line flavour |
|---|---|
| `formal_academic`        | Latinate vocab · subordinate clauses · hedged claims |
| `business_executive`     | Bottom-line-first · 3–5 KPIs · business idiom |
| `technical_precise`      | Precise terminology · numbers · complexity classes |
| `storytelling_narrative` | Scene + character + tension · concrete sensory detail |
| `eli5_playful`           | Only common words · toys / animals / food analogies |
| `hype_bro`               | Hype-bro slang — "bro" · "no cap" · "W move" · "fire" |
| `gen_z_online`           | Lowercase · chronically-online slang — "bestie" · "it's giving" |
| `keywords_only`          | Maximum density · noun-phrase driven · drop articles |
| `dad_joke_pun`           | Correct explanation peppered with terrible puns · "I'll see myself out" |
| `shakespeare_iambic`     | Early Modern English · "thou" / "doth" / "verily" · soliloquy register |

## 2.4 Role → model

| Role | Default model | Purpose |
|---|---|---|
| Knowledge | `gemma4:latest` | Neutral factual draft — no style pressure |
| Style     | `gemma4:latest` + retrieved card in prompt | Rewrites draft in the target style |
| Judge     | `rnj-1:latest` (**different family** from Knowledge/Style) | JSON verdict + local content cosine; routes the control loop |

Only Ollama for inference. Only local compute: `sentence-transformers/all-MiniLM-L6-v2` for FAISS retrieval and the Judge's content cosine.

## 2.5 The control loop (algorithm)

`Orchestrator.run(query, preference, top_k) -> PipelineTrace`:

1. **Retrieve.** FAISS top-K over MiniLM-embedded style cards.
2. **Draft.** Knowledge LLM drafts from the query alone.
3. **Loop over cards, attempts:**
   - Style LLM rewrites draft using the card (instruction + 2 exemplars inline).
   - Judge LLM returns `{ style_score (1–5), content_faithful (bool), action }`. Content cosine is computed **locally** — independent of Judge's LLM call.
4. **Action routing:**
   - `accept` → break, emit best.
   - `revise_style` / `content_drift` → same card, `attempt_for_style++`, stronger hint + lower temperature.
   - `wrong_style` → advance to next retrieved card, reset attempt.
5. **Cap:** `MAX_REVISIONS = 2`. Best-so-far `RevisionStep` is always emitted.

## 2.6 Config defaults (all overridable via `.env`)
- `MAX_REVISIONS = 2`
- `JUDGE_STYLE_PASS_THRESHOLD = 5` — only an unambiguous 5/5 accepts on attempt 0
- `CONTENT_PRESERVATION_MIN = 0.70` — cosine(draft, styled) must clear this
- `TOP_K = 5` (UI default 3)
- `MAX_NEW_TOKENS = 768` (prod)

## 2.7 Evaluation (last recorded run)

- **Pairwise wins:** 3-LLM + retrieval **13 / 20** vs same Ollama model direct **7 / 20** ≈ **1.85×**.
- **Content cosine:** mean **0.80**, every item ≥ 0.70 gate.
- **Judge style score (1–5):** mean **4.9 / 5** (on the old run; see caveats).
- **Mean revisions:** **0.05**.
- **Biggest movers** (baseline pairwise win rate → 3-LLM win rate):
  `casual_friendly` 0.15 → 1.00 · `debate_critical` 0.15 → 1.00 · `socratic_teaching` 0.17 → 0.75
  (These are from an earlier bank; wording of the slide is kept generic unless re-measured on the current 8-card set.)

## 2.8 Honest caveats (cite on Slide 5)

1. **Self-preference bias** — the recorded run had Knowledge, Style *and* Judge on the same model, so the judge rubber-stamped at 4.9/5 and the revision loop barely fired. Production now routes Judge to `rnj-1` — a different model family (Zheng 2023) — and tightens the accept threshold to 5/5.
2. **Retrieval ceiling** — 5 of 20 items retrieve the wrong style (top-1 ≈ 75%). Judged against a style the pipeline never tried; the first lever to fix.

## 2.9 Web UI (for Slide 6 screenshot)
- Three-column Playground at `/`: (1) preference + query form, (2) retrieval hits + live Knowledge draft, (3) per-attempt Style + Judge verdicts + final.
- Server-Sent Events stream retrieval, draft tokens, style tokens, verdicts, final.
- `/styles` — 8-card bank browser · `/history` — localStorage replay · `/traces` — persisted eval runs.
- Deployed: Docker Compose · Traefik on Dokploy · `krr.msantoki.com`.

## 2.10 Reference
- *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*, **Zheng et al., 2023** — the self-preference bias we designed around.
- Sentence-Transformers · FAISS · Ollama.

---

# §3 Slide-by-slide build spec

Every slide entry has five parts:
- **Layout** — concrete geometry in the 12-col / 1920×1080 grid.
- **On-slide content** — verbatim text the agent puts on the slide. No paraphrasing.
- **Visuals** — chart / diagram / image specs with exact colors and data.
- **Speaker notes** — read-aloud prose (timed).
- **Timing** — target seconds.

---

## Slide 1 — Title **(30 s)**

**Layout.** No chrome. Content stack centered vertically, left-aligned within a 12-col full-bleed block (outer margin preserved). No background imagery.

**On-slide content** (top to bottom, all `--text` unless specified):

- Overline (16 px Micro, `--muted`, uppercase, letter-spacing 0.08em):
  `ASU · KRR · SPRING 2026`
- Title (112 px, weight 700, color `--primary`, lh 1.05):
  `Zero-Shot Alignment`
  `via Retrieval`
- Subtitle (28 px, 500, `--text`):
  `Knowledge · Style · Judge — a bounded control loop`
- 24 px vertical spacer.
- **Team row** — five tiles in a single horizontal flex, gap 24 px, no borders. Each tile:
  - Line 1 (20 px, 600, `--text`): member name
  - Line 2 (14 px, 500, `--muted`, mono): ASU ID
  - (Order exactly as in front-matter: Tummala · Singareddy · Santoki · Godse · Bandi.)
- Footer micro, bottom-left at 32 px inside safe area (18 px, `--muted`):
  `github.com/Manan-Santoki/zero-shot-alignment-retrieval`
- Footer micro, bottom-right symmetric (18 px, `--muted`):
  `krr.msantoki.com`

**Visuals.** None. Negative space is the design.

**Speaker notes** (~70 words, ~30 s): Zero-shot alignment via retrieval. From the user's view, they type a preference in plain English and get a style-matched answer immediately — no fine-tuning, no training, no wait. We make that work by stocking the shelf ahead of time: ten style cards authored as JSONL, one shared FAISS index, and Ollama for every LLM call. In six minutes: why per-user fine-tuning is the wrong frame, our three-LLM retrieval loop, why it works, and what moved on the eval.

---

## Slide 2 — Problem **(50 s)**

**Layout.** Two equal columns (col 1–6 / col 7–12). Left = text block; right = diagram. Headline spans both columns, top.

**On-slide content**:

- Chrome: `02 / 06` · `Zero-Shot Alignment via Retrieval` · team row · `ASU · KRR · Spring 2026`.
- Headline (44 px, 700, `--primary`), col 1–12, top aligned:
  `Per-user fine-tuning doesn't scale`
- Sub-headline (26 px, 400, `--muted`), col 1–12, 16 px below:
  `Treat style as retrieval, not training.`

**Left column (col 1–6), starts 80 px below sub-headline:**

- Bullets, 24 px / 500 / `--text`, 32 px line gap. Render each bullet with a 6 px square `--primary` glyph at the start instead of a disc:
  - `N users → N trained models` — growing VRAM, labels, iteration.
  - `Updates mutate the shared base` — catastrophic forgetting, tenant drift.
  - `Alignment lives in weights` — no audit trail.
- 48 px vertical spacer.
- **Boxed statement** — `--surface` fill, 1 px `--border`, 24 px padding, 12 px radius:
  > 24 px, 500, `--text`: "Author each style once. Retrieve and compose at inference."
  > 18 px, `--muted`, 8 px below: `new style = one JSONL line · base stays frozen`

**Right column (col 7–12). Diagram, top aligned with the left bullets.**

Two stacked panels, each `--surface` filled, 1 px `--border`, 16 px radius, 24 px padding:

- Panel A header (20 px, 600, `--muted`): `Fine-tune per user`
  - Body: central `Base model` pill (`--surface`, 1 px `--bad` border, 18 px mono id). Four arrows (`--bad`, 2 px stroke) labelled `user 1`, `user 2`, `user 3`, `user N` pointing INTO the pill. Small `×` marks at each arrow tip.
  - Caption (18 px, `--muted`, below): `cost grows with users · weights drift`
- 16 px gap between panels.
- Panel B header (20 px, 600, `--muted`): `Retrieve per user`
  - Body: `Base model` pill (same style but 1 px `--good` border). To its left, a 2×4 grid of small `--surface` tiles representing style cards (`style card` label in 14 px). An arrow labelled `preference →` goes from a speech-bubble icon through the card grid (one card highlighted `--primary`) into the Base pill.
  - Caption (18 px, `--muted`): `bank once · infer N times · cost constant`

**Speaker notes** (~80 words, ~50 s): Personalising a model per user via fine-tuning doesn't scale. Each new user needs labelled data, VRAM, a training loop — and worse, updates mutate the shared base, so every tenant risks overwriting what worked for the last. Worse still, the alignment is baked into opaque weights you can't audit. The reframe: style is a retrieval problem, not a training problem. Author the style once as a card, index the bank once, compose at inference. No gradients leave the lab, the base never drifts, and adding a new style is one JSONL line.

---

## Slide 3 — KRR approach **(50 s)**

**Layout.** Two columns. Headline across top. Left (col 1–6): style-card grid. Right (col 7–12): retrieval flow + inline JSON excerpt.

**On-slide content**:

- Chrome as defined.
- Headline: `Style as a symbolic, retrievable module`
- Sub-headline: `Ten cards today. Scales by one JSONL line.`

**Left column (col 1–6)** — 2×5 grid of style-card tiles, gap 14 px. Each tile: `--surface` fill, 1 px `--border`, 12 px radius, 16 px padding. Tile anatomy:
- Line 1 (18 px, 600, `--primary`, mono): the id verbatim — `formal_academic` · `business_executive` · `technical_precise` · `storytelling_narrative` · `eli5_playful` · `hype_bro` · `gen_z_online` · `keywords_only` · `dad_joke_pun` · `shakespeare_iambic`
- Line 2 (14 px, 500, `--text`, lh 1.3, max 2 lines): the one-line flavour from §2.3 of this spec. Truncate with ellipsis if > 2 lines.

**Right column (col 7–12)** — stacked:

1. **Flow strip** at top, 200 px tall. Four horizontal nodes connected by 2 px `--muted` arrows with 8 px arrow-heads in `--primary`:
   - Node A: speech-bubble icon + label `preference` (20 px, 500, `--text`)
   - Node B: label `MiniLM embed` (20 px, 500, `--text`)
   - Node C: cylinder icon + label `FAISS top-K` (20 px, 500, `--text`)
   - Node D: card icon + label `selected card` in `--primary`, 20 px, 600
   Arrows 1 px `--muted` line, arrowhead `--primary`. Nodes render as `--surface` pills with 1 px `--border`, 12 px radius.

2. **JSON excerpt panel** below, `--surface` fill, 1 px `--border`, 16 px padding, 12 px radius. Mono 20 px, `--text`; keys in `--primary`; strings in `--text`. Syntax-colour the quotes in `--muted`:
   ```
   {
     "id": "formal_academic",
     "tags": ["formal", "academic", "scholarly"],
     "instruction": "Use formal academic register. Prefer
       Latinate vocabulary, subordinate clauses, and hedged
       claims ('it may be argued that…').",
     "examples": [
       { "prompt": "Explain gradient descent.",
         "answer": "Gradient descent is a first-order iterative
           optimisation procedure…" }
     ]
   }
   ```
   Caption below (18 px, `--muted`): `encoded with all-MiniLM-L6-v2 into a FAISS IndexFlatIP (cosine via inner product on unit vectors).`

**Speaker notes** (~80 words, ~50 s): The KRR framing. Each style is a small symbolic knowledge module — an id, tags, a natural-language instruction, and two exemplars. The library of modules is the bank; the user's preference is a query over that bank. Every card is encoded with all-MiniLM-L6-v2 and stored in a FAISS IndexFlatIP — cosine as inner product on unit-normalised embeddings. At query time we retrieve top-K and compose. Because style lives in data, not weights, the knowledge base is inspectable, editable, and extensible — properties fine-tuning cannot give you.

---

## Slide 4 — Reasoning: the KSJ loop **(80 s)**

**Layout.** Title across top. Below: left bullet column (col 1–4), centre loop diagram (col 5–12). One chrome row at bottom.

**On-slide content**:

- Chrome as defined.
- Headline: `Knowledge · Style · Judge — a bounded control loop`
- Sub-headline: `Three role-specialised LLMs · four judge actions · two revisions max.`

**Left column (col 1–4)** — bullet stack, 24 px Bullet / 500 / `--text`, with 6 px `--primary` square glyph:

- **Knowledge** drafts facts — no style pressure.
- **Style** rewrites — no factual pressure.
- **Judge** scores on 1–5 rubric · threshold **5/5** to accept.
- Judge runs a **different model family** (breaks self-preference, Zheng 2023).
- Content cosine computed **locally** — independent of Judge's LLM.
- `MAX_REVISIONS = 2` · best-so-far always emitted.

(48 px below the bullets, small caption):
Micro mono (14 px, `--muted`): `judge/agents/orchestrator.py : 43–110`

**Right diagram (col 5–12)** — horizontal KSJ flow, vertically centred.

Nodes are 160×80 `--surface` pills, 1 px `--border`, 16 px radius; 20 px, 600, `--text` label. Between each node, a 64 px horizontal arrow, 2 px `--muted` line, arrowhead `--primary`.

Ordered left to right:
1. `Preference` (pill)
2. `FAISS top-K` (pill with `--primary` left-edge tick)
3. `Knowledge` (pill) — small caption under: `neutral draft`
4. `Style` (pill) — caption: `rewrite · card in prompt`
5. `Judge` (pill) — caption: `style 1–5 · content cosine`
6. `Final` (pill, `--primary` fill, `--bg` text)

Below the Judge pill, a fan of four labelled return arrows, each 1.5 px:
- `accept` → straight right to `Final` · stroke `--good`, label 18 px `--good` bold
- `revise_style` → curves back up to `Style` · stroke `--warn`, label 18 px `--warn`
- `content_drift` → curves back up to `Style` (slightly different curve) · stroke `--warn`, label 18 px `--warn`
- `wrong_style` → long curve back to `FAISS top-K` (indicating "advance to next card") · stroke `--bad`, label 18 px `--bad`

Above the Style→Judge arrow, a small dashed side-arrow from Style through a tiny `cosine(draft, styled)` pill back into Judge. Pill: `--surface`, 1 px `--muted` dashed border, 14 px mono, `--muted` text. Label next to it (14 px, `--muted` italic): `local · not LLM`

Bottom of diagram, faint caption (14 px, `--muted`, centred):
`best-so-far RevisionStep always emitted · trace persisted to results/traces/trace_NN.json`

**Speaker notes** (~120 words, ~80 s): Why three LLMs and not one prompt. Knowledge drafts neutral facts — no style pressure. Style rewrites that draft using the retrieved card — no factual pressure. Judge evaluates the pair along two axes: is the style right on a 1-to-5 rubric, and is the content faithful — measured by a local sentence-transformers cosine, not the judge's own LLM call. The judge emits one of four actions. Accept exits. Revise_style re-tries the same card with a stronger hint and lower temperature. Content_drift does the same because the draft is still the source of truth. Wrong_style advances to the next retrieved card. Two design choices kill specific failure modes: running the judge on a different model family than Knowledge and Style prevents self-preference bias documented in Zheng et al. 2023, and computing the content cosine outside the judge's LLM catches hallucinations the judge missed. Revisions are capped at two; the best candidate is always emitted.

---

## Slide 5 — Insight + contribution + results **(70 s)**

**Layout.** Top half: insight quote (full width). Bottom half: chart (left, col 1–7) + three stat cards (right, col 8–12).

**On-slide content**:

- Chrome as defined.
- Headline: `Alignment as an auditable triple`
- Sub-headline: `(card_id, content_cosine, judge_verdict) — for every single output.`

**Top half — Insight panel** (full width, col 1–12, height ≈ 340 px, 64 px below sub-headline). `--surface` fill, **left border 4 px `--primary-2`** (the pull-quote accent), 24 px radius, 48 px padding. Inside:
- 36 px, 500, `--text`, lh 1.3:
  `Retrieval turns alignment into a discrete, auditable decision. A stakeholder can see exactly why an output looks the way it does — and exactly where to intervene when it's wrong.`
- 16 px below, 18 px, `--muted`:
  `Contrast with RLHF, where bias flows through opaque weight updates.`

**Bottom-left (col 1–7) — Chart** at the full remaining height.
- Chart type: vertical grouped bar, 2 groups (`3-LLM + retrieval`, `Ollama direct`).
- Values: `13` and `7` (out of 20).
- Bar widths: identical. Bar colors: `--primary` for `3-LLM + retrieval`, `--ref-bar` for `Ollama direct`.
- Y-axis: 0–20, gridlines at 5/10/15/20 in 1 px `--border`. Tick labels 14 px `--muted`.
- Y-axis title: `pairwise wins (n = 20)` — 14 px `--muted`.
- Data labels on top of each bar: `13` and `7`, 28 px, 700, matching bar color (primary for 13, `--text` for 7).
- Above chart: mini caption (18 px, `--muted`): `≈ 1.85× lift vs same Ollama model, no retrieval`
- Below chart: source (14 px, `--muted`): `source: results/evaluation_results_3llm.json · pre-cross-family Judge`

**Bottom-right (col 8–12) — Three stacked stat cards**, 16 px gap. Each card: `--surface` fill, 1 px `--border`, 12 px radius, 24 px padding. Card anatomy:
- Card 1:
  - 20 px, 500, `--muted`: `content cosine`
  - 112 px, 700, `--primary`: `0.80`
  - 18 px, `--muted`: `every item clears the 0.70 drift gate`
- Card 2:
  - 20 px, 500, `--muted`: `judge style score`
  - 112 px, 700, `--primary`: `4.9 / 5`
  - 18 px, `--muted`: `pre-cross-family (Judge swap tightens this)`
- Card 3:
  - 20 px, 500, `--muted`: `mean revisions`
  - 112 px, 700, `--primary`: `0.05`
  - 18 px, `--muted`: `loop rarely fired — fixed by cross-family Judge + 5/5 bar`

**Speaker notes** (~110 words, ~70 s): The main insight and our contribution. Retrieval turns alignment into an auditable discrete decision. Every response traces back to a specific card, a specific content cosine, and a specific judge verdict. That triple is the contribution — a stakeholder can see exactly why an output looks the way it does, and exactly where to intervene when it's wrong. Contrast with RLHF, where bias flows through opaque weight updates. On twenty prompts against the same Ollama model without retrieval, we win thirteen — roughly 1.85-times. Content cosine averages 0.80, every item clears the 0.70 drift gate. Two honest caveats on this run: the judge rated generously because all three roles used the same model family, so the revision loop barely fired. Production now routes Judge to a different-family model and tightens the accept threshold to 5 out of 5. And retrieval still misses 5 of 20 — that caps the ceiling and is the first thing to fix.

---

## Slide 6 — Demo + what's next **(50 s)**

**Layout.** Top half: large screenshot (full width, col 1–12, height ≈ 460 px). Bottom half: headline + three unlock cards (col 1–12, evenly split).

**On-slide content**:

- Chrome as defined.
- Headline (above screenshot): `Live SSE trace · Dokploy-deployed · what's next`
- Sub-headline: `Every step streams to the browser. Three concrete unlocks ahead.`

**Upper half — Screenshot.** Place the hero screenshot of the three-column Playground mid-stream (source: `krr.msantoki.com` running a fresh query). Frame it in a `--surface` panel, 1 px `--border`, 12 px radius, 8 px padding around the image. Below the frame, 16 px caption (14 px, `--muted`):
`Playground · three-column: form · retrieval + draft · attempts + verdicts. SSE streams retrieval, draft tokens, style tokens, judge verdicts, final.`

**Lower half — Three unlock cards** in a 3-col horizontal flex (col 1–4, 5–8, 9–12). Each card: `--surface` fill, 1 px `--border`, 16 px radius, 28 px padding, min-height 220 px.

- Card 1 — header line (18 px, 500, `--muted`): `01 · grow the bank`
  - Body (24 px, 500, `--text`): `Add more styles — one JSONL line each, zero retraining.`
  - Caption (16 px, `--muted`): `new user-type = new card · ingredient, not recipe`
- Card 2 — header: `02 · judge-in-loop rerank`
  - Body: `Fix the 5/20 retrieval misses by reranking top-K with the Judge.`
  - Caption: `recover the ceiling our top-1 retrieval leaves on the table`
- Card 3 — header: `03 · beyond cosine`
  - Body: `Add NLI / fact-level content checks alongside the embedding cosine.`
  - Caption: `catch hallucinations that look similar but claim new facts`

**Footer strip** (below the three cards, 32 px above bottom chrome), 18 px, `--muted`, one line:
`Shipped: Docker Compose · Traefik on Dokploy · krr.msantoki.com · stack: FastAPI · SSE · Next.js 16 · FAISS · Ollama`

**Speaker notes** (~100 words, ~50 s): The web UI streams every step of the loop over Server-Sent Events — retrieval hits, draft tokens, each style attempt's tokens, each judge verdict, and the final output. Same trace format we persist offline, so one renderer works for both live streams and the history view. The full stack ships as Docker Compose and runs behind Traefik on a Dokploy deployment; the public UI is same-origin, SSE bypasses Next.js directly to the API so streams don't buffer. Three queued unlocks, each a one-knob change thanks to the retrieval frame: grow the style bank — one JSONL line per style, no retraining; fix the five retrieval misses with a judge-in-the-loop rerank over top-K; and extend content preservation beyond cosine with NLI or fact-level checks.

---

# §4 Asset checklist

The deck-builder must pull / capture the following before producing the final file:

| # | asset | where to get it | used on |
|---|---|---|---|
| A1 | Playground screenshot — mid-stream, three-column, dark theme | `https://krr.msantoki.com/` — run a fresh query (e.g. preference "genz style", query "How does RAM work?") and screenshot at 1920×1080 just as attempt 0 is mid-generation. Include one retrieval column, the draft column, and the attempt+final column. | Slide 6 |
| A2 | Style-card JSON excerpt | Copy verbatim from §2.3 / §3 Slide 3 spec. No other source. | Slide 3 |
| A3 | Architecture flow (KSJ loop) | Render from §3 Slide 4 spec — do NOT pull from `README.md`'s ASCII. | Slide 4 |
| A4 | Problem two-panel diagram | Render from §3 Slide 2 spec. | Slide 2 |
| A5 | Chart data | `13 / 20` vs `7 / 20`; gridline scale 0–20 in increments of 5. Source `results/evaluation_results_3llm.json`. | Slide 5 |
| A6 | Stat numbers | `0.80`, `4.9 / 5`, `0.05`. Source same JSON. | Slide 5 |
| A7 | Team names + ASU IDs | Front-matter at top of this file. | Slide 1 |

# §5 Quality bar — self-check before delivery

Before handing off the deck, confirm each of the following. If any fails, iterate:

- [ ] Exactly 6 slides, 1920×1080.
- [ ] All typography sizes from §1.3 used (no default PowerPoint sizes).
- [ ] All colors from §1.2 used (no default PowerPoint palette).
- [ ] Chrome present on slides 2–6, absent on slide 1.
- [ ] Only numbers from §2.7 appear on Slide 5. No invented stats.
- [ ] Style-card grid on Slide 3 lists the 8 ids in §2.3 order.
- [ ] Judge action arrows on Slide 4 use the `--good` / `--warn` / `--bad` tokens as specified.
- [ ] Slide 6 screenshot is dark-themed (matches deck) and shows three columns.
- [ ] Speaker-note paragraph word-counts fall within ±15 % of the targets:
  S1 ≈ 70 · S2 ≈ 80 · S3 ≈ 80 · S4 ≈ 120 · S5 ≈ 110 · S6 ≈ 100.
- [ ] All five team members' names appear on Slide 1 in the front-matter order.
- [ ] Total read time (all speaker notes at ~140 wpm) ≤ 345 s.
