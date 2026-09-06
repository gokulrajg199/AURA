from __future__ import annotations

from typing import Any
import re

from models.project import AURAProject
from orchestration.contract import AURAStageResult
from orchestration.stages import AURAStage


class InnovationAgent:
    """
    AURA Stage 05 — Innovation Engine

    Purpose:
    Transform verified research findings, claim/evidence mappings,
    limitations, challenges, opportunities, and the Stage 04 verdict
    into ranked, traceable candidate innovation directions.

    Important:
    - AURA recommendations are AI synthesis.
    - They are not automatically scientific facts.
    - They are not global novelty certification.
    - Every innovation direction should retain a research basis.
    """

    stage = AURAStage.INNOVATE

    async def run(self, project: AURAProject) -> AURAStageResult:
        try:
            analysis = project.analysis or {}

            research = project.research or {}

            research_intelligence = analysis.get(
                "research_intelligence",
                {},
            )

            verdict = analysis.get(
                "verdict",
                {},
            )

            if not research_intelligence:
                return AURAStageResult(
                    stage=self.stage,
                    success=False,
                    message=(
                        "AURA cannot generate innovation directions "
                        "because research intelligence is unavailable."
                    ),
                )

            papers = self._as_list(
                research.get("papers", [])
            )

            limitations = self._as_list(
                research_intelligence.get(
                    "limitations",
                    [],
                )
            )

            challenges = self._as_list(
                research_intelligence.get(
                    "challenges",
                    [],
                )
            )

            opportunities = self._as_list(
                research_intelligence.get(
                    "opportunities",
                    [],
                )
            )

            technologies = self._as_list(
                research_intelligence.get(
                    "technologies",
                    [],
                )
            )

            themes = self._as_list(
                research_intelligence.get(
                    "themes",
                    [],
                )
            )

            methods = self._as_list(
                research_intelligence.get(
                    "methods",
                    [],
                )
            )

            conflicts = self._as_list(
                research_intelligence.get(
                    "conflicts",
                    [],
                )
            )

            claim_analysis = research_intelligence.get(
                "claim_analysis",
                {},
            )

            evidence_synthesis = research_intelligence.get(
                "evidence_synthesis",
                {},
            )

            claim_evidence_map = (
                research.get(
                    "claim_evidence_map",
                    {},
                )
                or research_intelligence.get(
                    "claim_evidence_map",
                    {},
                )
            )

            existing_strength = self._score(
                verdict,
                "existing_solution_strength",
            )

            gap_strength = self._score(
                verdict,
                "research_gap_strength",
            )

            feasibility = self._score(
                verdict,
                "technical_feasibility",
            )

            opportunity_score = self._score(
                verdict,
                "opportunity_score",
            )

            novelty_confidence = self._score(
                verdict,
                "novelty_confidence",
            )

            evidence_strength = self._score(
                verdict,
                "evidence_strength",
            )

            claim_coverage = self._extract_claim_coverage(
                claim_analysis
            )

            average_claim_evidence = self._safe_int(
                claim_analysis.get(
                    "average_evidence_strength",
                    claim_analysis.get(
                        "average_claim_evidence_strength",
                        0,
                    ),
                )
            )

            # ----------------------------------------------------
            # BUILD RESEARCH-BACKED INNOVATION INPUTS
            # ----------------------------------------------------

            research_basis = self._build_research_basis(
                papers=papers,
                limitations=limitations,
                challenges=challenges,
                opportunities=opportunities,
                technologies=technologies,
                themes=themes,
                methods=methods,
                conflicts=conflicts,
                claim_analysis=claim_analysis,
                claim_evidence_map=claim_evidence_map,
            )

            innovation_directions = (
                self._generate_innovation_directions(
                    project=project,
                    limitations=limitations,
                    challenges=challenges,
                    opportunities=opportunities,
                    technologies=technologies,
                    themes=themes,
                    methods=methods,
                    research_basis=research_basis,
                    gap_strength=gap_strength,
                    feasibility=feasibility,
                    evidence_strength=evidence_strength,
                    claim_coverage=claim_coverage,
                )
            )

            innovation_directions = self._rank_directions(
                innovation_directions,
                opportunity_score=opportunity_score,
                gap_strength=gap_strength,
                feasibility=feasibility,
                evidence_strength=evidence_strength,
                claim_coverage=claim_coverage,
            )

            recommended_direction = (
                innovation_directions[0]
                if innovation_directions
                else None
            )

            innovation_summary = self._build_summary(
                project=project,
                directions=innovation_directions,
                recommended_direction=recommended_direction,
                opportunity_score=opportunity_score,
                claim_coverage=claim_coverage,
            )

            confidence = self._innovation_confidence(
                evidence_strength=evidence_strength,
                claim_coverage=claim_coverage,
                average_claim_evidence=average_claim_evidence,
                feasibility=feasibility,
                gap_strength=gap_strength,
            )

            innovation = {
                "summary": innovation_summary,

                "status": (
                    "research_backed_candidate_directions_generated"
                ),

                "recommendation_policy": (
                    "AURA innovation directions are AI-generated "
                    "research syntheses based on retrieved evidence, "
                    "identified limitations, challenges, opportunities, "
                    "and technical signals. They are candidate directions "
                    "and require further validation."
                ),

                "directions": innovation_directions,

                "recommended_direction": (
                    recommended_direction
                    if recommended_direction
                    else {}
                ),

                "innovation_confidence": confidence,

                "research_basis": research_basis,

                "claim_evidence_context": {
                    "claim_count": self._safe_int(
                        claim_analysis.get(
                            "claim_count",
                            0,
                        )
                    ),
                    "claims_with_evidence": self._safe_int(
                        claim_analysis.get(
                            "claims_with_evidence",
                            0,
                        )
                    ),
                    "claims_without_evidence": self._safe_int(
                        claim_analysis.get(
                            "claims_without_evidence",
                            0,
                        )
                    ),
                    "evidence_coverage_percent": claim_coverage,
                    "average_evidence_strength": (
                        average_claim_evidence
                    ),
                    "evidence_synthesis_available": bool(
                        evidence_synthesis
                    ),
                },

                "decision_context": {
                    "existing_solution_strength": existing_strength,
                    "research_gap_strength": gap_strength,
                    "technical_feasibility": feasibility,
                    "opportunity_score": opportunity_score,
                    "novelty_confidence": novelty_confidence,
                    "evidence_strength": evidence_strength,
                },

                "verification_scope": {
                    "recommendations_are_ai_synthesis": True,
                    "research_basis_attached": True,
                    "claim_evidence_trace_available": (
                        bool(claim_analysis)
                    ),
                    "global_novelty_verified": False,
                    "patent_clearance_performed": False,
                    "full_text_validation_performed": False,
                    "expert_validation_required": True,
                    "interpretation": (
                        "Innovation directions represent candidate "
                        "research opportunities derived from the "
                        "investigated landscape. They must not be "
                        "interpreted as proof of global novelty."
                    ),
                },

                "next_stage_focus": [
                    "Select the strongest evidence-backed direction.",
                    "Convert the direction into a concrete solution.",
                    "Define system architecture.",
                    "Select hardware, software, AI models, datasets, and tools.",
                    "Identify implementation dependencies.",
                    "Define measurable validation criteria.",
                ],
            }

            project.analysis["innovation"] = innovation

            project.innovation = innovation

            project.memory.append(
                {
                    "stage": self.stage.value,
                    "type": "innovation_generation",
                    "summary": innovation_summary,
                    "direction_count": len(
                        innovation_directions
                    ),
                    "recommended_direction": (
                        recommended_direction.get(
                            "title"
                        )
                        if recommended_direction
                        else None
                    ),
                    "innovation_confidence": confidence,
                    "claim_evidence_coverage": claim_coverage,
                }
            )

            project.evidence.append(
                {
                    "stage": self.stage.value,
                    "type": "innovation",
                    "status": "aura_recommendation",
                    "source": (
                        "AURA research intelligence + "
                        "claim evidence analysis + verdict"
                    ),
                    "claim": (
                        "Candidate innovation directions generated "
                        "from evidence-backed research opportunities."
                    ),
                    "verification_scope": (
                        "AI synthesis based on retrieved research "
                        "evidence; not a global novelty claim."
                    ),
                    "claim_evidence_coverage_percent": (
                        claim_coverage
                    ),
                }
            )

            return AURAStageResult(
                stage=self.stage,
                success=True,
                message=(
                    "AURA generated and ranked research-backed "
                    "innovation directions with evidence context."
                ),
                data={
                    "innovation": innovation,
                },
                next_stage=AURAStage.SOLUTION,
            )

        except Exception as error:
            return AURAStageResult(
                stage=self.stage,
                success=False,
                message=f"Innovation generation failed: {error}",
            )

    # ============================================================
    # RESEARCH BASIS
    # ============================================================

    def _build_research_basis(
        self,
        papers: list[Any],
        limitations: list[Any],
        challenges: list[Any],
        opportunities: list[Any],
        technologies: list[Any],
        themes: list[Any],
        methods: list[Any],
        conflicts: list[Any],
        claim_analysis: dict[str, Any],
        claim_evidence_map: Any,
    ) -> dict[str, Any]:
        return {
            "papers_considered": len(papers),

            "limitations": [
                self._clean_text(item)
                for item in limitations[:15]
            ],

            "challenges": [
                self._clean_text(item)
                for item in challenges[:15]
            ],

            "opportunities": [
                self._clean_text(item)
                for item in opportunities[:15]
            ],

            "technologies": [
                self._clean_text(item)
                for item in technologies[:15]
            ],

            "themes": [
                self._clean_text(item)
                for item in themes[:15]
            ],

            "methods": [
                self._clean_text(item)
                for item in methods[:15]
            ],

            "conflicts": [
                self._clean_text(item)
                for item in conflicts[:10]
            ],

            "claim_count": self._safe_int(
                claim_analysis.get(
                    "claim_count",
                    0,
                )
            ),

            "claims_with_evidence": self._safe_int(
                claim_analysis.get(
                    "claims_with_evidence",
                    0,
                )
            ),

            "claims_without_evidence": self._safe_int(
                claim_analysis.get(
                    "claims_without_evidence",
                    0,
                )
            ),

            "evidence_coverage_percent": (
                self._extract_claim_coverage(
                    claim_analysis
                )
            ),

            "claim_evidence_map_available": bool(
                claim_evidence_map
            ),
        }

    # ============================================================
    # GENERATION
    # ============================================================

    def _generate_innovation_directions(
        self,
        project: AURAProject,
        limitations: list[Any],
        challenges: list[Any],
        opportunities: list[Any],
        technologies: list[Any],
        themes: list[Any],
        methods: list[Any],
        research_basis: dict[str, Any],
        gap_strength: int,
        feasibility: int,
        evidence_strength: int,
        claim_coverage: float,
    ) -> list[dict[str, Any]]:
        directions: list[dict[str, Any]] = []

        idea = project.original_idea.strip()

        primary_technology = (
            self._clean_text(
                technologies[0]
            )
            if technologies
            else "AI and IoT"
        )

        secondary_technology = (
            self._clean_text(
                technologies[1]
            )
            if len(technologies) > 1
            else "real-time analytics"
        )

        primary_limitation = (
            self._clean_text(
                limitations[0]
            )
            if limitations
            else (
                "Existing approaches may have limited "
                "adaptability."
            )
        )

        secondary_limitation = (
            self._clean_text(
                limitations[1]
            )
            if len(limitations) > 1
            else (
                "Existing systems may not provide sufficient "
                "real-time intelligence."
            )
        )

        primary_challenge = (
            self._clean_text(
                challenges[0]
            )
            if challenges
            else (
                "Reliable real-world deployment remains "
                "challenging."
            )
        )

        primary_opportunity = (
            self._clean_text(
                opportunities[0]
            )
            if opportunities
            else (
                "Improve intelligent decision support."
            )
        )

        secondary_opportunity = (
            self._clean_text(
                opportunities[1]
            )
            if len(opportunities) > 1
            else (
                "Develop a more adaptive integrated solution."
            )
        )

        # --------------------------------------------------------
        # INN-01
        # --------------------------------------------------------

        directions.append(
            self._create_direction(
                direction_id="INN-01",
                title=(
                    "Adaptive Intelligent Decision System"
                ),
                category=(
                    "Adaptive AI + Intelligent Automation"
                ),
                evidence_basis=[
                    primary_limitation,
                    primary_opportunity,
                    primary_technology,
                ],
                existing_approach=(
                    "The investigated landscape contains "
                    "domain-specific sensing, analytics, "
                    "automation, and machine-learning approaches."
                ),
                limitation=primary_limitation,
                research_gap=primary_opportunity,
                proposed_innovation=(
                    f"Develop an adaptive intelligence layer for "
                    f"{idea} that continuously interprets incoming "
                    f"data and updates recommendations or actions "
                    f"when operating conditions change."
                ),
                technical_mechanism=[
                    primary_technology,
                    secondary_technology,
                    "adaptive decision logic",
                    "continuous monitoring",
                    "confidence estimation",
                ],
                expected_contribution=(
                    "A transition from static or fixed decision "
                    "rules toward context-aware adaptive intelligence."
                ),
                feasibility=feasibility,
                evidence_strength=evidence_strength,
                claim_coverage=claim_coverage,
                validation=[
                    "Compare against a rule-based baseline.",
                    "Measure prediction or decision accuracy.",
                    "Evaluate performance under changing conditions.",
                    "Measure false alerts and missed decisions.",
                    "Evaluate robustness to noisy inputs.",
                ],
                research_questions=[
                    "Does adaptive decision logic improve performance?",
                    "How robust is the system under changing conditions?",
                    "Can useful performance be maintained with noisy data?",
                ],
            )
        )

        # --------------------------------------------------------
        # INN-02
        # --------------------------------------------------------

        directions.append(
            self._create_direction(
                direction_id="INN-02",
                title=(
                    "Predictive Early-Warning Intelligence Layer"
                ),
                category="Predictive AI",
                evidence_basis=[
                    secondary_limitation,
                    secondary_opportunity,
                    primary_challenge,
                ],
                existing_approach=(
                    "The investigated research landscape includes "
                    "monitoring and reactive response approaches."
                ),
                limitation=secondary_limitation,
                research_gap=secondary_opportunity,
                proposed_innovation=(
                    f"Introduce predictive intelligence into {idea} "
                    "to estimate emerging risks or future system "
                    "states before a critical condition occurs."
                ),
                technical_mechanism=[
                    "time-series analysis",
                    "machine learning",
                    "anomaly detection",
                    primary_technology,
                    "risk prediction",
                ],
                expected_contribution=(
                    "Move the system from reactive monitoring toward "
                    "predictive intervention."
                ),
                feasibility=max(
                    feasibility - 3,
                    0,
                ),
                evidence_strength=evidence_strength,
                claim_coverage=claim_coverage,
                validation=[
                    "Create historical or experimental test scenarios.",
                    "Measure prediction accuracy.",
                    "Measure precision, recall, and F1 where applicable.",
                    "Evaluate different prediction horizons.",
                    "Measure false-positive warning rate.",
                ],
                research_questions=[
                    "How early can emerging risks be identified?",
                    "Which signals contribute most to prediction?",
                    "How stable is performance across time?",
                ],
            )
        )

        # --------------------------------------------------------
        # INN-03
        # --------------------------------------------------------

        directions.append(
            self._create_direction(
                direction_id="INN-03",
                title=(
                    "Multi-Source Intelligence Fusion"
                ),
                category="Data Fusion + AI",
                evidence_basis=[
                    primary_limitation,
                    primary_challenge,
                    "multi-source research pattern",
                ],
                existing_approach=(
                    "Many research systems depend on a limited "
                    "number of sensors, datasets, or information "
                    "sources."
                ),
                limitation=(
                    "Single-source information can provide an "
                    "incomplete representation of real-world "
                    "conditions."
                ),
                research_gap=(
                    "Combine complementary information sources "
                    "to improve context awareness and reliability."
                ),
                proposed_innovation=(
                    f"Create a multi-source intelligence layer for "
                    f"{idea} that combines complementary sensor, "
                    "historical, environmental, visual, or external "
                    "information where justified by the domain."
                ),
                technical_mechanism=[
                    "multi-modal data fusion",
                    "feature extraction",
                    "sensor integration",
                    primary_technology,
                    "confidence estimation",
                ],
                expected_contribution=(
                    "More complete contextual understanding than "
                    "single-source monitoring."
                ),
                feasibility=max(
                    feasibility - 5,
                    0,
                ),
                evidence_strength=evidence_strength,
                claim_coverage=claim_coverage,
                validation=[
                    "Compare single-source and fused models.",
                    "Measure performance improvement.",
                    "Test missing-data scenarios.",
                    "Test noisy inputs.",
                    "Test conflicting signals.",
                ],
                research_questions=[
                    "Does data fusion improve decision reliability?",
                    "Which sources provide the largest benefit?",
                    "How should conflicting signals be handled?",
                ],
            )
        )

        # --------------------------------------------------------
        # INN-04
        # --------------------------------------------------------

        directions.append(
            self._create_direction(
                direction_id="INN-04",
                title=(
                    "Edge-AI Real-Time Intelligence"
                ),
                category="Edge AI + IoT",
                evidence_basis=[
                    primary_challenge,
                    primary_technology,
                    "real-time intelligence opportunity",
                ],
                existing_approach=(
                    "Cloud-based analytics can provide strong "
                    "processing capability but may introduce "
                    "latency, connectivity, bandwidth, or privacy "
                    "dependencies."
                ),
                limitation=(
                    "Real-time systems can be affected by "
                    "network availability, latency, bandwidth, "
                    "and transfer requirements."
                ),
                research_gap=(
                    "Move appropriate intelligence closer to "
                    "the data-generation point."
                ),
                proposed_innovation=(
                    f"Design a lightweight edge intelligence layer "
                    f"for {idea} that performs selected inference "
                    "locally while synchronizing important results "
                    "with a central platform."
                ),
                technical_mechanism=[
                    "edge AI",
                    "lightweight ML models",
                    "IoT",
                    "local inference",
                    "cloud synchronization",
                ],
                expected_contribution=(
                    "Lower latency and improved resilience for "
                    "time-sensitive intelligent operations."
                ),
                feasibility=max(
                    feasibility - 8,
                    0,
                ),
                evidence_strength=evidence_strength,
                claim_coverage=claim_coverage,
                validation=[
                    "Measure inference latency.",
                    "Measure bandwidth consumption.",
                    "Compare edge and cloud inference.",
                    "Test network interruption.",
                    "Measure resource consumption.",
                ],
                research_questions=[
                    "Can useful inference run within edge constraints?",
                    "What latency reduction is achieved?",
                    "How much accuracy is lost through compression?",
                ],
            )
        )

        # --------------------------------------------------------
        # INN-05
        # --------------------------------------------------------

        directions.append(
            self._create_direction(
                direction_id="INN-05",
                title=(
                    "Explainable and Trust-Aware AI Layer"
                ),
                category="Explainable AI + Human Verification",
                evidence_basis=[
                    "explainability research pattern",
                    "evidence traceability",
                    primary_opportunity,
                ],
                existing_approach=(
                    "AI systems can generate predictions or "
                    "recommendations without providing sufficient "
                    "explanation for expert verification."
                ),
                limitation=(
                    "Low interpretability can reduce trust and "
                    "make expert verification difficult."
                ),
                research_gap=(
                    "Connect AI outputs with understandable "
                    "evidence, confidence, and reasoning signals."
                ),
                proposed_innovation=(
                    f"Add an explainability and trust layer to "
                    f"{idea} that communicates why a prediction "
                    "or recommendation was generated, which inputs "
                    "influenced it, and how confident the system is."
                ),
                technical_mechanism=[
                    "Explainable AI",
                    "feature importance",
                    "confidence estimation",
                    "evidence traceability",
                    "human-in-the-loop review",
                ],
                expected_contribution=(
                    "Improved transparency and expert verification "
                    "of AI-assisted decisions."
                ),
                feasibility=max(
                    feasibility - 2,
                    0,
                ),
                evidence_strength=evidence_strength,
                claim_coverage=claim_coverage,
                validation=[
                    "Measure explanation consistency.",
                    "Evaluate confidence calibration.",
                    "Compare expert understanding.",
                    "Measure verification time.",
                    "Evaluate expert acceptance.",
                ],
                research_questions=[
                    "Do explanations improve user trust?",
                    "Are explanations consistent with model behavior?",
                    "Can experts verify AI recommendations efficiently?",
                ],
            )
        )

        # --------------------------------------------------------
        # INN-06 — INTEGRATED RESEARCH-TO-SYSTEM DIRECTION
        # --------------------------------------------------------

        directions.append(
            self._create_direction(
                direction_id="INN-06",
                title=(
                    "Evidence-Guided Closed-Loop Intelligence System"
                ),
                category=(
                    "AI + Evidence + Decision + Validation"
                ),
                evidence_basis=[
                    primary_opportunity,
                    primary_challenge,
                    "research evidence traceability",
                    "closed-loop validation opportunity",
                ],
                existing_approach=(
                    "Research solutions are frequently implemented "
                    "as isolated sensing, prediction, automation, "
                    "or decision components."
                ),
                limitation=(
                    "Disconnected components can make it difficult "
                    "to connect evidence, prediction, decision, "
                    "action, and validation into one measurable loop."
                ),
                research_gap=(
                    "Integrate evidence, intelligence, decision "
                    "making, action, and feedback into a measurable "
                    "closed-loop system."
                ),
                proposed_innovation=(
                    f"Develop {idea} as an evidence-guided closed-loop "
                    "intelligence system where incoming data is "
                    "interpreted, decisions are generated with "
                    "confidence/evidence context, actions are taken, "
                    "and outcomes are continuously evaluated."
                ),
                technical_mechanism=[
                    primary_technology,
                    secondary_technology,
                    "decision engine",
                    "feedback loop",
                    "evidence traceability",
                    "continuous validation",
                ],
                expected_contribution=(
                    "A unified system connecting observation, "
                    "intelligence, decision, action, and measurable "
                    "feedback rather than treating each component "
                    "as an isolated module."
                ),
                feasibility=max(
                    feasibility - 10,
                    0,
                ),
                evidence_strength=evidence_strength,
                claim_coverage=claim_coverage,
                validation=[
                    "Compare against isolated-module architecture.",
                    "Measure end-to-end system performance.",
                    "Measure decision-to-outcome accuracy.",
                    "Evaluate feedback-loop stability.",
                    "Test failure and recovery scenarios.",
                ],
                research_questions=[
                    "Does closed-loop integration improve outcomes?",
                    "Can evidence-aware decisions improve reliability?",
                    "How effectively can feedback update future decisions?",
                ],
            )
        )

        return directions

    # ============================================================
    # DIRECTION CONSTRUCTION
    # ============================================================

    def _create_direction(
        self,
        direction_id: str,
        title: str,
        category: str,
        evidence_basis: list[str],
        existing_approach: str,
        limitation: str,
        research_gap: str,
        proposed_innovation: str,
        technical_mechanism: list[str],
        expected_contribution: str,
        feasibility: int,
        evidence_strength: int,
        claim_coverage: float,
        validation: list[str],
        research_questions: list[str],
    ) -> dict[str, Any]:
        return {
            "id": direction_id,

            "title": title,

            "category": category,

            "evidence_status": "AURA_RECOMMENDATION",

            "evidence_basis": evidence_basis,

            "existing_approach": existing_approach,

            "limitation": limitation,

            "research_gap": research_gap,

            "proposed_innovation": proposed_innovation,

            "technical_mechanism": technical_mechanism,

            "expected_contribution": expected_contribution,

            "feasibility": {
                "score": int(
                    max(
                        0,
                        min(
                            100,
                            feasibility,
                        ),
                    )
                ),
                "assessment": self._feasibility_label(
                    feasibility
                ),
            },

            "research_evidence_context": {
                "evidence_strength": int(
                    max(
                        0,
                        min(
                            100,
                            evidence_strength,
                        ),
                    )
                ),
                "claim_evidence_coverage_percent": (
                    claim_coverage
                ),
            },

            "validation_requirements": validation,

            "research_questions": research_questions,

            "novelty_statement": (
                "This direction represents a candidate "
                "research opportunity identified by AURA. "
                "It is not a verified claim of global novelty."
            ),

            "development_readiness": (
                "Requires solution architecture, "
                "technology selection, implementation planning, "
                "and experimental validation."
            ),
        }

    # ============================================================
    # RANKING
    # ============================================================

    def _rank_directions(
        self,
        directions: list[dict[str, Any]],
        opportunity_score: int,
        gap_strength: int,
        feasibility: int,
        evidence_strength: int,
        claim_coverage: float,
    ) -> list[dict[str, Any]]:
        for direction in directions:

            direction_feasibility = int(
                direction.get(
                    "feasibility",
                    {},
                ).get(
                    "score",
                    0,
                )
            )

            gap_signal = self._gap_signal(
                direction
            )

            validation_strength = min(
                len(
                    direction.get(
                        "validation_requirements",
                        [],
                    )
                )
                * 8,
                24,
            )

            evidence_signal = min(
                max(
                    int(evidence_strength),
                    0,
                ),
                100,
            )

            claim_signal = min(
                max(
                    int(claim_coverage),
                    0,
                ),
                100,
            )

            score = (
                direction_feasibility * 0.30
                + gap_signal * 0.20
                + validation_strength * 0.10
                + evidence_signal * 0.15
                + claim_signal * 0.10
                + gap_strength * 0.05
                + opportunity_score * 0.10
            )

            direction["innovation_score"] = int(
                max(
                    0,
                    min(
                        100,
                        score,
                    ),
                )
            )

            direction["rank_explanation"] = (
                "Ranked using technical feasibility, "
                "research-gap alignment, evidence strength, "
                "claim-evidence coverage, validation specificity, "
                "and the Stage 04 opportunity assessment."
            )

        directions.sort(
            key=lambda item: item.get(
                "innovation_score",
                0,
            ),
            reverse=True,
        )

        for index, direction in enumerate(
            directions,
            start=1,
        ):
            direction["rank"] = index

        return directions

    def _gap_signal(
        self,
        direction: dict[str, Any],
    ) -> int:
        text = " ".join(
            [
                str(
                    direction.get(
                        "limitation",
                        "",
                    )
                ),
                str(
                    direction.get(
                        "research_gap",
                        "",
                    )
                ),
                str(
                    direction.get(
                        "proposed_innovation",
                        "",
                    )
                ),
            ]
        ).lower()

        keywords = [
            "limitation",
            "gap",
            "challenge",
            "unresolved",
            "improve",
            "adaptive",
            "predictive",
            "reliability",
            "real-time",
            "explain",
            "evidence",
            "validation",
            "feedback",
            "closed-loop",
        ]

        matches = sum(
            1
            for keyword in keywords
            if keyword in text
        )

        return min(
            100,
            30 + matches * 6,
        )

    # ============================================================
    # CONFIDENCE
    # ============================================================

    def _innovation_confidence(
        self,
        evidence_strength: int,
        claim_coverage: float,
        average_claim_evidence: int,
        feasibility: int,
        gap_strength: int,
    ) -> dict[str, Any]:
        score = (
            evidence_strength * 0.30
            + claim_coverage * 0.25
            + average_claim_evidence * 0.15
            + feasibility * 0.15
            + gap_strength * 0.15
        )

        score = int(
            max(
                0,
                min(
                    100,
                    score,
                ),
            )
        )

        if score >= 80:
            label = "HIGH"

        elif score >= 60:
            label = "MEDIUM-HIGH"

        elif score >= 40:
            label = "MEDIUM"

        else:
            label = "LOW"

        return {
            "score": score,
            "level": label,
            "interpretation": (
                "Confidence reflects evidence coverage, "
                "claim support, technical feasibility, and "
                "research-gap signals. It is not novelty probability."
            ),
        }

    # ============================================================
    # SUMMARY
    # ============================================================

    def _build_summary(
        self,
        project: AURAProject,
        directions: list[dict[str, Any]],
        recommended_direction: dict[str, Any] | None,
        opportunity_score: int,
        claim_coverage: float,
    ) -> str:
        if not recommended_direction:
            return (
                "AURA could not generate a sufficiently "
                "supported innovation direction."
            )

        title = recommended_direction.get(
            "title",
            "candidate direction",
        )

        score = recommended_direction.get(
            "innovation_score",
            0,
        )

        return (
            f"AURA generated {len(directions)} research-backed "
            f"candidate innovation directions for "
            f"'{project.original_idea.strip()}'. "
            f"The highest-ranked direction is '{title}' "
            f"with an innovation score of {score}/100. "
            f"The underlying research opportunity score is "
            f"{opportunity_score}/100, while the current "
            f"claim-evidence coverage is "
            f"{claim_coverage:.1f}%. "
            f"These directions are AURA recommendations and "
            f"require solution-level and experimental validation."
        )

    # ============================================================
    # HELPERS
    # ============================================================

    def _as_list(
        self,
        value: Any,
    ) -> list[Any]:
        if isinstance(value, list):
            return value

        if isinstance(value, tuple):
            return list(value)

        if value is None:
            return []

        return [value]

    def _clean_text(
        self,
        value: Any,
    ) -> str:
        if isinstance(value, dict):
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

            return str(value)

        return str(value)

    def _score(
        self,
        verdict: dict[str, Any],
        key: str,
    ) -> int:
        scores = verdict.get(
            "scores",
            {},
        )

        try:
            return int(
                max(
                    0,
                    min(
                        100,
                        float(
                            scores.get(
                                key,
                                0,
                            )
                        ),
                    ),
                )
            )
        except (
            TypeError,
            ValueError,
        ):
            return 0

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

    def _extract_claim_coverage(
        self,
        claim_analysis: Any,
    ) -> float:
        if not isinstance(
            claim_analysis,
            dict,
        ):
            return 0.0

        for key in (
            "evidence_coverage_percent",
            "claim_evidence_coverage_percent",
            "coverage_percent",
        ):
            if key in claim_analysis:
                try:
                    return max(
                        0.0,
                        min(
                            100.0,
                            float(
                                claim_analysis[key]
                            ),
                        ),
                    )
                except (
                    TypeError,
                    ValueError,
                ):
                    pass

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

        if claim_count > 0:
            return round(
                (
                    claims_with_evidence
                    / claim_count
                )
                * 100,
                1,
            )

        return 0.0

    def _feasibility_label(
        self,
        score: int,
    ) -> str:
        if score >= 80:
            return "HIGH"

        if score >= 60:
            return "MEDIUM-HIGH"

        if score >= 40:
            return "MEDIUM"

        return "LOW"


innovation_agent = InnovationAgent()