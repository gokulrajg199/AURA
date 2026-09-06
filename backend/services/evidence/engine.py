from __future__ import annotations

from typing import Any
from uuid import uuid4

from models.evidence import (
    EvidenceClaim,
    EvidenceCollection,
    EvidenceRecord,
    EvidenceSource,
    clamp_confidence,
    create_claim,
    create_source,
)


class EvidenceEngine:
    """
    Central evidence-processing layer for AURA.

    Responsibilities:
        - normalize external sources
        - create evidence claims
        - connect claims to sources
        - calculate evidence confidence
        - detect basic supporting/contradicting signals
        - build provenance records
    """

    # ========================================================
    # SOURCE NORMALIZATION
    # ========================================================

    def normalize_sources(
        self,
        sources: list[Any],
    ) -> list[EvidenceSource]:
        """
        Convert literature/search results into AURA source objects.
        """

        normalized: list[EvidenceSource] = []

        for index, source in enumerate(sources):
            data = self._to_dict(source)

            title = self._first_value(
                data,
                [
                    "title",
                    "name",
                ],
            )

            if not title:
                title = f"Untitled Source {index + 1}"

            source_id = self._first_value(
                data,
                [
                    "source_id",
                    "id",
                    "paper_id",
                    "doi",
                ],
            )

            if not source_id:
                source_id = (
                    f"source-{uuid4().hex[:12]}"
                )

            provider = self._first_value(
                data,
                [
                    "provider",
                    "source",
                    "database",
                    "publisher",
                ],
            )

            source_type = self._first_value(
                data,
                [
                    "source_type",
                    "type",
                ],
            )

            if not source_type:
                source_type = "research"

            authors = self._normalize_authors(
                data.get("authors", [])
            )

            year = self._first_value(
                data,
                [
                    "publication_year",
                    "year",
                    "published_year",
                ],
            )

            year = self._safe_int(year)

            doi = self._first_value(
                data,
                [
                    "doi",
                ],
            )

            url = self._first_value(
                data,
                [
                    "url",
                    "landing_page_url",
                    "link",
                ],
            )

            abstract = self._first_value(
                data,
                [
                    "abstract",
                    "description",
                    "summary",
                ],
            )

            citation_count = self._first_value(
                data,
                [
                    "citation_count",
                    "cited_by_count",
                    "citations",
                ],
            )

            citation_count = self._safe_int(
                citation_count
            )

            open_access = self._safe_bool(
                self._first_value(
                    data,
                    [
                        "open_access",
                        "is_oa",
                    ],
                )
            )

            source_quality = self._safe_float(
                self._first_value(
                    data,
                    [
                        "source_quality",
                        "quality_score",
                    ]
                )
            )

            relevance_score = self._safe_float(
                self._first_value(
                    data,
                    [
                        "relevance_score",
                        "relevance",
                        "score",
                    ]
                )
            )

            normalized.append(
                create_source(
                    source_id=str(source_id),
                    provider=str(provider or ""),
                    title=str(title),
                    source_type=str(source_type),
                    url=str(url) if url else None,
                    doi=str(doi) if doi else None,
                    publication_year=year,
                    authors=authors,
                    abstract=(
                        str(abstract)
                        if abstract
                        else None
                    ),
                    citation_count=citation_count,
                    open_access=open_access,
                    source_quality=source_quality,
                    relevance_score=relevance_score,
                    metadata=data,
                )
            )

        return normalized

    # ========================================================
    # CLAIM CREATION
    # ========================================================

    def create_evidence_claim(
        self,
        *,
        text: str,
        category: str = "",
        sources: list[EvidenceSource] | None = None,
    ) -> EvidenceClaim:
        """
        Create a claim and evaluate its initial evidence state.

        Important:
            This is NOT a large language model fact checker.

        It only determines what the available evidence can
        reasonably support structurally. Later AURA verification
        agents can perform deeper semantic verification.
        """

        sources = sources or []

        claim_id = (
            f"claim-{uuid4().hex[:12]}"
        )

        if not text.strip():
            return create_claim(
                claim_id=claim_id,
                text="",
                category=category,
                status="needs_verification",
                confidence=0.0,
            )

        supporting: list[str] = []
        contradicting: list[str] = []

        claim_terms = self._keywords(text)

        for source in sources:
            source_text = " ".join(
                [
                    source.title or "",
                    source.abstract or "",
                ]
            )

            source_terms = self._keywords(
                source_text
            )

            overlap = self._keyword_overlap(
                claim_terms,
                source_terms,
            )

            if overlap >= 0.15:
                supporting.append(
                    source.source_id
                )

        confidence = self._calculate_confidence(
            sources=sources,
            supporting_source_ids=supporting,
        )

        if not supporting:
            status = "needs_verification"
        elif confidence >= 75:
            status = "verified"
        else:
            status = "ai_synthesis"

        reasoning = self._build_reasoning(
            status=status,
            supporting_count=len(supporting),
            contradicting_count=len(
                contradicting
            ),
            confidence=confidence,
        )

        return create_claim(
            claim_id=claim_id,
            text=text,
            category=category,
            status=status,
            confidence=confidence,
            supporting_source_ids=supporting,
            contradicting_source_ids=contradicting,
            reasoning=reasoning,
        )

    # ========================================================
    # EVIDENCE RECORD
    # ========================================================

    def build_evidence_record(
        self,
        claim: EvidenceClaim,
        sources: list[EvidenceSource],
    ) -> EvidenceRecord:
        """
        Build the complete provenance record for a claim.
        """

        source_map = {
            source.source_id: source
            for source in sources
        }

        supporting_sources = [
            source_map[source_id].title
            for source_id in claim.supporting_source_ids
            if source_id in source_map
        ]

        contradicting_sources = [
            source_map[source_id].title
            for source_id in claim.contradicting_source_ids
            if source_id in source_map
        ]

        notes: list[str] = []

        if supporting_sources:
            notes.append(
                f"{len(supporting_sources)} source(s) "
                "provide potentially supporting evidence."
            )

        if contradicting_sources:
            notes.append(
                f"{len(contradicting_sources)} source(s) "
                "contain potentially conflicting evidence."
            )

        if claim.status == "needs_verification":
            notes.append(
                "Available evidence is insufficient "
                "for verification."
            )

        if claim.status == "ai_synthesis":
            notes.append(
                "The claim is supported by multiple "
                "signals but should not be treated as "
                "directly verified fact."
            )

        if claim.status == "verified":
            notes.append(
                "The available evidence provides "
                "strong support, but source inspection "
                "remains recommended for high-stakes claims."
            )

        return EvidenceRecord(
            evidence_id=(
                f"evidence-{uuid4().hex[:12]}"
            ),
            claim_id=claim.claim_id,
            claim=claim.text,
            status=claim.status,
            confidence=clamp_confidence(
                claim.confidence
            ),
            sources=[
                source
                for source in sources
                if source.source_id
                in (
                    claim.supporting_source_ids
                    + claim.contradicting_source_ids
                )
            ],
            supporting_sources=(
                supporting_sources
            ),
            contradicting_sources=(
                contradicting_sources
            ),
            verification_notes=notes,
            reasoning=claim.reasoning,
            created_by="AURA Evidence Engine",
        )

    # ========================================================
    # COLLECTION
    # ========================================================

    def build_collection(
        self,
        *,
        project_id: str,
        query: str,
        sources: list[Any],
        claims: list[dict[str, Any]] | None = None,
    ) -> EvidenceCollection:
        """
        Build a complete evidence collection.

        This is the main entry point used by future AURA stages.
        """

        normalized_sources = (
            self.normalize_sources(
                sources
            )
        )

        evidence_claims: list[
            EvidenceClaim
        ] = []

        evidence_records: list[
            EvidenceRecord
        ] = []

        for claim_data in claims or []:
            claim_text = str(
                claim_data.get("text", "")
            ).strip()

            if not claim_text:
                continue

            claim = self.create_evidence_claim(
                text=claim_text,
                category=str(
                    claim_data.get(
                        "category",
                        "",
                    )
                ),
                sources=normalized_sources,
            )

            record = (
                self.build_evidence_record(
                    claim,
                    normalized_sources,
                )
            )

            evidence_claims.append(claim)
            evidence_records.append(record)

        verified = sum(
            1
            for claim in evidence_claims
            if claim.status == "verified"
        )

        synthesis = sum(
            1
            for claim in evidence_claims
            if claim.status == "ai_synthesis"
        )

        recommendations = sum(
            1
            for claim in evidence_claims
            if claim.status == "recommendation"
        )

        needs_verification = sum(
            1
            for claim in evidence_claims
            if claim.status
            == "needs_verification"
        )

        conflicts = sum(
            1
            for claim in evidence_claims
            if claim.status == "conflict"
        )

        if evidence_claims:
            overall_confidence = (
                sum(
                    claim.confidence
                    for claim in evidence_claims
                )
                / len(evidence_claims)
            )
        else:
            overall_confidence = 0.0

        return EvidenceCollection(
            project_id=project_id,
            query=query,
            sources=normalized_sources,
            claims=evidence_claims,
            evidence=evidence_records,
            verified_claims=verified,
            synthesis_claims=synthesis,
            recommendation_claims=recommendations,
            needs_verification=needs_verification,
            conflicts=conflicts,
            overall_confidence=clamp_confidence(
                overall_confidence
            ),
            metadata={
                "engine": "AURA Evidence Engine",
                "source_count": len(
                    normalized_sources
                ),
                "claim_count": len(
                    evidence_claims
                ),
            },
        )

    # ========================================================
    # CONFIDENCE
    # ========================================================

    def _calculate_confidence(
        self,
        *,
        sources: list[EvidenceSource],
        supporting_source_ids: list[str],
    ) -> float:
        """
        Calculate a preliminary confidence score.

        This is deliberately conservative.

        More sources alone do NOT automatically mean truth.
        Source quality and relevance influence the score.
        """

        supporting = [
            source
            for source in sources
            if source.source_id
            in supporting_source_ids
        ]

        if not supporting:
            return 0.0

        quality_scores = [
            max(
                source.source_quality,
                0.0,
            )
            for source in supporting
        ]

        relevance_scores = [
            max(
                source.relevance_score,
                0.0,
            )
            for source in supporting
        ]

        quality = (
            sum(quality_scores)
            / len(quality_scores)
            if quality_scores
            else 0.0
        )

        relevance = (
            sum(relevance_scores)
            / len(relevance_scores)
            if relevance_scores
            else 0.0
        )

        source_bonus = min(
            len(supporting) * 5.0,
            20.0,
        )

        confidence = (
            quality * 0.45
            + relevance * 0.40
            + source_bonus
        )

        return clamp_confidence(
            confidence
        )

    # ========================================================
    # REASONING
    # ========================================================

    def _build_reasoning(
        self,
        *,
        status: str,
        supporting_count: int,
        contradicting_count: int,
        confidence: float,
    ) -> str:
        """
        Produce transparent reasoning metadata.
        """

        if status == "verified":
            return (
                "The claim has strong supporting "
                f"evidence from {supporting_count} "
                "source(s), with a preliminary "
                f"confidence of {confidence:.1f}/100."
            )

        if status == "ai_synthesis":
            return (
                "The claim is supported by "
                f"{supporting_count} source signal(s), "
                "but the evidence is not strong enough "
                "for direct verification."
            )

        if status == "conflict":
            return (
                "Available sources contain conflicting "
                "signals. AURA must not merge them into "
                "a single unsupported conclusion."
            )

        return (
            "AURA does not currently have enough "
            "evidence to verify this claim."
        )

    # ========================================================
    # TEXT HELPERS
    # ========================================================

    def _keywords(
        self,
        text: str,
    ) -> set[str]:
        """
        Extract lightweight comparison terms.

        This is intentionally not presented as semantic
        verification. It is only a retrieval/evidence signal.
        """

        import re

        stop_words = {
            "the",
            "and",
            "for",
            "with",
            "from",
            "that",
            "this",
            "are",
            "was",
            "were",
            "has",
            "have",
            "into",
            "using",
            "used",
            "their",
            "they",
            "than",
            "which",
            "what",
            "where",
            "when",
            "how",
            "why",
            "can",
            "could",
            "should",
            "would",
            "about",
            "between",
            "through",
            "within",
            "based",
        }

        tokens = re.findall(
            r"[a-zA-Z0-9][a-zA-Z0-9_-]{2,}",
            text.lower(),
        )

        return {
            token
            for token in tokens
            if token not in stop_words
        }

    def _keyword_overlap(
        self,
        claim_terms: set[str],
        source_terms: set[str],
    ) -> float:
        """
        Calculate lightweight lexical overlap.
        """

        if not claim_terms:
            return 0.0

        return len(
            claim_terms & source_terms
        ) / len(claim_terms)

    # ========================================================
    # NORMALIZATION HELPERS
    # ========================================================

    def _to_dict(
        self,
        value: Any,
    ) -> dict[str, Any]:
        if hasattr(value, "model_dump"):
            dumped = value.model_dump()

            if isinstance(dumped, dict):
                return dumped

        if hasattr(value, "dict"):
            dumped = value.dict()

            if isinstance(dumped, dict):
                return dumped

        if isinstance(value, dict):
            return value.copy()

        return {
            "raw_value": value,
        }

    def _first_value(
        self,
        data: dict[str, Any],
        keys: list[str],
    ) -> Any:
        for key in keys:
            value = data.get(key)

            if value is not None and value != "":
                return value

        return None

    def _safe_int(
        self,
        value: Any,
    ) -> int | None:
        if value is None:
            return None

        try:
            return int(value)
        except (
            TypeError,
            ValueError,
        ):
            return None

    def _safe_float(
        self,
        value: Any,
    ) -> float:
        if value is None:
            return 0.0

        try:
            return clamp_confidence(
                float(value)
            )
        except (
            TypeError,
            ValueError,
        ):
            return 0.0

    def _safe_bool(
        self,
        value: Any,
    ) -> bool | None:
        if value is None:
            return None

        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            lowered = value.lower().strip()

            if lowered in {
                "true",
                "yes",
                "1",
            }:
                return True

            if lowered in {
                "false",
                "no",
                "0",
            }:
                return False

        return None

    def _normalize_authors(
        self,
        authors: Any,
    ) -> list[str]:
        if not authors:
            return []

        if isinstance(authors, str):
            return [authors]

        if not isinstance(authors, list):
            return []

        normalized: list[str] = []

        for author in authors:
            if isinstance(author, str):
                normalized.append(author)

            elif isinstance(author, dict):
                name = (
                    author.get("name")
                    or author.get("display_name")
                    or author.get("author_name")
                )

                if name:
                    normalized.append(
                        str(name)
                    )

        return normalized


# ============================================================
# GLOBAL AURA EVIDENCE ENGINE
# ============================================================

evidence_engine = EvidenceEngine()