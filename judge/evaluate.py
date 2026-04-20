"""Evaluation for the 3-LLM pipeline (Ollama backend).

Runs the orchestrator on the 20-prompt eval set, scores outputs with the
heuristic scorer, and compares against a base-model baseline generated
directly via Ollama (same model as Knowledge/Style, no style card, no judge).
"""

import json
import numpy as np
from pathlib import Path

from eval_data import EVAL_DATASET, keyword_style_scorer
from agents.orchestrator import Orchestrator
from agents.ollama_client import OllamaClient
from config import RESULTS_DIR, TRACES_DIR, STYLE_MODEL


def run_three_llm_evaluation():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    TRACES_DIR.mkdir(parents=True, exist_ok=True)

    orch = Orchestrator()
    # Baseline: same underlying Ollama model as Style, but no style card and no judge.
    baseline = OllamaClient(STYLE_MODEL)

    per_item = []
    wins_3llm_vs_base = 0

    for i, item in enumerate(EVAL_DATASET):
        print(f"\n[{i+1}/{len(EVAL_DATASET)}] {item['prompt'][:60]}")

        trace = orch.run(item["prompt"], item["preference"], top_k=3)
        base_out = baseline.generate(prompt=item["prompt"], temperature=0.7)

        expected_card = orch.retriever.cards.get(item["expected_style"])
        three_llm_score = keyword_style_scorer(trace.final_output, expected_card)["overall"]
        base_score = keyword_style_scorer(base_out, expected_card)["overall"]

        if three_llm_score > base_score:
            wins_3llm_vs_base += 1

        trace_path = TRACES_DIR / f"trace_{i:02d}.json"
        with open(trace_path, "w") as f:
            json.dump(trace.to_dict(), f, indent=2, default=str)

        per_item.append({
            "prompt": item["prompt"],
            "preference": item["preference"],
            "expected_style": item["expected_style"],
            "retrieved_style": trace.final_style_id,
            "n_revisions": len(trace.revisions) - 1,
            "judge_style_score": trace.final_verdict.style_score if trace.final_verdict else None,
            "judge_action": trace.final_verdict.action if trace.final_verdict else None,
            "content_cosine": trace.final_verdict.content_cosine if trace.final_verdict else None,
            "three_llm_heuristic": three_llm_score,
            "base_heuristic": base_score,
            "three_llm_output": trace.final_output[:400],
            "base_output": base_out[:400],
            "trace_path": str(trace_path.relative_to(Path(__file__).resolve().parent.parent)),
        })

        print(
            f"  style={trace.final_style_id}  revs={len(trace.revisions)-1}  "
            f"heur 3llm/base={three_llm_score:.2f}/{base_score:.2f}  "
            f"judge={per_item[-1]['judge_style_score']}/5"
        )

    n = len(per_item)
    report = {
        "n": n,
        "wins_3llm_vs_base": wins_3llm_vs_base,
        "win_rate_3llm_vs_base": wins_3llm_vs_base / n if n else 0,
        "mean_three_llm_heuristic": float(np.mean([p["three_llm_heuristic"] for p in per_item])),
        "mean_base_heuristic": float(np.mean([p["base_heuristic"] for p in per_item])),
        "mean_revisions": float(np.mean([p["n_revisions"] for p in per_item])),
        "mean_judge_style_score": float(np.mean(
            [p["judge_style_score"] for p in per_item if p["judge_style_score"] is not None]
        )),
        "mean_content_cosine": float(np.mean(
            [p["content_cosine"] for p in per_item if p["content_cosine"] is not None]
        )),
        "per_item": per_item,
    }

    out_path = RESULTS_DIR / "evaluation_results_3llm.json"
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2, default=str)

    print(f"\n{'='*60}")
    print("3-LLM EVALUATION SUMMARY")
    print(f"{'='*60}")
    print(f"3-LLM vs Base (heuristic win rate): {wins_3llm_vs_base}/{n}")
    print(f"Mean heuristic — 3-LLM : {report['mean_three_llm_heuristic']:.3f}")
    print(f"Mean heuristic — Base  : {report['mean_base_heuristic']:.3f}")
    print(f"Mean judge style score : {report['mean_judge_style_score']:.2f}/5")
    print(f"Mean content cosine    : {report['mean_content_cosine']:.3f}")
    print(f"Mean revisions/request : {report['mean_revisions']:.2f}")
    print(f"Full report            : {out_path}")
    print(f"Traces                 : {TRACES_DIR}/")
    return report


if __name__ == "__main__":
    run_three_llm_evaluation()
