#!/usr/bin/env python3
"""3-LLM pipeline entry point (Knowledge / Style / Judge).

Build the FAISS index once (`python scripts/build_index.py`), then:

    python judge/run_pipeline.py --step evaluate   # 20-prompt eval
    python judge/run_pipeline.py --step demo       # interactive REPL
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(__file__))


def step_evaluate():
    print("\n" + "=" * 60)
    print("3-LLM EVALUATION (Knowledge / Style / Judge)")
    print("=" * 60)
    from evaluate import run_three_llm_evaluation
    run_three_llm_evaluation()


def step_demo():
    print("\n" + "=" * 60)
    print("3-LLM INTERACTIVE DEMO")
    print("=" * 60)
    from agents.orchestrator import Orchestrator

    orch = Orchestrator()
    print("\nType 'quit' at any prompt to exit.\n")

    while True:
        preference = input("Your preference: ").strip()
        if preference.lower() == "quit":
            break
        query = input("Your question: ").strip()
        if query.lower() == "quit":
            break

        trace = orch.run(query, preference, top_k=3)

        print(f"\n--- Retrieval top-3 ---")
        for r in trace.retrieval:
            print(f"  #{r['rank']} {r['style_id']} (score={r['score']:.3f})")
        print(f"\n--- Knowledge draft ---\n{trace.draft}")
        for i, rev in enumerate(trace.revisions):
            print(f"\n--- Style attempt {i} [{rev.style_id}] ---")
            print(rev.styled[:400])
            print(
                f"  judge: action={rev.verdict.action} "
                f"style={rev.verdict.style_score}/5 "
                f"content_cos={rev.verdict.content_cosine:.2f}"
            )
        print(f"\n=== FINAL ({trace.final_style_id}) ===\n{trace.final_output}\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--step", choices=["evaluate", "demo"], default="evaluate")
    args = parser.parse_args()
    if args.step == "evaluate":
        step_evaluate()
    else:
        step_demo()


if __name__ == "__main__":
    main()
