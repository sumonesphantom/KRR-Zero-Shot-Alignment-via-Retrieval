"""Eval dataset + keyword-based style adherence scorer.

Copied from previous/src/evaluate.py so judge/ does not transitively import
the single-LLM generator (which would load the base model twice).
"""

import numpy as np


EVAL_DATASET = [
    {"prompt": "Explain how a computer stores data.",
     "preference": "formal academic tone with precise terminology",
     "expected_style": "formal_academic"},
    {"prompt": "What causes the seasons to change?",
     "preference": "casual and friendly, like talking to a buddy",
     "expected_style": "casual_friendly"},
    {"prompt": "How does a search engine work?",
     "preference": "short bullet points, concise, no extra words",
     "expected_style": "concise_bullet"},
    {"prompt": "Explain what a black hole is.",
     "preference": "explain like I'm 5, use simple words and fun analogies",
     "expected_style": "eli5_simple"},
    {"prompt": "How does HTTPS encryption work?",
     "preference": "technical and precise, include specific details and formulas",
     "expected_style": "technical_precise"},
    {"prompt": "What is inflation in economics?",
     "preference": "use the Socratic method, guide me with questions",
     "expected_style": "socratic_teaching"},
    {"prompt": "Explain how airplanes fly.",
     "preference": "tell it as a story, make it engaging and narrative",
     "expected_style": "storytelling_narrative"},
    {"prompt": "What is cloud computing?",
     "preference": "professional business tone, focus on actionable insights",
     "expected_style": "professional_business"},
    {"prompt": "How does the human heart work?",
     "preference": "be warm, encouraging, and patient in your explanation",
     "expected_style": "empathetic_supportive"},
    {"prompt": "Should we colonize Mars?",
     "preference": "present multiple perspectives, analyze critically",
     "expected_style": "debate_critical"},
    {"prompt": "What is DNA?",
     "preference": "scholarly, well-structured, use proper scientific terms",
     "expected_style": "formal_academic"},
    {"prompt": "How do computers learn?",
     "preference": "make it super simple for a child to understand",
     "expected_style": "eli5_simple"},
    {"prompt": "Explain the stock market.",
     "preference": "keep it brief, just the key points in bullets",
     "expected_style": "concise_bullet"},
    {"prompt": "What is renewable energy?",
     "preference": "chill and conversational, like explaining to a friend over coffee",
     "expected_style": "casual_friendly"},
    {"prompt": "How does Wi-Fi work?",
     "preference": "engineering-level detail with specifics and numbers",
     "expected_style": "technical_precise"},
    {"prompt": "What causes volcanic eruptions?",
     "preference": "weave it into an engaging story",
     "expected_style": "storytelling_narrative"},
    {"prompt": "Explain cryptocurrency.",
     "preference": "executive summary style, ROI and strategic relevance",
     "expected_style": "professional_business"},
    {"prompt": "How does memory work?",
     "preference": "ask me questions to make me think, don't just tell me",
     "expected_style": "socratic_teaching"},
    {"prompt": "What is gene editing?",
     "preference": "give me both sides, pros and cons, be balanced",
     "expected_style": "debate_critical"},
    {"prompt": "Explain gravity.",
     "preference": "be supportive and gentle, I find physics scary",
     "expected_style": "empathetic_supportive"},
]


def keyword_style_scorer(response: str, style_card: dict) -> dict:
    scores = {}
    if not style_card:
        return {"overall": 0.5}
    style_id = style_card["id"]
    rl = response.lower()

    if style_id == "concise_bullet":
        bullets = response.count("•") + response.count("-") + response.count("*")
        scores["has_bullets"] = min(bullets / 3, 1.0)
        scores["is_concise"] = 1.0 if len(response.split()) < 100 else 0.5
        scores["overall"] = (scores["has_bullets"] + scores["is_concise"]) / 2
    elif style_id == "formal_academic":
        formal = ["therefore", "furthermore", "consequently", "thus", "moreover",
                  "hence", "whereby", "constitutes", "demonstrates", "indicates", "significant"]
        fc = sum(1 for w in formal if w in rl)
        scores["formal_words"] = min(fc / 3, 1.0)
        scores["no_contractions"] = 1.0 if not any(
            c in rl for c in ["don't", "won't", "can't", "it's", "that's"]
        ) else 0.3
        scores["overall"] = (scores["formal_words"] + scores["no_contractions"]) / 2
    elif style_id == "casual_friendly":
        markers = ["!", "pretty", "cool", "right?", "basically", "like", "gonna", "kinda", "you know", "hey"]
        c = sum(1 for m in markers if m in rl)
        scores["casual_markers"] = min(c / 3, 1.0)
        scores["has_contractions"] = 1.0 if any(
            x in rl for x in ["don't", "won't", "can't", "it's", "that's", "you're"]
        ) else 0.3
        scores["overall"] = (scores["casual_markers"] + scores["has_contractions"]) / 2
    elif style_id == "eli5_simple":
        markers = ["imagine", "like", "think of", "pretend", "picture"]
        c = sum(1 for m in markers if m in rl)
        scores["uses_analogies"] = min(c / 2, 1.0)
        awl = np.mean([len(w) for w in response.split()]) if response.split() else 5
        scores["simple_words"] = 1.0 if awl < 5.5 else 0.5
        scores["overall"] = (scores["uses_analogies"] + scores["simple_words"]) / 2
    elif style_id == "technical_precise":
        markers = ["algorithm", "function", "parameter", "optimize", "complexity",
                   "implementation", "architecture", "protocol", "specification", "=", "O("]
        c = sum(1 for m in markers if m in rl)
        scores["technical_terms"] = min(c / 3, 1.0)
        scores["has_specifics"] = 1.0 if any(ch.isdigit() for ch in response) else 0.3
        scores["overall"] = (scores["technical_terms"] + scores["has_specifics"]) / 2
    elif style_id == "socratic_teaching":
        scores["has_questions"] = min(response.count("?") / 3, 1.0)
        guides = ["think about", "consider", "what if", "how might", "why do you think", "what do you"]
        c = sum(1 for g in guides if g in rl)
        scores["guiding_language"] = min(c / 2, 1.0)
        scores["overall"] = (scores["has_questions"] + scores["guiding_language"]) / 2
    elif style_id == "storytelling_narrative":
        markers = ["once", "imagine", "picture", "one day", "story", "journey", "adventure", "character", "scene"]
        c = sum(1 for m in markers if m in rl)
        scores["narrative_markers"] = min(c / 2, 1.0)
        scores["length_appropriate"] = 1.0 if len(response.split()) > 50 else 0.5
        scores["overall"] = (scores["narrative_markers"] + scores["length_appropriate"]) / 2
    elif style_id == "professional_business":
        markers = ["impact", "strategy", "roi", "stakeholder", "actionable",
                   "key takeaway", "bottom line", "leverage", "optimize"]
        c = sum(1 for m in markers if m in rl)
        scores["business_terms"] = min(c / 3, 1.0)
        scores["has_structure"] = 1.0 if ("**" in response or ":" in response) else 0.3
        scores["overall"] = (scores["business_terms"] + scores["has_structure"]) / 2
    elif style_id == "empathetic_supportive":
        markers = ["it's okay", "don't worry", "great question", "you're doing", "perfectly",
                   "normal", "take your time", "no rush", "that's completely", "i understand"]
        c = sum(1 for m in markers if m in rl)
        scores["empathy_markers"] = min(c / 2, 1.0)
        scores["warm_tone"] = 1.0 if "!" in response else 0.5
        scores["overall"] = (scores["empathy_markers"] + scores["warm_tone"]) / 2
    elif style_id == "debate_critical":
        markers = ["however", "on the other hand", "counter", "argument", "perspective",
                   "critics", "proponents", "debate", "consider", "alternatively", "pros", "cons"]
        c = sum(1 for m in markers if m in rl)
        scores["debate_terms"] = min(c / 3, 1.0)
        scores["balanced"] = 1.0 if c >= 2 else 0.3
        scores["overall"] = (scores["debate_terms"] + scores["balanced"]) / 2
    else:
        scores["overall"] = 0.5
    return scores
