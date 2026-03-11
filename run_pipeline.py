#!/usr/bin/env python3
"""
Zero-Shot Alignment via Retrieval — Full Pipeline

Run the complete pipeline end-to-end:
  1. Build FAISS index from style cards
  2. Train LoRA adapters for each style
  3. Run evaluation (retrieval accuracy + style adherence + win rates)

Usage:
  python run_pipeline.py                  # Run all steps
  python run_pipeline.py --step index     # Only build the index
  python run_pipeline.py --step train     # Only train adapters
  python run_pipeline.py --step evaluate  # Only run evaluation
  python run_pipeline.py --step demo      # Run interactive demo
"""

import sys
import os
import argparse

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def step_build_index():
    print("\n" + "=" * 60)
    print("STEP 1: Building FAISS index from style cards")
    print("=" * 60)
    from build_index import build_index
    build_index()


def step_train_adapters():
    print("\n" + "=" * 60)
    print("STEP 2: Training LoRA adapters")
    print("=" * 60)
    from train_adapters import train_all_adapters
    train_all_adapters()


def step_evaluate(use_llm_judge=False):
    print("\n" + "=" * 60)
    print("STEP 3: Running evaluation")
    print("=" * 60)
    from evaluate import run_evaluation
    run_evaluation(use_llm_judge=use_llm_judge)


def step_demo():
    print("\n" + "=" * 60)
    print("INTERACTIVE DEMO")
    print("=" * 60)
    from generate import StyledGenerator

    gen = StyledGenerator()

    print("\nAvailable styles:")
    for sid in gen.retriever.cards:
        card = gen.retriever.cards[sid]
        print(f"  - {sid}: {card['instruction'][:60]}...")

    print("\nEnter your preference and question. Type 'quit' to exit.\n")

    while True:
        preference = input("Your preference (e.g., 'formal and academic'): ").strip()
        if preference.lower() == "quit":
            break

        prompt = input("Your question: ").strip()
        if prompt.lower() == "quit":
            break

        print("\nRetrieving best style...")
        retrieval = gen.retriever.retrieve(preference, top_k=3)
        print(f"Top matches:")
        for r in retrieval:
            print(f"  #{r['rank']} {r['style_id']} (score: {r['score']:.4f})")

        print(f"\nGenerating with style: {retrieval[0]['style_id']}...")
        result = gen.generate_with_style(prompt, preference_query=preference)
        print(f"\n--- Response ({result['style_id']}) ---")
        print(result["response"])
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Zero-Shot Alignment via Retrieval Pipeline"
    )
    parser.add_argument(
        "--step",
        choices=["all", "index", "train", "evaluate", "demo"],
        default="all",
        help="Which pipeline step to run (default: all)",
    )
    parser.add_argument(
        "--llm-judge",
        action="store_true",
        help="Use LLM-as-judge scoring during evaluation",
    )
    args = parser.parse_args()

    if args.step in ("all", "index"):
        step_build_index()

    if args.step in ("all", "train"):
        step_train_adapters()

    if args.step in ("all", "evaluate"):
        step_evaluate(use_llm_judge=args.llm_judge)

    if args.step == "demo":
        step_demo()

    if args.step == "all":
        print("\n" + "=" * 60)
        print("PIPELINE COMPLETE")
        print("=" * 60)
        print("Results saved to results/evaluation_results.json")


if __name__ == "__main__":
    main()
