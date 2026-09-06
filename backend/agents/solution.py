from __future__ import annotations

from typing import Any

from models.project import AURAProject
from orchestration.contract import AURAStageResult
from orchestration.stages import AURAStage


class SolutionAgent:
    """
    AURA Stage 06 — Solution Architect

    Converts the evidence-backed innovation direction from Stage 05
    into a structured, traceable and build-oriented solution design.

    Design principle:
        Research → Evidence → Verdict → Innovation → Solution

    Important:
        This agent produces an AI-generated design recommendation.
        It does NOT claim that the solution is experimentally validated,
        globally novel, deployed, or expert-approved.
    """

    stage = AURAStage.SOLUTION

    async def run(
        self,
        project: AURAProject,
    ) -> AURAStageResult:
        try:
            analysis = project.analysis or {}

            research = project.research or {}

            research_intelligence = analysis.get(
                "research_intelligence",
                {},
            ) or {}

            verdict = analysis.get(
                "verdict",
                {},
            ) or {}

            innovation = (
                project.innovation
                or analysis.get("innovation", {})
                or {}
            )

            directions = self._as_list(
                innovation.get("directions", [])
            )

            if not directions:
                return AURAStageResult(
                    stage=self.stage,
                    success=False,
                    message=(
                        "AURA cannot design a solution because "
                        "no innovation directions are available "
                        "from the previous stage."
                    ),
                )

            selected = self._select_direction(
                innovation
            )

            if not selected:
                return AURAStageResult(
                    stage=self.stage,
                    success=False,
                    message=(
                        "AURA could not identify a valid innovation "
                        "direction for solution architecture."
                    ),
                )

            solution = self._build_solution(
                project=project,
                research=research,
                research_intelligence=research_intelligence,
                verdict=verdict,
                innovation=innovation,
                selected=selected,
            )

            project.solution = solution
            project.analysis["solution"] = solution

            project.memory.append(
                {
                    "stage": self.stage.value,
                    "type": "solution_design",
                    "summary": solution["summary"],
                    "selected_innovation": selected.get(
                        "title"
                    ),
                    "evidence_coverage": solution[
                        "evidence_context"
                    ].get(
                        "claim_evidence_coverage_percent"
                    ),
                }
            )

            project.evidence.append(
                {
                    "stage": self.stage.value,
                    "type": "solution_design",
                    "status": "aura_synthesis",
                    "source": (
                        "AURA research intelligence, evidence "
                        "analysis, verdict and innovation engine"
                    ),
                    "claim": (
                        "The proposed solution is derived from "
                        "the evidence-backed research landscape, "
                        "identified gaps and selected innovation "
                        "direction."
                    ),
                    "verification_scope": (
                        "AI-generated design recommendation. "
                        "Implementation, experimentation, expert "
                        "review and deployment validation remain pending."
                    ),
                    "claim_evidence_coverage_percent": solution[
                        "evidence_context"
                    ].get(
                        "claim_evidence_coverage_percent"
                    ),
                }
            )

            return AURAStageResult(
                stage=self.stage,
                success=True,
                message=(
                    "AURA converted the evidence-backed innovation "
                    "direction into a traceable, feasibility-aware "
                    "and build-oriented solution design."
                ),
                data={
                    "solution": solution,
                },
                next_stage=AURAStage.ARCHITECT,
            )

        except Exception as error:
            return AURAStageResult(
                stage=self.stage,
                success=False,
                message=(
                    f"Solution design failed: {error}"
                ),
            )

    # ============================================================
    # MASTER SOLUTION BUILDER
    # ============================================================

    def _build_solution(
        self,
        project: AURAProject,
        research: dict[str, Any],
        research_intelligence: dict[str, Any],
        verdict: dict[str, Any],
        innovation: dict[str, Any],
        selected: dict[str, Any],
    ) -> dict[str, Any]:

        idea = (
            project.original_idea or ""
        ).strip()

        understanding = (
            project.analysis.get(
                "problem_understanding",
                {},
            )
            or {}
        )

        innovation_title = self._clean_text(
            selected.get(
                "title",
                "Selected Innovation",
            )
        )

        category = self._clean_text(
            selected.get(
                "category",
                "Intelligent System",
            )
        )

        proposed_innovation = self._clean_text(
            selected.get(
                "proposed_innovation",
                "",
            )
        )

        expected_contribution = self._clean_text(
            selected.get(
                "expected_contribution",
                "",
            )
        )

        existing_approach = self._clean_text(
            selected.get(
                "existing_approach",
                "",
            )
        )

        limitation = self._clean_text(
            selected.get(
                "limitation",
                "",
            )
        )

        research_gap = self._clean_text(
            selected.get(
                "research_gap",
                "",
            )
        )

        technical_mechanism = self._string_list(
            selected.get(
                "technical_mechanism",
                [],
            )
        )

        validation_requirements = self._string_list(
            selected.get(
                "validation_requirements",
                [],
            )
        )

        research_questions = self._string_list(
            selected.get(
                "research_questions",
                [],
            )
        )

        domains = self._string_list(
            understanding.get(
                "domains",
                project.domain,
            )
        )

        objectives = self._string_list(
            understanding.get(
                "objectives",
                project.objectives,
            )
        )

        requirements = self._string_list(
            understanding.get(
                "functional_requirements",
                project.requirements,
            )
        )

        constraints = self._string_list(
            understanding.get(
                "constraints",
                project.constraints,
            )
        )

        papers = self._as_list(
            research.get(
                "papers",
                [],
            )
        )

        claim_analysis = (
            research_intelligence.get(
                "claim_analysis",
                {},
            )
            or {}
        )

        evidence_synthesis = (
            research_intelligence.get(
                "evidence_synthesis",
                {},
            )
            or {}
        )

        claim_evidence_map = (
            research.get(
                "claim_evidence_map",
                {},
            )
            or {}
        )

        components = self._build_components(
            technical_mechanism=technical_mechanism,
            idea=idea,
        )

        data_flow = self._build_data_flow(
            technical_mechanism=technical_mechanism,
        )

        ai_layer = self._build_ai_layer(
            technical_mechanism=technical_mechanism,
            innovation_title=innovation_title,
            research_intelligence=research_intelligence,
        )

        hardware = self._build_hardware(
            idea=idea,
            technical_mechanism=technical_mechanism,
            domains=domains,
        )

        software = self._build_software(
            technical_mechanism=technical_mechanism,
        )

        features = self._build_features(
            innovation_title=innovation_title,
            technical_mechanism=technical_mechanism,
            requirements=requirements,
        )

        users = self._build_users(
            project=project,
            understanding=understanding,
        )

        implementation = self._build_implementation(
            components=components,
            ai_layer=ai_layer,
            hardware=hardware,
            software=software,
        )

        validation = self._build_validation(
            requirements=requirements,
            research_questions=research_questions,
            validation_requirements=validation_requirements,
            research_intelligence=research_intelligence,
        )

        evidence_context = self._build_evidence_context(
            research=research,
            research_intelligence=research_intelligence,
            verdict=verdict,
            innovation=innovation,
            selected=selected,
            claim_analysis=claim_analysis,
            evidence_synthesis=evidence_synthesis,
            claim_evidence_map=claim_evidence_map,
            papers=papers,
        )

        solution_rationale = self._build_solution_rationale(
            existing_approach=existing_approach,
            limitation=limitation,
            research_gap=research_gap,
            proposed_innovation=proposed_innovation,
            expected_contribution=expected_contribution,
        )

        feasibility = self._build_feasibility(
            verdict=verdict,
            selected=selected,
            constraints=constraints,
        )

        risks = self._build_risks(
            constraints=constraints,
            research_intelligence=research_intelligence,
            technical_mechanism=technical_mechanism,
        )

        traceability = self._build_traceability(
            selected=selected,
            research=research,
            research_intelligence=research_intelligence,
            verdict=verdict,
            evidence_context=evidence_context,
        )

        summary = (
            f"AURA designed a build-oriented solution for "
            f"'{idea}' using the selected innovation direction "
            f"'{innovation_title}'. The design connects the "
            f"identified research gap, evidence context, "
            f"technical mechanisms, system components, AI layer, "
            f"implementation strategy and validation requirements. "
            f"The design remains an AURA recommendation and is "
            f"not presented as experimentally validated or "
            f"globally novel."
        )

        return {
            "summary": summary,

            "status": "solution_designed",

            "solution_title": (
                f"AURA Solution — {innovation_title}"
            ),

            "problem_context": {
                "original_idea": idea,
                "interpreted_problem": self._clean_text(
                    understanding.get(
                        "problem_definition",
                        idea,
                    )
                ),
                "target_context": self._clean_text(
                    understanding.get(
                        "target_context",
                        "",
                    )
                ),
                "domains": domains,
            },

            "solution_rationale": solution_rationale,

            "innovation_basis": {
                "title": innovation_title,
                "category": category,
                "proposed_innovation": proposed_innovation,
                "expected_contribution": expected_contribution,
                "existing_approach": existing_approach,
                "limitation": limitation,
                "research_gap": research_gap,
                "evidence_status": "AURA_RECOMMENDATION",
            },

            "solution_objective": (
                "Design and implement a measurable intelligent "
                "system that addresses the research opportunity "
                "identified by AURA while preserving traceability "
                "between research evidence, innovation and "
                "implementation decisions."
            ),

            "core_features": features,

            "users_and_stakeholders": users,

            "system_components": components,

            "data_flow": data_flow,

            "ai_intelligence": ai_layer,

            "hardware": hardware,

            "software": software,

            "implementation": implementation,

            "feasibility": feasibility,

            "risks_and_dependencies": risks,

            "expected_outputs": [
                "Real-time system state where applicable",
                "AI-generated prediction, classification or recommendation",
                "Decision-support or intervention output",
                "Confidence or uncertainty information",
                "Historical records for analysis",
                "Dashboard or user-facing visualization",
                "Validation and experiment records",
                "Traceable evidence-to-solution mapping",
            ],

            "validation": validation,

            "research_questions": research_questions,

            "objectives": objectives,

            "requirements": requirements,

            "constraints": constraints,

            "evidence_context": evidence_context,

            "traceability": traceability,

            "design_assumptions": [
                (
                    "Required datasets, sensors, APIs, devices or "
                    "domain resources must be available."
                ),
                (
                    "Candidate AI/ML methods must be evaluated "
                    "against appropriate baselines."
                ),
                (
                    "Research evidence supports the design rationale "
                    "but does not itself prove implementation success."
                ),
                (
                    "Real-world performance may differ from "
                    "laboratory or dataset performance."
                ),
                (
                    "Final technology selection must be confirmed "
                    "during detailed architecture and feasibility analysis."
                ),
                (
                    "Expert review may be required for domain-specific "
                    "safety, regulatory or high-impact decisions."
                ),
            ],

            "verification_scope": {
                "research_evidence_used": (
                    evidence_context.get(
                        "research_evidence_available",
                        False,
                    )
                ),
                "claim_evidence_coverage_percent": (
                    evidence_context.get(
                        "claim_evidence_coverage_percent",
                        0,
                    )
                ),
                "solution_is_ai_generated_design": True,
                "research_gap_verified": (
                    bool(research_gap)
                ),
                "implementation_verified": False,
                "experimental_validation_completed": False,
                "deployment_verified": False,
                "expert_review_required": True,
                "global_novelty_claim_allowed": False,
            },

            "next_stage_focus": [
                "Convert the solution into a detailed system architecture.",
                "Define component interfaces and responsibilities.",
                "Map data movement between components.",
                "Select concrete hardware and software technologies.",
                "Define deployment and communication architecture.",
                "Define module boundaries for implementation.",
                "Prepare architecture-level technology decisions.",
            ],
        }

    # ============================================================
    # SOLUTION RATIONALE
    # ============================================================

    def _build_solution_rationale(
        self,
        existing_approach: str,
        limitation: str,
        research_gap: str,
        proposed_innovation: str,
        expected_contribution: str,
    ) -> dict[str, str]:

        return {
            "existing_approach": (
                existing_approach
                or "Existing approaches identified during research."
            ),
            "identified_limitation": (
                limitation
                or "Limitations identified from the research landscape."
            ),
            "research_gap": (
                research_gap
                or "A research opportunity requiring further validation."
            ),
            "proposed_change": (
                proposed_innovation
                or "AURA-proposed improvement based on the selected direction."
            ),
            "expected_contribution": (
                expected_contribution
                or "A measurable improvement requiring experimental validation."
            ),
        }

    # ============================================================
    # EVIDENCE CONTEXT
    # ============================================================

    def _build_evidence_context(
        self,
        research: dict[str, Any],
        research_intelligence: dict[str, Any],
        verdict: dict[str, Any],
        innovation: dict[str, Any],
        selected: dict[str, Any],
        claim_analysis: dict[str, Any],
        evidence_synthesis: dict[str, Any],
        claim_evidence_map: dict[str, Any],
        papers: list[Any],
    ) -> dict[str, Any]:

        claim_count = self._number(
            claim_analysis.get(
                "claim_count",
                0,
            )
        )

        claims_with_evidence = self._number(
            claim_analysis.get(
                "claims_with_evidence",
                0,
            )
        )

        claims_without_evidence = self._number(
            claim_analysis.get(
                "claims_without_evidence",
                0,
            )
        )

        coverage = self._number(
            claim_analysis.get(
                "evidence_coverage_percent",
                0,
            )
        )

        average_strength = self._number(
            claim_analysis.get(
                "average_evidence_strength",
                0,
            )
        )

        if coverage <= 0 and claim_count > 0:
            coverage = round(
                (
                    claims_with_evidence
                    / claim_count
                )
                * 100,
                2,
            )

        evidence_strength = self._extract_score(
            verdict,
            "evidence_strength",
        )

        opportunity_score = self._extract_score(
            verdict,
            "opportunity_score",
        )

        feasibility_score = self._extract_score(
            verdict,
            "technical_feasibility",
        )

        gap_strength = self._extract_score(
            verdict,
            "research_gap_strength",
        )

        innovation_confidence = (
            innovation.get(
                "innovation_confidence",
                {},
            )
            or {}
        )

        selected_research_context = (
            selected.get(
                "research_evidence_context",
                {},
            )
            or {}
        )

        evidence_ids = self._collect_evidence_ids(
            research=research,
            selected=selected,
        )

        return {
            "research_evidence_available": bool(
                papers
                or research.get("evidence_records")
                or research.get("source_registry")
            ),

            "paper_count_used": len(
                papers
            ),

            "claim_count": claim_count,

            "claims_with_evidence": claims_with_evidence,

            "claims_without_evidence": claims_without_evidence,

            "claim_evidence_coverage_percent": coverage,

            "average_claim_evidence_strength": (
                average_strength
            ),

            "evidence_strength_score": evidence_strength,

            "research_gap_strength_score": gap_strength,

            "technical_feasibility_score": feasibility_score,

            "opportunity_score": opportunity_score,

            "evidence_synthesis_available": bool(
                evidence_synthesis
            ),

            "claim_evidence_map_available": bool(
                claim_evidence_map
            ),

            "supporting_evidence_ids": evidence_ids,

            "selected_innovation_evidence_status": (
                selected.get(
                    "evidence_status",
                    "AURA_RECOMMENDATION",
                )
            ),

            "selected_innovation_evidence_basis": (
                selected_research_context
            ),

            "innovation_confidence": {
                "score": self._number(
                    innovation_confidence.get(
                        "score",
                        0,
                    )
                ),
                "level": self._clean_text(
                    innovation_confidence.get(
                        "level",
                        "UNKNOWN",
                    )
                ),
            },

            "verification_interpretation": (
                "Research evidence supports the reasoning "
                "behind this design. It does not prove that "
                "the proposed solution will outperform existing "
                "systems until implementation and experiments "
                "are completed."
            ),
        }

    # ============================================================
    # COMPONENT ARCHITECTURE
    # ============================================================

    def _build_components(
        self,
        technical_mechanism: list[str],
        idea: str,
    ) -> list[dict[str, Any]]:

        mechanisms = " ".join(
            technical_mechanism
        ).lower()

        components = [
            {
                "id": "COMP-01",
                "name": "Data Acquisition Layer",
                "purpose": (
                    "Collect relevant sensor, user, dataset, "
                    "environmental or external information."
                ),
                "inputs": [
                    "Sensors",
                    "Datasets",
                    "External APIs",
                    "User input",
                ],
                "outputs": [
                    "Raw data stream",
                ],
            },
            {
                "id": "COMP-02",
                "name": "Data Processing Layer",
                "purpose": (
                    "Clean, validate, normalize, synchronize "
                    "and prepare incoming data."
                ),
                "inputs": [
                    "Raw data",
                ],
                "outputs": [
                    "Validated processed data",
                ],
            },
            {
                "id": "COMP-03",
                "name": "Feature / Representation Layer",
                "purpose": (
                    "Extract meaningful features, embeddings, "
                    "patterns or representations."
                ),
                "inputs": [
                    "Processed data",
                ],
                "outputs": [
                    "Model-ready representation",
                ],
            },
            {
                "id": "COMP-04",
                "name": "Intelligence Layer",
                "purpose": (
                    "Apply the selected AI, ML, analytics, "
                    "prediction, classification or anomaly "
                    "detection methods."
                ),
                "inputs": [
                    "Model-ready data",
                ],
                "outputs": [
                    "Prediction",
                    "Classification",
                    "Recommendation",
                    "Risk signal",
                ],
            },
            {
                "id": "COMP-05",
                "name": "Decision / Reasoning Layer",
                "purpose": (
                    "Translate intelligence outputs and system "
                    "context into interpretable decisions."
                ),
                "inputs": [
                    "AI outputs",
                    "System rules",
                    "Context",
                ],
                "outputs": [
                    "Decision",
                    "Alert",
                    "Recommended action",
                ],
            },
            {
                "id": "COMP-06",
                "name": "Application Layer",
                "purpose": (
                    "Expose monitoring, intelligence, decisions "
                    "and reporting capabilities to users."
                ),
                "inputs": [
                    "Data",
                    "AI results",
                    "Decision outputs",
                ],
                "outputs": [
                    "Dashboard",
                    "Reports",
                    "Alerts",
                ],
            },
            {
                "id": "COMP-07",
                "name": "Feedback / Learning Layer",
                "purpose": (
                    "Capture outcomes and feedback for evaluation, "
                    "monitoring and future improvement."
                ),
                "inputs": [
                    "System outcomes",
                    "User feedback",
                    "Validation results",
                ],
                "outputs": [
                    "Evaluation records",
                    "Improvement signals",
                ],
            },
        ]

        if (
            "edge" in mechanisms
            or "iot" in mechanisms
            or "real-time" in mechanisms
            or "realtime" in mechanisms
        ):
            components.insert(
                3,
                {
                    "id": "COMP-EDGE",
                    "name": "Edge Intelligence Layer",
                    "purpose": (
                        "Perform selected processing or inference "
                        "near the data source to reduce latency "
                        "and communication requirements."
                    ),
                    "inputs": [
                        "Sensor or local data",
                    ],
                    "outputs": [
                        "Local inference",
                        "Filtered data",
                    ],
                },
            )

        return components

    # ============================================================
    # DATA FLOW
    # ============================================================

    def _build_data_flow(
        self,
        technical_mechanism: list[str],
    ) -> list[dict[str, Any]]:

        mechanisms = " ".join(
            technical_mechanism
        ).lower()

        flow = [
            {
                "step": 1,
                "stage": "INPUT",
                "description": (
                    "Collect raw information from relevant "
                    "devices, datasets, users or external sources."
                ),
            },
            {
                "step": 2,
                "stage": "VALIDATE",
                "description": (
                    "Check completeness, quality, consistency "
                    "and validity of incoming information."
                ),
            },
            {
                "step": 3,
                "stage": "PREPROCESS",
                "description": (
                    "Clean, normalize, synchronize and transform "
                    "data into a usable representation."
                ),
            },
            {
                "step": 4,
                "stage": "FEATURES",
                "description": (
                    "Extract relevant features, embeddings, "
                    "patterns or representations."
                ),
            },
            {
                "step": 5,
                "stage": "INTELLIGENCE",
                "description": (
                    "Apply the selected AI/ML/analytics mechanisms."
                ),
            },
            {
                "step": 6,
                "stage": "DECISION",
                "description": (
                    "Convert model outputs into a recommendation, "
                    "risk signal, classification or decision."
                ),
            },
            {
                "step": 7,
                "stage": "ACTION",
                "description": (
                    "Trigger an intervention, notification, "
                    "automation or user decision where applicable."
                ),
            },
            {
                "step": 8,
                "stage": "FEEDBACK",
                "description": (
                    "Capture outcomes and feedback for validation, "
                    "monitoring and future improvement."
                ),
            },
        ]

        if (
            "closed-loop" in mechanisms
            or "feedback" in mechanisms
            or "adaptive" in mechanisms
        ):
            flow.append(
                {
                    "step": 9,
                    "stage": "ADAPT",
                    "description": (
                        "Use validated feedback to update "
                        "thresholds, models, rules or future decisions."
                    ),
                }
            )

        return flow

    # ============================================================
    # AI INTELLIGENCE
    # ============================================================

    def _build_ai_layer(
        self,
        technical_mechanism: list[str],
        innovation_title: str,
        research_intelligence: dict[str, Any],
    ) -> dict[str, Any]:

        mechanisms = [
            item.lower()
            for item in technical_mechanism
        ]

        corpus_text = " ".join(
            self._string_list(
                research_intelligence.get(
                    "methods",
                    [],
                )
            )
        ).lower()

        models: list[str] = []

        if any(
            "time-series" in item
            or "time series" in item
            or "temporal" in item
            for item in mechanisms
        ):
            models.extend(
                [
                    "LSTM / GRU",
                    "Temporal Transformer",
                ]
            )

        if any(
            "anomaly" in item
            for item in mechanisms
        ):
            models.append(
                "Isolation Forest / Autoencoder"
            )

        if any(
            "classification" in item
            or "machine learning" in item
            or "prediction" in item
            for item in mechanisms
        ):
            models.extend(
                [
                    "Random Forest",
                    "XGBoost",
                    "Neural Network",
                ]
            )

        if (
            "transformer" in corpus_text
            and "Transformer" not in models
        ):
            models.append(
                "Transformer-based model"
            )

        if any(
            "computer vision" in item
            or "image" in item
            or "vision" in item
            for item in mechanisms
        ):
            models.extend(
                [
                    "YOLO-family detector where appropriate",
                    "CNN / Vision Transformer",
                ]
            )

        if not models:
            models = [
                "Baseline statistical model",
                "Tree-based ML model",
                "Neural model where justified",
            ]

        models = self._unique_strings(
            models
        )

        return {
            "role": (
                f"Provide the intelligence required by "
                f"'{innovation_title}'."
            ),

            "candidate_model_families": models,

            "processing": [
                "Data preprocessing",
                "Feature engineering or representation learning",
                "Model inference",
                "Confidence / uncertainty estimation",
                "Performance monitoring",
            ],

            "explainability": [
                "Feature importance where supported",
                "Prediction confidence",
                "Decision rationale",
                "Failure-case inspection",
            ],

            "baseline_requirement": (
                "Every proposed AI/ML model must be evaluated "
                "against a suitable baseline or competing approach."
            ),

            "model_selection_policy": (
                "Final model selection must depend on the "
                "research evidence, dataset characteristics, "
                "validation results, computational resources, "
                "latency requirements and deployment constraints."
            ),

            "research_alignment": (
                "Candidate models are design options, not "
                "claims that any specific model is already proven "
                "to be optimal for this project."
            ),
        }

    # ============================================================
    # HARDWARE
    # ============================================================

    def _build_hardware(
        self,
        idea: str,
        technical_mechanism: list[str],
        domains: list[str],
    ) -> list[dict[str, Any]]:

        mechanisms = " ".join(
            technical_mechanism
        ).lower()

        domain_text = " ".join(
            domains
        ).lower()

        hardware = []

        if (
            "sensor" in mechanisms
            or "iot" in mechanisms
            or "smart agriculture" in domain_text
            or "agriculture" in idea.lower()
        ):
            hardware.append(
                {
                    "category": "Sensors / Actuators",
                    "candidates": [
                        "Domain-specific sensors",
                        "Environmental sensors",
                        "Actuators where required",
                    ],
                    "selection_status": (
                        "Exact components must be selected "
                        "from final measurable requirements."
                    ),
                }
            )

        hardware.extend(
            [
                {
                    "category": "Controller / Edge Device",
                    "candidates": [
                        "ESP32",
                        "Raspberry Pi",
                        "Arduino",
                    ],
                    "selection_status": (
                        "To be finalized based on computation, "
                        "connectivity and deployment requirements."
                    ),
                },
                {
                    "category": "Connectivity",
                    "candidates": [
                        "Wi-Fi",
                        "LoRa / LoRaWAN",
                        "Bluetooth",
                        "4G/5G where required",
                    ],
                    "selection_status": (
                        "Depends on deployment environment and range."
                    ),
                },
            ]
        )

        return hardware

    # ============================================================
    # SOFTWARE
    # ============================================================

    def _build_software(
        self,
        technical_mechanism: list[str],
    ) -> list[dict[str, Any]]:

        return [
            {
                "layer": "Backend",
                "candidates": [
                    "Python",
                    "FastAPI",
                    "Node.js where appropriate",
                ],
                "purpose": (
                    "Application services, APIs and orchestration."
                ),
            },
            {
                "layer": "AI / ML",
                "candidates": [
                    "Python",
                    "scikit-learn",
                    "PyTorch",
                    "TensorFlow where appropriate",
                ],
                "purpose": (
                    "Model development, inference and evaluation."
                ),
            },
            {
                "layer": "Database",
                "candidates": [
                    "PostgreSQL",
                    "SQLite for prototype",
                    "Time-series database where required",
                ],
                "purpose": (
                    "Store project, operational and experimental data."
                ),
            },
            {
                "layer": "Frontend",
                "candidates": [
                    "Next.js",
                    "React",
                    "Dashboard visualization",
                ],
                "purpose": (
                    "User interaction, monitoring and visualization."
                ),
            },
            {
                "layer": "Communication",
                "candidates": [
                    "REST API",
                    "MQTT",
                    "WebSocket where real-time updates are required",
                ],
                "purpose": (
                    "Data and service communication."
                ),
            },
        ]

    # ============================================================
    # FEATURES
    # ============================================================

    def _build_features(
        self,
        innovation_title: str,
        technical_mechanism: list[str],
        requirements: list[str],
    ) -> list[dict[str, Any]]:

        features = [
            {
                "id": "FEAT-01",
                "name": "Data Monitoring",
                "priority": "HIGH",
                "description": (
                    "Monitor relevant incoming data and system conditions."
                ),
            },
            {
                "id": "FEAT-02",
                "name": "Intelligent Analysis",
                "priority": "HIGH",
                "description": (
                    f"Apply intelligence associated with "
                    f"'{innovation_title}'."
                ),
            },
            {
                "id": "FEAT-03",
                "name": "Prediction / Recommendation",
                "priority": "HIGH",
                "description": (
                    "Generate actionable predictions, "
                    "recommendations or risk signals where justified."
                ),
            },
            {
                "id": "FEAT-04",
                "name": "Decision Support",
                "priority": "HIGH",
                "description": (
                    "Translate analytical outputs into "
                    "interpretable decision-support information."
                ),
            },
            {
                "id": "FEAT-05",
                "name": "Alerts",
                "priority": "MEDIUM",
                "description": (
                    "Notify users when important conditions "
                    "or risk thresholds are detected."
                ),
            },
            {
                "id": "FEAT-06",
                "name": "Historical Analytics",
                "priority": "MEDIUM",
                "description": (
                    "Store and visualize historical information "
                    "for comparison and evaluation."
                ),
            },
            {
                "id": "FEAT-07",
                "name": "Explainability",
                "priority": "MEDIUM",
                "description": (
                    "Expose confidence, feature importance or "
                    "decision rationale where technically supported."
                ),
            },
            {
                "id": "FEAT-08",
                "name": "Validation Monitoring",
                "priority": "MEDIUM",
                "description": (
                    "Track model/system performance against "
                    "defined validation metrics."
                ),
            },
        ]

        if requirements:
            features.append(
                {
                    "id": "FEAT-REQ",
                    "name": "Requirement Alignment",
                    "priority": "HIGH",
                    "description": (
                        "Implementation must map final features "
                        "to the functional requirements identified "
                        "during Stage 01."
                    ),
                }
            )

        return features

    # ============================================================
    # USERS
    # ============================================================

    def _build_users(
        self,
        project: AURAProject,
        understanding: dict[str, Any],
    ) -> list[dict[str, Any]]:

        stakeholders = self._string_list(
            understanding.get(
                "stakeholders",
                [],
            )
        )

        if not stakeholders:
            stakeholders = [
                "Primary end user",
                "Project developer",
                "Domain expert",
                "System administrator",
            ]

        return [
            {
                "role": stakeholder,
                "interaction": (
                    "Uses relevant monitoring, decision-support, "
                    "development, reporting or validation functions."
                ),
            }
            for stakeholder in stakeholders[:8]
        ]

    # ============================================================
    # IMPLEMENTATION
    # ============================================================

    def _build_implementation(
        self,
        components: list[dict[str, Any]],
        ai_layer: dict[str, Any],
        hardware: list[dict[str, Any]],
        software: list[dict[str, Any]],
    ) -> dict[str, Any]:

        return {
            "phases": [
                {
                    "phase": 1,
                    "name": "Requirements & Scope",
                    "activities": [
                        "Freeze measurable requirements",
                        "Define system boundaries",
                        "Identify data and hardware dependencies",
                        "Define success metrics",
                    ],
                },
                {
                    "phase": 2,
                    "name": "Prototype",
                    "activities": [
                        "Prepare development environment",
                        "Connect initial data sources",
                        "Build minimum viable workflow",
                    ],
                },
                {
                    "phase": 3,
                    "name": "Data Pipeline",
                    "activities": [
                        "Implement acquisition",
                        "Implement validation and preprocessing",
                        "Store historical data",
                        "Document dataset characteristics",
                    ],
                },
                {
                    "phase": 4,
                    "name": "Intelligence",
                    "activities": [
                        "Prepare dataset",
                        "Train baseline models",
                        "Train candidate models",
                        "Evaluate candidate models",
                    ],
                },
                {
                    "phase": 5,
                    "name": "System Integration",
                    "activities": [
                        "Integrate AI with backend",
                        "Integrate hardware where required",
                        "Build user interface",
                        "Connect monitoring and decision layers",
                    ],
                },
                {
                    "phase": 6,
                    "name": "Experimentation",
                    "activities": [
                        "Define controlled experiments",
                        "Run baseline comparison",
                        "Perform ablation or sensitivity analysis where appropriate",
                        "Analyze failure cases",
                    ],
                },
                {
                    "phase": 7,
                    "name": "Validation & Delivery",
                    "activities": [
                        "Validate against success criteria",
                        "Document limitations",
                        "Prepare reproducibility records",
                        "Prepare project deliverables",
                    ],
                },
            ],

            "component_count": len(
                components
            ),

            "hardware_categories": len(
                hardware
            ),

            "software_layers": len(
                software
            ),

            "ai_model_candidates": len(
                ai_layer.get(
                    "candidate_model_families",
                    [],
                )
            ),
        }

    # ============================================================
    # VALIDATION
    # ============================================================

    def _build_validation(
        self,
        requirements: list[str],
        research_questions: list[str],
        validation_requirements: list[str],
        research_intelligence: dict[str, Any],
    ) -> dict[str, Any]:

        tests = self._unique_strings(
            validation_requirements
            + requirements
        )

        if not tests:
            tests = [
                "Compare system performance against a baseline.",
                "Measure prediction, classification or decision quality.",
                "Evaluate latency and resource usage where applicable.",
                "Test robustness under changing conditions.",
                "Evaluate failure cases and edge cases.",
                "Document reproducibility conditions.",
            ]

        metrics = [
            "Accuracy where applicable",
            "Precision",
            "Recall",
            "F1-score",
            "MAE / RMSE for regression",
            "Latency",
            "Resource consumption",
            "False-positive rate",
            "False-negative rate",
            "Robustness / sensitivity",
        ]

        return {
            "required_tests": tests,

            "candidate_metrics": metrics,

            "experimental_comparison": (
                "The proposed system should be compared against "
                "a clearly defined baseline or existing approach."
            ),

            "research_questions_to_validate": (
                research_questions[:10]
            ),

            "research_alignment": (
                "Validation should directly test the claims, "
                "research questions and expected contribution "
                "that motivated the solution."
            ),

            "success_policy": (
                "The solution should only be considered successful "
                "after measurable experimental evidence supports "
                "the intended improvement."
            ),

            "failure_policy": (
                "Negative or inconclusive results must be retained "
                "and reported rather than hidden."
            ),
        }

    # ============================================================
    # FEASIBILITY
    # ============================================================

    def _build_feasibility(
        self,
        verdict: dict[str, Any],
        selected: dict[str, Any],
        constraints: list[str],
    ) -> dict[str, Any]:

        technical = self._extract_score(
            verdict,
            "technical_feasibility",
        )

        opportunity = self._extract_score(
            verdict,
            "opportunity_score",
        )

        selected_feasibility = (
            selected.get(
                "feasibility",
                {},
            )
            or {}
        )

        direction_score = self._number(
            selected_feasibility.get(
                "score",
                selected.get(
                    "innovation_score",
                    0,
                ),
            )
        )

        if technical >= 70:
            technical_assessment = "HIGH"
        elif technical >= 45:
            technical_assessment = "MEDIUM"
        else:
            technical_assessment = "LOW"

        if constraints:
            dependency_note = (
                "Implementation depends on resolving the "
                "constraints identified during problem understanding."
            )
        else:
            dependency_note = (
                "No explicit implementation constraints were "
                "carried forward from Stage 01."
            )

        return {
            "technical_feasibility_score": technical,
            "technical_feasibility_assessment": technical_assessment,
            "opportunity_score": opportunity,
            "selected_direction_feasibility_score": direction_score,
            "implementation_dependency_note": dependency_note,
            "overall_interpretation": (
                "Feasibility is an AURA assessment based on "
                "available research and design signals. It is "
                "not a guarantee of successful implementation."
            ),
        }

    # ============================================================
    # RISKS
    # ============================================================

    def _build_risks(
        self,
        constraints: list[str],
        research_intelligence: dict[str, Any],
        technical_mechanism: list[str],
    ) -> list[dict[str, Any]]:

        risks = [
            {
                "id": "RISK-01",
                "risk": "Data quality",
                "impact": "HIGH",
                "mitigation": (
                    "Validate data quality, missingness, "
                    "noise and distribution before training."
                ),
            },
            {
                "id": "RISK-02",
                "risk": "Model overfitting",
                "impact": "HIGH",
                "mitigation": (
                    "Use appropriate train/validation/test splits, "
                    "cross-validation and baseline comparisons."
                ),
            },
            {
                "id": "RISK-03",
                "risk": "Domain shift",
                "impact": "MEDIUM",
                "mitigation": (
                    "Evaluate performance under realistic "
                    "deployment conditions."
                ),
            },
            {
                "id": "RISK-04",
                "risk": "Insufficient evidence",
                "impact": "MEDIUM",
                "mitigation": (
                    "Maintain claim-to-evidence traceability "
                    "and flag unsupported claims."
                ),
            },
            {
                "id": "RISK-05",
                "risk": "Implementation complexity",
                "impact": "MEDIUM",
                "mitigation": (
                    "Build incrementally using clear module "
                    "boundaries and prototype milestones."
                ),
            },
        ]

        if constraints:
            risks.append(
                {
                    "id": "RISK-CONSTRAINT",
                    "risk": "Project constraints",
                    "impact": "MEDIUM",
                    "mitigation": (
                        "Resolve or explicitly document the "
                        "constraints before final implementation."
                    ),
                }
            )

        mechanisms = " ".join(
            technical_mechanism
        ).lower()

        if (
            "real-time" in mechanisms
            or "realtime" in mechanisms
            or "edge" in mechanisms
        ):
            risks.append(
                {
                    "id": "RISK-REALTIME",
                    "risk": "Latency / resource limitations",
                    "impact": "MEDIUM",
                    "mitigation": (
                        "Measure latency, memory and compute "
                        "requirements under realistic workloads."
                    ),
                }
            )

        return risks

    # ============================================================
    # TRACEABILITY
    # ============================================================

    def _build_traceability(
        self,
        selected: dict[str, Any],
        research: dict[str, Any],
        research_intelligence: dict[str, Any],
        verdict: dict[str, Any],
        evidence_context: dict[str, Any],
    ) -> dict[str, Any]:

        return {
            "pipeline": [
                {
                    "stage": "UNDERSTAND",
                    "source": "Problem understanding",
                    "status": "carried_forward",
                },
                {
                    "stage": "INVESTIGATE",
                    "source": "Cross-source literature discovery",
                    "status": (
                        "evidence_backed"
                        if evidence_context.get(
                            "research_evidence_available"
                        )
                        else "limited_evidence"
                    ),
                },
                {
                    "stage": "ANALYZE",
                    "source": "Research intelligence",
                    "status": (
                        "evidence_synthesis"
                        if evidence_context.get(
                            "evidence_synthesis_available"
                        )
                        else "ai_analysis"
                    ),
                },
                {
                    "stage": "VERDICT",
                    "source": "Evidence-aware research verdict",
                    "status": "ai_synthesis",
                },
                {
                    "stage": "INNOVATE",
                    "source": selected.get(
                        "title",
                        "Selected innovation",
                    ),
                    "status": "aura_recommendation",
                },
                {
                    "stage": "SOLUTION",
                    "source": "AURA Solution Architect",
                    "status": "aura_design",
                },
            ],

            "selected_innovation": selected.get(
                "title",
                "",
            ),

            "supporting_evidence_ids": (
                evidence_context.get(
                    "supporting_evidence_ids",
                    [],
                )
            ),

            "claim_evidence_coverage_percent": (
                evidence_context.get(
                    "claim_evidence_coverage_percent",
                    0,
                )
            ),

            "verification_boundary": (
                "Solution design is derived from available "
                "research intelligence but still requires "
                "implementation and experimental validation."
            ),
        }

    # ============================================================
    # SELECTION
    # ============================================================

    def _select_direction(
        self,
        innovation: dict[str, Any],
    ) -> dict[str, Any] | None:

        recommended = innovation.get(
            "recommended_direction"
        )

        if isinstance(
            recommended,
            dict,
        ) and recommended:
            return recommended

        directions = innovation.get(
            "directions",
            [],
        )

        valid = [
            item
            for item in self._as_list(
                directions
            )
            if isinstance(
                item,
                dict,
            )
        ]

        if not valid:
            return None

        return max(
            valid,
            key=lambda item: self._number(
                item.get(
                    "innovation_score",
                    item.get(
                        "score",
                        0,
                    ),
                )
            ),
        )

    # ============================================================
    # EVIDENCE IDS
    # ============================================================

    def _collect_evidence_ids(
        self,
        research: dict[str, Any],
        selected: dict[str, Any],
    ) -> list[str]:

        ids: list[str] = []

        evidence_records = self._as_list(
            research.get(
                "evidence_records",
                [],
            )
        )

        papers = self._as_list(
            research.get(
                "papers",
                [],
            )
        )

        for record in evidence_records:
            if isinstance(
                record,
                dict,
            ):
                for key in (
                    "evidence_id",
                    "paper_id",
                    "source_id",
                    "id",
                    "work_id",
                    "doi",
                ):
                    value = record.get(
                        key
                    )
                    if value:
                        ids.append(
                            str(value)
                        )
                        break

        for paper in papers:
            if isinstance(
                paper,
                dict,
            ):
                for key in (
                    "evidence_id",
                    "paper_id",
                    "id",
                    "work_id",
                    "openalex_id",
                    "doi",
                ):
                    value = paper.get(
                        key
                    )
                    if value:
                        ids.append(
                            str(value)
                        )
                        break

        context = selected.get(
            "research_evidence_context",
            {},
        )

        if isinstance(
            context,
            dict,
        ):
            for key in (
                "evidence_ids",
                "supporting_evidence_ids",
            ):
                ids.extend(
                    [
                        str(value)
                        for value in self._as_list(
                            context.get(
                                key,
                                [],
                            )
                        )
                        if value
                    ]
                )

        return self._unique_strings(
            ids
        )

    # ============================================================
    # HELPERS
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

    def _string_list(
        self,
        value: Any,
    ) -> list[str]:

        items = self._as_list(
            value
        )

        result: list[str] = []

        for item in items:
            text = self._clean_text(
                item
            )

            if text:
                result.append(
                    text
                )

        return self._unique_strings(
            result
        )

    def _clean_text(
        self,
        value: Any,
    ) -> str:

        if value is None:
            return ""

        if isinstance(
            value,
            str,
        ):
            return value.strip()

        if isinstance(
            value,
            dict,
        ):
            for key in (
                "text",
                "name",
                "title",
                "term",
                "value",
                "description",
                "claim",
                "opportunity",
                "limitation",
                "challenge",
                "research_gap",
                "proposed_innovation",
            ):
                candidate = value.get(
                    key
                )

                if candidate is not None:
                    text = self._clean_text(
                        candidate
                    )

                    if text:
                        return text

            return ""

        if isinstance(
            value,
            (list, tuple),
        ):
            return "; ".join(
                [
                    self._clean_text(
                        item
                    )
                    for item in value
                    if self._clean_text(
                        item
                    )
                ]
            )

        return str(
            value
        ).strip()

    def _unique_strings(
        self,
        values: list[str],
    ) -> list[str]:

        result: list[str] = []

        seen: set[str] = set()

        for value in values:
            text = str(
                value
            ).strip()

            if not text:
                continue

            key = text.lower()

            if key in seen:
                continue

            seen.add(
                key
            )

            result.append(
                text
            )

        return result

    def _number(
        self,
        value: Any,
    ) -> float:

        try:
            return float(
                value or 0
            )
        except (
            TypeError,
            ValueError,
        ):
            return 0.0

    def _extract_score(
        self,
        verdict: dict[str, Any],
        key: str,
    ) -> float:

        scores = (
            verdict.get(
                "scores",
                {},
            )
            or {}
        )

        return self._number(
            scores.get(
                key,
                verdict.get(
                    key,
                    0,
                ),
            )
        )


solution_agent = SolutionAgent()