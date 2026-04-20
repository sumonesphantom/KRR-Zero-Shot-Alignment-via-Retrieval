"""Evaluate preference alignment: retrieved style vs baselines."""

import json
import time
import numpy as np
from pathlib import Path
from collections import defaultdict
from generate import StyledGenerator
from config import RESULTS_DIR


# Evaluation dataset: (prompt, preference_query, expected_style_id)
EVAL_DATASET = [
    {
        "prompt": "Explain how a computer stores data.",
        "preference": "formal academic tone with precise terminology",
        "expected_style": "formal_academic",
    },
    {
        "prompt": "What causes the seasons to change?",
        "preference": "casual and friendly, like talking to a buddy",
        "expected_style": "casual_friendly",
    },
    {
        "prompt": "How does a search engine work?",
        "preference": "short bullet points, concise, no extra words",
        "expected_style": "concise_bullet",
    },
    {
        "prompt": "Explain what a black hole is.",
        "preference": "explain like I'm 5, use simple words and fun analogies",
        "expected_style": "eli5_simple",
    },
    {
        "prompt": "How does HTTPS encryption work?",
        "preference": "technical and precise, include specific details and formulas",
        "expected_style": "technical_precise",
    },
    {
        "prompt": "What is inflation in economics?",
        "preference": "use the Socratic method, guide me with questions",
        "expected_style": "socratic_teaching",
    },
    {
        "prompt": "Explain how airplanes fly.",
        "preference": "tell it as a story, make it engaging and narrative",
        "expected_style": "storytelling_narrative",
    },
    {
        "prompt": "What is cloud computing?",
        "preference": "professional business tone, focus on actionable insights",
        "expected_style": "professional_business",
    },
    {
        "prompt": "How does the human heart work?",
        "preference": "be warm, encouraging, and patient in your explanation",
        "expected_style": "empathetic_supportive",
    },
    {
        "prompt": "Should we colonize Mars?",
        "preference": "present multiple perspectives, analyze critically",
        "expected_style": "debate_critical",
    },
    # Additional test cases for robustness
    {
        "prompt": "What is DNA?",
        "preference": "scholarly, well-structured, use proper scientific terms",
        "expected_style": "formal_academic",
    },
    {
        "prompt": "How do computers learn?",
        "preference": "make it super simple for a child to understand",
        "expected_style": "eli5_simple",
    },
    {
        "prompt": "Explain the stock market.",
        "preference": "keep it brief, just the key points in bullets",
        "expected_style": "concise_bullet",
    },
    {
        "prompt": "What is renewable energy?",
        "preference": "chill and conversational, like explaining to a friend over coffee",
        "expected_style": "casual_friendly",
    },
    {
        "prompt": "How does Wi-Fi work?",
        "preference": "engineering-level detail with specifics and numbers",
        "expected_style": "technical_precise",
    },
    {
        "prompt": "What causes volcanic eruptions?",
        "preference": "weave it into an engaging story",
        "expected_style": "storytelling_narrative",
    },
    {
        "prompt": "Explain cryptocurrency.",
        "preference": "executive summary style, ROI and strategic relevance",
        "expected_style": "professional_business",
    },
    {
        "prompt": "How does memory work?",
        "preference": "ask me questions to make me think, don't just tell me",
        "expected_style": "socratic_teaching",
    },
    {
        "prompt": "What is gene editing?",
        "preference": "give me both sides, pros and cons, be balanced",
        "expected_style": "debate_critical",
    },
    {
        "prompt": "Explain gravity.",
        "preference": "be supportive and gentle, I find physics scary",
        "expected_style": "empathetic_supportive",
    },
]


def llm_judge_style_adherence(response: str, style_card: dict, generator: StyledGenerator):
    """
    Use the base LLM as a judge to score style adherence.
    Returns a score from 1-5.
    """
    judge_prompt = (
        f"Rate how well the following response matches this style description.\n\n"
        f"Style: {style_card['instruction']}\n"
        f"Tags: {', '.join(style_card['tags'])}\n\n"
        f"Response to evaluate:\n{response[:500]}\n\n"
        f"Rate from 1 (poor match) to 5 (perfect match). "
        f"Reply with ONLY a single number 1-5."
    )
    output = generator.generate_base(judge_prompt)

    # Extract score
    for char in output:
        if char.isdigit() and char in "12345":
            return int(char)
    return 3  # Default if parsing fails


def keyword_style_scorer(response: str, style_card: dict):
    """
    Rule-based style adherence scoring using heuristics.
    Returns a dict of sub-scores and an overall score.
    """
    scores = {}
    style_id = style_card["id"]
    response_lower = response.lower()

    # Universal scores
    scores["length"] = len(response.split())

    if style_id == "concise_bullet":
        bullet_count = response.count("•") + response.count("-") + response.count("*")
        scores["has_bullets"] = min(bullet_count / 3, 1.0)
        scores["is_concise"] = 1.0 if len(response.split()) < 100 else 0.5
        scores["overall"] = (scores["has_bullets"] + scores["is_concise"]) / 2

    elif style_id == "formal_academic":
        formal_words = ["therefore", "furthermore", "consequently", "thus",
                        "moreover", "hence", "whereby", "constitutes",
                        "demonstrates", "indicates", "significant"]
        formal_count = sum(1 for w in formal_words if w in response_lower)
        scores["formal_words"] = min(formal_count / 3, 1.0)
        scores["no_contractions"] = 1.0 if not any(
            c in response_lower for c in ["don't", "won't", "can't", "it's", "that's"]
        ) else 0.3
        scores["overall"] = (scores["formal_words"] + scores["no_contractions"]) / 2

    elif style_id == "casual_friendly":
        casual_markers = ["!", "pretty", "cool", "right?", "basically",
                          "like", "gonna", "kinda", "you know", "hey"]
        casual_count = sum(1 for m in casual_markers if m in response_lower)
        scores["casual_markers"] = min(casual_count / 3, 1.0)
        has_contractions = any(
            c in response_lower for c in ["don't", "won't", "can't", "it's", "that's", "you're"]
        )
        scores["has_contractions"] = 1.0 if has_contractions else 0.3
        scores["overall"] = (scores["casual_markers"] + scores["has_contractions"]) / 2

    elif style_id == "eli5_simple":
        simple_markers = ["imagine", "like", "think of", "pretend", "picture"]
        simple_count = sum(1 for m in simple_markers if m in response_lower)
        scores["uses_analogies"] = min(simple_count / 2, 1.0)
        avg_word_len = np.mean([len(w) for w in response.split()]) if response.split() else 5
        scores["simple_words"] = 1.0 if avg_word_len < 5.5 else 0.5
        scores["overall"] = (scores["uses_analogies"] + scores["simple_words"]) / 2

    elif style_id == "technical_precise":
        tech_markers = ["algorithm", "function", "parameter", "optimize",
                        "complexity", "implementation", "architecture",
                        "protocol", "specification", "=", "O("]
        tech_count = sum(1 for m in tech_markers if m in response_lower)
        scores["technical_terms"] = min(tech_count / 3, 1.0)
        has_numbers = any(c.isdigit() for c in response)
        scores["has_specifics"] = 1.0 if has_numbers else 0.3
        scores["overall"] = (scores["technical_terms"] + scores["has_specifics"]) / 2

    elif style_id == "socratic_teaching":
        question_count = response.count("?")
        scores["has_questions"] = min(question_count / 3, 1.0)
        guiding_words = ["think about", "consider", "what if", "how might",
                         "why do you think", "what do you"]
        guide_count = sum(1 for g in guiding_words if g in response_lower)
        scores["guiding_language"] = min(guide_count / 2, 1.0)
        scores["overall"] = (scores["has_questions"] + scores["guiding_language"]) / 2

    elif style_id == "storytelling_narrative":
        story_markers = ["once", "imagine", "picture", "one day", "story",
                         "journey", "adventure", "character", "scene"]
        story_count = sum(1 for m in story_markers if m in response_lower)
        scores["narrative_markers"] = min(story_count / 2, 1.0)
        scores["length_appropriate"] = 1.0 if len(response.split()) > 50 else 0.5
        scores["overall"] = (scores["narrative_markers"] + scores["length_appropriate"]) / 2

    elif style_id == "professional_business":
        biz_markers = ["impact", "strategy", "roi", "stakeholder", "actionable",
                       "key takeaway", "bottom line", "leverage", "optimize"]
        biz_count = sum(1 for m in biz_markers if m in response_lower)
        scores["business_terms"] = min(biz_count / 3, 1.0)
        has_structure = "**" in response or ":" in response
        scores["has_structure"] = 1.0 if has_structure else 0.3
        scores["overall"] = (scores["business_terms"] + scores["has_structure"]) / 2

    elif style_id == "empathetic_supportive":
        empathy_markers = ["it's okay", "don't worry", "great question",
                           "you're doing", "perfectly", "normal", "take your time",
                           "no rush", "that's completely", "i understand"]
        emp_count = sum(1 for m in empathy_markers if m in response_lower)
        scores["empathy_markers"] = min(emp_count / 2, 1.0)
        scores["warm_tone"] = 1.0 if "!" in response else 0.5
        scores["overall"] = (scores["empathy_markers"] + scores["warm_tone"]) / 2

    elif style_id == "debate_critical":
        debate_markers = ["however", "on the other hand", "counter", "argument",
                          "perspective", "critics", "proponents", "debate",
                          "consider", "alternatively", "pros", "cons"]
        debate_count = sum(1 for m in debate_markers if m in response_lower)
        scores["debate_terms"] = min(debate_count / 3, 1.0)
        scores["balanced"] = 1.0 if debate_count >= 2 else 0.3
        scores["overall"] = (scores["debate_terms"] + scores["balanced"]) / 2

    else:
        scores["overall"] = 0.5

    return scores


def evaluate_retrieval_accuracy(generator: StyledGenerator):
    """Evaluate if retrieval returns the correct style for each preference query."""
    correct = 0
    correct_top3 = 0
    total = len(EVAL_DATASET)

    results = []
    for item in EVAL_DATASET:
        retrieval = generator.retriever.retrieve(item["preference"], top_k=3)
        retrieved_id = retrieval[0]["style_id"]
        top3_ids = [r["style_id"] for r in retrieval]

        is_correct = retrieved_id == item["expected_style"]
        is_in_top3 = item["expected_style"] in top3_ids

        correct += is_correct
        correct_top3 += is_in_top3

        results.append({
            "preference": item["preference"],
            "expected": item["expected_style"],
            "retrieved": retrieved_id,
            "correct": is_correct,
            "in_top3": is_in_top3,
            "scores": [r["score"] for r in retrieval],
        })

    accuracy = correct / total
    top3_accuracy = correct_top3 / total

    print(f"\n{'='*60}")
    print("RETRIEVAL ACCURACY")
    print(f"{'='*60}")
    print(f"Top-1 Accuracy: {accuracy:.1%} ({correct}/{total})")
    print(f"Top-3 Accuracy: {top3_accuracy:.1%} ({correct_top3}/{total})")

    # Show mistakes
    mistakes = [r for r in results if not r["correct"]]
    if mistakes:
        print(f"\nMistakes ({len(mistakes)}):")
        for m in mistakes:
            print(f"  Expected: {m['expected']:25s} Got: {m['retrieved']:25s}")
            print(f"    Query: {m['preference'][:60]}")

    return {"top1_accuracy": accuracy, "top3_accuracy": top3_accuracy, "details": results}


def evaluate_style_adherence(generator: StyledGenerator, use_llm_judge=False):
    """
    Evaluate style adherence of generated outputs.

    Compares:
    - Base model (no adapter)
    - Retrieved adapter (top-1)
    - Random adapter
    """
    print(f"\n{'='*60}")
    print("STYLE ADHERENCE EVALUATION")
    print(f"{'='*60}")

    all_results = []

    for i, item in enumerate(EVAL_DATASET):
        print(f"\n[{i+1}/{len(EVAL_DATASET)}] {item['prompt'][:50]}...")
        print(f"  Preference: {item['preference'][:50]}...")

        # Generate comparison
        comparison = generator.generate_comparison(
            item["prompt"], item["preference"], top_k=3
        )

        # Get the expected style card for scoring
        expected_card = generator.retriever.cards.get(item["expected_style"])
        retrieved_card = generator.retriever.cards.get(comparison["retrieved_style_id"])

        # Score with keyword-based heuristics
        base_score = keyword_style_scorer(comparison["base_output"], expected_card)
        retrieved_score = keyword_style_scorer(comparison["retrieved_output"], expected_card)
        random_score = keyword_style_scorer(comparison["random_output"], expected_card)

        result = {
            "prompt": item["prompt"],
            "preference": item["preference"],
            "expected_style": item["expected_style"],
            "retrieved_style": comparison["retrieved_style_id"],
            "random_style": comparison["random_style_id"],
            "base_output": comparison["base_output"][:300],
            "retrieved_output": comparison["retrieved_output"][:300],
            "random_output": comparison["random_output"][:300],
            "base_score": base_score["overall"],
            "retrieved_score": retrieved_score["overall"],
            "random_score": random_score["overall"],
            "base_detail": base_score,
            "retrieved_detail": retrieved_score,
            "random_detail": random_score,
        }

        # Optional LLM judge
        if use_llm_judge and expected_card:
            result["llm_base_score"] = llm_judge_style_adherence(
                comparison["base_output"], expected_card, generator
            )
            result["llm_retrieved_score"] = llm_judge_style_adherence(
                comparison["retrieved_output"], expected_card, generator
            )
            result["llm_random_score"] = llm_judge_style_adherence(
                comparison["random_output"], expected_card, generator
            )

        all_results.append(result)
        print(f"  Scores -> Base: {result['base_score']:.2f}  "
              f"Retrieved: {result['retrieved_score']:.2f}  "
              f"Random: {result['random_score']:.2f}")

    return all_results


def compute_win_rates(results):
    """Compute pairwise win rates from evaluation results."""
    wins = defaultdict(lambda: {"retrieved_vs_base": 0, "retrieved_vs_random": 0,
                                 "random_vs_base": 0, "total": 0})

    for r in results:
        wins["overall"]["total"] += 1
        if r["retrieved_score"] > r["base_score"]:
            wins["overall"]["retrieved_vs_base"] += 1
        if r["retrieved_score"] > r["random_score"]:
            wins["overall"]["retrieved_vs_random"] += 1
        if r["random_score"] > r["base_score"]:
            wins["overall"]["random_vs_base"] += 1

        # Per-style wins
        style = r["expected_style"]
        wins[style]["total"] += 1
        if r["retrieved_score"] > r["base_score"]:
            wins[style]["retrieved_vs_base"] += 1
        if r["retrieved_score"] > r["random_score"]:
            wins[style]["retrieved_vs_random"] += 1

    print(f"\n{'='*60}")
    print("PAIRWISE WIN RATES")
    print(f"{'='*60}")

    overall = wins["overall"]
    n = overall["total"]
    print(f"\nOverall ({n} examples):")
    print(f"  Retrieved vs Base:   {overall['retrieved_vs_base']/n:.1%}")
    print(f"  Retrieved vs Random: {overall['retrieved_vs_random']/n:.1%}")
    print(f"  Random vs Base:      {overall['random_vs_base']/n:.1%}")

    return dict(wins)


def generate_report(retrieval_results, adherence_results, win_rates):
    """Generate a summary report and save to disk."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    report = {
        "retrieval_accuracy": {
            "top1": retrieval_results["top1_accuracy"],
            "top3": retrieval_results["top3_accuracy"],
        },
        "style_adherence": {
            "mean_base_score": np.mean([r["base_score"] for r in adherence_results]),
            "mean_retrieved_score": np.mean([r["retrieved_score"] for r in adherence_results]),
            "mean_random_score": np.mean([r["random_score"] for r in adherence_results]),
        },
        "win_rates": {
            k: {kk: vv for kk, vv in v.items()}
            for k, v in win_rates.items()
        },
        "detailed_results": adherence_results,
    }

    # Save full results
    with open(RESULTS_DIR / "evaluation_results.json", "w") as f:
        json.dump(report, f, indent=2, default=str)

    # Print summary
    print(f"\n{'='*60}")
    print("FINAL REPORT SUMMARY")
    print(f"{'='*60}")
    print(f"Retrieval Accuracy (Top-1):  {report['retrieval_accuracy']['top1']:.1%}")
    print(f"Retrieval Accuracy (Top-3):  {report['retrieval_accuracy']['top3']:.1%}")
    print(f"Mean Style Score (Base):     {report['style_adherence']['mean_base_score']:.3f}")
    print(f"Mean Style Score (Retrieved):{report['style_adherence']['mean_retrieved_score']:.3f}")
    print(f"Mean Style Score (Random):   {report['style_adherence']['mean_random_score']:.3f}")
    print(f"\nFull results saved to {RESULTS_DIR / 'evaluation_results.json'}")

    return report


def run_evaluation(use_llm_judge=False):
    """Run the complete evaluation pipeline."""
    print("Initializing generator...")
    generator = StyledGenerator()

    # Step 1: Retrieval accuracy
    retrieval_results = evaluate_retrieval_accuracy(generator)

    # Step 2: Style adherence
    adherence_results = evaluate_style_adherence(generator, use_llm_judge=use_llm_judge)

    # Step 3: Win rates
    win_rates = compute_win_rates(adherence_results)

    # Step 4: Generate report
    report = generate_report(retrieval_results, adherence_results, win_rates)

    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--llm-judge", action="store_true",
                        help="Use LLM-as-judge in addition to heuristic scoring")
    args = parser.parse_args()
    run_evaluation(use_llm_judge=args.llm_judge)
