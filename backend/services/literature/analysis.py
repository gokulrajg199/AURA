"""
AURA - AI Paper Analysis Engine
--------------------------------
Converts retrieved literature metadata into structured research intelligence.

This is the first analysis layer:
Discovery -> Paper Analysis -> Cross-Paper Comparison -> Gap Detection
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any


# ============================================================
# TEXT UTILITIES
# ============================================================

STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "to", "for", "in",
    "on", "with", "using", "based", "from", "by", "as", "is",
    "are", "was", "were", "this", "that", "these", "those",
    "system", "study", "analysis", "approach", "method"
}


def clean_text(value: Any) -> str:
    """Safely convert arbitrary metadata into clean text."""
    if value is None:
        return ""

    text = str(value)

    # Remove common XML/JATS tags found in Crossref abstracts.
    text = re.sub(r"<[^>]+>", " ", text)

    # Fix common mojibake characters.
    replacements = {
        "â€“": "-",
        "â€”": "-",
        "â€˜": "'",
        "â€™": "'",
        "â€œ": '"',
        "â€\x9d": '"',
        "â€¦": "...",
        "Â": "",
    }

    for bad, good in replacements.items():
        text = text.replace(bad, good)

    return re.sub(r"\s+", " ", text).strip()


def tokenize(text: str) -> list[str]:
    """Extract useful normalized terms."""
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9\-]{2,}", text.lower())

    return [
        word
        for word in words
        if word not in STOPWORDS
    ]


def top_terms(text: str, limit: int = 12) -> list[str]:
    """Return frequent technical terms from text."""
    counts = Counter(tokenize(text))

    return [
        word
        for word, _ in counts.most_common(limit)
    ]


# ============================================================
# PAPER FIELD EXTRACTION
# ============================================================

def extract_authors(paper: dict[str, Any]) -> list[str]:
    """Normalize author information from different providers."""
    authors = paper.get("authors", [])

    if not authors:
        return []

    result: list[str] = []

    if isinstance(authors, list):
        for author in authors:
            if isinstance(author, str):
                result.append(author)

            elif isinstance(author, dict):
                name = (
                    author.get("name")
                    or author.get("display_name")
                    or author.get("author_name")
                )

                if name:
                    result.append(clean_text(name))

    return result


def extract_abstract(paper: dict[str, Any]) -> str:
    """Find abstract from normalized or provider-specific fields."""
    return clean_text(
        paper.get("abstract")
        or paper.get("abstract_text")
        or paper.get("description")
        or ""
    )


def extract_keywords(paper: dict[str, Any]) -> list[str]:
    """Extract available keywords/topics."""
    keywords: list[str] = []

    raw_keywords = paper.get("keywords", [])

    if isinstance(raw_keywords, list):
        for item in raw_keywords:
            if isinstance(item, str):
                keywords.append(clean_text(item))

            elif isinstance(item, dict):
                value = (
                    item.get("keyword")
                    or item.get("display_name")
                    or item.get("name")
                )

                if value:
                    keywords.append(clean_text(value))

    topics = paper.get("topics", [])

    if isinstance(topics, list):
        for topic in topics:
            if isinstance(topic, str):
                keywords.append(clean_text(topic))

            elif isinstance(topic, dict):
                value = (
                    topic.get("display_name")
                    or topic.get("name")
                    or topic.get("topic")
                )

                if value:
                    keywords.append(clean_text(value))

    # Deduplicate while preserving order.
    seen = set()
    result = []

    for item in keywords:
        normalized = item.lower()

        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(item)

    return result[:20]


# ============================================================
# RESEARCH SIGNAL DETECTION
# ============================================================

METHOD_TERMS = {
    "machine learning",
    "deep learning",
    "artificial intelligence",
    "neural network",
    "cnn",
    "convolutional neural network",
    "lstm",
    "transformer",
    "random forest",
    "support vector machine",
    "svm",
    "decision tree",
    "reinforcement learning",
    "federated learning",
    "computer vision",
    "iot",
    "internet of things",
    "edge computing",
    "cloud computing",
    "data mining",
    "optimization",
    "prediction",
    "classification",
    "regression",
    "monitoring",
    "sensor",
    "image processing",
}


DATASET_TERMS = {
    "dataset",
    "data set",
    "plantvillage",
    "kaggle",
    "uci",
    "benchmark",
    "images",
    "sensor data",
    "real-world data",
    "experimental data",
}


EXPERIMENT_TERMS = {
    "experiment",
    "evaluation",
    "accuracy",
    "precision",
    "recall",
    "f1",
    "rmse",
    "mae",
    "validation",
    "testing",
    "comparison",
    "baseline",
    "performance",
    "results",
}


LIMITATION_TERMS = {
    "limitation",
    "limitations",
    "future work",
    "future research",
    "challenge",
    "challenges",
    "constraint",
    "constraints",
    "drawback",
    "shortcoming",
    "lack of",
    "however",
    "remains",
}


def find_terms(text: str, vocabulary: set[str]) -> list[str]:
    """Find research signals present in text."""
    lowered = text.lower()

    found = []

    for term in vocabulary:
        if term in lowered:
            found.append(term)

    return sorted(found)


# ============================================================
# PAPER ANALYSIS
# ============================================================

def analyze_paper(
    paper: dict[str, Any],
    user_question: str = "",
) -> dict[str, Any]:
    """
    Produce structured intelligence for one paper.

    Important:
    This layer does NOT invent unsupported facts.
    It labels signals as detected/unknown where metadata
    is insufficient.
    """

    title = clean_text(paper.get("title", ""))
    abstract = extract_abstract(paper)
    keywords = extract_keywords(paper)
    authors = extract_authors(paper)

    combined_text = " ".join(
        [
            title,
            abstract,
            " ".join(keywords),
        ]
    )

    methods = find_terms(combined_text, METHOD_TERMS)
    datasets = find_terms(combined_text, DATASET_TERMS)
    experiments = find_terms(combined_text, EXPERIMENT_TERMS)
    limitation_signals = find_terms(
        combined_text,
        LIMITATION_TERMS,
    )

    terms = top_terms(combined_text)

    question_terms = set(tokenize(user_question))
    paper_terms = set(tokenize(combined_text))

    if question_terms:
        overlap = question_terms.intersection(paper_terms)
        relevance_overlap = round(
            len(overlap) / max(len(question_terms), 1),
            3,
        )
    else:
        overlap = set()
        relevance_overlap = 0.0

    # Evidence strength depends on the information actually
    # available rather than pretending every paper is complete.
    evidence_fields = 0

    if title:
        evidence_fields += 1

    if abstract:
        evidence_fields += 1

    if keywords:
        evidence_fields += 1

    if authors:
        evidence_fields += 1

    if paper.get("doi"):
        evidence_fields += 1

    evidence_score = round(
        evidence_fields / 5 * 100,
        1,
    )

    if evidence_score >= 80:
        evidence_level = "strong"

    elif evidence_score >= 50:
        evidence_level = "moderate"

    else:
        evidence_level = "limited"

    return {
        "id": paper.get("id"),
        "title": title,
        "year": paper.get("year"),
        "doi": paper.get("doi"),
        "url": paper.get("url"),
        "open_access_url": paper.get("open_access_url"),
        "providers": paper.get("providers", []),

        "authors": authors,

        "abstract": abstract,

        "keywords": keywords,

        "detected": {
            "methods": methods,
            "datasets": datasets,
            "experiment_signals": experiments,
            "limitation_signals": limitation_signals,
        },

        "top_terms": terms,

        "project_relevance": {
            "query_term_overlap": sorted(overlap),
            "overlap_score": relevance_overlap,
        },

        "evidence": {
            "score": evidence_score,
            "level": evidence_level,
            "available_fields": evidence_fields,
        },

        "interpretation": {
            "problem": (
                "Abstract available for further problem extraction."
                if abstract
                else "Problem cannot be reliably extracted from available metadata."
            ),

            "method": (
                ", ".join(methods)
                if methods
                else "Method not reliably identified from available metadata."
            ),

            "dataset": (
                ", ".join(datasets)
                if datasets
                else "Dataset not identified from available metadata."
            ),

            "experiments": (
                ", ".join(experiments)
                if experiments
                else "Experimental evidence not identified from available metadata."
            ),

            "limitations": (
                ", ".join(limitation_signals)
                if limitation_signals
                else "No explicit limitation signal detected in available metadata."
            ),
        },

        "evidence_labels": {
            "metadata": "Verified Evidence",
            "detected_methods": "AI Synthesis",
            "detected_limitations": "AI Synthesis",
            "recommendations": "AURA Recommendation",
        },
    }


# ============================================================
# CROSS-PAPER COMPARISON
# ============================================================

def compare_papers(
    analyses: list[dict[str, Any]],
) -> dict[str, Any]:
    """Find common methods, datasets, terms and limitation signals."""

    method_counter = Counter()
    dataset_counter = Counter()
    experiment_counter = Counter()
    limitation_counter = Counter()
    term_counter = Counter()

    for analysis in analyses:
        method_counter.update(
            analysis.get("detected", {}).get("methods", [])
        )

        dataset_counter.update(
            analysis.get("detected", {}).get("datasets", [])
        )

        experiment_counter.update(
            analysis.get("detected", {}).get("experiment_signals", [])
        )

        limitation_counter.update(
            analysis.get("detected", {}).get("limitation_signals", [])
        )

        term_counter.update(
            analysis.get("top_terms", [])
        )

    def frequent(counter: Counter, minimum: int = 2) -> list[dict[str, Any]]:
        return [
            {
                "item": item,
                "paper_count": count,
            }
            for item, count in counter.most_common()
            if count >= minimum
        ]

    return {
        "papers_analyzed": len(analyses),

        "common_methods": frequent(method_counter),

        "common_datasets": frequent(dataset_counter),

        "common_experiment_signals": frequent(
            experiment_counter
        ),

        "common_limitation_signals": frequent(
            limitation_counter
        ),

        "recurring_terms": frequent(
            term_counter,
            minimum=max(2, len(analyses) // 5),
        ),
    }


# ============================================================
# MAIN ENGINE
# ============================================================

def analyze_literature(
    papers: list[dict[str, Any]],
    user_question: str = "",
) -> dict[str, Any]:
    """
    Analyze a complete literature result set.

    Returns:
        - individual paper intelligence
        - cross-paper comparison
        - evidence statistics
    """

    analyses = [
        analyze_paper(
            paper,
            user_question=user_question,
        )
        for paper in papers
    ]

    comparison = compare_papers(analyses)

    evidence_scores = [
        item["evidence"]["score"]
        for item in analyses
    ]

    average_evidence = round(
        sum(evidence_scores) / len(evidence_scores),
        1,
    ) if evidence_scores else 0.0

    strong = sum(
        1
        for item in analyses
        if item["evidence"]["level"] == "strong"
    )

    moderate = sum(
        1
        for item in analyses
        if item["evidence"]["level"] == "moderate"
    )

    limited = sum(
        1
        for item in analyses
        if item["evidence"]["level"] == "limited"
    )

    return {
        "engine": "AURA Paper Analysis Engine",
        "version": "1.0.0",

        "question": user_question,

        "summary": {
            "papers_analyzed": len(analyses),
            "average_evidence_score": average_evidence,
            "strong_evidence_papers": strong,
            "moderate_evidence_papers": moderate,
            "limited_evidence_papers": limited,
        },

        "papers": analyses,

        "comparison": comparison,

        "evidence_policy": {
            "verified_evidence": (
                "Directly supported by retrieved metadata."
            ),
            "ai_synthesis": (
                "Derived from detected patterns across available evidence."
            ),
            "aura_recommendation": (
                "A proposed direction and not a published fact."
            ),
            "needs_verification": (
                "Used when available metadata is insufficient."
            ),
        },
    }