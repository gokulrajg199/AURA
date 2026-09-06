import re
from collections import Counter
from typing import Any


# =========================================================
# EVIDENCE CLASSIFICATIONS
# =========================================================

EVIDENCE_SUPPORTED = "evidence_supported"
CROSS_PAPER_SYNTHESIS = "cross_paper_synthesis"
AURA_OPPORTUNITY = "aura_opportunity"
NEEDS_VERIFICATION = "needs_verification"


# =========================================================
# BASIC TEXT HELPERS
# =========================================================

def clean_text(value: Any) -> str:
    if value is None:
        return ""

    text = str(value)

    # Remove HTML / XML tags
    text = re.sub(r"<[^>]+>", " ", text)

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def normalize_items(items: Any) -> list[str]:
    if not items:
        return []

    if isinstance(items, str):
        items = [items]

    result = []

    for item in items:
        text = clean_text(item).lower()

        if text and text not in result:
            result.append(text)

    return result


# =========================================================
# PAPER DATA EXTRACTION
# =========================================================

def get_detected(paper: dict, category: str) -> list[str]:
    """
    Read detected signals from AURA paper-analysis output.

    Supports both the internal Gap Engine names and the
    names used by the Paper Analysis Engine.
    """

    detected = paper.get("detected", {})

    if not isinstance(detected, dict):
        return []

    aliases = {
        "methods": [
            "methods",
            "methodology"
        ],

        "datasets": [
            "datasets",
            "dataset"
        ],

        "experiment_signals": [
            "experiment_signals",
            "experimentation"
        ],

        "limitation_signals": [
            "limitation_signals",
            "limitations"
        ],
    }

    possible_keys = aliases.get(
        category,
        [category]
    )

    for key in possible_keys:

        values = detected.get(key)

        if values:
            return normalize_items(values)

    return []


def get_title(paper: dict) -> str:
    return clean_text(
        paper.get("title", "")
    )


def get_year(paper: dict) -> int | None:

    value = paper.get("year")

    try:
        return int(value) if value else None

    except (TypeError, ValueError):
        return None


def get_relevance(paper: dict) -> float:

    relevance = paper.get(
        "project_relevance",
        {}
    )

    if not isinstance(relevance, dict):
        return 0.0

    try:
        return float(
            relevance.get(
                "overlap_score",
                0.0
            )
        )

    except (TypeError, ValueError):
        return 0.0


# =========================================================
# CATEGORY COUNTING
# =========================================================

def count_category(
    papers: list[dict],
    category: str
):

    counter = Counter()

    for paper in papers:

        items = set(
            get_detected(
                paper,
                category
            )
        )

        for item in items:
            counter[item] += 1

    return counter


def recurring_items(
    papers: list[dict],
    category: str,
    minimum_ratio: float = 0.3
):

    if not papers:
        return []

    counter = count_category(
        papers,
        category
    )

    threshold = max(
        2,
        int(
            len(papers)
            * minimum_ratio
        )
    )

    results = []

    for item, count in counter.most_common():

        if count >= threshold:

            results.append(
                {
                    "item": item,
                    "paper_count": count,
                    "coverage": round(
                        count / len(papers),
                        3
                    )
                }
            )

    return results


# =========================================================
# MISSING EVIDENCE CATEGORIES
# =========================================================

def detect_missing_categories(
    papers: list[dict]
):

    categories = {

        "methods": "methodology",

        "datasets": "dataset",

        "experiment_signals": "experimentation",

        "limitation_signals": "limitations",

    }

    results = []

    for category, label in categories.items():

        available = sum(
            1
            for paper in papers
            if get_detected(
                paper,
                category
            )
        )

        coverage = (
            available / len(papers)
            if papers
            else 0
        )

        if coverage < 0.30:

            results.append(
                {
                    "area": label,

                    "coverage": round(
                        coverage,
                        3
                    ),

                    "classification":
                        NEEDS_VERIFICATION,

                    "reason":
                        f"Only {available} "
                        f"of {len(papers)} "
                        f"retrieved papers "
                        f"contained detectable "
                        f"{label} signals."
                }
            )

    return results


# =========================================================
# METHOD CONCENTRATION
# =========================================================

def detect_method_concentration(
    papers: list[dict]
):

    methods = recurring_items(
        papers,
        "methods",
        minimum_ratio=0.5
    )

    results = []

    for method in methods:

        if method["coverage"] >= 0.6:

            results.append(
                {
                    "type":
                        "method_concentration",

                    "method":
                        method["item"],

                    "coverage":
                        method["coverage"],

                    "classification":
                        CROSS_PAPER_SYNTHESIS,

                    "interpretation":
                        "A substantial portion of "
                        "the retrieved literature "
                        "uses this approach. "
                        "Alternative or complementary "
                        "methods may be worth "
                        "investigating."
                }
            )

    return results


# =========================================================
# RECURRING LIMITATIONS
# =========================================================

def detect_limitation_patterns(
    papers: list[dict]
):

    limitations = recurring_items(
        papers,
        "limitation_signals",
        minimum_ratio=0.2
    )

    results = []

    for limitation in limitations:

        results.append(
            {
                "type":
                    "recurring_limitation",

                "signal":
                    limitation["item"],

                "paper_count":
                    limitation["paper_count"],

                "coverage":
                    limitation["coverage"],

                "classification":
                    EVIDENCE_SUPPORTED,

                "interpretation":
                    "This limitation signal "
                    "appears repeatedly in the "
                    "retrieved literature and "
                    "should be examined in the "
                    "underlying papers before "
                    "being treated as a confirmed "
                    "research gap."
            }
        )

    return results


# =========================================================
# DOMAIN OVERLAP
# =========================================================

def detect_domain_overlap(
    papers: list[dict]
):

    high_relevance = [
        paper
        for paper in papers
        if get_relevance(paper) >= 0.50
    ]

    if len(high_relevance) < 2:
        return []

    return [

        {
            "type":
                "high_domain_overlap",

            "paper_count":
                len(high_relevance),

            "coverage":
                round(
                    len(high_relevance)
                    / len(papers),
                    3
                ),

            "classification":
                CROSS_PAPER_SYNTHESIS,

            "interpretation":
                "Multiple retrieved papers "
                "are strongly related to the "
                "submitted project. The concept "
                "should not be described as "
                "globally novel without deeper "
                "similarity analysis."
        }

    ]


# =========================================================
# AURA OPPORTUNITY GENERATION
# =========================================================

def generate_opportunities(
    papers: list[dict],
    user_question: str
):

    opportunities = []

    methods = recurring_items(
        papers,
        "methods",
        minimum_ratio=0.4
    )

    datasets = recurring_items(
        papers,
        "datasets",
        minimum_ratio=0.3
    )

    experiments = recurring_items(
        papers,
        "experiment_signals",
        minimum_ratio=0.3
    )

    # -----------------------------------------------------
    # Methodology opportunity
    # -----------------------------------------------------

    if methods:

        opportunities.append(
            {
                "title":
                    "Investigate alternative "
                    "or hybrid methodologies",

                "classification":
                    AURA_OPPORTUNITY,

                "basis":
                    [
                        item["item"]
                        for item in methods[:5]
                    ],

                "description":
                    "The retrieved literature "
                    "shows repeated use of similar "
                    "methodological approaches. "
                    "AURA recommends investigating "
                    "whether a complementary or "
                    "hybrid approach can address "
                    "known limitations."
            }
        )

    # -----------------------------------------------------
    # Dataset opportunity
    # -----------------------------------------------------

    if datasets:

        opportunities.append(
            {
                "title":
                    "Evaluate dataset diversity "
                    "and generalization",

                "classification":
                    AURA_OPPORTUNITY,

                "basis":
                    [
                        item["item"]
                        for item in datasets[:5]
                    ],

                "description":
                    "Recurring dataset usage may "
                    "indicate an opportunity to "
                    "evaluate the approach on "
                    "additional, diverse, or "
                    "real-world data."
            }
        )

    # -----------------------------------------------------
    # Experiment opportunity
    # -----------------------------------------------------

    if experiments:

        opportunities.append(
            {
                "title":
                    "Strengthen experimental "
                    "validation",

                "classification":
                    AURA_OPPORTUNITY,

                "basis":
                    [
                        item["item"]
                        for item in experiments[:5]
                    ],

                "description":
                    "AURA recommends stronger "
                    "baseline comparison, robust "
                    "evaluation metrics, parameter "
                    "analysis, and real-world "
                    "validation where appropriate."
            }
        )

    return opportunities


# =========================================================
# GAP SCORE
# =========================================================

def build_gap_score(
    papers: list[dict],
    evidence_gaps: list[dict],
    synthesis_gaps: list[dict]
):

    if not papers:
        return 0.0

    high_relevance = sum(
        1
        for paper in papers
        if get_relevance(paper) >= 0.50
    )

    relevance_penalty = (
        high_relevance
        / len(papers)
    )

    evidence_signal = min(
        len(evidence_gaps) / 4,
        1.0
    )

    synthesis_signal = min(
        len(synthesis_gaps) / 4,
        1.0
    )

    score = (
        evidence_signal * 45
        +
        synthesis_signal * 35
        +
        (1 - relevance_penalty) * 20
    )

    return round(
        max(
            0.0,
            min(
                score,
                100.0
            )
        ),
        1
    )


# =========================================================
# MAIN RESEARCH GAP ENGINE
# =========================================================

def analyze_research_gap(
    papers: list[dict],
    user_question: str
):

    if not papers:

        return {
            "success": False,
            "message":
                "No papers available "
                "for gap analysis."
        }

    # -----------------------------------------------------
    # Evidence-supported signals
    # -----------------------------------------------------

    evidence_gaps = []

    evidence_gaps.extend(
        detect_limitation_patterns(
            papers
        )
    )

    evidence_gaps.extend(
        detect_missing_categories(
            papers
        )
    )

    # -----------------------------------------------------
    # Cross-paper synthesis
    # -----------------------------------------------------

    synthesis_gaps = []

    synthesis_gaps.extend(
        detect_method_concentration(
            papers
        )
    )

    synthesis_gaps.extend(
        detect_domain_overlap(
            papers
        )
    )

    # -----------------------------------------------------
    # AURA opportunities
    # -----------------------------------------------------

    opportunities = generate_opportunities(
        papers,
        user_question
    )

    # -----------------------------------------------------
    # Gap score
    # -----------------------------------------------------

    gap_score = build_gap_score(
        papers,
        evidence_gaps,
        synthesis_gaps
    )

    # -----------------------------------------------------
    # Literature years
    # -----------------------------------------------------

    years = [
        get_year(paper)
        for paper in papers
        if get_year(paper)
    ]

    # -----------------------------------------------------
    # Final result
    # -----------------------------------------------------

    return {

        "success": True,

        "research_question":
            user_question,

        "papers_analyzed":
            len(papers),

        "gap_score":
            gap_score,

        "evidence_supported_gaps":
            evidence_gaps,

        "cross_paper_synthesis":
            synthesis_gaps,

        "aura_opportunities":
            opportunities,

        "needs_verification":
            [

                {
                    "classification":
                        NEEDS_VERIFICATION,

                    "statement":
                        "A sparse or missing "
                        "signal in the retrieved "
                        "literature does not prove "
                        "that no such work exists."
                },

                {
                    "classification":
                        NEEDS_VERIFICATION,

                    "statement":
                        "Global novelty cannot "
                        "be established from this "
                        "retrieval set alone."
                }

            ],

        "literature_window":
            {

                "from":
                    min(years)
                    if years
                    else None,

                "to":
                    max(years)
                    if years
                    else None
            },

        "summary":
            {

                "evidence_gap_count":
                    len(evidence_gaps),

                "synthesis_gap_count":
                    len(synthesis_gaps),

                "opportunity_count":
                    len(opportunities),

                "confidence":
                    "moderate"
                    if len(papers) < 20
                    else "high"
            }
    }