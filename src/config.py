"""Shared configuration for the project."""

import os
import torch
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.parent

# Paths
STYLE_BANK_DIR = PROJECT_ROOT / "style_bank"
STYLE_CARDS_PATH = STYLE_BANK_DIR / "style_cards.jsonl"
ADAPTERS_DIR = STYLE_BANK_DIR / "adapters"
INDEX_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"

# Model settings
BASE_MODEL_NAME = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Device selection
def get_device():
    if torch.cuda.is_available():
        return "cuda"
    elif torch.backends.mps.is_available():
        return "mps"
    return "cpu"

DEVICE = get_device()

# LoRA training config
LORA_R = 16
LORA_ALPHA = 32
LORA_DROPOUT = 0.05
LORA_TARGET_MODULES = ["q_proj", "v_proj", "k_proj", "o_proj"]
TRAIN_EPOCHS = 3
TRAIN_BATCH_SIZE = 4
LEARNING_RATE = 2e-4
MAX_SEQ_LENGTH = 512

# Retrieval config
TOP_K = 5
TEMPERATURE = 0.1  # for softmax weighting

# Generation config
MAX_NEW_TOKENS = 256
