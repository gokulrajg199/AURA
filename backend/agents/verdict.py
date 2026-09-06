from __future__ import annotations

from typing import Any
import re

from models.project import AURAProject
from orchestration.contract import AURAStageResult
from orchestration.stages import AURAStage


class VerdictAgent:
    stage = AURAStage.VERDICT

    async def run(self, project: AURAProject) -> AURAStageResult:
        """
        Stage 04 — Evidence-aware AURA research verdict.

        Consumes:
        - Investigation results
        - Cross-source research intelligence
        - Claim-to-evidence analysis
        - Evidence synthesis

        Important:
        - This is an opportunity-oriented research assessment.
        - It is NOT a global novelty certification.
        - Metadata/abstract evidence is not equivalent to full-text
          scientific verification.
        """

        try:
            research = (
                project.research
                if isinstance(project.research, dict)
                else {}
            )

            analysis = (
                project.analysis
                if isinstance(project.analysis, dict)
                else {}
            )

            papers = research.get("papers", [])

            if not isinstance(papers, list):
                papers = []

            research_intelligence = analysis.get(
                "research_intelligence",
                {},
            )

            if not isinstance(research_intelligence, dict):
                research_intelligence = {}

            # --------------------------------------------------------
            # CLAIM / EVIDENCE LAYERS FROM STAGE 03
            # --------------------------------------------------------

            claim_analysis = self._get_dict(
                research_intelligence.get("claim_analysis"),
                analysis.get("claim_analysis"),
            )

            evidence_synthesis = self._get_dict(
                research_intelligence.get("evidence_synthesis"),
                analysis.get("evidence_synthesis"),
            )

            if not papers:
                return AURAStageResult(
                    stage=self.stage,
                    success=False,
                    message=(
                        "AURA cannot produce a research verdict because "
                        "no investigated papers are available."
                    ),
                )

            # --------------------------------------------------------
            # RESEARCH INTELLIGENCE
            # --------------------------------------------------------

            themes = self._as_list(
                research_intelligence.get("themes", [])
            )

            technologies = self._as_list(
                research_intelligence.get("technologies", [])
            )

            methods = self._as_list(
                research_intelligence.get("methods", [])
            )

            limitations = self._as_list(
                research_intelligence.get("limitations", [])
            )

            challenges = self._as_list(
                research_intelligence.get("challenges", [])
            )

            opportunities = self._as_list(
                research_intelligence.get("opportunities", [])
            )

            conflicts = self._as_list(
                research_intelligence.get("conflicts", [])
            )

            source_distribution = research_intelligence.get(
                "source_distribution",
                {},
            )

            evidence_quality = research_intelligence.get(
                "evidence_quality",
                {},
            )

            relevance = research_intelligence.get(
                "relevance_analysis",
                research_intelligence.get(
                    "relevance",
                    {},
                ),
            )

            # --------------------------------------------------------
            # BASIC RESEARCH SIGNALS
            # --------------------------------------------------------

            paper_count = len(papers)

            source_count = self._source_count(
                source_distribution,
                papers,
            )

            oa_count = self._open_access_count(
                papers,
            )

            recent_count = self._recent_paper_count(
                papers,
            )

            highly_cited_count = self._highly_cited_count(
                papers,
            )

            # --------------------------------------------------------
            # CLAIM / EVIDENCE METRICS
            # --------------------------------------------------------

            claim_metrics = self._claim_metrics(
                claim_analysis,
            )

            # --------------------------------------------------------
            # SCORE ENGINES
            # --------------------------------------------------------

            maturity = self._calculate_research_maturity(
                paper_count=paper_count,
                theme_count=len(themes),
                technology_count=len(technologies),
                limitation_count=len(limitations),
                challenge_count=len(challenges),
            )

            existing_strength = self._calculate_existing_strength(
                paper_count=paper_count,
                technology_count=len(technologies),
                method_count=len(methods),
                source_count=source_count,
                recent_count=recent_count,
            )

            base_evidence_strength = self._calculate_evidence_strength(
                papers=papers,
                source_count=source_count,
                oa_count=oa_count,
                evidence_quality=evidence_quality,
            )

            evidence_strength = (
                self._adjust_evidence_strength_for_claims(
                    base_score=base_evidence_strength,
                    claim_metrics=claim_metrics,
                )
            )

            gap_strength = self._calculate_gap_strength(
                limitations=limitations,
                challenges=challenges,
                opportunities=opportunities,
                conflicts=conflicts,
            )

            feasibility = self._calculate_feasibility(
                technologies=technologies,
                methods=methods,
                opportunities=opportunities,
                limitations=limitations,
            )

            novelty_confidence = self._calculate_novelty_confidence(
                gap_strength=gap_strength,
                existing_strength=existing_strength,
                evidence_strength=evidence_strength,
                paper_count=paper_count,
                source_count=source_count,
                claim_coverage=claim_metrics[
                    "coverage_percent"
                ],
            )

            opportunity_score = self._calculate_opportunity_score(
                gap_strength=gap_strength,
                feasibility=feasibility,
                evidence_strength=evidence_strength,
                novelty_confidence=novelty_confidence,
            )

            risk_level = self._risk_level(
                evidence_strength=evidence_strength,
                novelty_confidence=novelty_confidence,
                feasibility=feasibility,
                conflicts=conflicts,
                claim_coverage=claim_metrics[
                    "coverage_percent"
                ],
            )

            recommendation = self._recommend_direction(
                opportunity_score=opportunity_score,
                gap_strength=gap_strength,
                existing_strength=existing_strength,
                feasibility=feasibility,
                novelty_confidence=novelty_confidence,
                claim_metrics=claim_metrics,
            )

            verdict_confidence = self._overall_verdict_confidence(
                evidence_strength=evidence_strength,
                claim_metrics=claim_metrics,
                source_count=source_count,
                paper_count=paper_count,
                conflicts=conflicts,
            )

            # --------------------------------------------------------
            # EXPLANATION
            # --------------------------------------------------------

            verdict_summary = self._build_verdict_summary(
                project=project,
                recommendation=recommendation,
                opportunity_score=opportunity_score,
                maturity=maturity,
                gap_strength=gap_strength,
                novelty_confidence=novelty_confidence,
                evidence_strength=evidence_strength,
                risk_level=risk_level,
                confidence=verdict_confidence,
            )

            reasoning = self._build_reasoning(
                paper_count=paper_count,
                source_count=source_count,
                recent_count=recent_count,
                oa_count=oa_count,
                themes=themes,
                technologies=technologies,
                limitations=limitations,
                challenges=challenges,
                opportunities=opportunities,
                conflicts=conflicts,
                existing_strength=existing_strength,
                gap_strength=gap_strength,
                feasibility=feasibility,
                claim_metrics=claim_metrics,
            )

            verification_scope = {
                "papers_examined": paper_count,
                "sources_represented": source_count,
                "recent_papers_2022_2026": recent_count,
                "open_access_or_fulltext_signals": oa_count,

                "claim_count": claim_metrics[
                    "claim_count"
                ],

                "claims_with_evidence": claim_metrics[
                    "claims_with_evidence"
                ],

                "claims_without_evidence": claim_metrics[
                    "claims_without_evidence"
                ],

                "claim_evidence_coverage_percent": (
                    claim_metrics[
                        "coverage_percent"
                    ]
                ),

                "average_claim_evidence_strength_percent": (
                    claim_metrics[
                        "average_evidence_strength_percent"
                    ]
                ),

                "metadata_based_analysis": True,
                "full_text_verification": False,
                "global_novelty_verified": False,

                "interpretation": (
                    "Verdict is based on retrieved research records "
                    "and available metadata/abstract evidence. "
                    "It is not a global novelty certification."
                ),
            }

            # --------------------------------------------------------
            # FINAL VERDICT OBJECT
            # --------------------------------------------------------

            verdict = {
                "summary": verdict_summary,

                "recommendation": recommendation,

                "confidence": verdict_confidence,

                "scores": {
                    "research_maturity": maturity,
                    "existing_solution_strength": existing_strength,
                    "evidence_strength": evidence_strength,
                    "research_gap_strength": gap_strength,
                    "technical_feasibility": feasibility,
                    "novelty_confidence": novelty_confidence,
                    "opportunity_score": opportunity_score,
                },

                "risk": {
                    "level": risk_level,

                    "reasons": self._risk_reasons(
                        evidence_strength=evidence_strength,
                        novelty_confidence=novelty_confidence,
                        feasibility=feasibility,
                        conflicts=conflicts,
                        claim_coverage=claim_metrics[
                            "coverage_percent"
                        ],
                    ),
                },

                "reasoning": reasoning,

                "research_signals": {
                    "paper_count": paper_count,
                    "source_count": source_count,
                    "recent_paper_count": recent_count,
                    "open_access_count": oa_count,
                    "highly_cited_count": highly_cited_count,
                    "theme_count": len(themes),
                    "technology_count": len(technologies),
                    "method_count": len(methods),
                    "limitation_count": len(limitations),
                    "challenge_count": len(challenges),
                    "opportunity_count": len(opportunities),
                    "conflict_count": len(conflicts),
                },

                # ----------------------------------------------------
                # NEW: CLAIM → EVIDENCE ASSESSMENT
                # ----------------------------------------------------

                "claim_evidence_assessment": (
                    self._build_claim_evidence_assessment(
                        claim_analysis=claim_analysis,
                        claim_metrics=claim_metrics,
                    )
                ),

                # ----------------------------------------------------
                # NEW: EVIDENCE SYNTHESIS
                # ----------------------------------------------------

                "evidence_synthesis": evidence_synthesis,

                "relevance": relevance,

                "verification_scope": verification_scope,

                # ----------------------------------------------------
                # EVIDENCE TRACE
                # ----------------------------------------------------

                "evidence": self._build_evidence_trace(
                    papers=papers,
                    limitations=limitations,
                    challenges=challenges,
                    opportunities=opportunities,
                    claim_analysis=claim_analysis,
                ),

                # ----------------------------------------------------
                # TRANSPARENT DECISION LOGIC
                # ----------------------------------------------------

                "decision_logic": {
                    "evidence": (
                        "claim coverage + evidence strength + "
                        "source diversity"
                    ),

                    "gap": (
                        "limitations + challenges + "
                        "opportunity signals"
                    ),

                    "feasibility": (
                        "technology + method + "
                        "opportunity signals"
                    ),

                    "novelty": (
                        "opportunity-oriented confidence only; "
                        "not global novelty"
                    ),

                    "recommendation": (
                        "weighted synthesis of opportunity, "
                        "gap, feasibility, evidence, and "
                        "verification risk"
                    ),
                },
            }

            # --------------------------------------------------------
            # STORE IN PROJECT
            # --------------------------------------------------------

            project.analysis["verdict"] = verdict

            project.analysis["verdict_summary"] = (
                verdict_summary
            )

            project.analysis["recommendation"] = (
                recommendation
            )

            if not isinstance(project.memory, list):
                project.memory = []

            project.memory.append(
                {
                    "stage": self.stage.value,
                    "type": "research_verdict",
                    "summary": verdict_summary,
                    "recommendation": recommendation,
                    "opportunity_score": opportunity_score,
                    "risk_level": risk_level,
                    "confidence": verdict_confidence,
                    "claim_evidence_coverage_percent": (
                        claim_metrics[
                            "coverage_percent"
                        ]
                    ),
                }
            )

            if not isinstance(project.evidence, list):
                project.evidence = []

            project.evidence.append(
                {
                    "stage": self.stage.value,
                    "type": "verdict",
                    "status": "synthesized",
                    "source": (
                        "AURA cross-source research analysis"
                    ),
                    "claim": verdict_summary,
                    "confidence": verdict_confidence,
                    "claim_evidence_coverage_percent": (
                        claim_metrics[
                            "coverage_percent"
                        ]
                    ),
                    "verification_scope": (
                        "Retrieved metadata and abstract-level "
                        "research landscape; not global novelty "
                        "proof."
                    ),
                }
            )

            # --------------------------------------------------------
            # NEXT STAGE
            # --------------------------------------------------------

            return AURAStageResult(
                stage=self.stage,
                success=True,
                message=(
                    "AURA completed an evidence-aware research "
                    "verdict using cross-source research "
                    "intelligence and claim-to-evidence "
                    "traceability."
                ),
                data={
                    "verdict": verdict,
                },
                next_stage=AURAStage.INNOVATE,
            )

        except Exception as error:
            return AURAStageResult(
                stage=self.stage,
                success=False,
                message=(
                    f"Verdict analysis failed: {error}"
                ),
            )

    # ============================================================
    # DATA EXTRACTION
    # ============================================================

    def _get_dict(
        self,
        primary: Any,
        fallback: Any,
    ) -> dict[str, Any]:
        if isinstance(primary, dict):
            return primary

        if isinstance(fallback, dict):
            return fallback

        return {}

    def _claim_metrics(
        self,
        claim_analysis: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Extract reliable claim/evidence coverage.

        Supports both:
        - explicit summary metrics from Stage 03
        - individual claim evidence_ids
        """

        claims = claim_analysis.get(
            "claims",
            [],
        )

        if not isinstance(claims, list):
            claims = []

        claim_count = self._safe_int(
            claim_analysis.get(
                "claim_count",
                0,
            )
        )

        claims_with_evidence = self._safe_int(
            claim_analysis.get(
                "claims_with_evidence",
                0,
            )
        )

        claims_without_evidence = self._safe_int(
            claim_analysis.get(
                "claims_without_evidence",
                0,
            )
        )

        coverage = self._safe_number(
            claim_analysis.get(
                "coverage_percent",
                0,
            )
        )

        strengths: list[float] = []

        # --------------------------------------------------------
        # Prefer individual claims when available
        # --------------------------------------------------------

        if claims:

            actual_count = 0
            actual_with_evidence = 0

            for claim in claims:

                if not isinstance(claim, dict):
                    continue

                actual_count += 1

                evidence_ids = claim.get(
                    "evidence_ids",
                    [],
                )

                if (
                    isinstance(evidence_ids, list)
                    and evidence_ids
                ):
                    actual_with_evidence += 1

                strength = (
                    claim.get(
                        "evidence_strength_percent"
                    )
                    or claim.get(
                        "evidence_strength"
                    )
                    or claim.get(
                        "strength"
                    )
                )

                numeric_strength = self._safe_number(
                    strength
                )

                if numeric_strength > 0:
                    strengths.append(
                        min(
                            max(
                                numeric_strength,
                                0.0,
                            ),
                            100.0,
                        )
                    )

            if actual_count:

                claim_count = actual_count

                claims_with_evidence = (
                    actual_with_evidence
                )

                claims_without_evidence = max(
                    actual_count
                    - actual_with_evidence,
                    0,
                )

                coverage = (
                    actual_with_evidence
                    / actual_count
                    * 100
                )

        elif claim_count > 0:

            claims_without_evidence = max(
                claim_count
                - claims_with_evidence,
                0,
            )

            if coverage <= 0:

                coverage = (
                    claims_with_evidence
                    / claim_count
                    * 100
                )

        # --------------------------------------------------------
        # Evidence strength
        # --------------------------------------------------------

        average_strength = 0.0

        evidence_strength = claim_analysis.get(
            "evidence_strength",
            {},
        )

        if isinstance(
            evidence_strength,
            dict,
        ):

            average_strength = (
                self._safe_number(
                    evidence_strength.get(
                        "average_claim_evidence_strength_percent"
                    )
                )
            )

            if average_strength <= 0:

                average_strength = (
                    self._safe_number(
                        evidence_strength.get(
                            "average_evidence_strength_percent"
                        )
                    )
                )

        if (
            average_strength <= 0
            and strengths
        ):

            average_strength = (
                sum(strengths)
                / len(strengths)
            )

        return {
            "claim_count": max(
                claim_count,
                0,
            ),

            "claims_with_evidence": max(
                claims_with_evidence,
                0,
            ),

            "claims_without_evidence": max(
                claims_without_evidence,
                0,
            ),

            "coverage_percent": min(
                max(
                    coverage,
                    0.0,
                ),
                100.0,
            ),

            "average_evidence_strength_percent": min(
                max(
                    average_strength,
                    0.0,
                ),
                100.0,
            ),
        }

    # ============================================================
    # BASIC HELPERS
    # ============================================================

    def _as_list(
        self,
        value: Any,
    ) -> list[Any]:

        if isinstance(
            value,
            list,
        ):
            return value

        if isinstance(
            value,
            tuple,
        ):
            return list(value)

        if value is None:
            return []

        return [value]

    def _source_count(
        self,
        source_distribution: Any,
        papers: list[Any],
    ) -> int:

        if isinstance(
            source_distribution,
            dict,
        ):

            nested = source_distribution.get(
                "paper_distribution"
            )

            if isinstance(
                nested,
                dict,
            ):

                count = sum(
                    1
                    for value in nested.values()
                    if self._safe_number(value) > 0
                )

                if count:
                    return count

            count = sum(
                1
                for value in source_distribution.values()
                if self._safe_number(value) > 0
            )

            if count:
                return count

        sources: set[str] = set()

        for paper in papers:

            if not isinstance(
                paper,
                dict,
            ):
                continue

            source = (
                paper.get("source")
                or paper.get("provider")
                or paper.get("database")
            )

            if source:
                sources.add(
                    str(source)
                    .strip()
                    .lower()
                )

        return len(sources)

    def _open_access_count(
        self,
        papers: list[Any],
    ) -> int:

        count = 0

        for paper in papers:

            if not isinstance(
                paper,
                dict,
            ):
                continue

            value = paper.get(
                "open_access"
            )

            if value is True:
                count += 1
                continue

            if (
                isinstance(
                    value,
                    dict,
                )
                and value.get(
                    "is_oa"
                ) is True
            ):
                count += 1
                continue

            for key in (
                "is_open_access",
                "oa",
                "open_access_available",
            ):

                if paper.get(key) is True:
                    count += 1
                    break

        return count

    def _recent_paper_count(
        self,
        papers: list[Any],
    ) -> int:

        count = 0

        for paper in papers:

            if not isinstance(
                paper,
                dict,
            ):
                continue

            year = self._extract_year(
                paper
            )

            if (
                year is not None
                and 2022 <= year <= 2026
            ):
                count += 1

        return count

    def _highly_cited_count(
        self,
        papers: list[Any],
    ) -> int:

        count = 0

        for paper in papers:

            if not isinstance(
                paper,
                dict,
            ):
                continue

            citations = (
                paper.get(
                    "citation_count"
                )
                or paper.get(
                    "cited_by_count"
                )
                or paper.get(
                    "citations"
                )
                or 0
            )

            if (
                self._safe_number(
                    citations
                )
                >= 50
            ):
                count += 1

        return count

    def _extract_year(
        self,
        paper: dict[str, Any],
    ) -> int | None:

        for key in (
            "year",
            "publication_year",
            "published_year",
        ):

            value = paper.get(
                key
            )

            if value is not None:

                try:
                    return int(
                        value
                    )
                except (
                    TypeError,
                    ValueError,
                ):
                    pass

        date_value = (
            paper.get(
                "publication_date"
            )
            or paper.get(
                "published_date"
            )
            or paper.get(
                "date"
            )
        )

        if date_value:

            match = re.search(
                r"(20\d{2})",
                str(date_value),
            )

            if match:
                return int(
                    match.group(1)
                )

        return None

    def _safe_number(
        self,
        value: Any,
    ) -> float:

        try:
            return float(
                value
            )
        except (
            TypeError,
            ValueError,
        ):
            return 0.0

    def _safe_int(
        self,
        value: Any,
    ) -> int:

        try:
            return int(
                float(value)
            )
        except (
            TypeError,
            ValueError,
        ):
            return 0

    # ============================================================
    # SCORE ENGINES
    # ============================================================

    def _calculate_research_maturity(
        self,
        paper_count: int,
        theme_count: int,
        technology_count: int,
        limitation_count: int,
        challenge_count: int,
    ) -> int:

        score = 0

        if paper_count >= 20:
            score += 35
        elif paper_count >= 10:
            score += 25
        elif paper_count >= 5:
            score += 15
        else:
            score += 5

        score += min(
            theme_count * 4,
            20,
        )

        score += min(
            technology_count * 3,
            15,
        )

        score += min(
            limitation_count * 3,
            15,
        )

        score += min(
            challenge_count * 2,
            15,
        )

        return min(
            score,
            100,
        )

    def _calculate_existing_strength(
        self,
        paper_count: int,
        technology_count: int,
        method_count: int,
        source_count: int,
        recent_count: int,
    ) -> int:

        score = 0

        if paper_count >= 20:
            score += 30
        elif paper_count >= 10:
            score += 22
        elif paper_count >= 5:
            score += 14
        else:
            score += 6

        score += min(
            technology_count * 4,
            20,
        )

        score += min(
            method_count * 5,
            15,
        )

        score += min(
            source_count * 7,
            20,
        )

        if recent_count >= 10:
            score += 15
        elif recent_count >= 5:
            score += 10
        elif recent_count > 0:
            score += 5

        return min(
            score,
            100,
        )

    def _calculate_evidence_strength(
        self,
        papers: list[Any],
        source_count: int,
        oa_count: int,
        evidence_quality: Any,
    ) -> int:

        paper_count = len(
            papers
        )

        score = 0

        if paper_count >= 20:
            score += 25
        elif paper_count >= 10:
            score += 20
        elif paper_count >= 5:
            score += 12
        else:
            score += 5

        score += min(
            source_count * 10,
            30,
        )

        if oa_count >= 10:
            score += 20
        elif oa_count >= 5:
            score += 15
        elif oa_count > 0:
            score += 8

        quality_value = self._quality_score(
            evidence_quality
        )

        score += min(
            quality_value // 5,
            20,
        )

        return min(
            score,
            100,
        )

    def _adjust_evidence_strength_for_claims(
        self,
        base_score: int,
        claim_metrics: dict[str, Any],
    ) -> int:
        """
        Blend general source quality with actual
        claim-to-evidence coverage.

        This prevents a large paper count from automatically
        producing a high evidence score when the claims are
        poorly supported.
        """

        claim_count = self._safe_int(
            claim_metrics.get(
                "claim_count"
            )
        )

        if claim_count <= 0:
            return base_score

        coverage = min(
            max(
                self._safe_number(
                    claim_metrics.get(
                        "coverage_percent"
                    )
                ),
                0.0,
            ),
            100.0,
        )

        strength = min(
            max(
                self._safe_number(
                    claim_metrics.get(
                        "average_evidence_strength_percent"
                    )
                ),
                0.0,
            ),
            100.0,
        )

        if strength <= 0:
            strength = coverage

        claim_signal = (
            coverage * 0.60
            + strength * 0.40
        )

        adjusted = (
            base_score * 0.70
            + claim_signal * 0.30
        )

        return int(
            min(
                max(
                    round(adjusted),
                    0,
                ),
                100,
            )
        )

    def _calculate_gap_strength(
        self,
        limitations: list[Any],
        challenges: list[Any],
        opportunities: list[Any],
        conflicts: list[Any],
    ) -> int:

        score = 0

        score += min(
            len(limitations) * 8,
            32,
        )

        score += min(
            len(challenges) * 5,
            25,
        )

        score += min(
            len(opportunities) * 6,
            30,
        )

        if conflicts:
            score += min(
                len(conflicts) * 3,
                13,
            )

        return min(
            score,
            100,
        )

    def _calculate_feasibility(
        self,
        technologies: list[Any],
        methods: list[Any],
        opportunities: list[Any],
        limitations: list[Any],
    ) -> int:

        score = 20

        score += min(
            len(technologies) * 7,
            30,
        )

        score += min(
            len(methods) * 8,
            20,
        )

        score += min(
            len(opportunities) * 4,
            20,
        )

        if limitations:
            score += 10

        return min(
            score,
            100,
        )

    def _calculate_novelty_confidence(
        self,
        gap_strength: int,
        existing_strength: int,
        evidence_strength: int,
        paper_count: int,
        source_count: int,
        claim_coverage: float = 0.0,
    ) -> int:
        """
        IMPORTANT:

        This is NOT a global novelty score.

        It represents AURA's confidence that the investigated
        landscape contains unresolved opportunity signals.
        """

        score = 0

        score += int(
            gap_strength * 0.45
        )

        score += int(
            (100 - existing_strength)
            * 0.20
        )

        score += int(
            evidence_strength * 0.20
        )

        if paper_count >= 10:
            score += 5

        if source_count >= 3:
            score += 5

        if claim_coverage >= 80:
            score += 5
        elif claim_coverage >= 60:
            score += 2

        return min(
            max(
                score,
                0,
            ),
            100,
        )

    def _calculate_opportunity_score(
        self,
        gap_strength: int,
        feasibility: int,
        evidence_strength: int,
        novelty_confidence: int,
    ) -> int:

        score = (
            gap_strength * 0.35
            + feasibility * 0.25
            + evidence_strength * 0.15
            + novelty_confidence * 0.25
        )

        return int(
            min(
                max(
                    score,
                    0,
                ),
                100,
            )
        )

    def _overall_verdict_confidence(
        self,
        evidence_strength: int,
        claim_metrics: dict[str, Any],
        source_count: int,
        paper_count: int,
        conflicts: list[Any],
    ) -> int:

        claim_count = self._safe_int(
            claim_metrics.get(
                "claim_count"
            )
        )

        coverage = self._safe_number(
            claim_metrics.get(
                "coverage_percent"
            )
        )

        score = (
            evidence_strength * 0.55
        )

        if claim_count:
            score += (
                coverage * 0.30
            )
        else:
            score += (
                50 * 0.30
            )

        if source_count >= 4:
            score += 10
        elif source_count >= 2:
            score += 6

        if paper_count >= 10:
            score += 5
        elif paper_count >= 5:
            score += 3

        if conflicts:
            score -= min(
                len(conflicts) * 3,
                15,
            )

        return int(
            min(
                max(
                    round(score),
                    0,
                ),
                100,
            )
        )

    # ============================================================
    # DECISION ENGINE
    # ============================================================

    def _risk_level(
        self,
        evidence_strength: int,
        novelty_confidence: int,
        feasibility: int,
        conflicts: list[Any],
        claim_coverage: float = 0.0,
    ) -> str:

        risk = 0

        if evidence_strength < 50:
            risk += 2
        elif evidence_strength < 70:
            risk += 1

        if novelty_confidence < 40:
            risk += 2
        elif novelty_confidence < 60:
            risk += 1

        if feasibility < 50:
            risk += 2
        elif feasibility < 70:
            risk += 1

        if conflicts:
            risk += 1

        if (
            0 < claim_coverage < 60
        ):
            risk += 2

        elif (
            60 <= claim_coverage < 80
        ):
            risk += 1

        if risk >= 6:
            return "HIGH"

        if risk >= 3:
            return "MEDIUM"

        return "LOW"

    def _recommend_direction(
        self,
        opportunity_score: int,
        gap_strength: int,
        existing_strength: int,
        feasibility: int,
        novelty_confidence: int,
        claim_metrics: dict[str, Any],
    ) -> str:

        claim_count = self._safe_int(
            claim_metrics.get(
                "claim_count"
            )
        )

        coverage = self._safe_number(
            claim_metrics.get(
                "coverage_percent"
            )
        )

        # Evidence gates
        evidence_gate_new = (
            claim_count == 0
            or coverage >= 70
        )

        evidence_gate_improve = (
            claim_count == 0
            or coverage >= 60
        )

        if (
            opportunity_score >= 75
            and gap_strength >= 65
            and feasibility >= 60
            and evidence_gate_new
        ):
            return "BUILD_NEW_DIRECTION"

        if (
            opportunity_score >= 60
            and gap_strength >= 50
            and existing_strength >= 60
            and evidence_gate_improve
        ):
            return "IMPROVE_EXISTING"

        if feasibility < 45:
            return "PIVOT_OR_REDESIGN"

        if novelty_confidence < 35:
            return "REFINE_RESEARCH_QUESTION"

        if (
            claim_count
            and coverage < 60
        ):
            return "INVESTIGATE_FURTHER"

        return "INVESTIGATE_FURTHER"

    # ============================================================
    # EXPLANATION
    # ============================================================

    def _build_verdict_summary(
        self,
        project: AURAProject,
        recommendation: str,
        opportunity_score: int,
        maturity: int,
        gap_strength: int,
        novelty_confidence: int,
        evidence_strength: int,
        risk_level: str,
        confidence: int,
    ) -> str:

        idea = project.original_idea.strip()

        return (
            f"For '{idea}', AURA identifies an opportunity "
            f"score of {opportunity_score}/100. "
            f"The investigated landscape shows research maturity "
            f"of {maturity}/100, gap strength of {gap_strength}/100, "
            f"evidence strength of {evidence_strength}/100, and "
            f"opportunity-oriented novelty confidence of "
            f"{novelty_confidence}/100. "
            f"AURA recommends "
            f"{recommendation.replace('_', ' ').lower()} "
            f"with {risk_level.lower()} research risk and "
            f"{confidence}/100 verdict confidence."
        )

    def _build_reasoning(
        self,
        paper_count: int,
        source_count: int,
        recent_count: int,
        oa_count: int,
        themes: list[Any],
        technologies: list[Any],
        limitations: list[Any],
        challenges: list[Any],
        opportunities: list[Any],
        conflicts: list[Any],
        existing_strength: int,
        gap_strength: int,
        feasibility: int,
        claim_metrics: dict[str, Any],
    ) -> list[str]:

        reasoning: list[str] = []

        reasoning.append(
            f"AURA examined {paper_count} retrieved research "
            f"records across approximately {source_count} "
            f"source/provider groups."
        )

        reasoning.append(
            f"{recent_count} records fall within the configured "
            f"2022–2026 research window."
        )

        if oa_count:
            reasoning.append(
                f"{oa_count} records contain open-access signals. "
                f"This improves inspectability but does not by "
                f"itself prove scientific validity."
            )

        if themes:
            reasoning.append(
                f"The literature forms {len(themes)} identifiable "
                f"research themes."
            )

        if technologies:
            reasoning.append(
                f"{len(technologies)} recurring technologies or "
                f"technical approaches were identified."
            )

        if limitations:
            reasoning.append(
                f"{len(limitations)} limitation signals were "
                f"extracted."
            )

        if challenges:
            reasoning.append(
                f"{len(challenges)} challenge signals were "
                f"identified."
            )

        if opportunities:
            reasoning.append(
                f"{len(opportunities)} candidate opportunity "
                f"signals were derived from observed research "
                f"patterns."
            )

        if conflicts:
            reasoning.append(
                f"{len(conflicts)} potentially conflicting "
                f"signals require additional verification."
            )

        # --------------------------------------------------------
        # CLAIM EVIDENCE REASONING
        # --------------------------------------------------------

        claim_count = self._safe_int(
            claim_metrics.get(
                "claim_count"
            )
        )

        if claim_count:

            covered = self._safe_int(
                claim_metrics.get(
                    "claims_with_evidence"
                )
            )

            uncovered = self._safe_int(
                claim_metrics.get(
                    "claims_without_evidence"
                )
            )

            coverage = self._safe_number(
                claim_metrics.get(
                    "coverage_percent"
                )
            )

            reasoning.append(
                f"AURA traced {covered} of {claim_count} "
                f"registered research claims to linked evidence "
                f"({coverage:.2f}% coverage)."
            )

            if uncovered:

                reasoning.append(
                    f"{uncovered} research claims remain "
                    f"uncovered and must not be presented as "
                    f"verified findings."
                )

        else:

            reasoning.append(
                "No explicit claim register was available from "
                "the current research analysis, so claim-level "
                "coverage could not be independently measured."
            )

        reasoning.append(
            f"Existing-solution strength is estimated at "
            f"{existing_strength}/100."
        )

        reasoning.append(
            f"Research-gap strength is estimated at "
            f"{gap_strength}/100."
        )

        reasoning.append(
            f"Technical feasibility is estimated at "
            f"{feasibility}/100."
        )

        reasoning.append(
            "The verdict is an AURA evidence synthesis and "
            "opportunity assessment, not a formal global "
            "novelty certification."
        )

        return reasoning

    # ============================================================
    # CLAIM / EVIDENCE
    # ============================================================

    def _build_claim_evidence_assessment(
        self,
        claim_analysis: dict[str, Any],
        claim_metrics: dict[str, Any],
    ) -> dict[str, Any]:

        claims = claim_analysis.get(
            "claims",
            [],
        )

        if not isinstance(
            claims,
            list,
        ):
            claims = []

        rows: list[dict[str, Any]] = []

        for claim in claims[:50]:

            if not isinstance(
                claim,
                dict,
            ):
                continue

            evidence_ids = claim.get(
                "evidence_ids",
                [],
            )

            if not isinstance(
                evidence_ids,
                list,
            ):
                evidence_ids = []

            rows.append(
                {
                    "claim_id": claim.get(
                        "claim_id"
                    ),

                    "claim": self._clean_text(
                        claim.get(
                            "claim",
                            "",
                        )
                    ),

                    "evidence_status": claim.get(
                        "evidence_status",
                        "uncovered",
                    ),

                    "evidence_ids": evidence_ids,

                    "evidence_count": claim.get(
                        "evidence_count",
                        len(evidence_ids),
                    ),

                    "evidence_strength_percent": (
                        claim.get(
                            "evidence_strength_percent"
                        )
                    ),

                    "verification_status": claim.get(
                        "verification_status",
                        "requires_review",
                    ),
                }
            )

        coverage = claim_metrics[
            "coverage_percent"
        ]

        if coverage >= 85:
            status = "strong"
        elif coverage >= 60:
            status = "partial"
        elif claim_metrics[
            "claim_count"
        ]:
            status = "limited"
        else:
            status = "unavailable"

        return {
            "status": status,

            "claim_count": claim_metrics[
                "claim_count"
            ],

            "claims_with_evidence": claim_metrics[
                "claims_with_evidence"
            ],

            "claims_without_evidence": claim_metrics[
                "claims_without_evidence"
            ],

            "coverage_percent": coverage,

            "average_evidence_strength_percent": (
                claim_metrics[
                    "average_evidence_strength_percent"
                ]
            ),

            "uncovered_claim_ids": (
                claim_analysis.get(
                    "uncovered_claim_ids",
                    [],
                )
            ),

            "claims": rows,

            "traceability": (
                "claim → evidence → synthesis → verdict"
            ),
        }

    # ============================================================
    # EVIDENCE TRACE
    # ============================================================

    def _build_evidence_trace(
        self,
        papers: list[Any],
        limitations: list[Any],
        challenges: list[Any],
        opportunities: list[Any],
        claim_analysis: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:

        evidence: list[dict[str, Any]] = []

        # --------------------------------------------------------
        # Research records
        # --------------------------------------------------------

        for index, paper in enumerate(
            papers[:20],
            start=1,
        ):

            if not isinstance(
                paper,
                dict,
            ):
                continue

            evidence_id = (
                paper.get(
                    "evidence_id"
                )
                or paper.get(
                    "paper_id"
                )
                or paper.get(
                    "id"
                )
                or paper.get(
                    "doi"
                )
                or paper.get(
                    "openalex_id"
                )
            )

            title = (
                paper.get(
                    "title"
                )
                or paper.get(
                    "paper_title"
                )
                or f"Retrieved paper {index}"
            )

            source = (
                paper.get(
                    "source"
                )
                or paper.get(
                    "provider"
                )
                or paper.get(
                    "database"
                )
                or "Unknown source"
            )

            evidence.append(
                {
                    "type": "research_record",

                    "status": "retrieved",

                    "evidence_id": evidence_id,

                    "title": str(title),

                    "source": str(source),

                    "year": self._extract_year(
                        paper
                    ),

                    "supports": (
                        "Research-landscape assessment from "
                        "retrieved metadata/abstract evidence."
                    ),
                }
            )

        # --------------------------------------------------------
        # Claim → evidence trace
        # --------------------------------------------------------

        if isinstance(
            claim_analysis,
            dict,
        ):

            claims = claim_analysis.get(
                "claims",
                [],
            )

            if isinstance(
                claims,
                list,
            ):

                for claim in claims[:50]:

                    if not isinstance(
                        claim,
                        dict,
                    ):
                        continue

                    evidence_ids = claim.get(
                        "evidence_ids",
                        [],
                    )

                    if not isinstance(
                        evidence_ids,
                        list,
                    ):
                        evidence_ids = []

                    evidence.append(
                        {
                            "type": (
                                "claim_evidence_trace"
                            ),

                            "status": claim.get(
                                "evidence_status",
                                "uncovered",
                            ),

                            "claim_id": claim.get(
                                "claim_id"
                            ),

                            "claim": self._clean_text(
                                claim.get(
                                    "claim",
                                    "",
                                )
                            ),

                            "evidence_ids": evidence_ids,

                            "evidence_count": claim.get(
                                "evidence_count",
                                len(evidence_ids),
                            ),

                            "evidence_strength_percent": (
                                claim.get(
                                    "evidence_strength_percent"
                                )
                            ),

                            "verification_status": (
                                claim.get(
                                    "verification_status",
                                    "requires_review",
                                )
                            ),

                            "supports": (
                                "Claim-level traceability "
                                "from the AURA evidence "
                                "mapping layer."
                            ),
                        }
                    )

        # --------------------------------------------------------
        # Limitation signals
        # --------------------------------------------------------

        for item in limitations[:10]:

            evidence.append(
                {
                    "type": "limitation_signal",

                    "status": "ai_extracted",

                    "claim": self._clean_text(
                        item
                    ),

                    "supports": (
                        "Research gap assessment."
                    ),
                }
            )

        # --------------------------------------------------------
        # Challenge signals
        # --------------------------------------------------------

        for item in challenges[:10]:

            evidence.append(
                {
                    "type": "challenge_signal",

                    "status": "ai_extracted",

                    "claim": self._clean_text(
                        item
                    ),

                    "supports": (
                        "Unresolved challenge assessment."
                    ),
                }
            )

        # --------------------------------------------------------
        # Opportunity signals
        # --------------------------------------------------------

        for item in opportunities[:10]:

            evidence.append(
                {
                    "type": "opportunity_signal",

                    "status": "aura_recommendation",

                    "claim": self._clean_text(
                        item
                    ),

                    "supports": (
                        "Candidate research opportunity; "
                        "requires downstream validation."
                    ),
                }
            )

        return evidence

    def _clean_text(
        self,
        value: Any,
    ) -> str:

        if isinstance(
            value,
            dict,
        ):

            for key in (
                "text",
                "term",
                "name",
                "description",
                "claim",
                "value",
                "opportunity",
                "limitation",
                "challenge",
                "title",
            ):

                if value.get(key):
                    return str(
                        value[key]
                    )

            return str(
                value
            )

        return str(
            value
        )

    # ============================================================
    # QUALITY / RISK
    # ============================================================

    def _quality_score(
        self,
        evidence_quality: Any,
    ) -> int:

        if isinstance(
            evidence_quality,
            (int, float),
        ):

            return int(
                min(
                    max(
                        evidence_quality,
                        0,
                    ),
                    100,
                )
            )

        if isinstance(
            evidence_quality,
            dict,
        ):

            for key in (
                "score",
                "quality_score",
                "overall",
                "percentage",
            ):

                if key in evidence_quality:

                    value = self._safe_number(
                        evidence_quality[key]
                    )

                    return int(
                        min(
                            max(
                                value,
                                0,
                            ),
                            100,
                        )
                    )

        return 50

    def _risk_reasons(
        self,
        evidence_strength: int,
        novelty_confidence: int,
        feasibility: int,
        conflicts: list[Any],
        claim_coverage: float = 0.0,
    ) -> list[str]:

        reasons: list[str] = []

        if evidence_strength < 60:

            reasons.append(
                "Evidence strength is not high enough "
                "for high-confidence conclusions."
            )

        if novelty_confidence < 50:

            reasons.append(
                "The retrieved landscape does not provide "
                "enough confidence to treat the direction "
                "as clearly novel."
            )

        if feasibility < 60:

            reasons.append(
                "Technical feasibility requires additional "
                "validation or prototyping."
            )

        if conflicts:

            reasons.append(
                "Conflicting research signals require "
                "additional source-level verification."
            )

        if (
            0 < claim_coverage < 60
        ):

            reasons.append(
                "Some registered research claims lack "
                "sufficient linked evidence coverage."
            )

        elif (
            60 <= claim_coverage < 80
        ):

            reasons.append(
                "Claim/evidence coverage is partial and "
                "should be strengthened before "
                "high-confidence conclusions."
            )

        if not reasons:

            reasons.append(
                "No major risk signal was detected from "
                "the current research landscape."
            )

        return reasons


verdict_agent = VerdictAgent()