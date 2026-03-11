# Zero-Shot Alignment via Retrieval

Align LLM outputs to user preferences by **retrieving pre-trained style modules (LoRA adapters)** at inference time, instead of fine-tuning per user. Given a natural language preference description (e.g., "be formal and academic"), the system retrieves the best-matching style adapter from a bank of pre-trained modules and composes it onto a base LLM to generate preference-aligned responses.

## Core Idea

Traditional alignment requires fine-tuning a model for each user's preferences — expensive and not scalable. This project takes a different approach:

1. **Pre-train** a bank of LoRA adapters, each capturing a distinct communication style
2. **Retrieve** the best adapter at inference time using embedding similarity over style descriptions
3. **Compose** the adapter onto the base model and generate

No per-user training is needed. The user simply describes what they want, and the system finds and applies the right style module.

## Architecture

```
User Preference Query ──► Embedding Model ──► FAISS Index ──► Top-K Style Cards
        │                  (MiniLM-L6-v2)      (cosine sim)         │
        │                                                           │
        ▼                                                           ▼
   User Prompt ──────────────────────────────► Base LLM + LoRA ──► Styled Response
                                               (TinyLlama 1.1B)
```

### Components

| Component | Implementation | Purpose |
|---|---|---|
| Style Representation | Style Cards (JSONL) | Searchable descriptions with tags, instructions, and examples |
| Retrieval | Sentence embeddings + FAISS | Fast nearest-neighbor search over style descriptions |
| Adaptation | LoRA adapters (PEFT) | Lightweight style modules composed onto base model |
| Evaluation | Heuristic + LLM-as-judge scoring | Measures retrieval accuracy, style adherence, and win rates |

## Project Structure

```
├── run_pipeline.py              # Main entry point for all pipeline steps
├── requirements.txt             # Python dependencies
├── style_bank/
│   ├── style_cards.jsonl        # 10 style definitions with examples
│   └── adapters/                # Trained LoRA weights (created during training)
├── src/
│   ├── config.py                # Shared configuration (model, paths, hyperparameters)
│   ├── build_index.py           # Builds FAISS index from style cards
│   ├── retrieve.py              # Retrieves top-k styles via embedding similarity
│   ├── train_adapters.py        # Trains LoRA adapters using synthetic data
│   ├── generate.py              # Generates responses with retrieved adapters
│   └── evaluate.py              # Evaluation: retrieval accuracy, style adherence, win rates
├── data/                        # FAISS index and metadata (created during indexing)
└── results/                     # Evaluation results (created during evaluation)
```

## Setup

### Requirements

- Python 3.10+
- macOS with Apple Silicon (MPS) or a CUDA GPU
- ~8 GB RAM minimum

### Installation

```bash
git clone https://github.com/<your-repo>/KRR-Zero-Shot-Alignment-via-Retrieval.git
cd KRR-Zero-Shot-Alignment-via-Retrieval
pip install -r requirements.txt
```

## Usage

### Run the Full Pipeline

```bash
python run_pipeline.py --step all
```

This runs all three steps sequentially: index building, adapter training, and evaluation.

### Run Individual Steps

```bash
# Step 1: Build the FAISS retrieval index from style cards
python run_pipeline.py --step index

# Step 2: Train LoRA adapters for all 10 styles
python run_pipeline.py --step train

# Step 3: Run the evaluation suite
python run_pipeline.py --step evaluate

# Optional: Add LLM-as-judge scoring (slower but more nuanced)
python run_pipeline.py --step evaluate --llm-judge

# Interactive demo: enter your own preferences and questions
python run_pipeline.py --step demo
```

### Interactive Demo

```bash
python run_pipeline.py --step demo
```

```
Your preference: explain things simply with fun analogies
Your question: How does Wi-Fi work?

Retrieving best style...
Top matches:
  #1 eli5_simple (score: 0.8234)
  #2 casual_friendly (score: 0.7102)
  #3 storytelling_narrative (score: 0.6543)

Generating with style: eli5_simple...

--- Response (eli5_simple) ---
Imagine your phone is sending invisible letters through the air...
```

## Implementation Details

### 1. Style Representation (Style Cards)

Each style is defined as a **Style Card** in `style_bank/style_cards.jsonl`:

```json
{
  "id": "formal_academic",
  "tags": ["formal", "academic", "detailed", "structured"],
  "instruction": "Answer in a formal academic tone. Use precise terminology...",
  "examples": [
    {
      "prompt": "Explain gradient descent.",
      "answer": "Gradient descent is a first-order iterative optimization..."
    }
  ],
  "adapter_path": "style_bank/adapters/formal_academic"
}
```

The 10 styles defined:

| Style | Tags | Description |
|---|---|---|
| `formal_academic` | formal, academic, detailed | Precise terminology, structured paragraphs |
| `casual_friendly` | casual, friendly, warm | Conversational, contractions, light humor |
| `concise_bullet` | concise, bullet points, minimal | Key facts only, no fluff |
| `eli5_simple` | simple, eli5, analogies | Explain like I'm 5, fun analogies |
| `technical_precise` | technical, precise, code-oriented | Specific details, formulas, numbers |
| `socratic_teaching` | socratic, teaching, questions | Guide understanding through questions |
| `storytelling_narrative` | storytelling, creative, engaging | Weave explanations into narratives |
| `professional_business` | professional, executive, actionable | ROI focus, strategic relevance |
| `empathetic_supportive` | empathetic, encouraging, patient | Warm, validating, gentle explanations |
| `debate_critical` | critical, analytical, balanced | Multiple perspectives, pros and cons |

### 2. Style Embedding and Retrieval

**Indexing** (`src/build_index.py`):
- Builds a text representation for each style card by combining its instruction, tags, and example Q&A pairs
- Encodes with `sentence-transformers/all-MiniLM-L6-v2` (384-dim embeddings)
- Stores normalized embeddings in a FAISS `IndexFlatIP` index (inner product = cosine similarity on normalized vectors)

**Retrieval** (`src/retrieve.py`):
- Encodes the user's preference query with the same embedding model
- Performs FAISS nearest-neighbor search to find top-k matching styles
- Computes softmax weights over similarity scores (with temperature scaling) for potential weighted composition

```python
retriever = StyleRetriever()
results = retriever.retrieve("I want formal academic explanations", top_k=3)
# Returns: [(style_card, similarity_score, weight), ...]
```

### 3. LoRA Adapter Training

**Training** (`src/train_adapters.py`):
- For each style, generates **synthetic training data** by prompting the base model with the style instruction across 30 diverse prompts
- Trains a **LoRA adapter** (rank=16, alpha=32) on the `q_proj`, `v_proj`, `k_proj`, `o_proj` attention layers
- Each adapter adds only ~4M trainable parameters vs 1.1B total — lightweight and composable

**LoRA Configuration:**
| Parameter | Value |
|---|---|
| Rank (r) | 16 |
| Alpha | 32 |
| Dropout | 0.05 |
| Target Modules | q_proj, v_proj, k_proj, o_proj |
| Training Epochs | 3 |
| Learning Rate | 2e-4 |

### 4. Generation with Composed Adapters

**Generation** (`src/generate.py`):
- Loads the base model (TinyLlama 1.1B Chat) once
- For each request, loads the retrieved LoRA adapter on top
- Generates with the composed model (base + adapter)
- Supports comparison mode: generates base, retrieved-style, and random-style outputs for the same prompt

### 5. Evaluation

**Evaluation** (`src/evaluate.py`) measures three things:

#### a) Retrieval Accuracy
- Tests whether the retriever returns the correct style for 20 diverse preference queries
- Reports **top-1 accuracy** (exact match) and **top-3 accuracy** (correct style in top 3)

#### b) Style Adherence Scoring
Two scoring methods:

- **Keyword heuristics**: Rule-based scoring per style (e.g., checking for bullet points in `concise_bullet`, question marks in `socratic_teaching`, formal vocabulary in `formal_academic`)
- **LLM-as-judge** (optional): Uses the base model to rate style adherence on a 1-5 scale

#### c) Pairwise Win Rates
Compares outputs across three conditions:
- **Retrieved adapter** vs **base model** (no adapter)
- **Retrieved adapter** vs **random adapter** (wrong style)
- **Random adapter** vs **base model**

The retrieved adapter should win against both the base model and a random adapter.

#### Baselines

| Baseline | Description |
|---|---|
| Base model | TinyLlama 1.1B with no adapter applied |
| Random adapter | A randomly selected (wrong) style adapter |
| Retrieved adapter | Our method — style selected by retrieval |

## Configuration

All configurable parameters are in `src/config.py`:

```python
# Model
BASE_MODEL_NAME = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# LoRA
LORA_R = 16
LORA_ALPHA = 32
LORA_DROPOUT = 0.05
TRAIN_EPOCHS = 3
LEARNING_RATE = 2e-4

# Retrieval
TOP_K = 5
TEMPERATURE = 0.1

# Generation
MAX_NEW_TOKENS = 256
```

To use a larger base model (e.g., Llama 3.1 8B, Mistral 7B), change `BASE_MODEL_NAME` and ensure you have sufficient VRAM/RAM.

## Expected Results

After running the full pipeline, results are saved to `results/evaluation_results.json` containing:

- Retrieval accuracy metrics
- Per-example style adherence scores for all three conditions
- Pairwise win rates
- Generated outputs for qualitative inspection

## Key Design Decisions

1. **Why retrieval over fine-tuning?** Retrieval is zero-shot — no per-user training needed. Adding new styles only requires a new style card and adapter, not retraining the whole system.

2. **Why LoRA?** LoRA adapters are small (~16 MB each vs 4 GB for the full model), fast to train, and can be swapped at inference time without reloading the base model.

3. **Why synthetic training data?** Generating style-specific training data from the base model itself ensures consistency and avoids the need for large curated datasets per style.

4. **Why FAISS?** FAISS provides sub-millisecond nearest-neighbor search, making retrieval negligible compared to generation time.

## References

- [LoRA: Low-Rank Adaptation of Large Language Models](https://arxiv.org/abs/2106.09685) (Hu et al., 2021)
- [PEFT: Parameter-Efficient Fine-Tuning](https://github.com/huggingface/peft)
- [Sentence-Transformers](https://www.sbert.net/)
- [FAISS: A Library for Efficient Similarity Search](https://github.com/facebookresearch/faiss)
