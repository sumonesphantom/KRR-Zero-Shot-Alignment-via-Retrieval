"""Train LoRA adapters for each style using synthetic training data."""

import json
import torch
from pathlib import Path
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
)
from peft import LoraConfig, get_peft_model, TaskType
from torch.utils.data import Dataset
from config import (
    BASE_MODEL_NAME, STYLE_CARDS_PATH, ADAPTERS_DIR, DEVICE,
    LORA_R, LORA_ALPHA, LORA_DROPOUT, LORA_TARGET_MODULES,
    TRAIN_EPOCHS, TRAIN_BATCH_SIZE, LEARNING_RATE, MAX_SEQ_LENGTH,
    PROJECT_ROOT, TRAINING_DATA_DIR,
)


# Diverse training prompts for generating synthetic style data
TRAINING_PROMPTS = [
    "Explain how neural networks work.",
    "What is climate change and why does it matter?",
    "Describe the process of evolution by natural selection.",
    "Explain the concept of supply and demand in economics.",
    "What is quantum computing?",
    "How does the immune system protect the body?",
    "Explain the theory of relativity in simple terms.",
    "What is blockchain technology?",
    "How does machine learning differ from traditional programming?",
    "Explain the water cycle.",
    "What causes earthquakes?",
    "How does encryption keep data secure?",
    "Explain the concept of compound interest.",
    "What is the greenhouse effect?",
    "How do vaccines work?",
    "Explain what an algorithm is.",
    "What is artificial intelligence?",
    "How does the internet work?",
    "Explain the concept of DNA and genetics.",
    "What is dark matter?",
    "How does a computer processor work?",
    "Explain the Big Bang theory.",
    "What is the difference between weather and climate?",
    "How do batteries store energy?",
    "Explain the concept of recursion in programming.",
    "What is the scientific method?",
    "How does GPS navigation work?",
    "Explain the concept of entropy.",
    "What is renewable energy?",
    "How does memory work in the human brain?",
]


class StyleDataset(Dataset):
    """Dataset of (prompt, styled_response) pairs for LoRA training."""

    def __init__(self, examples, tokenizer, max_length=MAX_SEQ_LENGTH):
        self.examples = examples
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.examples)

    def __getitem__(self, idx):
        ex = self.examples[idx]
        # Format as chat
        text = format_chat(ex["prompt"], ex["answer"])
        encodings = self.tokenizer(
            text,
            truncation=True,
            max_length=self.max_length,
            padding="max_length",
            return_tensors="pt",
        )
        input_ids = encodings["input_ids"].squeeze()
        attention_mask = encodings["attention_mask"].squeeze()
        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "labels": input_ids.clone(),
        }


def format_chat(prompt, answer):
    """Format a prompt-answer pair as a chat template."""
    return (
        f"<|user|>\n{prompt}\n<|assistant|>\n{answer}</s>"
    )


def load_curated_data(style_card):
    """Load curated training data from JSONL files in data/training/."""
    style_id = style_card["id"]
    data_path = TRAINING_DATA_DIR / f"{style_id}.jsonl"

    if not data_path.exists():
        return None

    examples = []
    with open(data_path, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                examples.append(json.loads(line))

    print(f"  Loaded {len(examples)} curated examples from {data_path}")
    return examples


def generate_synthetic_data(style_card, tokenizer, model):
    """Generate synthetic training data for a style using the base model."""
    examples = []

    # First, use the examples from the style card itself
    for ex in style_card.get("examples", []):
        examples.append({"prompt": ex["prompt"], "answer": ex["answer"]})

    # Generate more examples using the base model with the style instruction
    print(f"  Generating synthetic data for style: {style_card['id']}")
    style_instruction = style_card["instruction"]

    for prompt in TRAINING_PROMPTS:
        styled_prompt = (
            f"<|user|>\n"
            f"You must answer in this style: {style_instruction}\n\n"
            f"Question: {prompt}\n"
            f"<|assistant|>\n"
        )
        inputs = tokenizer(styled_prompt, return_tensors="pt", truncation=True,
                           max_length=MAX_SEQ_LENGTH).to(model.device)

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=200,
                temperature=0.7,
                do_sample=True,
                top_p=0.9,
                pad_token_id=tokenizer.eos_token_id,
            )

        generated = tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[1]:],
            skip_special_tokens=True
        ).strip()

        if generated:
            examples.append({"prompt": prompt, "answer": generated})

    print(f"  Generated {len(examples)} training examples.")
    return examples


def train_single_adapter(style_card, base_model, tokenizer):
    """Train a LoRA adapter for a single style."""
    style_id = style_card["id"]
    adapter_path = PROJECT_ROOT / style_card["adapter_path"]
    adapter_path.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"Training adapter: {style_id}")
    print(f"{'='*60}")

    # Load curated data first, fall back to synthetic generation
    examples = load_curated_data(style_card)
    if examples is None:
        print(f"  No curated dataset found, falling back to synthetic generation...")
        examples = generate_synthetic_data(style_card, tokenizer, base_model)

    # Save training data for reproducibility
    with open(adapter_path / "training_data.json", "w") as f:
        json.dump(examples, f, indent=2)

    # Create LoRA model
    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        target_modules=LORA_TARGET_MODULES,
    )
    lora_model = get_peft_model(base_model, lora_config)
    lora_model.print_trainable_parameters()

    # Create dataset
    dataset = StyleDataset(examples, tokenizer)

    # Training arguments
    training_args = TrainingArguments(
        output_dir=str(adapter_path / "checkpoints"),
        num_train_epochs=TRAIN_EPOCHS,
        per_device_train_batch_size=TRAIN_BATCH_SIZE,
        learning_rate=LEARNING_RATE,
        weight_decay=0.01,
        logging_steps=10,
        save_strategy="epoch",
        fp16=False,  # MPS doesn't support fp16 training well
        report_to="none",
        remove_unused_columns=False,
        dataloader_pin_memory=False,  # Required for MPS
    )

    # Train
    trainer = Trainer(
        model=lora_model,
        args=training_args,
        train_dataset=dataset,
        data_collator=DataCollatorForLanguageModeling(
            tokenizer=tokenizer, mlm=False
        ),
    )
    trainer.train()

    # Save adapter weights only
    lora_model.save_pretrained(str(adapter_path))
    print(f"Adapter saved to {adapter_path}")

    # Clean up LoRA layers for next adapter
    del lora_model
    del trainer
    torch.mps.empty_cache() if DEVICE == "mps" else None

    return adapter_path


def train_all_adapters():
    """Train LoRA adapters for all styles defined in style_cards.jsonl."""
    # Load style cards
    cards = []
    with open(STYLE_CARDS_PATH, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                cards.append(json.loads(line))

    print(f"Found {len(cards)} style cards to train.")

    # Load base model once
    print(f"Loading base model: {BASE_MODEL_NAME}")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_NAME)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_NAME,
        torch_dtype=torch.float32,  # float32 for MPS stability
        device_map={"": DEVICE} if DEVICE != "mps" else None,
    )
    if DEVICE == "mps":
        model = model.to("mps")

    # Train each adapter
    for card in cards:
        adapter_path = PROJECT_ROOT / card["adapter_path"]
        if (adapter_path / "adapter_config.json").exists():
            print(f"Skipping {card['id']} (already trained)")
            continue
        train_single_adapter(card, model, tokenizer)
        # Reload base model to clear LoRA layers
        del model
        torch.mps.empty_cache() if DEVICE == "mps" else None
        model = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL_NAME,
            torch_dtype=torch.float32,
            device_map={"": DEVICE} if DEVICE != "mps" else None,
        )
        if DEVICE == "mps":
            model = model.to("mps")

    print("\nAll adapters trained successfully!")


if __name__ == "__main__":
    train_all_adapters()
