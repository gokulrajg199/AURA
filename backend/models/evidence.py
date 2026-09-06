from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, ConfigDict


# ============================================================
# TYPES
# ============================================================

VerificationStatus = Literal[
    "metadata_retrieved",
    "abstract_available",
    "full_text_available",
    "directly_verified",
    "partially_verified",
    "unverified",
    "conflict",
    "failed",
]

EvidenceLevel = Literal[
    "source_metadata",
    "abstract",
    "full_text",
    "official_document",
    "dataset",
    "repository",
    "implementation",
    "experiment",
    "system_output",
    "expert_review",
]

ClaimStatus = Literal[
    "supported",
    "partially_supported",
    "unsupported",
    "unverified",
    "conflict",
]

EvidenceType = Literal[
    "paper",
    "preprint",
    "dataset",
    "github",
    "official_source",
    "standard",
    "patent",
    "technical_documentation",
    "project",
    "experiment",
    "system_output",
    "other",
]


# ============================================================
# HELPERS
# ============================================================

def utc_now() -> str:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def make_id(prefix: str) -> str:
    """Create a stable-looking runtime identifier."""
    return f"{prefix}-{uuid4().hex[:12].upper()}"


def clean_text(value: Any) -> str:
    """Safely convert a value to clean text."""
    if value is None:
        return ""

    if isinstance(value, str):
        return " ".join(value.split()).strip()

    return " ".join(str(value).split()).strip()


# ============================================================
# PROVENANCE
# ============================================================

class EvidenceProvenance(BaseModel):
    """
    Describes where an evidence record came from and what
    AURA actually retrieved.
    """

    model_config = ConfigDict(extra="allow")

    provider: str = ""
    provider_type: str = ""

    source_url: str = ""
    landing_url: str = ""
    api_url: str = ""

    retrieved_at: str = Field(default_factory=utc_now)

    retrieval_method: str = ""

    query: str = ""

    metadata_retrieved: bool = False
    abstract_retrieved: bool = False
    full_text_retrieved: bool = False

    source_identifier: str = ""
    doi: str = ""

    notes: list[str] = Field(default_factory=list)


# ============================================================
# EVIDENCE RECORD
# ============================================================

class EvidenceRecord(BaseModel):
    """
    Canonical evidence object used throughout AURA.

    Important:
    A retrieved paper is evidence that the source exists.
    It does NOT automatically verify every statement extracted
    or generated from that paper.
    """

    model_config = ConfigDict(extra="allow")

    evidence_id: str = Field(default_factory=lambda: make_id("EVID"))

    source: str = ""
    provider: str = ""

    evidence_type: str = "other"

    title: str = ""
    authors: list[str] = Field(default_factory=list)

    year: int | None = None

    doi: str = ""
    url: str = ""

    abstract: str = ""

    keywords: list[str] = Field(default_factory=list)

    methods: list[str] = Field(default_factory=list)
    datasets: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    models: list[str] = Field(default_factory=list)

    application_areas: list[str] = Field(default_factory=list)

    reported_findings: list[str] = Field(default_factory=list)
    reported_limitations: list[str] = Field(default_factory=list)

    evidence_type_detail: str = ""

    verification_status: str = "metadata_retrieved"

    verification_scope: list[str] = Field(default_factory=list)

    evidence_level: str = "source_metadata"

    relevance_score: float = 0.0

    source_quality_score: float = 0.0

    evidence_strength: float = 0.0

    claim_ids: list[str] = Field(default_factory=list)

    provenance: EvidenceProvenance = Field(
        default_factory=EvidenceProvenance
    )

    extraction_notes: list[str] = Field(default_factory=list)

    limitations_of_evidence: list[str] = Field(default_factory=list)

    conflicts_with: list[str] = Field(default_factory=list)

    created_at: str = Field(default_factory=utc_now)


# ============================================================
# CLAIM
# ============================================================

class ClaimEvidenceLink(BaseModel):
    """
    Explicit relationship between a claim and evidence.
    """

    model_config = ConfigDict(extra="allow")

    evidence_id: str

    support_type: Literal[
        "supports",
        "partially_supports",
        "contradicts",
        "context_only",
        "insufficient",
    ] = "context_only"

    strength: float = 0.0

    rationale: str = ""

    verification_scope: str = ""

    source_excerpt_available: bool = False

    created_at: str = Field(default_factory=utc_now)


class ClaimRecord(BaseModel):
    """
    Canonical research claim.

    Claims are deliberately separated from evidence so that
    AURA can distinguish:
        source → evidence → claim → synthesis → decision
    """

    model_config = ConfigDict(extra="allow")

    claim_id: str = Field(default_factory=lambda: make_id("CLAIM"))

    statement: str = ""

    claim_type: str = "research"

    source_question: str = ""

    status: str = "unverified"

    evidence_ids: list[str] = Field(default_factory=list)

    evidence_links: list[ClaimEvidenceLink] = Field(
        default_factory=list
    )

    supporting_evidence_count: int = 0
    contradicting_evidence_count: int = 0

    evidence_coverage: float = 0.0

    evidence_strength: float = 0.0

    confidence: float = 0.0

    rationale: str = ""

    uncertainties: list[str] = Field(default_factory=list)

    conflicts: list[str] = Field(default_factory=list)

    verification_scope: list[str] = Field(default_factory=list)

    created_at: str = Field(default_factory=utc_now)


# ============================================================
# FINDING
# ============================================================

class FindingRecord(BaseModel):
    """
    AURA synthesis derived from one or more claims/evidence
    records.

    A finding is NOT automatically a verified fact.
    """

    model_config = ConfigDict(extra="allow")

    finding_id: str = Field(default_factory=lambda: make_id("FIND"))

    statement: str = ""

    finding_type: str = "synthesis"

    claim_ids: list[str] = Field(default_factory=list)

    evidence_ids: list[str] = Field(default_factory=list)

    status: Literal[
        "verified",
        "synthesized",
        "recommended",
        "unverified",
        "conflict",
    ] = "synthesized"

    confidence: float = 0.0

    reasoning: str = ""

    implications: list[str] = Field(default_factory=list)

    uncertainties: list[str] = Field(default_factory=list)

    created_at: str = Field(default_factory=utc_now)


# ============================================================
# EVIDENCE REGISTRY
# ============================================================

class EvidenceRegistry(BaseModel):
    """
    Project-level evidence registry.

    This is the object later agents can consume instead of
    repeatedly interpreting raw paper dictionaries.
    """

    model_config = ConfigDict(extra="allow")

    registry_id: str = Field(
        default_factory=lambda: make_id("REG")
    )

    created_at: str = Field(default_factory=utc_now)

    updated_at: str = Field(default_factory=utc_now)

    evidence: list[EvidenceRecord] = Field(
        default_factory=list
    )

    claims: list[ClaimRecord] = Field(
        default_factory=list
    )

    findings: list[FindingRecord] = Field(
        default_factory=list
    )

    source_count: int = 0

    claim_count: int = 0

    finding_count: int = 0

    verified_evidence_count: int = 0

    unverified_evidence_count: int = 0

    conflict_count: int = 0

    claim_coverage: float = 0.0

    average_evidence_strength: float = 0.0

    verification_scope: list[str] = Field(
        default_factory=list
    )

    warnings: list[str] = Field(
        default_factory=list
    )


# ============================================================
# FACTORY FUNCTIONS
# ============================================================

def evidence_from_dict(
    data: dict[str, Any],
    *,
    evidence_id: str | None = None,
) -> EvidenceRecord:
    """
    Convert an existing search result into a canonical
    EvidenceRecord without throwing away unknown fields.
    """

    raw = dict(data or {})

    identifier = (
        evidence_id
        or clean_text(
            raw.get("evidence_id")
            or raw.get("paper_id")
            or raw.get("work_id")
            or raw.get("openalex_id")
            or raw.get("id")
        )
        or make_id("EVID")
    )

    provider = clean_text(
        raw.get("provider")
        or raw.get("source")
        or raw.get("database")
    )

    title = clean_text(
        raw.get("title")
        or raw.get("paper_title")
    )

    authors_raw = raw.get("authors", [])

    if isinstance(authors_raw, str):
        authors = [clean_text(authors_raw)]
    elif isinstance(authors_raw, list):
        authors = []

        for author in authors_raw:
            if isinstance(author, dict):
                name = (
                    author.get("name")
                    or author.get("author")
                    or author.get("display_name")
                )
                if name:
                    authors.append(clean_text(name))
            else:
                text = clean_text(author)
                if text:
                    authors.append(text)
    else:
        authors = []

    year = raw.get("year") or raw.get("publication_year")

    try:
        if year is not None:
            year = int(year)
    except (TypeError, ValueError):
        year = None

    evidence_type = clean_text(
        raw.get("evidence_type")
        or raw.get("source_type")
        or "paper"
    )

    verification_status = clean_text(
        raw.get("verification_status")
        or "metadata_retrieved"
    )

    evidence_level = clean_text(
        raw.get("evidence_level")
        or "source_metadata"
    )

    url = clean_text(
        raw.get("url")
        or raw.get("landing_url")
        or raw.get("source_url")
    )

    doi = clean_text(raw.get("doi"))

    abstract = clean_text(
        raw.get("abstract")
        or raw.get("summary")
    )

    provenance = EvidenceProvenance(
        provider=provider,
        provider_type=clean_text(
            raw.get("provider_type")
            or raw.get("source_type")
        ),
        source_url=url,
        landing_url=clean_text(raw.get("landing_url")),
        api_url=clean_text(raw.get("api_url")),
        retrieval_method=clean_text(
            raw.get("retrieval_method")
            or "official_api"
        ),
        query=clean_text(raw.get("query")),
        metadata_retrieved=True,
        abstract_retrieved=bool(abstract),
        full_text_retrieved=bool(
            raw.get("full_text")
            or raw.get("fulltext")
        ),
        source_identifier=identifier,
        doi=doi,
    )

    verification_scope = raw.get(
        "verification_scope",
        [],
    )

    if isinstance(verification_scope, str):
        verification_scope = [verification_scope]

    if not verification_scope:
        verification_scope = ["metadata"]

        if abstract:
            verification_scope.append("abstract")

        if provenance.full_text_retrieved:
            verification_scope.append("full_text")

    relevance = raw.get(
        "relevance_score",
        raw.get("relevance", 0.0),
    )

    source_quality = raw.get(
        "source_quality_score",
        raw.get("quality_score", 0.0),
    )

    strength = raw.get(
        "evidence_strength",
        0.0,
    )

    def numeric(value: Any) -> float:
        try:
            return max(0.0, min(100.0, float(value)))
        except (TypeError, ValueError):
            return 0.0

    record = EvidenceRecord(
        **{
            **raw,
            "evidence_id": identifier,
            "source": provider,
            "provider": provider,
            "evidence_type": evidence_type,
            "title": title,
            "authors": authors,
            "year": year,
            "doi": doi,
            "url": url,
            "abstract": abstract,
            "verification_status": verification_status,
            "verification_scope": verification_scope,
            "evidence_level": evidence_level,
            "relevance_score": numeric(relevance),
            "source_quality_score": numeric(source_quality),
            "evidence_strength": numeric(strength),
            "provenance": provenance,
            "created_at": raw.get(
                "created_at",
                utc_now(),
            ),
        }
    )

    return record


def claim_from_dict(
    data: dict[str, Any],
    *,
    claim_id: str | None = None,
) -> ClaimRecord:
    """
    Normalize an existing claim dictionary.
    """

    raw = dict(data or {})

    identifier = (
        claim_id
        or clean_text(raw.get("claim_id"))
        or make_id("CLAIM")
    )

    evidence_ids = []

    raw_ids = raw.get("evidence_ids", [])

    if isinstance(raw_ids, str):
        raw_ids = [raw_ids]

    if isinstance(raw_ids, list):
        for item in raw_ids:
            if isinstance(item, dict):
                value = (
                    item.get("evidence_id")
                    or item.get("id")
                )
            else:
                value = item

            value = clean_text(value)

            if value and value not in evidence_ids:
                evidence_ids.append(value)

    return ClaimRecord(
        **{
            **raw,
            "claim_id": identifier,
            "statement": clean_text(
                raw.get("statement")
                or raw.get("claim")
            ),
            "evidence_ids": evidence_ids,
            "created_at": raw.get(
                "created_at",
                utc_now(),
            ),
        }
    )


# ============================================================
# REGISTRY OPERATIONS
# ============================================================

def add_evidence_record(
    registry: EvidenceRegistry,
    evidence: EvidenceRecord,
) -> EvidenceRegistry:
    """Add evidence while preventing duplicate evidence IDs."""

    existing_ids = {
        item.evidence_id
        for item in registry.evidence
    }

    if evidence.evidence_id not in existing_ids:
        registry.evidence.append(evidence)

    _refresh_registry(registry)

    return registry


def add_claim_record(
    registry: EvidenceRegistry,
    claim: ClaimRecord,
) -> EvidenceRegistry:
    """Add a claim while preventing duplicate claim IDs."""

    existing_ids = {
        item.claim_id
        for item in registry.claims
    }

    if claim.claim_id not in existing_ids:
        registry.claims.append(claim)

    _refresh_registry(registry)

    return registry


def add_finding_record(
    registry: EvidenceRegistry,
    finding: FindingRecord,
) -> EvidenceRegistry:
    """Add a synthesized finding."""

    existing_ids = {
        item.finding_id
        for item in registry.findings
    }

    if finding.finding_id not in existing_ids:
        registry.findings.append(finding)

    _refresh_registry(registry)

    return registry


def link_claim_to_evidence(
    registry: EvidenceRegistry,
    claim_id: str,
    evidence_id: str,
    *,
    support_type: str = "supports",
    strength: float = 0.0,
    rationale: str = "",
    verification_scope: str = "",
) -> bool:
    """
    Create an explicit claim → evidence relationship.
    """

    claim = next(
        (
            item
            for item in registry.claims
            if item.claim_id == claim_id
        ),
        None,
    )

    evidence = next(
        (
            item
            for item in registry.evidence
            if item.evidence_id == evidence_id
        ),
        None,
    )

    if claim is None or evidence is None:
        return False

    if evidence_id not in claim.evidence_ids:
        claim.evidence_ids.append(evidence_id)

    existing_link = next(
        (
            item
            for item in claim.evidence_links
            if item.evidence_id == evidence_id
        ),
        None,
    )

    if existing_link is None:
        claim.evidence_links.append(
            ClaimEvidenceLink(
                evidence_id=evidence_id,
                support_type=support_type,
                strength=max(
                    0.0,
                    min(100.0, float(strength)),
                ),
                rationale=rationale,
                verification_scope=verification_scope,
                source_excerpt_available=bool(
                    evidence.abstract
                ),
            )
        )

    if claim_id not in evidence.claim_ids:
        evidence.claim_ids.append(claim_id)

    _refresh_claim(claim, registry)

    _refresh_registry(registry)

    return True


# ============================================================
# REFRESH / ANALYSIS
# ============================================================

def _refresh_claim(
    claim: ClaimRecord,
    registry: EvidenceRegistry,
) -> None:
    """Recalculate claim support from explicit links."""

    links = claim.evidence_links

    supporting = [
        item
        for item in links
        if item.support_type == "supports"
    ]

    partial = [
        item
        for item in links
        if item.support_type == "partially_supports"
    ]

    contradicting = [
        item
        for item in links
        if item.support_type == "contradicts"
    ]

    claim.supporting_evidence_count = (
        len(supporting) + len(partial)
    )

    claim.contradicting_evidence_count = len(
        contradicting
    )

    if links:
        claim.evidence_coverage = round(
            min(
                100.0,
                (
                    claim.supporting_evidence_count
                    / len(links)
                )
                * 100.0,
            ),
            2,
        )

        claim.evidence_strength = round(
            sum(
                link.strength
                for link in links
            )
            / len(links),
            2,
        )

    if contradicting:
        claim.status = "conflict"

    elif claim.supporting_evidence_count == 0:
        claim.status = "unverified"

    elif partial and not supporting:
        claim.status = "partially_supported"

    else:
        claim.status = "supported"

    claim.confidence = round(
        (
            claim.evidence_strength * 0.6
            + claim.evidence_coverage * 0.4
        ),
        2,
    )


def _refresh_registry(
    registry: EvidenceRegistry,
) -> None:
    """Refresh project-level evidence statistics."""

    for claim in registry.claims:
        _refresh_claim(
            claim,
            registry,
        )

    registry.source_count = len(
        registry.evidence
    )

    registry.claim_count = len(
        registry.claims
    )

    registry.finding_count = len(
        registry.findings
    )

    registry.verified_evidence_count = sum(
        1
        for item in registry.evidence
        if item.verification_status
        in {
            "directly_verified",
            "full_text_available",
            "abstract_available",
        }
    )

    registry.unverified_evidence_count = sum(
        1
        for item in registry.evidence
        if item.verification_status
        in {
            "unverified",
            "failed",
        }
    )

    registry.conflict_count = sum(
        1
        for item in registry.claims
        if item.status == "conflict"
    )

    if registry.claims:
        registry.claim_coverage = round(
            sum(
                1
                for claim in registry.claims
                if claim.evidence_ids
            )
            / len(registry.claims)
            * 100.0,
            2,
        )

        registry.average_evidence_strength = round(
            sum(
                claim.evidence_strength
                for claim in registry.claims
            )
            / len(registry.claims),
            2,
        )
    else:
        registry.claim_coverage = 0.0
        registry.average_evidence_strength = 0.0

    registry.updated_at = utc_now()


# ============================================================
# SERIALIZATION
# ============================================================

def registry_to_dict(
    registry: EvidenceRegistry,
) -> dict[str, Any]:
    """Return a JSON-compatible registry."""

    _refresh_registry(registry)

    return registry.model_dump(
        mode="json"
    )


def evidence_to_dict(
    evidence: EvidenceRecord,
) -> dict[str, Any]:
    """Return a JSON-compatible evidence record."""

    return evidence.model_dump(
        mode="json"
    )


def claim_to_dict(
    claim: ClaimRecord,
) -> dict[str, Any]:
    """Return a JSON-compatible claim."""

    return claim.model_dump(
        mode="json"
    )


# ============================================================
# LOOKUP HELPERS
# ============================================================

def get_evidence_by_id(
    registry: EvidenceRegistry,
    evidence_id: str,
) -> EvidenceRecord | None:
    return next(
        (
            item
            for item in registry.evidence
            if item.evidence_id == evidence_id
        ),
        None,
    )


def get_claim_by_id(
    registry: EvidenceRegistry,
    claim_id: str,
) -> ClaimRecord | None:
    return next(
        (
            item
            for item in registry.claims
            if item.claim_id == claim_id
        ),
        None,
    )


def get_evidence_for_claim(
    registry: EvidenceRegistry,
    claim_id: str,
) -> list[EvidenceRecord]:
    claim = get_claim_by_id(
        registry,
        claim_id,
    )

    if claim is None:
        return []

    evidence_map = {
        item.evidence_id: item
        for item in registry.evidence
    }

    return [
        evidence_map[evidence_id]
        for evidence_id in claim.evidence_ids
        if evidence_id in evidence_map
    ]


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "VerificationStatus",
    "EvidenceLevel",
    "ClaimStatus",
    "EvidenceType",
    "EvidenceProvenance",
    "EvidenceRecord",
    "ClaimEvidenceLink",
    "ClaimRecord",
    "FindingRecord",
    "EvidenceRegistry",
    "evidence_from_dict",
    "claim_from_dict",
    "add_evidence_record",
    "add_claim_record",
    "add_finding_record",
    "link_claim_to_evidence",
    "registry_to_dict",
    "evidence_to_dict",
    "claim_to_dict",
    "get_evidence_by_id",
    "get_claim_by_id",
    "get_evidence_for_claim",
]