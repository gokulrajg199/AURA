from __future__ import annotations

from typing import Any
import re

from models.project import AURAProject
from models.evidence import (
    EvidenceRegistry,
    evidence_from_dict,
    claim_from_dict,
    add_evidence_record,
    add_claim_record,
    link_claim_to_evidence,
    registry_to_dict,
)
from orchestration.contract import AURAStageResult
from orchestration.stages import AURAStage

from services.literature.search import search_literature


class InvestigationAgent:
    """
    AURA Investigation Agent
    =========================

    Stage 02 transforms Stage 01 understanding into a
    traceable multi-source research evidence base.

    Pipeline:

        IDEA
          ↓
        STAGE 01 UNDERSTANDING
          ↓
        INVESTIGATION STRATEGY
          ↓
        MULTI-SOURCE DISCOVERY
          ↓
        SOURCE NORMALIZATION
          ↓
        CANONICAL EVIDENCE
          ↓
        CLAIM REGISTER
          ↓
        CLAIM ↔ EVIDENCE LINKING
          ↓
        VERIFICATION BOUNDARIES
          ↓
        STAGE 03 ANALYSIS

    IMPORTANT:

    AURA distinguishes:

        source existence
        metadata retrieval
        abstract availability
        candidate relevance
        candidate claim support
        evidence synthesis
        scientific verification

    Retrieval or lexical similarity NEVER becomes scientific truth.
    """

    stage = AURAStage.INVESTIGATE

    DEFAULT_YEAR_FROM = 2022
    DEFAULT_YEAR_TO = 2026
    DEFAULT_MAX_RESULTS = 20

    MAX_KEYWORDS = 12
    MAX_DOMAINS = 6
    MAX_RESEARCH_QUESTIONS = 12
    MAX_EVIDENCE_RECORDS = 50
    MAX_CLAIM_CANDIDATES = 40
    MAX_EVIDENCE_PER_CLAIM = 12

    MIN_TOKEN_OVERLAP = 0.18
    STRONG_TOKEN_OVERLAP = 0.35

    # ============================================================
    # MAIN RUN
    # ============================================================

    async def run(
        self,
        project: AURAProject,
    ) -> AURAStageResult:

        idea = self._clean_text(
            project.original_idea
        )

        if not idea:
            return AURAStageResult(
                stage=self.stage,
                success=False,
                message="Cannot investigate an empty project idea.",
            )

        # --------------------------------------------------------
        # STAGE 01 UNDERSTANDING
        # --------------------------------------------------------

        understanding = self._get_understanding(
            project
        )

        investigation_plan = self._build_investigation_plan(
            project,
            understanding,
        )

        query = investigation_plan["primary_query"]

        year_from = self.DEFAULT_YEAR_FROM
        year_to = self.DEFAULT_YEAR_TO
        max_results = self.DEFAULT_MAX_RESULTS

        # --------------------------------------------------------
        # MULTI-SOURCE LITERATURE DISCOVERY
        # --------------------------------------------------------

        try:
            literature = await search_literature(
                query=query,
                year_from=year_from,
                year_to=year_to,
                max_results=max_results,
            )

        except Exception as error:
            return AURAStageResult(
                stage=self.stage,
                success=False,
                message=(
                    "Literature investigation failed: "
                    f"{error}"
                ),
            )

        literature_data = self._normalize_result(
            literature
        )

        # --------------------------------------------------------
        # RAW → LEGACY EVIDENCE RECORDS
        # --------------------------------------------------------

        legacy_evidence_records = (
            self._build_evidence_records(
                literature_data=literature_data,
                query=query,
            )
        )

        # --------------------------------------------------------
        # CANONICAL SHARED EVIDENCE REGISTRY
        # --------------------------------------------------------

        evidence_registry = (
            self._build_canonical_evidence_registry(
                literature_data=literature_data,
                legacy_records=legacy_evidence_records,
                query=query,
            )
        )

        # --------------------------------------------------------
        # CLAIM REGISTER
        # --------------------------------------------------------

        claim_register = self._build_claim_register(
            project=project,
            understanding=understanding,
        )

        claim_candidates = claim_register

        # --------------------------------------------------------
        # CLAIM → EVIDENCE MAPPING
        # --------------------------------------------------------

        claim_evidence_map = self._map_claims_to_evidence(
            claim_register=claim_register,
            evidence_records=legacy_evidence_records,
        )

        # --------------------------------------------------------
        # ENRICH LEGACY CLAIM REGISTER
        # --------------------------------------------------------

        self._enrich_claim_register(
            claim_register=claim_register,
            claim_evidence_map=claim_evidence_map,
        )

        # --------------------------------------------------------
        # LINK CANONICAL CLAIMS TO CANONICAL EVIDENCE
        # --------------------------------------------------------

        self._link_canonical_claims(
            registry=evidence_registry,
            claim_register=claim_register,
            claim_evidence_map=claim_evidence_map,
        )

        # --------------------------------------------------------
        # VERIFICATION SUMMARY
        # --------------------------------------------------------

        verification_summary = (
            self._build_verification_summary(
                literature_data=literature_data,
                evidence_records=legacy_evidence_records,
                claim_register=claim_register,
                claim_evidence_map=claim_evidence_map,
            )
        )

        # --------------------------------------------------------
        # EVIDENCE SUMMARY
        # --------------------------------------------------------

        evidence_summary = self._build_evidence_summary(
            literature_data=literature_data,
            query=query,
            year_from=year_from,
            year_to=year_to,
            evidence_records=legacy_evidence_records,
            verification_summary=verification_summary,
        )

        provider_summary = self._build_provider_summary(
            literature_data
        )

        retrieval_summary = self._build_retrieval_summary(
            literature_data
        )

        source_registry = literature_data.get(
            "source_registry",
            {},
        )

        if not isinstance(
            source_registry,
            dict,
        ):
            source_registry = {}

        # --------------------------------------------------------
        # CANONICAL REGISTRY SUMMARY
        # --------------------------------------------------------

        canonical_registry_data = registry_to_dict(
            evidence_registry
        )

        canonical_claim_count = len(
            evidence_registry.claims
        )

        canonical_evidence_count = len(
            evidence_registry.evidence
        )

        canonical_claim_coverage = (
            evidence_registry.claim_coverage
        )

        # --------------------------------------------------------
        # INVESTIGATION RECORD
        # --------------------------------------------------------

        investigation_record = {
            "status": "completed",

            "query": query,

            "year_from": year_from,

            "year_to": year_to,

            "max_results": max_results,

            "investigation_mode": (
                "evidence_driven_multi_source"
            ),

            "evidence_mode": (
                "canonical_shared_evidence_layer"
            ),

            "investigation_plan": investigation_plan,

            "source_policy": {
                "scholarly_sources": True,
                "official_apis_only": True,
                "unauthorized_scraping": False,
                "google_scholar_scraping": False,
                "ieee_full_text_scraping": False,
                "claim_verification_from_metadata": False,
                "scientific_truth_from_keyword_match": False,
            },

            "evidence_summary": evidence_summary,

            "provider_summary": provider_summary,

            "retrieval_summary": retrieval_summary,

            "verification_summary": verification_summary,

            "claim_register": claim_register,

            "claim_candidates": claim_candidates,

            "claim_evidence_map": claim_evidence_map,

            "source_registry": source_registry,

            # ----------------------------------------------------
            # CANONICAL EVIDENCE LAYER
            # ----------------------------------------------------

            "canonical_evidence_layer": {
                "registry_id": (
                    evidence_registry.registry_id
                ),

                "evidence_count": (
                    canonical_evidence_count
                ),

                "claim_count": (
                    canonical_claim_count
                ),

                "finding_count": len(
                    evidence_registry.findings
                ),

                "claim_coverage": (
                    canonical_claim_coverage
                ),

                "average_evidence_strength": (
                    evidence_registry.average_evidence_strength
                ),

                "verified_evidence_count": (
                    evidence_registry.verified_evidence_count
                ),

                "unverified_evidence_count": (
                    evidence_registry.unverified_evidence_count
                ),

                "conflict_count": (
                    evidence_registry.conflict_count
                ),

                "verification_scope": [
                    "source provenance",
                    "metadata retrieval",
                    "abstract availability",
                    "candidate claim relevance",
                    "claim-to-evidence relationships",
                ],

                "scientific_verification_completed": False,

                "scientific_truth_claim": False,

                "registry": canonical_registry_data,
            },
        }

        # --------------------------------------------------------
        # STORE COMPLETE RESEARCH PACKAGE
        # --------------------------------------------------------

        project.research = literature_data

        project.research["investigation"] = (
            investigation_record
        )

        # Existing compatibility structure.
        project.research["evidence_records"] = (
            legacy_evidence_records
        )

        project.research["claim_register"] = (
            claim_register
        )

        project.research["claim_candidates"] = (
            claim_candidates
        )

        project.research["claim_evidence_map"] = (
            claim_evidence_map
        )

        project.research["verification_summary"] = (
            verification_summary
        )

        # --------------------------------------------------------
        # CANONICAL EVIDENCE REGISTRY
        # --------------------------------------------------------

        project.research["evidence_registry"] = (
            canonical_registry_data
        )

        project.research["canonical_evidence"] = (
            canonical_registry_data.get(
                "evidence",
                [],
            )
        )

        project.research["canonical_claims"] = (
            canonical_registry_data.get(
                "claims",
                [],
            )
        )

        project.research["canonical_findings"] = (
            canonical_registry_data.get(
                "findings",
                [],
            )
        )

        # --------------------------------------------------------
        # PROJECT EVIDENCE
        # --------------------------------------------------------

        self._append_project_evidence(
            project,
            legacy_evidence_records,
        )

        # --------------------------------------------------------
        # PROJECT MEMORY
        # --------------------------------------------------------

        self._append_memory(
            project,
            {
                "type": "investigation",

                "stage": (
                    self.stage.value
                    if hasattr(
                        self.stage,
                        "value",
                    )
                    else str(self.stage)
                ),

                "query": query,

                "years": (
                    f"{year_from}-{year_to}"
                ),

                "papers_discovered": (
                    evidence_summary[
                        "papers_discovered"
                    ]
                ),

                "providers_attempted": (
                    evidence_summary[
                        "providers_attempted"
                    ]
                ),

                "providers_successful": (
                    evidence_summary[
                        "providers_successful"
                    ]
                ),

                "evidence_records": len(
                    legacy_evidence_records
                ),

                "canonical_evidence_records": (
                    canonical_evidence_count
                ),

                "claim_register": len(
                    claim_register
                ),

                "claims_with_evidence": (
                    verification_summary[
                        "claims_with_evidence"
                    ]
                ),

                "claims_without_evidence": (
                    verification_summary[
                        "claims_without_evidence"
                    ]
                ),

                "claim_coverage": (
                    canonical_claim_coverage
                ),

                "verification_status": (
                    verification_summary[
                        "overall_status"
                    ]
                ),

                "scientific_verification_completed": False,

                "timestamp_note": (
                    "Investigation completed during "
                    "current AURA run."
                ),
            },
        )

        # --------------------------------------------------------
        # FINAL RESULT
        # --------------------------------------------------------

        return AURAStageResult(
            stage=self.stage,

            success=True,

            message=(
                "AURA completed evidence-driven "
                "multi-source investigation, created "
                "canonical evidence records, built a "
                "research claim register, linked claims "
                "to retrieved evidence using explicit "
                "candidate/context relationships, "
                "preserved provenance, and established "
                "verification boundaries for downstream "
                "research analysis."
            ),

            data={
                "query": query,

                "year_from": year_from,

                "year_to": year_to,

                "literature": literature_data,

                "investigation": investigation_record,

                "investigation_plan": investigation_plan,

                "evidence_summary": evidence_summary,

                "provider_summary": provider_summary,

                "retrieval_summary": retrieval_summary,

                "verification_summary": verification_summary,

                "evidence_records": legacy_evidence_records,

                "claim_register": claim_register,

                "claim_candidates": claim_candidates,

                "claim_evidence_map": claim_evidence_map,

                # NEW
                "evidence_registry": canonical_registry_data,

                "canonical_evidence": (
                    canonical_registry_data.get(
                        "evidence",
                        [],
                    )
                ),

                "canonical_claims": (
                    canonical_registry_data.get(
                        "claims",
                        [],
                    )
                ),

                "canonical_findings": (
                    canonical_registry_data.get(
                        "findings",
                        [],
                    )
                ),

                "evidence_layer_summary": {
                    "evidence_count": (
                        canonical_evidence_count
                    ),

                    "claim_count": (
                        canonical_claim_count
                    ),

                    "claim_coverage": (
                        canonical_claim_coverage
                    ),

                    "average_evidence_strength": (
                        evidence_registry
                        .average_evidence_strength
                    ),

                    "verified_evidence_count": (
                        evidence_registry
                        .verified_evidence_count
                    ),

                    "unverified_evidence_count": (
                        evidence_registry
                        .unverified_evidence_count
                    ),

                    "conflict_count": (
                        evidence_registry
                        .conflict_count
                    ),

                    "scientific_verification": False,
                },
            },

            next_stage=AURAStage.ANALYZE,
        )

    # ============================================================
    # STAGE 01 UNDERSTANDING
    # ============================================================

    def _get_understanding(
        self,
        project: AURAProject,
    ) -> dict[str, Any]:

        analysis = project.analysis

        if not isinstance(
            analysis,
            dict,
        ):
            return {}

        understanding = analysis.get(
            "problem_understanding",
            {},
        )

        if not isinstance(
            understanding,
            dict,
        ):
            return {}

        return understanding

    # ============================================================
    # INVESTIGATION PLAN
    # ============================================================

    def _build_investigation_plan(
        self,
        project: AURAProject,
        understanding: dict[str, Any],
    ) -> dict[str, Any]:

        idea = self._clean_text(
            project.original_idea
        )

        normalized_title = self._clean_text(
            understanding.get(
                "normalized_title"
            )
        )

        keywords = self._clean_list(
            understanding.get(
                "keywords",
                [],
            )
        )

        domains = self._clean_list(
            project.domain
        )

        if not domains:
            domains = self._clean_list(
                understanding.get(
                    "domains",
                    [],
                )
            )

        research_questions = self._clean_list(
            understanding.get(
                "research_questions",
                [],
            )
        )

        target_context = self._clean_text(
            understanding.get(
                "target_context"
            )
        )

        problem_definition = self._clean_text(
            understanding.get(
                "problem_definition"
            )
        )

        investigation_focus = self._clean_list(
            understanding.get(
                "investigation_focus",
                [],
            )
        )

        query_parts: list[str] = []

        self._add_unique(
            query_parts,
            normalized_title,
        )

        if not query_parts:
            self._add_unique(
                query_parts,
                idea,
            )

        self._add_unique(
            query_parts,
            target_context,
        )

        for keyword in keywords[
            : self.MAX_KEYWORDS
        ]:
            self._add_unique(
                query_parts,
                keyword,
            )

        for domain in domains[
            : self.MAX_DOMAINS
        ]:
            self._add_unique(
                query_parts,
                domain,
            )

        if (
            problem_definition
            and len(query_parts) < 10
        ):
            self._add_unique(
                query_parts,
                problem_definition,
            )

        primary_query = " ".join(
            query_parts
        ).strip()

        if not primary_query:
            primary_query = idea

        focused_queries: list[str] = []

        for question in research_questions[
            : self.MAX_RESEARCH_QUESTIONS
        ]:
            self._add_unique(
                focused_queries,
                question,
            )

        search_dimensions = [
            "existing approaches",
            "methods",
            "technologies",
            "datasets",
            "models",
            "limitations",
            "challenges",
            "research gaps",
            "recent trends",
            "validation",
            "deployment",
            "real-world feasibility",
        ]

        return {
            "primary_query": primary_query,

            "focused_queries": focused_queries,

            "keywords": keywords[
                : self.MAX_KEYWORDS
            ],

            "domains": domains[
                : self.MAX_DOMAINS
            ],

            "research_questions": research_questions[
                : self.MAX_RESEARCH_QUESTIONS
            ],

            "investigation_focus": (
                investigation_focus
            ),

            "search_dimensions": (
                search_dimensions
            ),

            "target_context": (
                target_context
            ),

            "problem_definition": (
                problem_definition
            ),

            "research_window": {
                "from": self.DEFAULT_YEAR_FROM,
                "to": self.DEFAULT_YEAR_TO,
            },

            "source_strategy": [
                "OpenAlex",
                "Crossref",
                "Semantic Scholar",
                "PubMed",
                "arXiv",
                "IEEE Xplore",
            ],

            "source_policy": (
                "Official/public APIs and legitimate "
                "scholarly access routes only."
            ),
        }

    # ============================================================
    # RESULT NORMALIZATION
    # ============================================================

    def _normalize_result(
        self,
        result: Any,
    ) -> dict[str, Any]:

        if hasattr(
            result,
            "model_dump",
        ):
            data = result.model_dump()

        elif isinstance(
            result,
            dict,
        ):
            data = result.copy()

        else:
            data = {
                "raw_result": result,
            }

        if not isinstance(
            data,
            dict,
        ):
            data = {
                "raw_result": data,
            }

        if not isinstance(
            data.get("papers"),
            list,
        ):
            data["papers"] = []

        if not isinstance(
            data.get("stats"),
            dict,
        ):
            data["stats"] = {}

        if not isinstance(
            data.get("provider_stats"),
            list,
        ):
            data["provider_stats"] = []

        if not isinstance(
            data.get("source_registry"),
            dict,
        ):
            data["source_registry"] = {}

        if not isinstance(
            data.get("evidence_layer"),
            dict,
        ):
            data["evidence_layer"] = {}

        if not isinstance(
            data.get("ranking"),
            dict,
        ):
            data["ranking"] = {}

        return data

    # ============================================================
    # LEGACY EVIDENCE RECORDS
    # ============================================================

    def _build_evidence_records(
        self,
        literature_data: dict[str, Any],
        query: str,
    ) -> list[dict[str, Any]]:

        papers = literature_data.get(
            "papers",
            [],
        )

        if not isinstance(
            papers,
            list,
        ):
            return []

        records: list[dict[str, Any]] = []

        for index, paper in enumerate(
            papers[
                : self.MAX_EVIDENCE_RECORDS
            ],
            start=1,
        ):

            if not isinstance(
                paper,
                dict,
            ):
                continue

            title = self._first_value(
                paper,
                [
                    "title",
                    "paper_title",
                ],
            )

            if not title:
                continue

            provider = self._first_value(
                paper,
                [
                    "provider",
                    "source",
                ],
                default="Unknown",
            )

            providers = paper.get(
                "providers",
                [],
            )

            if not isinstance(
                providers,
                list,
            ):
                providers = [
                    provider
                ]

            providers = [
                str(item)
                for item in providers
                if item
            ]

            ranking = paper.get(
                "ranking",
                {},
            )

            if not isinstance(
                ranking,
                dict,
            ):
                ranking = {}

            evidence = paper.get(
                "evidence",
                {},
            )

            if not isinstance(
                evidence,
                dict,
            ):
                evidence = {}

            raw_metadata = paper.get(
                "raw_metadata",
                {},
            )

            if not isinstance(
                raw_metadata,
                dict,
            ):
                raw_metadata = {}

            abstract = self._clean_text(
                paper.get(
                    "abstract"
                )
            )

            topics = self._clean_list(
                paper.get(
                    "topics",
                    [],
                )
            )

            authors = paper.get(
                "authors",
                [],
            )

            if not isinstance(
                authors,
                list,
            ):
                authors = []

            external_ids = paper.get(
                "external_ids",
                {},
            )

            if not isinstance(
                external_ids,
                dict,
            ):
                external_ids = {}

            evidence_id = (
                f"INV-{index:03d}"
            )

            record = {
                "evidence_id": evidence_id,

                "type": "literature_record",

                "stage": "INVESTIGATE",

                "title": str(title),

                "abstract_available": bool(
                    abstract
                ),

                "abstract": abstract,

                "provider": str(
                    provider
                ),

                "providers": providers,

                "provider_count": len(
                    providers
                ),

                "publication_year": (
                    paper.get(
                        "publication_year"
                    )
                ),

                "authors": authors,

                "journal": paper.get(
                    "journal",
                    "",
                ),

                "doi": paper.get(
                    "doi",
                    "",
                ),

                "url": paper.get(
                    "url",
                    "",
                ),

                "external_ids": external_ids,

                "topics": topics,

                "citation_count": (
                    paper.get(
                        "citation_count",
                        0,
                    )
                ),

                "query": query,

                "source_type": paper.get(
                    "source_type",
                    "",
                ),

                "retrieval_mode": paper.get(
                    "retrieval_mode",
                    "",
                ),

                "open_access": (
                    raw_metadata.get(
                        "is_oa"
                    )
                    is True
                    or bool(
                        raw_metadata.get(
                            "open_access_pdf"
                        )
                    )
                ),

                "metadata_verified": (
                    evidence.get(
                        "metadata_verified",
                        False,
                    )
                    is True
                ),

                "claim_verified": False,

                "verification_status": (
                    evidence.get(
                        "verification_status",
                        "metadata_retrieved",
                    )
                ),

                "relevance_score": (
                    ranking.get(
                        "relevance_score"
                    )
                ),

                "source_quality_score": (
                    ranking.get(
                        "source_quality_score"
                    )
                ),

                "source_quality_percent": (
                    ranking.get(
                        "source_quality_percent"
                    )
                ),

                "final_retrieval_score": (
                    ranking.get(
                        "final_score"
                    )
                ),

                "evidence_level": (
                    "source_metadata"
                ),

                "scientific_verification": False,

                "verification_note": (
                    "This record establishes that "
                    "bibliographic/source information "
                    "was retrieved from an identified "
                    "provider. Retrieval does not "
                    "automatically verify every scientific "
                    "claim contained in the source."
                ),
            }

            records.append(
                record
            )

        return records

    # ============================================================
    # CANONICAL EVIDENCE REGISTRY
    # ============================================================

    def _build_canonical_evidence_registry(
        self,
        literature_data: dict[str, Any],
        legacy_records: list[dict[str, Any]],
        query: str,
    ) -> EvidenceRegistry:

        registry = EvidenceRegistry()

        papers = literature_data.get(
            "papers",
            [],
        )

        if not isinstance(
            papers,
            list,
        ):
            papers = []

        for index, paper in enumerate(
            papers[
                : self.MAX_EVIDENCE_RECORDS
            ],
            start=1,
        ):

            if not isinstance(
                paper,
                dict,
            ):
                continue

            raw = dict(
                paper
            )

            legacy = (
                legacy_records[index - 1]
                if index - 1
                < len(legacy_records)
                else {}
            )

            evidence_id = legacy.get(
                "evidence_id"
            )

            raw["evidence_id"] = (
                evidence_id
                or raw.get(
                    "evidence_id"
                )
                or f"INV-{index:03d}"
            )

            raw["query"] = query

            raw["provider"] = (
                raw.get(
                    "provider"
                )
                or raw.get(
                    "source"
                )
            )

            raw["abstract"] = (
                raw.get(
                    "abstract"
                )
                or legacy.get(
                    "abstract",
                    "",
                )
            )

            raw["url"] = (
                raw.get(
                    "url"
                )
                or legacy.get(
                    "url",
                    "",
                )
            )

            raw["doi"] = (
                raw.get(
                    "doi"
                )
                or legacy.get(
                    "doi",
                    "",
                )
            )

            raw["verification_status"] = (
                legacy.get(
                    "verification_status",
                    "metadata_retrieved",
                )
            )

            raw["evidence_level"] = (
                legacy.get(
                    "evidence_level",
                    "source_metadata",
                )
            )

            raw["relevance_score"] = (
                legacy.get(
                    "relevance_score"
                )
                or 0.0
            )

            raw["source_quality_score"] = (
                legacy.get(
                    "source_quality_score"
                )
                or 0.0
            )

            raw["scientific_verification"] = False

            raw["verification_scope"] = [
                "bibliographic metadata",
                "source provenance",
            ]

            if raw.get("abstract"):
                raw["verification_scope"].append(
                    "abstract availability"
                )

            canonical = evidence_from_dict(
                raw,
                evidence_id=raw[
                    "evidence_id"
                ],
            )

            # ----------------------------------------------------
            # Explicit safety boundary:
            # metadata/abstract retrieval is NOT scientific
            # verification.
            # ----------------------------------------------------

            canonical.verification_status = (
                "abstract_available"
                if canonical.abstract
                else "metadata_retrieved"
            )

            canonical.evidence_level = (
                "abstract"
                if canonical.abstract
                else "source_metadata"
            )

            canonical.extraction_notes.append(
                "Retrieved through AURA's legitimate "
                "multi-source literature discovery layer."
            )

            canonical.limitations_of_evidence.append(
                "Scientific claims have not been independently "
                "verified at this stage."
            )

            add_evidence_record(
                registry,
                canonical,
            )

        registry.verification_scope = [
            "bibliographic provenance",
            "metadata retrieval",
            "abstract availability",
            "source identification",
            "candidate relevance",
        ]

        registry.warnings.append(
            "Canonical evidence records represent "
            "retrieved source evidence. They do not "
            "automatically verify scientific claims."
        )

        registry.warnings.append(
            "Claim/evidence relationships created during "
            "Stage 02 represent candidate contextual "
            "relevance and require downstream analysis."
        )

        return registry

    # ============================================================
    # CLAIM REGISTER
    # ============================================================

    def _build_claim_register(
        self,
        project: AURAProject,
        understanding: dict[str, Any],
    ) -> list[dict[str, Any]]:

        claims: list[dict[str, Any]] = []

        research_questions = self._extract_text_list(
            understanding.get(
                "research_questions",
                [],
            )
        )

        objectives = self._extract_text_list(
            understanding.get(
                "objectives",
                [],
            )
        )

        investigation_focus = self._extract_text_list(
            understanding.get(
                "investigation_focus",
                [],
            )
        )

        for question in research_questions[
            : self.MAX_RESEARCH_QUESTIONS
        ]:

            if len(claims) >= self.MAX_CLAIM_CANDIDATES:
                break

            claims.append(
                self._make_claim(
                    project=project,
                    claim_type="research_question",
                    text=question,
                    source_stage="UNDERSTAND",
                )
            )

        for objective in objectives:

            if len(claims) >= self.MAX_CLAIM_CANDIDATES:
                break

            claims.append(
                self._make_claim(
                    project=project,
                    claim_type="project_objective",
                    text=objective,
                    source_stage="UNDERSTAND",
                )
            )

        for focus in investigation_focus:

            if len(claims) >= self.MAX_CLAIM_CANDIDATES:
                break

            claims.append(
                self._make_claim(
                    project=project,
                    claim_type="investigation_focus",
                    text=focus,
                    source_stage="UNDERSTAND",
                )
            )

        if not claims:

            problem_definition = self._clean_text(
                understanding.get(
                    "problem_definition"
                )
            )

            if problem_definition:

                claims.append(
                    self._make_claim(
                        project=project,
                        claim_type="problem_definition",
                        text=problem_definition,
                        source_stage="UNDERSTAND",
                    )
                )

        for index, claim in enumerate(
            claims,
            start=1,
        ):
            claim["claim_id"] = (
                f"CLM-{index:03d}"
            )

        return claims

    def _make_claim(
        self,
        project: AURAProject,
        claim_type: str,
        text: str,
        source_stage: str,
    ) -> dict[str, Any]:

        cleaned = self._clean_text(
            text
        )

        return {
            "claim_id": "",

            "project_id": (
                project.project_id
            ),

            "type": claim_type,

            "text": cleaned,

            "source_stage": source_stage,

            "status": "candidate",

            "verification_status": (
                "needs_evidence_analysis"
            ),

            "evidence_required": True,

            "metadata_proof": False,

            "scientific_verification": False,

            "candidate_support": False,

            "evidence_supported": False,

            "primary_source_verification_required": True,

            "supporting_evidence_ids": [],

            "supporting_sources": [],

            "support_count": 0,

            "evidence_coverage": 0.0,

            "confidence": "unverified",

            "note": (
                "This claim was derived from Stage 01 "
                "understanding. Candidate evidence can "
                "support relevance, but scientific "
                "verification requires downstream "
                "analysis and appropriate primary-source "
                "inspection."
            ),
        }

    # ============================================================
    # CLAIM → EVIDENCE MAPPING
    # ============================================================

    def _map_claims_to_evidence(
        self,
        claim_register: list[dict[str, Any]],
        evidence_records: list[dict[str, Any]],
    ) -> dict[str, Any]:

        mappings: list[dict[str, Any]] = []

        for claim in claim_register:

            claim_id = claim.get(
                "claim_id"
            )

            claim_text = self._clean_text(
                claim.get(
                    "text"
                )
            )

            claim_tokens = self._tokenize(
                claim_text
            )

            candidates: list[dict[str, Any]] = []

            for evidence in evidence_records:

                evidence_id = evidence.get(
                    "evidence_id"
                )

                title = self._clean_text(
                    evidence.get(
                        "title"
                    )
                )

                abstract = self._clean_text(
                    evidence.get(
                        "abstract"
                    )
                )

                topics = self._clean_list(
                    evidence.get(
                        "topics",
                        [],
                    )
                )

                evidence_text = " ".join(
                    [
                        title,
                        abstract,
                        " ".join(topics),
                    ]
                )

                evidence_tokens = self._tokenize(
                    evidence_text
                )

                if not claim_tokens:
                    continue

                overlap = (
                    len(
                        claim_tokens
                        & evidence_tokens
                    )
                    / max(
                        len(claim_tokens),
                        1,
                    )
                )

                title_tokens = self._tokenize(
                    title
                )

                abstract_tokens = self._tokenize(
                    abstract
                )

                title_overlap = (
                    len(
                        claim_tokens
                        & title_tokens
                    )
                    / max(
                        len(claim_tokens),
                        1,
                    )
                )

                abstract_overlap = (
                    len(
                        claim_tokens
                        & abstract_tokens
                    )
                    / max(
                        len(claim_tokens),
                        1,
                    )
                )

                topic_tokens = self._tokenize(
                    " ".join(topics)
                )

                topic_overlap = (
                    len(
                        claim_tokens
                        & topic_tokens
                    )
                    / max(
                        len(claim_tokens),
                        1,
                    )
                )

                phrase_bonus = (
                    self._phrase_similarity(
                        claim_text,
                        evidence_text,
                    )
                )

                relevance = (
                    overlap * 0.35
                    + title_overlap * 0.25
                    + abstract_overlap * 0.25
                    + topic_overlap * 0.10
                    + phrase_bonus * 0.05
                )

                if relevance < self.MIN_TOKEN_OVERLAP:
                    continue

                candidates.append(
                    {
                        "evidence_id": evidence_id,

                        "title": title,

                        "provider": evidence.get(
                            "provider",
                            "Unknown",
                        ),

                        "providers": evidence.get(
                            "providers",
                            [],
                        ),

                        "publication_year": evidence.get(
                            "publication_year"
                        ),

                        "relevance_score": round(
                            relevance,
                            4,
                        ),

                        "token_overlap": round(
                            overlap,
                            4,
                        ),

                        "title_overlap": round(
                            title_overlap,
                            4,
                        ),

                        "abstract_overlap": round(
                            abstract_overlap,
                            4,
                        ),

                        "topic_overlap": round(
                            topic_overlap,
                            4,
                        ),

                        "phrase_similarity": round(
                            phrase_bonus,
                            4,
                        ),

                        "abstract_available": bool(
                            abstract
                        ),

                        "evidence_verification_status": (
                            evidence.get(
                                "verification_status",
                                "metadata_retrieved",
                            )
                        ),

                        "scientific_verification": False,

                        "relationship_type": (
                            "context_only"
                        ),
                    }
                )

            candidates.sort(
                key=lambda item: (
                    item.get(
                        "relevance_score",
                        0,
                    ),
                    item.get(
                        "abstract_overlap",
                        0,
                    ),
                    item.get(
                        "title_overlap",
                        0,
                    ),
                ),
                reverse=True,
            )

            selected = candidates[
                : self.MAX_EVIDENCE_PER_CLAIM
            ]

            supporting_ids = [
                str(
                    item["evidence_id"]
                )
                for item in selected
            ]

            providers: list[str] = []

            for item in selected:

                provider = self._clean_text(
                    item.get(
                        "provider"
                    )
                )

                if provider:
                    providers.append(
                        provider
                    )

                item_providers = item.get(
                    "providers",
                    [],
                )

                if isinstance(
                    item_providers,
                    list,
                ):

                    for provider_name in item_providers:

                        provider_name = (
                            self._clean_text(
                                provider_name
                            )
                        )

                        if provider_name:
                            providers.append(
                                provider_name
                            )

            providers = list(
                dict.fromkeys(
                    providers
                )
            )

            support_count = len(
                selected
            )

            if support_count == 0:

                relationship_status = (
                    "no_direct_match"
                )

                verification_status = (
                    "not_supported_by_retrieved_corpus"
                )

            else:

                relationship_status = (
                    "candidate_support"
                )

                strong_candidate = any(
                    item.get(
                        "relevance_score",
                        0,
                    )
                    >= self.STRONG_TOKEN_OVERLAP
                    and item.get(
                        "abstract_available"
                    )
                    for item in selected
                )

                if strong_candidate:

                    verification_status = (
                        "candidate_supported_requires_primary_source_verification"
                    )

                else:

                    verification_status = (
                        "candidate_support_metadata_or_abstract_level"
                    )

            evidence_coverage = min(
                1.0,
                support_count / 3.0,
            )

            mappings.append(
                {
                    "claim_id": claim_id,

                    "candidate_supporting_evidence": (
                        supporting_ids
                    ),

                    "supporting_evidence": selected,

                    "supporting_sources": providers,

                    "support_count": support_count,

                    "evidence_coverage": round(
                        evidence_coverage,
                        3,
                    ),

                    "relationship_status": (
                        relationship_status
                    ),

                    "verification_status": (
                        verification_status
                    ),

                    "scientific_verification": False,

                    "primary_source_verification_required": (
                        support_count > 0
                    ),

                    "relationship_semantics": (
                        "context_only_candidate_relevance"
                    ),

                    "method": (
                        "conservative multi-signal "
                        "lexical, title, abstract and "
                        "topic relevance matching"
                    ),

                    "note": (
                        "Matching establishes candidate "
                        "relevance/context only. It does "
                        "not establish scientific truth "
                        "or verified claim support."
                    ),
                }
            )

        return {
            "mappings": mappings,

            "method": (
                "conservative multi-signal "
                "claim/evidence matching"
            ),

            "verification_required": True,

            "scientific_verification_completed": False,

            "relationship_semantics": (
                "candidate_contextual_relevance"
            ),
        }

    # ============================================================
    # CANONICAL CLAIM LINKING
    # ============================================================

    def _link_canonical_claims(
        self,
        registry: EvidenceRegistry,
        claim_register: list[dict[str, Any]],
        claim_evidence_map: dict[str, Any],
    ) -> None:

        # --------------------------------------------------------
        # Add canonical claims.
        # --------------------------------------------------------

        for raw_claim in claim_register:

            claim = claim_from_dict(
                {
                    "claim_id": raw_claim.get(
                        "claim_id"
                    ),
                    "statement": raw_claim.get(
                        "text"
                    ),
                    "claim_type": raw_claim.get(
                        "type",
                        "research",
                    ),
                    "source_question": raw_claim.get(
                        "text"
                    ),
                    "status": "unverified",
                    "evidence_ids": [],
                    "verification_scope": [
                        "retrieved corpus",
                        "candidate relevance",
                    ],
                    "rationale": (
                        "Claim originated from Stage 01 "
                        "and has not yet undergone "
                        "scientific verification."
                    ),
                    "confidence": 0.0,
                },
                claim_id=raw_claim.get(
                    "claim_id"
                ),
            )

            add_claim_record(
                registry,
                claim,
            )

        # --------------------------------------------------------
        # Create explicit claim ↔ evidence links.
        #
        # CRITICAL:
        # Candidate lexical relevance is CONTEXT ONLY.
        # It must not mark the claim scientifically supported.
        # --------------------------------------------------------

        mappings = claim_evidence_map.get(
            "mappings",
            [],
        )

        if not isinstance(
            mappings,
            list,
        ):
            return

        for mapping in mappings:

            if not isinstance(
                mapping,
                dict,
            ):
                continue

            claim_id = self._clean_text(
                mapping.get(
                    "claim_id"
                )
            )

            if not claim_id:
                continue

            supporting = mapping.get(
                "supporting_evidence",
                [],
            )

            if not isinstance(
                supporting,
                list,
            ):
                supporting = []

            for item in supporting:

                if not isinstance(
                    item,
                    dict,
                ):
                    continue

                evidence_id = self._clean_text(
                    item.get(
                        "evidence_id"
                    )
                )

                if not evidence_id:
                    continue

                relevance = item.get(
                    "relevance_score",
                    0.0,
                )

                try:
                    strength = min(
                        100.0,
                        max(
                            0.0,
                            float(
                                relevance
                            ) * 100.0,
                        ),
                    )
                except (
                    TypeError,
                    ValueError,
                ):
                    strength = 0.0

                link_claim_to_evidence(
                    registry=registry,
                    claim_id=claim_id,
                    evidence_id=evidence_id,

                    # ------------------------------------------------
                    # IMPORTANT:
                    # Do NOT use "supports" here.
                    #
                    # "context_only" means:
                    # the source is potentially relevant to the
                    # claim, but AURA has not verified the claim.
                    # ------------------------------------------------

                    support_type="context_only",

                    strength=strength,

                    rationale=(
                        "Candidate relevance identified "
                        "through title, abstract, topic and "
                        "lexical overlap. This relationship "
                        "provides contextual evidence only "
                        "and does not verify the scientific "
                        "claim."
                    ),

                    verification_scope=(
                        "retrieved metadata/abstract; "
                        "candidate contextual relevance"
                    ),
                )

        # --------------------------------------------------------
        # Explicitly keep canonical claims unverified.
        # --------------------------------------------------------

        for claim in registry.claims:

            claim.status = "unverified"

            claim.verification_scope = list(
                dict.fromkeys(
                    [
                        *claim.verification_scope,
                        "scientific verification pending",
                    ]
                )
            )

            claim.rationale = (
                "Stage 02 identified candidate contextual "
                "relationships. Scientific verification "
                "requires downstream evidence analysis, "
                "primary-source inspection where necessary, "
                "and appropriate validation."
            )

    # ============================================================
    # CLAIM ENRICHMENT
    # ============================================================

    def _enrich_claim_register(
        self,
        claim_register: list[dict[str, Any]],
        claim_evidence_map: dict[str, Any],
    ) -> None:

        mappings = claim_evidence_map.get(
            "mappings",
            [],
        )

        mapping_by_id = {
            str(
                mapping.get(
                    "claim_id"
                )
            ): mapping
            for mapping in mappings
            if isinstance(
                mapping,
                dict,
            )
        }

        for claim in claim_register:

            claim_id = str(
                claim.get(
                    "claim_id",
                    "",
                )
            )

            mapping = mapping_by_id.get(
                claim_id
            )

            if not mapping:
                continue

            support_count = self._safe_int(
                mapping.get(
                    "support_count"
                )
            )

            evidence_coverage = float(
                mapping.get(
                    "evidence_coverage",
                    0.0,
                )
                or 0.0
            )

            claim[
                "supporting_evidence_ids"
            ] = mapping.get(
                "candidate_supporting_evidence",
                [],
            )

            claim[
                "supporting_sources"
            ] = mapping.get(
                "supporting_sources",
                [],
            )

            claim[
                "support_count"
            ] = support_count

            claim[
                "evidence_coverage"
            ] = evidence_coverage

            claim[
                "candidate_support"
            ] = support_count > 0

            # ----------------------------------------------------
            # Compatibility field.
            #
            # This indicates candidate evidence exists.
            # It does NOT mean scientific verification.
            # ----------------------------------------------------

            claim[
                "evidence_supported"
            ] = False

            claim[
                "candidate_evidence_available"
            ] = support_count > 0

            claim[
                "primary_source_verification_required"
            ] = support_count > 0

            claim[
                "scientific_verification"
            ] = False

            if support_count == 0:

                claim[
                    "verification_status"
                ] = (
                    "not_supported_by_retrieved_corpus"
                )

                claim[
                    "confidence"
                ] = "unverified"

            elif any(
                item.get(
                    "relevance_score",
                    0,
                )
                >= self.STRONG_TOKEN_OVERLAP
                and item.get(
                    "abstract_available"
                )
                for item in mapping.get(
                    "supporting_evidence",
                    [],
                )
                if isinstance(
                    item,
                    dict,
                )
            ):

                claim[
                    "verification_status"
                ] = (
                    "candidate_supported_requires_primary_source_verification"
                )

                claim[
                    "confidence"
                ] = (
                    "moderate_candidate_support"
                )

            else:

                claim[
                    "verification_status"
                ] = (
                    "candidate_support_metadata_or_abstract_level"
                )

                claim[
                    "confidence"
                ] = (
                    "low_to_moderate_candidate_support"
                )

            claim[
                "note"
            ] = (
                "Candidate evidence was identified, but "
                "the claim remains scientifically unverified. "
                "Stage 03 must analyze the retrieved evidence "
                "before any research conclusion is treated "
                "as supported."
            )

    # ============================================================
    # VERIFICATION SUMMARY
    # ============================================================

    def _build_verification_summary(
        self,
        literature_data: dict[str, Any],
        evidence_records: list[dict[str, Any]],
        claim_register: list[dict[str, Any]],
        claim_evidence_map: dict[str, Any],
    ) -> dict[str, Any]:

        metadata_verified = sum(
            1
            for record in evidence_records
            if record.get(
                "metadata_verified"
            )
        )

        multi_source = sum(
            1
            for record in evidence_records
            if record.get(
                "provider_count",
                0,
            )
            > 1
        )

        abstract_available = sum(
            1
            for record in evidence_records
            if record.get(
                "abstract_available"
            )
        )

        open_access = sum(
            1
            for record in evidence_records
            if record.get(
                "open_access"
            )
        )

        mappings = claim_evidence_map.get(
            "mappings",
            [],
        )

        claims_with_evidence = sum(
            1
            for mapping in mappings
            if self._safe_int(
                mapping.get(
                    "support_count"
                )
            )
            > 0
        )

        claims_without_evidence = max(
            0,
            len(claim_register)
            - claims_with_evidence,
        )

        claims_with_strong_candidate_support = sum(
            1
            for mapping in mappings
            if any(
                item.get(
                    "relevance_score",
                    0,
                )
                >= self.STRONG_TOKEN_OVERLAP
                for item in mapping.get(
                    "supporting_evidence",
                    []
                )
                if isinstance(
                    item,
                    dict,
                )
            )
        )

        coverage_ratio = (
            claims_with_evidence
            / len(claim_register)
            if claim_register
            else 0.0
        )

        if not evidence_records:

            overall_status = (
                "insufficient_evidence"
            )

        elif (
            claim_register
            and claims_with_evidence == 0
        ):

            overall_status = (
                "provenance_verified_claim_support_insufficient"
            )

        elif (
            claim_register
            and claims_without_evidence > 0
        ):

            overall_status = (
                "partial_claim_evidence_coverage"
            )

        elif (
            metadata_verified
            == len(evidence_records)
        ):

            overall_status = (
                "metadata_provenance_verified_candidate_claim_support"
            )

        else:

            overall_status = (
                "partial_metadata_verification"
            )

        return {
            "overall_status": overall_status,

            "evidence_records": len(
                evidence_records
            ),

            "metadata_verified_records": (
                metadata_verified
            ),

            "multi_source_records": (
                multi_source
            ),

            "abstract_available_records": (
                abstract_available
            ),

            "open_access_records": (
                open_access
            ),

            "claim_candidates": len(
                claim_register
            ),

            "claim_register_count": len(
                claim_register
            ),

            "claims_with_evidence": (
                claims_with_evidence
            ),

            "claims_without_evidence": (
                claims_without_evidence
            ),

            "claims_with_strong_candidate_support": (
                claims_with_strong_candidate_support
            ),

            "claim_evidence_coverage_ratio": round(
                coverage_ratio,
                3,
            ),

            "scientific_claims_verified": 0,

            "scientific_verification_completed": (
                False
            ),

            "candidate_relationships_are_not_verified": True,

            "verification_boundary": (
                "Stage 02 establishes source provenance, "
                "retrieval availability and candidate "
                "claim/evidence relationships. It does "
                "not establish scientific truth."
            ),

            "confidence_policy": (
                "Retrieval relevance, citation count, "
                "metadata confidence and lexical "
                "similarity must never be converted "
                "directly into scientific truth."
            ),

            "evidence_policy": (
                "Every candidate-supported claim retains "
                "its supporting evidence IDs and source "
                "providers, while scientific verification "
                "remains false until downstream analysis."
            ),
        }

    # ============================================================
    # EVIDENCE SUMMARY
    # ============================================================

    def _build_evidence_summary(
        self,
        literature_data: dict[str, Any],
        query: str,
        year_from: int,
        year_to: int,
        evidence_records: list[dict[str, Any]],
        verification_summary: dict[str, Any],
    ) -> dict[str, Any]:

        provider_stats = literature_data.get(
            "provider_stats",
            [],
        )

        stats = literature_data.get(
            "stats",
            {},
        )

        successful = 0
        attempted = 0
        failed = 0
        not_configured = 0

        if not isinstance(
            provider_stats,
            list,
        ):
            provider_stats = []

        for provider in provider_stats:

            if not isinstance(
                provider,
                dict,
            ):
                continue

            attempted += 1

            status = str(
                provider.get(
                    "status",
                    "",
                )
            ).lower()

            if status == "success":
                successful += 1

            elif status == "failed":
                failed += 1

            elif status == "not_configured":
                not_configured += 1

        papers = literature_data.get(
            "papers",
            [],
        )

        if not isinstance(
            papers,
            list,
        ):
            papers = []

        return {
            "investigation_status": (
                "completed"
            ),

            "query": query,

            "research_window": {
                "from": year_from,
                "to": year_to,
            },

            "papers_discovered": len(
                papers
            ),

            "evidence_records": len(
                evidence_records
            ),

            "providers_attempted": (
                attempted
            ),

            "providers_successful": (
                successful
            ),

            "providers_failed": (
                failed
            ),

            "providers_not_configured": (
                not_configured
            ),

            "open_access_count": (
                self._safe_int(
                    stats.get(
                        "open_access_count"
                    )
                )
            ),

            "highly_cited_count": (
                self._safe_int(
                    stats.get(
                        "highly_cited_count"
                    )
                )
            ),

            "duplicates_removed": (
                self._safe_int(
                    stats.get(
                        "duplicates_removed"
                    )
                )
            ),

            "metadata_verified_count": (
                verification_summary[
                    "metadata_verified_records"
                ]
            ),

            "multi_source_records": (
                verification_summary[
                    "multi_source_records"
                ]
            ),

            "claims_with_evidence": (
                verification_summary[
                    "claims_with_evidence"
                ]
            ),

            "claims_without_evidence": (
                verification_summary[
                    "claims_without_evidence"
                ]
            ),

            "claim_evidence_coverage_ratio": (
                verification_summary[
                    "claim_evidence_coverage_ratio"
                ]
            ),

            "scientific_claims_verified": 0,

            "evidence_collection": (
                "Multi-source scholarly and "
                "technical metadata collection "
                "completed."
            ),

            "verification_scope": (
                "Source provenance, metadata, "
                "abstract availability and "
                "candidate claim/evidence relationships "
                "are recorded."
            ),

            "scientific_verification": False,
        }

    # ============================================================
    # PROVIDER SUMMARY
    # ============================================================

    def _build_provider_summary(
        self,
        literature_data: dict[str, Any],
    ) -> list[dict[str, Any]]:

        provider_stats = literature_data.get(
            "provider_stats",
            [],
        )

        summary: list[dict[str, Any]] = []

        if not isinstance(
            provider_stats,
            list,
        ):
            return summary

        for provider in provider_stats:

            if not isinstance(
                provider,
                dict,
            ):
                continue

            summary.append(
                {
                    "provider": str(
                        provider.get(
                            "provider",
                            "Unknown",
                        )
                    ),

                    "status": str(
                        provider.get(
                            "status",
                            "unknown",
                        )
                    ),

                    "count": self._safe_int(
                        provider.get(
                            "count"
                        )
                    ),

                    "retrieval_mode": str(
                        provider.get(
                            "retrieval_mode",
                            "unknown",
                        )
                    ),

                    "message": provider.get(
                        "message"
                    ),

                    "error": provider.get(
                        "error"
                    ),
                }
            )

        return summary

    # ============================================================
    # RETRIEVAL SUMMARY
    # ============================================================

    def _build_retrieval_summary(
        self,
        literature_data: dict[str, Any],
    ) -> dict[str, Any]:

        stats = literature_data.get(
            "stats",
            {},
        )

        if not isinstance(
            stats,
            dict,
        ):
            stats = {}

        ranking = literature_data.get(
            "ranking",
            {},
        )

        if not isinstance(
            ranking,
            dict,
        ):
            ranking = {}

        ranking_weights = ranking.get(
            "weights",
            {},
        )

        retrieval_modes = literature_data.get(
            "retrieval_modes",
            [],
        )

        source_registry = literature_data.get(
            "source_registry",
            {},
        )

        if not isinstance(
            source_registry,
            dict,
        ):
            source_registry = {}

        return {
            "raw_results": self._safe_int(
                stats.get(
                    "raw_results"
                )
            ),

            "unique_results": self._safe_int(
                stats.get(
                    "unique_results"
                )
            ),

            "returned_results": self._safe_int(
                stats.get(
                    "returned_results"
                )
            ),

            "duplicates_removed": (
                self._safe_int(
                    stats.get(
                        "duplicates_removed"
                    )
                )
            ),

            "retrieval_duration_seconds": (
                stats.get(
                    "retrieval_duration_seconds"
                )
            ),

            "retrieval_modes": (
                retrieval_modes
                if isinstance(
                    retrieval_modes,
                    list,
                )
                else []
            ),

            "ranking_weights": (
                ranking_weights
                if isinstance(
                    ranking_weights,
                    dict,
                )
                else {}
            ),

            "source_registry_count": len(
                source_registry
            ),

            "ranking_transparency": (
                "Retrieval ranking is an AURA "
                "discovery-priority signal. It is "
                "not a scientific truth score or "
                "official impact-factor measure."
            ),
        }

    # ============================================================
    # PROJECT EVIDENCE
    # ============================================================

    def _append_project_evidence(
        self,
        project: AURAProject,
        evidence_records: list[dict[str, Any]],
    ) -> None:

        if not isinstance(
            project.evidence,
            list,
        ):
            project.evidence = []

        existing_ids = {
            str(
                item.get(
                    "evidence_id"
                )
            )
            for item in project.evidence
            if isinstance(
                item,
                dict,
            )
        }

        for record in evidence_records:

            evidence_id = str(
                record.get(
                    "evidence_id"
                )
            )

            if evidence_id in existing_ids:
                continue

            project.evidence.append(
                record
            )

            existing_ids.add(
                evidence_id
            )

    # ============================================================
    # PROJECT MEMORY
    # ============================================================

    def _append_memory(
        self,
        project: AURAProject,
        record: dict[str, Any],
    ) -> None:

        if not isinstance(
            project.memory,
            list,
        ):
            project.memory = []

        project.memory.append(
            record
        )

    # ============================================================
    # TOKENIZATION
    # ============================================================

    @staticmethod
    def _tokenize(
        text: str,
    ) -> set[str]:

        words = re.findall(
            r"[a-zA-Z0-9]+",
            text.lower(),
        )

        stopwords = {
            "the",
            "and",
            "for",
            "with",
            "from",
            "this",
            "that",
            "into",
            "using",
            "based",
            "are",
            "was",
            "were",
            "have",
            "has",
            "been",
            "can",
            "may",
            "new",
            "study",
            "research",
            "system",
            "model",
            "method",
            "methods",
            "approach",
            "approaches",
            "use",
            "used",
            "develop",
            "development",
            "analysis",
            "analyze",
            "investigate",
            "investigation",
            "project",
            "data",
        }

        return {
            word
            for word in words
            if len(word) > 2
            and word not in stopwords
        }

    # ============================================================
    # PHRASE SIMILARITY
    # ============================================================

    def _phrase_similarity(
        self,
        claim: str,
        evidence: str,
    ) -> float:

        claim_words = re.findall(
            r"[a-zA-Z0-9]+",
            claim.lower(),
        )

        evidence_tokens = self._tokenize(
            evidence
        )

        if len(claim_words) < 2:
            return 0.0

        matched_pairs = 0

        total_pairs = max(
            len(claim_words) - 1,
            1,
        )

        for index in range(
            len(claim_words) - 1
        ):

            first = claim_words[
                index
            ]

            second = claim_words[
                index + 1
            ]

            if (
                first in evidence_tokens
                and second in evidence_tokens
            ):
                matched_pairs += 1

        return min(
            1.0,
            matched_pairs
            / total_pairs,
        )

    # ============================================================
    # TEXT LIST EXTRACTION
    # ============================================================

    @classmethod
    def _extract_text_list(
        cls,
        value: Any,
    ) -> list[str]:

        if value is None:
            return []

        if isinstance(
            value,
            str,
        ):

            cleaned = cls._clean_text(
                value
            )

            return (
                [cleaned]
                if cleaned
                else []
            )

        if isinstance(
            value,
            dict,
        ):

            for key in (
                "text",
                "value",
                "question",
                "title",
                "name",
                "description",
            ):

                if key in value:

                    extracted = (
                        cls._extract_text_list(
                            value.get(
                                key
                            )
                        )
                    )

                    if extracted:
                        return extracted

            return []

        if isinstance(
            value,
            (
                list,
                tuple,
                set,
            ),
        ):

            result: list[str] = []

            for item in value:

                result.extend(
                    cls._extract_text_list(
                        item
                    )
                )

            return list(
                dict.fromkeys(
                    result
                )
            )

        cleaned = cls._clean_text(
            value
        )

        return (
            [cleaned]
            if cleaned
            else []
        )

    # ============================================================
    # LIST CLEANING
    # ============================================================

    @staticmethod
    def _clean_list(
        value: Any,
    ) -> list[str]:

        if not isinstance(
            value,
            list,
        ):
            return []

        cleaned: list[str] = []

        for item in value:

            if item is None:
                continue

            if isinstance(
                item,
                dict,
            ):
                text = (
                    item.get(
                        "name"
                    )
                    or item.get(
                        "title"
                    )
                    or item.get(
                        "text"
                    )
                    or item.get(
                        "value"
                    )
                )

                if text is None:
                    continue

                text = " ".join(
                    str(text).strip().split()
                )

            else:
                text = " ".join(
                    str(item).strip().split()
                )

            if text:
                cleaned.append(
                    text
                )

        return list(
            dict.fromkeys(
                cleaned
            )
        )

    # ============================================================
    # BASIC HELPERS
    # ============================================================

    @staticmethod
    def _clean_text(
        value: Any,
    ) -> str:

        if value is None:
            return ""

        return " ".join(
            str(value).strip().split()
        )

    @staticmethod
    def _safe_int(
        value: Any,
        default: int = 0,
    ) -> int:

        try:

            if value is None:
                return default

            return int(
                value
            )

        except (
            TypeError,
            ValueError,
        ):
            return default

    @staticmethod
    def _first_value(
        data: dict[str, Any],
        keys: list[str],
        default: Any = None,
    ) -> Any:

        for key in keys:

            value = data.get(
                key
            )

            if value is None:
                continue

            if isinstance(
                value,
                str,
            ):

                if value.strip():
                    return value.strip()

            else:
                return value

        return default

    @staticmethod
    def _add_unique(
        values: list[str],
        value: Any,
    ) -> None:

        if value is None:
            return

        cleaned = " ".join(
            str(value).strip().split()
        )

        if not cleaned:
            return

        normalized = cleaned.lower()

        existing = {
            str(item).strip().lower()
            for item in values
        }

        if normalized not in existing:

            values.append(
                cleaned
            )


investigation_agent = InvestigationAgent()