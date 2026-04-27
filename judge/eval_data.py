"""Eval dataset + keyword-based style adherence scorer.

Each EVAL_DATASET item is { prompt, preference, expected_style }, where the
preference is natural-language phrasing that should retrieve `expected_style`
top-1 from the current 10-card bank in style_bank/style_cards.jsonl.

The heuristic scorer rewards observable style markers (vocabulary, structure,
register cues). It is *not* a quality measure — it's a coarse, deterministic
proxy used to compare 3-LLM output against a no-retrieval baseline. The Judge
LLM and the content-preservation cosine carry the real evaluation load.
"""

import numpy as np


EVAL_DATASET = [
    # formal_academic ×2
    {"prompt": "Explain how a computer stores data.",
     "preference": "formal academic register, precise terminology, hedged claims",
     "expected_style": "formal_academic"},
    {"prompt": "What is DNA?",
     "preference": "scholarly tone with subordinate clauses and Latinate vocabulary",
     "expected_style": "formal_academic"},

    # business_executive ×2
    {"prompt": "What is cloud computing?",
     "preference": "executive briefing — bottom line first, key takeaways, business idiom",
     "expected_style": "business_executive"},
    {"prompt": "Explain cryptocurrency.",
     "preference": "business strategy lens, ROI and KPI framing, actionable",
     "expected_style": "business_executive"},

    # technical_precise ×2
    {"prompt": "How does HTTPS encryption work?",
     "preference": "technical documentation register with specific numbers, units, and protocols",
     "expected_style": "technical_precise"},
    {"prompt": "How does Wi-Fi work?",
     "preference": "engineering-level detail, frequencies, complexity classes, formulas",
     "expected_style": "technical_precise"},

    # storytelling_narrative ×2
    {"prompt": "Explain how airplanes fly.",
     "preference": "tell it as a story — establish a scene, a character, build tension",
     "expected_style": "storytelling_narrative"},
    {"prompt": "What causes volcanic eruptions?",
     "preference": "vivid narrative with sensory detail, specific moments, past tense",
     "expected_style": "storytelling_narrative"},

    # eli5_playful ×2
    {"prompt": "Explain what a black hole is.",
     "preference": "explain like I'm five, only common words, use toys or animals as analogies",
     "expected_style": "eli5_playful"},
    {"prompt": "How do computers learn?",
     "preference": "make it super simple for a child, use Lego or food analogies",
     "expected_style": "eli5_playful"},

    # hype_bro ×2
    {"prompt": "How does a rocket launch into space?",
     "preference": "hype-bro / gym-culture voice — bro, no cap, W move, fire",
     "expected_style": "hype_bro"},
    {"prompt": "What is machine learning?",
     "preference": "streamer hype-bro slang, all-caps emphasis, let's go energy",
     "expected_style": "hype_bro"},

    # gen_z_online ×2
    {"prompt": "What is climate change?",
     "preference": "chronically online gen z voice, lowercase, bestie, it's giving",
     "expected_style": "gen_z_online"},
    {"prompt": "How does a search engine work?",
     "preference": "gen z internet slang, lowercase only, no thoughts head empty",
     "expected_style": "gen_z_online"},

    # keywords_only ×2
    {"prompt": "What is gravity?",
     "preference": "wikipedia-infobox style, key:value pairs, terse noun phrases, drop articles",
     "expected_style": "keywords_only"},
    {"prompt": "How does the human heart work?",
     "preference": "maximum density, no full sentences, short labelled bullets",
     "expected_style": "keywords_only"},

    # dad_joke_pun ×2
    {"prompt": "How does photosynthesis work?",
     "preference": "explain it correctly but with terrible dad jokes and puns drawn from the topic",
     "expected_style": "dad_joke_pun"},
    {"prompt": "What is recursion?",
     "preference": "groan-worthy puns, weary-parent voice, end with 'I'll see myself out'",
     "expected_style": "dad_joke_pun"},

    # shakespeare_iambic ×2
    {"prompt": "What is inflation in economics?",
     "preference": "Early Modern English — thee, thou, doth, verily, soliloquy register",
     "expected_style": "shakespeare_iambic"},
    {"prompt": "Explain gravity.",
     "preference": "Shakespearean voice, archaic verb endings, theatrical opening like 'Hark!'",
     "expected_style": "shakespeare_iambic"},
]


def keyword_style_scorer(response: str, style_card: dict) -> dict:
    """Heuristic 0–1 score per style. Branches per style id; falls back to 0.5
    for unknown ids (so a missing card doesn't auto-fail a comparison)."""
    scores: dict = {}
    if not style_card:
        return {"overall": 0.5}
    style_id = style_card["id"]
    rl = response.lower()
    words = response.split()
    n_words = len(words)

    if style_id == "formal_academic":
        formal = ["therefore", "furthermore", "consequently", "thus", "moreover",
                  "hence", "whereby", "wherein", "constitutes", "demonstrates",
                  "indicates", "significant", "notwithstanding", "albeit",
                  "may be argued", "in essence"]
        fc = sum(1 for w in formal if w in rl)
        scores["formal_words"] = min(fc / 4, 1.0)
        contractions = ["don't", "won't", "can't", "it's", "that's", "you're", "i'm"]
        scores["no_contractions"] = 1.0 if not any(c in rl for c in contractions) else 0.3
        scores["overall"] = (scores["formal_words"] + scores["no_contractions"]) / 2

    elif style_id == "business_executive":
        terms = ["bottom line", "roi", "kpi", "stakeholder", "north star",
                 "actionable", "key takeaway", "leverage", "deliverable",
                 "strategic", "execution", "scale", "value prop", "tldr",
                 "bluf", "executive summary"]
        bc = sum(1 for t in terms if t in rl)
        scores["business_terms"] = min(bc / 3, 1.0)
        # Lead-with-the-bottom-line heuristic
        head = response[:120].lower()
        scores["structured_lead"] = (
            1.0 if any(s in head for s in ["bottom line", "tl;dr", "tldr", "bluf",
                                            "1.", "1)", "executive summary",
                                            "key takeaway"])
            else 0.4
        )
        scores["overall"] = (scores["business_terms"] + scores["structured_lead"]) / 2

    elif style_id == "technical_precise":
        markers = ["algorithm", "function", "parameter", "complexity",
                   "implementation", "architecture", "protocol", "specification",
                   "throughput", "latency", "byte", "bit", "frequency",
                   "wavelength", "encryption", "handshake", "o(n", "o(log"]
        c = sum(1 for m in markers if m in rl)
        scores["technical_terms"] = min(c / 3, 1.0)
        scores["has_specifics"] = 1.0 if any(ch.isdigit() for ch in response) else 0.3
        units = ["mhz", "ghz", " ms", " ns", "%", "kb", "mb", "gb", " hz",
                 " nm", "bps"]
        scores["has_units"] = 1.0 if any(u in rl for u in units) else 0.5
        scores["overall"] = (
            scores["technical_terms"] + scores["has_specifics"] + scores["has_units"]
        ) / 3

    elif style_id == "storytelling_narrative":
        markers = ["once", "imagine", "picture", "one day", "story", "journey",
                   "adventure", "character", "scene", "morning", "evening",
                   "saw", "felt", "heard", "remembered", "stood", "watched",
                   "whispered"]
        c = sum(1 for m in markers if m in rl)
        scores["narrative_markers"] = min(c / 3, 1.0)
        scores["length_appropriate"] = 1.0 if n_words > 80 else 0.5
        scores["overall"] = (scores["narrative_markers"] + scores["length_appropriate"]) / 2

    elif style_id == "eli5_playful":
        markers = ["imagine", "like", "think of", "pretend", "picture",
                   "lego", "toy", "puppy", "kitten", "candy", "ice cream",
                   "play", "magic", "pizza", "cookie", "squirrel"]
        c = sum(1 for m in markers if m in rl)
        scores["playful_markers"] = min(c / 3, 1.0)
        avg_word_len = float(np.mean([len(w) for w in words])) if words else 5.0
        scores["simple_words"] = (
            1.0 if avg_word_len < 4.8
            else 0.6 if avg_word_len < 5.5
            else 0.3
        )
        scores["overall"] = (scores["playful_markers"] + scores["simple_words"]) / 2

    elif style_id == "hype_bro":
        markers = ["bro", "ayy", "no cap", "w move", "let him cook", "fire",
                   "cracked", "absolutely", "literally", "fr", "ngl",
                   "let's go", "goated", "elite", "based", "lock in"]
        c = sum(1 for m in markers if m in rl)
        scores["hype_markers"] = min(c / 3, 1.0)
        scores["exclamation"] = min(response.count("!") / 3, 1.0)
        caps_words = sum(
            1 for w in words if len(w) > 1 and w.isalpha() and w.isupper()
        )
        scores["caps_emphasis"] = 1.0 if caps_words >= 2 else 0.4
        scores["overall"] = (
            scores["hype_markers"] + scores["exclamation"] + scores["caps_emphasis"]
        ) / 3

    elif style_id == "gen_z_online":
        markers = ["bestie", "it's giving", "literally", "no thoughts",
                   "the way", "core", "rent free", "icon", "slay", "ate",
                   "lowkey", "highkey", "vibe", "main character", "cap",
                   "deadass"]
        c = sum(1 for m in markers if m in rl)
        scores["genz_markers"] = min(c / 3, 1.0)
        # Mostly lowercase — count ratio of uppercase letters
        letters = [ch for ch in response if ch.isalpha()]
        upper_ratio = (
            sum(1 for ch in letters if ch.isupper()) / len(letters)
            if letters else 0.5
        )
        scores["lowercase"] = (
            1.0 if upper_ratio < 0.04
            else 0.6 if upper_ratio < 0.10
            else 0.2
        )
        scores["overall"] = (scores["genz_markers"] + scores["lowercase"]) / 2

    elif style_id == "keywords_only":
        lines = [l for l in (ln.strip() for ln in response.splitlines()) if l]
        if not lines:
            scores["overall"] = 0.0
            return scores
        colon_lines = sum(1 for l in lines if ":" in l)
        scores["uses_colons"] = min(colon_lines / max(len(lines) * 0.5, 1), 1.0)
        avg_wpl = float(np.mean([len(l.split()) for l in lines]))
        scores["dense"] = (
            1.0 if avg_wpl < 8
            else 0.6 if avg_wpl < 14
            else 0.2
        )
        scores["overall"] = (scores["uses_colons"] + scores["dense"]) / 2

    elif style_id == "dad_joke_pun":
        closing_tags = ["i'll see myself out", "i know, i know",
                        "thank you, i'll be here", "yes, my kids hate me",
                        "you know what they say"]
        scores["closing_tag"] = 1.0 if any(t in rl for t in closing_tags) else 0.3
        # Markdown emphasis is a strong pun-highlight signal in our outputs
        scores["pun_emphasis"] = 1.0 if response.count("*") >= 4 else 0.5
        groan = ["pun", "groan", "see myself", "thank you",
                 "kids hate", "dad joke"]
        scores["groan_signal"] = 1.0 if any(s in rl for s in groan) else 0.5
        scores["overall"] = (
            scores["closing_tag"] + scores["pun_emphasis"] + scores["groan_signal"]
        ) / 3

    elif style_id == "shakespeare_iambic":
        archaic = ["thou", " thee", " thy", "thine", "doth", "hath", " art ",
                   "wilt ", "shalt", "hast", "verily", "forsooth", "lo,",
                   "lo!", "behold", "hark", "methinks", "'tis", "'twas",
                   "o'er", "-eth", "-est"]
        c = sum(1 for w in archaic if w in rl)
        scores["archaic_pronouns"] = min(c / 4, 1.0)
        head = response[:40].lower()
        scores["theatrical_open"] = (
            1.0 if any(s in head for s in ["hark", "lo!", "behold", "verily",
                                            "forsooth"])
            else 0.4
        )
        scores["overall"] = (
            scores["archaic_pronouns"] + scores["theatrical_open"]
        ) / 2

    else:
        scores["overall"] = 0.5

    return scores
