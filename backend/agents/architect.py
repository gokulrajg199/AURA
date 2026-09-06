from __future__ import annotations

from typing import Any

from models.project import AURAProject
from orchestration.contract import AURAStageResult
from orchestration.stages import AURAStage


class ArchitectureAgent:
    """
    AURA Stage 07 — Technology & Architecture Intelligence.

    Purpose:
    Convert the evidence-aware solution produced by Stage 06 into
    a concrete, traceable technical architecture.

    Important:
    - Technology choices are recommendations, not implementation proof.
    - Research evidence supports architectural reasoning.
    - Final hardware compatibility, performance, security and deployment
      require implementation/testing.
    """

    stage = AURAStage.ARCHITECT

    async def run(
        self,
        project: AURAProject,
    ) -> AURAStageResult:

        try:
            solution = (
                project.solution
                or project.analysis.get("solution", {})
                or {}
            )

            if not solution:
                return AURAStageResult(
                    stage=self.stage,
                    success=False,
                    message=(
                        "AURA cannot create the architecture because "
                        "the Stage 06 solution specification is unavailable."
                    ),
                )

            architecture = self._build_architecture(
                project=project,
                solution=solution,
            )

            project.architecture = architecture
            project.analysis["architecture"] = architecture

            project.memory.append(
                {
                    "stage": self.stage.value,
                    "type": "technology_architecture",
                    "summary": architecture["summary"],
                    "technology_count": architecture[
                        "technology_intelligence"
                    ]["technology_count"],
                    "evidence_coverage": architecture[
                        "evidence_context"
                    ]["claim_evidence_coverage_percent"],
                }
            )

            project.evidence.append(
                {
                    "stage": self.stage.value,
                    "type": "technology_architecture",
                    "status": "aura_synthesis",
                    "source": "AURA evidence-aware solution and research pipeline",
                    "claim": (
                        "AURA generated a proposed technical architecture "
                        "and technology blueprint from the verified research "
                        "context and selected solution."
                    ),
                    "evidence_ids": architecture[
                        "evidence_context"
                    ]["supporting_evidence_ids"],
                    "verification_scope": (
                        "Architecture and technology recommendations are "
                        "AI-generated synthesis. Final technology suitability, "
                        "hardware compatibility, security, performance and "
                        "deployment require implementation and testing."
                    ),
                }
            )

            return AURAStageResult(
                stage=self.stage,
                success=True,
                message=(
                    "AURA generated an evidence-aware technology blueprint "
                    "and detailed system architecture."
                ),
                data={
                    "architecture": architecture,
                },
                next_stage=AURAStage.BUILD,
            )

        except Exception as error:
            return AURAStageResult(
                stage=self.stage,
                success=False,
                message=f"Architecture design failed: {error}",
            )

    # ============================================================
    # MASTER ARCHITECTURE
    # ============================================================

    def _build_architecture(
        self,
        project: AURAProject,
        solution: dict[str, Any],
    ) -> dict[str, Any]:

        research = project.research or {}
        analysis = project.analysis or {}

        research_intelligence = (
            analysis.get("research_intelligence", {})
            or {}
        )

        verdict = (
            analysis.get("verdict", {})
            or {}
        )

        innovation = (
            project.innovation
            or analysis.get("innovation", {})
            or {}
        )

        problem_understanding = (
            analysis.get("problem_understanding", {})
            or {}
        )

        title = self._clean_text(
            solution.get(
                "solution_title",
                "AURA Intelligent System",
            )
        )

        problem = self._clean_text(
            solution.get(
                "problem_context",
                problem_understanding.get(
                    "problem_definition",
                    project.original_idea,
                ),
            )
        )

        evidence_context = self._build_evidence_context(
            project=project,
            research=research,
            research_intelligence=research_intelligence,
            verdict=verdict,
            innovation=innovation,
            solution=solution,
        )

        layers = self._build_layers(
            solution=solution,
            project=project,
        )

        components = self._build_architecture_components(
            solution=solution,
            project=project,
        )

        interfaces = self._build_interfaces(
            components=components,
            project=project,
        )

        data_flow = self._build_data_flow(
            solution=solution,
            project=project,
        )

        database = self._build_database(
            solution=solution,
            project=project,
        )

        api = self._build_api(
            solution=solution,
            project=project,
        )

        security = self._build_security(
            project=project,
            solution=solution,
        )

        deployment = self._build_deployment(
            solution=solution,
            project=project,
        )

        observability = self._build_observability()

        scalability = self._build_scalability()

        technology_intelligence = (
            self._build_technology_intelligence(
                project=project,
                solution=solution,
                research=research,
                innovation=innovation,
            )
        )

        ai_architecture = self._build_ai_architecture(
            solution=solution,
            research=research,
        )

        architecture_decisions = (
            self._build_architecture_decisions(
                solution=solution,
                technology_intelligence=technology_intelligence,
                evidence_context=evidence_context,
            )
        )

        development_boundaries = (
            self._build_development_boundaries()
        )

        architecture_validation = (
            self._build_architecture_validation()
        )

        verification_scope = (
            self._build_verification_scope()
        )

        traceability = self._build_traceability(
            project=project,
            solution=solution,
            evidence_context=evidence_context,
        )

        summary = (
            f"AURA generated a technology-aware layered architecture "
            f"for '{title}'. The design connects the evidence-aware "
            f"research context, selected innovation and solution into "
            f"data, intelligence, decision, application and monitoring "
            f"layers. Technology selections remain candidate "
            f"recommendations until experimentally validated."
        )

        return {
            "status": "architecture_designed",

            "summary": summary,

            "system_name": title,

            "problem_context": problem,

            "architecture_style": (
                "Evidence-aware layered modular intelligent-system architecture"
            ),

            "architecture_principles": [
                "Evidence-aware design",
                "Modularity",
                "Loose coupling",
                "API-first integration",
                "Observable components",
                "Replaceable AI models",
                "Technology portability",
                "Security by design",
                "Experiment reproducibility",
                "Independent component testing",
                "Scalable deployment",
            ],

            "layers": layers,

            "components": components,

            "interfaces": interfaces,

            "data_flow": data_flow,

            "database": database,

            "api": api,

            "ai_architecture": ai_architecture,

            "technology_intelligence": technology_intelligence,

            "security": security,

            "deployment": deployment,

            "observability": observability,

            "scalability": scalability,

            "architecture_decisions": architecture_decisions,

            "development_boundaries": development_boundaries,

            "architecture_validation": architecture_validation,

            "evidence_context": evidence_context,

            "verification_scope": verification_scope,

            "traceability": traceability,
        }

    # ============================================================
    # EVIDENCE CONTEXT
    # ============================================================

    def _build_evidence_context(
        self,
        project: AURAProject,
        research: dict[str, Any],
        research_intelligence: dict[str, Any],
        verdict: dict[str, Any],
        innovation: dict[str, Any],
        solution: dict[str, Any],
    ) -> dict[str, Any]:

        claim_analysis = (
            research_intelligence.get(
                "claim_analysis",
                {},
            )
            or {}
        )

        coverage = self._number(
            claim_analysis.get(
                "evidence_coverage_percent",
                claim_analysis.get(
                    "coverage_percent",
                    0,
                ),
            )
        )

        claim_count = int(
            self._number(
                claim_analysis.get(
                    "claim_count",
                    0,
                )
            )
        )

        claims_with_evidence = int(
            self._number(
                claim_analysis.get(
                    "claims_with_evidence",
                    0,
                )
            )
        )

        claims_without_evidence = int(
            self._number(
                claim_analysis.get(
                    "claims_without_evidence",
                    max(
                        0,
                        claim_count - claims_with_evidence,
                    ),
                )
            )
        )

        average_strength = self._number(
            claim_analysis.get(
                "average_evidence_strength",
                0,
            )
        )

        if not average_strength:
            average_strength = self._number(
                research_intelligence.get(
                    "average_evidence_strength",
                    0,
                )
            )

        evidence_ids = self._collect_evidence_ids(
            project=project,
            research=research,
            innovation=innovation,
            solution=solution,
        )

        scores = (
            verdict.get("scores", {})
            if isinstance(verdict.get("scores"), dict)
            else verdict
        )

        return {
            "research_papers": len(
                research.get("papers", [])
                if isinstance(research.get("papers", []), list)
                else []
            ),

            "claim_count": claim_count,

            "claims_with_evidence": claims_with_evidence,

            "claims_without_evidence": claims_without_evidence,

            "claim_evidence_coverage_percent": round(
                coverage,
                2,
            ),

            "average_claim_evidence_strength": round(
                average_strength,
                2,
            ),

            "evidence_synthesis_available": bool(
                research_intelligence.get(
                    "evidence_synthesis"
                )
                or research.get(
                    "evidence_synthesis"
                )
            ),

            "supporting_evidence_ids": evidence_ids,

            "verdict_scores": {
                "existing_solution_strength": self._extract_score(
                    scores,
                    "existing_solution_strength",
                ),
                "research_gap_strength": self._extract_score(
                    scores,
                    "research_gap_strength",
                ),
                "technical_feasibility": self._extract_score(
                    scores,
                    "technical_feasibility",
                ),
                "opportunity_score": self._extract_score(
                    scores,
                    "opportunity_score",
                ),
                "evidence_strength": self._extract_score(
                    scores,
                    "evidence_strength",
                ),
                "novelty_confidence": self._extract_score(
                    scores,
                    "novelty_confidence",
                ),
            },

            "interpretation": (
                "Research evidence supports the architectural rationale "
                "and technology-selection context. It does not prove that "
                "the proposed architecture will work until implementation "
                "and validation are completed."
            ),

            "status": "EVIDENCE_AWARE_SYNTHESIS",
        }

    # ============================================================
    # LAYERS
    # ============================================================

    def _build_layers(
        self,
        solution: dict[str, Any],
        project: AURAProject,
    ) -> list[dict[str, Any]]:

        domains = self._get_domains(project)

        first_layer = (
            "Data Acquisition Layer"
            if self._contains_any(
                domains,
                [
                    "iot",
                    "smart agriculture",
                    "robotics",
                    "computer vision",
                    "sensor",
                    "healthcare",
                ],
            )
            else "Input & Data Acquisition Layer"
        )

        return [
            {
                "order": 1,
                "name": first_layer,
                "purpose": (
                    "Collect structured and unstructured inputs "
                    "from users, sensors, devices, datasets, "
                    "images, files or external systems."
                ),
            },
            {
                "order": 2,
                "name": "Data Processing & Quality Layer",
                "purpose": (
                    "Validate, clean, normalize, transform, "
                    "encode and prepare information for downstream "
                    "analysis and intelligence."
                ),
            },
            {
                "order": 3,
                "name": "Storage & Provenance Layer",
                "purpose": (
                    "Persist operational data, historical records, "
                    "experiments, predictions, model versions and "
                    "provenance information."
                ),
            },
            {
                "order": 4,
                "name": "AI / Intelligence Layer",
                "purpose": (
                    "Execute machine learning, deep learning, "
                    "classification, prediction, anomaly detection, "
                    "retrieval or recommendation functions."
                ),
            },
            {
                "order": 5,
                "name": "Decision & Explainability Layer",
                "purpose": (
                    "Convert intelligence outputs into interpretable "
                    "recommendations, alerts, actions or decisions."
                ),
            },
            {
                "order": 6,
                "name": "Application & Interaction Layer",
                "purpose": (
                    "Expose the system through dashboards, APIs, "
                    "interfaces, reports, notifications and user workflows."
                ),
            },
            {
                "order": 7,
                "name": "Monitoring & Validation Layer",
                "purpose": (
                    "Track system health, model behavior, data quality, "
                    "latency, errors, experiments and validation metrics."
                ),
            },
        ]

    # ============================================================
    # COMPONENTS
    # ============================================================

    def _build_architecture_components(
        self,
        solution: dict[str, Any],
        project: AURAProject,
    ) -> list[dict[str, Any]]:

        domains = self._get_domains(project)

        components = [
            {
                "id": "ARCH-INPUT",
                "layer": "Data Acquisition",
                "component": "Input & Data Collector",
                "responsibility": (
                    "Collect project-specific inputs from available "
                    "devices, datasets, users or external systems."
                ),
                "input": [
                    "Sensors",
                    "Datasets",
                    "User input",
                    "External APIs",
                    "Files or media where required",
                ],
                "output": [
                    "Validated raw input",
                ],
            },
            {
                "id": "ARCH-PROC",
                "layer": "Data Processing",
                "component": "Data Processing Engine",
                "responsibility": (
                    "Validate, clean, transform and prepare incoming data."
                ),
                "input": [
                    "Raw input",
                ],
                "output": [
                    "Processed data",
                    "Features",
                    "Quality metadata",
                ],
            },
            {
                "id": "ARCH-STORE",
                "layer": "Storage",
                "component": "Data & Provenance Store",
                "responsibility": (
                    "Store operational records, historical data, "
                    "experiments, predictions and provenance."
                ),
                "input": [
                    "Processed data",
                    "Predictions",
                    "Experiments",
                    "Events",
                ],
                "output": [
                    "Historical records",
                    "Query results",
                    "Experiment records",
                ],
            },
            {
                "id": "ARCH-AI",
                "layer": "AI",
                "component": "AI Intelligence Engine",
                "responsibility": (
                    "Execute the selected model family and generate "
                    "predictions, classifications, anomaly scores or "
                    "other intelligence outputs."
                ),
                "input": [
                    "Features",
                    "Validated model inputs",
                ],
                "output": [
                    "Prediction",
                    "Confidence",
                    "Model metadata",
                    "Explanation where supported",
                ],
            },
            {
                "id": "ARCH-DECISION",
                "layer": "Decision",
                "component": "Decision & Recommendation Engine",
                "responsibility": (
                    "Combine model outputs, confidence, rules and "
                    "context to generate interpretable recommendations."
                ),
                "input": [
                    "Prediction",
                    "Confidence",
                    "Context",
                    "Rules",
                ],
                "output": [
                    "Recommendation",
                    "Alert",
                    "Action",
                ],
            },
            {
                "id": "ARCH-API",
                "layer": "Application",
                "component": "Application API",
                "responsibility": (
                    "Provide controlled communication between "
                    "frontend, backend, AI and external integrations."
                ),
                "input": [
                    "Client requests",
                    "System events",
                ],
                "output": [
                    "Structured API responses",
                ],
            },
            {
                "id": "ARCH-UI",
                "layer": "Application",
                "component": "User Interface",
                "responsibility": (
                    "Present project information, intelligence, "
                    "recommendations, evidence, alerts and reports."
                ),
                "input": [
                    "API responses",
                ],
                "output": [
                    "User interaction",
                    "Configuration",
                    "Feedback",
                ],
            },
            {
                "id": "ARCH-MONITOR",
                "layer": "Monitoring",
                "component": "Monitoring & Validation Engine",
                "responsibility": (
                    "Track system health, model performance, "
                    "experiments, errors and validation metrics."
                ),
                "input": [
                    "Logs",
                    "Metrics",
                    "Model results",
                    "Experiment results",
                ],
                "output": [
                    "Metrics",
                    "Alerts",
                    "Validation records",
                ],
            },
        ]

        if self._contains_any(
            domains,
            [
                "iot",
                "smart agriculture",
                "robotics",
                "edge ai",
                "embedded",
            ],
        ):
            components.insert(
                1,
                {
                    "id": "ARCH-EDGE",
                    "layer": "Data Acquisition",
                    "component": "Edge / Device Gateway",
                    "responsibility": (
                        "Receive device or sensor data and provide "
                        "local filtering, buffering or preprocessing."
                    ),
                    "input": [
                        "Sensors",
                        "Embedded devices",
                        "Edge devices",
                    ],
                    "output": [
                        "Device telemetry",
                        "Filtered data",
                    ],
                },
            )

        if self._contains_any(
            domains,
            [
                "computer vision",
                "image",
                "medical image",
                "video",
            ],
        ):
            components.insert(
                2,
                {
                    "id": "ARCH-VISION",
                    "layer": "Data Processing",
                    "component": "Vision Preprocessing Pipeline",
                    "responsibility": (
                        "Prepare image or video data through "
                        "validation, resizing, normalization, "
                        "augmentation or frame extraction."
                    ),
                    "input": [
                        "Images",
                        "Video frames",
                    ],
                    "output": [
                        "Model-ready visual tensors",
                    ],
                },
            )

        return components

    # ============================================================
    # INTERFACES
    # ============================================================

    def _build_interfaces(
        self,
        components: list[dict[str, Any]],
        project: AURAProject,
    ) -> list[dict[str, Any]]:

        interfaces = [
            {
                "from": "Input & Data Collector",
                "to": "Data Processing Engine",
                "interface": "Data ingestion",
                "protocol": (
                    "REST, MQTT, file ingestion or local interface "
                    "depending on project requirements."
                ),
                "verification": "Requires integration testing.",
            },
            {
                "from": "Data Processing Engine",
                "to": "Data & Provenance Store",
                "interface": "Persistence interface",
                "protocol": "Database connection / ORM",
                "verification": "Requires schema and transaction testing.",
            },
            {
                "from": "Data Processing Engine",
                "to": "AI Intelligence Engine",
                "interface": "Model input interface",
                "protocol": "Internal service/API call",
                "verification": "Requires input-contract testing.",
            },
            {
                "from": "AI Intelligence Engine",
                "to": "Decision & Recommendation Engine",
                "interface": "Prediction interface",
                "protocol": "Internal API",
                "verification": "Requires model-output testing.",
            },
            {
                "from": "Decision & Recommendation Engine",
                "to": "Application API",
                "interface": "Decision response",
                "protocol": "REST / JSON",
                "verification": "Requires API contract testing.",
            },
            {
                "from": "Application API",
                "to": "User Interface",
                "interface": "Application API",
                "protocol": "HTTPS / REST / WebSocket where required",
                "verification": "Requires frontend integration testing.",
            },
            {
                "from": "All Services",
                "to": "Monitoring & Validation Engine",
                "interface": "Telemetry",
                "protocol": "Logs / metrics / events",
                "verification": "Requires observability testing.",
            },
        ]

        if any(
            component.get("id") == "ARCH-EDGE"
            for component in components
        ):
            interfaces.insert(
                1,
                {
                    "from": "Edge / Device Gateway",
                    "to": "Data Processing Engine",
                    "interface": "Telemetry ingestion",
                    "protocol": "MQTT / HTTP / local transport",
                    "verification": "Requires device communication testing.",
                },
            )

        return interfaces

    # ============================================================
    # DATA FLOW
    # ============================================================

    def _build_data_flow(
        self,
        solution: dict[str, Any],
        project: AURAProject,
    ) -> list[dict[str, Any]]:

        return [
            {
                "sequence": 1,
                "from": "Input Sources",
                "to": "Input & Data Collector",
                "data": "Raw project input",
            },
            {
                "sequence": 2,
                "from": "Input & Data Collector",
                "to": "Data Processing Engine",
                "data": "Collected input",
            },
            {
                "sequence": 3,
                "from": "Data Processing Engine",
                "to": "Data & Provenance Store",
                "data": "Validated processed data",
            },
            {
                "sequence": 4,
                "from": "Data Processing Engine",
                "to": "AI Intelligence Engine",
                "data": "Model-ready features",
            },
            {
                "sequence": 5,
                "from": "AI Intelligence Engine",
                "to": "Decision & Recommendation Engine",
                "data": (
                    "Prediction + confidence + model metadata"
                ),
            },
            {
                "sequence": 6,
                "from": "Decision & Recommendation Engine",
                "to": "Application API",
                "data": "Recommendation / alert / action",
            },
            {
                "sequence": 7,
                "from": "Application API",
                "to": "User Interface",
                "data": "Visualization / response / report data",
            },
            {
                "sequence": 8,
                "from": "User Interface",
                "to": "Decision & Recommendation Engine",
                "data": "User feedback or decision input",
            },
            {
                "sequence": 9,
                "from": "System",
                "to": "Data & Provenance Store",
                "data": "Outcome + experiment + historical record",
            },
            {
                "sequence": 10,
                "from": "System",
                "to": "Monitoring & Validation Engine",
                "data": "Logs + metrics + validation results",
            },
        ]

    # ============================================================
    # DATABASE
    # ============================================================

    def _build_database(
        self,
        solution: dict[str, Any],
        project: AURAProject,
    ) -> dict[str, Any]:

        return {
            "recommended_type": (
                "Relational database with optional time-series "
                "or object storage depending on project data."
            ),

            "primary_candidate": "PostgreSQL",

            "prototype_candidate": "SQLite",

            "optional_storage": [
                "Object storage for large files or datasets",
                "Time-series storage where high-frequency telemetry requires it",
            ],

            "entities": [
                {
                    "table": "users",
                    "purpose": "User identity and roles.",
                },
                {
                    "table": "projects",
                    "purpose": "Project configuration and lifecycle.",
                },
                {
                    "table": "data_sources",
                    "purpose": "Registered input sources.",
                },
                {
                    "table": "observations",
                    "purpose": "Raw and processed observations.",
                },
                {
                    "table": "predictions",
                    "purpose": "AI predictions and confidence.",
                },
                {
                    "table": "decisions",
                    "purpose": "Recommendations, alerts and actions.",
                },
                {
                    "table": "experiments",
                    "purpose": "Experiment configuration and provenance.",
                },
                {
                    "table": "experiment_results",
                    "purpose": "Experimental measurements.",
                },
                {
                    "table": "model_versions",
                    "purpose": "Model version and evaluation tracking.",
                },
                {
                    "table": "evidence_records",
                    "purpose": "Research evidence and provenance.",
                },
                {
                    "table": "audit_events",
                    "purpose": "Important system events.",
                },
            ],

            "data_policy": [
                "Validate incoming data.",
                "Timestamp important observations.",
                "Preserve experiment provenance.",
                "Track model versions.",
                "Track evidence provenance.",
                "Avoid unnecessary sensitive data.",
                "Define retention requirements.",
            ],
        }

    # ============================================================
    # API
    # ============================================================

    def _build_api(
        self,
        solution: dict[str, Any],
        project: AURAProject,
    ) -> dict[str, Any]:

        return {
            "style": "Versioned REST API",

            "versioning": "Version API contracts from the first stable release.",

            "endpoints": [
                {
                    "method": "POST",
                    "path": "/api/data",
                    "purpose": "Submit project input data.",
                },
                {
                    "method": "GET",
                    "path": "/api/data",
                    "purpose": "Retrieve historical data.",
                },
                {
                    "method": "POST",
                    "path": "/api/predict",
                    "purpose": "Request AI prediction or inference.",
                },
                {
                    "method": "GET",
                    "path": "/api/predictions",
                    "purpose": "Retrieve prediction history.",
                },
                {
                    "method": "GET",
                    "path": "/api/decisions",
                    "purpose": "Retrieve recommendations and decisions.",
                },
                {
                    "method": "POST",
                    "path": "/api/feedback",
                    "purpose": "Submit user or system feedback.",
                },
                {
                    "method": "GET",
                    "path": "/api/experiments",
                    "purpose": "Retrieve experiment records.",
                },
                {
                    "method": "GET",
                    "path": "/api/status",
                    "purpose": "Retrieve current system status.",
                },
                {
                    "method": "GET",
                    "path": "/api/metrics",
                    "purpose": "Retrieve system and model metrics.",
                },
            ],

            "requirements": [
                "Input validation",
                "Authentication where required",
                "Authorization",
                "Rate limiting where required",
                "Structured error responses",
                "Request logging",
                "API versioning",
                "Schema validation",
            ],
        }

    # ============================================================
    # AI ARCHITECTURE
    # ============================================================

    def _build_ai_architecture(
        self,
        solution: dict[str, Any],
        research: dict[str, Any],
    ) -> dict[str, Any]:

        ai = (
            solution.get(
                "ai_intelligence",
                {},
            )
            or {}
        )

        return {
            "model_layer": ai,

            "candidate_model_families": (
                ai.get(
                    "candidate_model_families",
                    [],
                )
                if isinstance(
                    ai.get(
                        "candidate_model_families",
                        [],
                    ),
                    list,
                )
                else []
            ),

            "training_pipeline": [
                "Data collection",
                "Data validation",
                "Dataset profiling",
                "Dataset preparation",
                "Feature engineering where required",
                "Train / validation / test split",
                "Baseline establishment",
                "Candidate model training",
                "Hyperparameter tuning where justified",
                "Model evaluation",
                "Error analysis",
                "Model selection",
                "Model versioning",
            ],

            "inference_pipeline": [
                "Receive input",
                "Validate input",
                "Preprocess input",
                "Generate prediction",
                "Calculate confidence where supported",
                "Apply decision logic",
                "Generate explanation where supported",
                "Return result",
            ],

            "evaluation": [
                "Task-specific primary metric",
                "Secondary performance metrics",
                "Baseline comparison",
                "Error analysis",
                "Robustness evaluation",
                "Latency measurement where relevant",
                "Resource measurement where relevant",
            ],

            "model_registry": (
                "Recommended for reproducible multi-model development."
            ),

            "status": (
                "Candidate AI architecture — model suitability requires "
                "dataset and experimental validation."
            ),
        }

    # ============================================================
    # TECHNOLOGY INTELLIGENCE
    # ============================================================

    def _build_technology_intelligence(
        self,
        project: AURAProject,
        solution: dict[str, Any],
        research: dict[str, Any],
        innovation: dict[str, Any],
    ) -> dict[str, Any]:

        domains = self._get_domains(project)

        technology = {
            "frontend": {
                "recommended": "Next.js + React + TypeScript",
                "reason": (
                    "Provides a structured web application layer suitable "
                    "for dashboards, project workflows and interactive "
                    "research/engineering interfaces."
                ),
                "status": "AURA_RECOMMENDATION",
                "verification": "Validate against project UI requirements.",
            },

            "backend": {
                "recommended": "Python + FastAPI",
                "reason": (
                    "Provides a lightweight API boundary and integrates "
                    "naturally with Python-based AI/ML workloads."
                ),
                "status": "AURA_RECOMMENDATION",
                "verification": "Validate API workload and deployment requirements.",
            },

            "ai_ml": {
                "recommended": [
                    "Python",
                    "scikit-learn where classical ML is appropriate",
                    "PyTorch where deep learning is justified",
                ],
                "reason": (
                    "Python provides broad support for data processing, "
                    "machine learning and experimental workflows."
                ),
                "status": "AURA_RECOMMENDATION",
                "verification": "Select final model after dataset and baseline testing.",
            },

            "database": {
                "recommended": "PostgreSQL",
                "prototype": "SQLite",
                "reason": (
                    "Relational storage provides structured project, "
                    "experiment, prediction and provenance management."
                ),
                "status": "AURA_RECOMMENDATION",
                "verification": "Validate data volume and query workload.",
            },

            "communication": {
                "recommended": [
                    "HTTPS",
                    "REST",
                ],
                "conditional": [
                    "MQTT for IoT telemetry",
                    "WebSocket for real-time application updates",
                    "Message queues for asynchronous workloads",
                ],
                "reason": (
                    "Communication mechanisms should match the project's "
                    "latency, connectivity and device requirements."
                ),
                "status": "AURA_RECOMMENDATION",
                "verification": "Requires integration and load testing.",
            },

            "deployment": {
                "recommended": "Docker-compatible deployment",
                "options": [
                    "Cloud",
                    "On-premise",
                    "Edge + Cloud hybrid",
                ],
                "reason": (
                    "Containerization improves deployment consistency while "
                    "allowing deployment strategy to depend on privacy, "
                    "latency, cost and connectivity."
                ),
                "status": "AURA_RECOMMENDATION",
                "verification": "Requires deployment validation.",
            },
        }

        if self._contains_any(
            domains,
            [
                "iot",
                "smart agriculture",
                "robotics",
                "embedded",
                "edge ai",
            ],
        ):
            technology["edge"] = {
                "recommended": [
                    "ESP32 or equivalent microcontroller where appropriate",
                    "Raspberry Pi or equivalent edge computer where required",
                ],
                "reason": (
                    "Edge hardware may reduce communication dependency "
                    "and support local acquisition or preprocessing."
                ),
                "status": "AURA_RECOMMENDATION",
                "verification": (
                    "Hardware selection depends on sensor interfaces, "
                    "compute requirements, power and environmental conditions."
                ),
            }

        if self._contains_any(
            domains,
            [
                "computer vision",
                "medical image",
                "image analysis",
                "deep learning",
            ],
        ):
            technology["vision"] = {
                "recommended": [
                    "OpenCV for image processing where appropriate",
                    "PyTorch for deep-learning workflows where justified",
                ],
                "reason": (
                    "Visual projects require dedicated image preprocessing "
                    "and model-training/inference capabilities."
                ),
                "status": "AURA_RECOMMENDATION",
                "verification": "Validate against dataset characteristics and task metrics.",
            }

        if self._contains_any(
            domains,
            [
                "robotics",
                "ros",
                "robot operating system",
            ],
        ):
            technology["robotics"] = {
                "recommended": [
                    "ROS 2 where robotic middleware is required",
                ],
                "reason": (
                    "ROS 2 can provide modular communication between "
                    "robotic software components."
                ),
                "status": "AURA_RECOMMENDATION",
                "verification": "Validate against robot hardware and middleware requirements.",
            }

        technology["selection_policy"] = {
            "factors": [
                "Research evidence",
                "Project requirements",
                "Dataset characteristics",
                "Latency",
                "Accuracy requirements",
                "Hardware constraints",
                "Connectivity",
                "Privacy",
                "Security",
                "Cost",
                "Maintainability",
                "Deployment environment",
            ],
            "rule": (
                "AURA recommends technologies from the available project "
                "context; final selection must be validated experimentally."
            ),
        }

        technology["technology_count"] = self._count_recommended_technologies(
            technology
        )

        return technology

    # ============================================================
    # ARCHITECTURE DECISIONS
    # ============================================================

    def _build_architecture_decisions(
        self,
        solution: dict[str, Any],
        technology_intelligence: dict[str, Any],
        evidence_context: dict[str, Any],
    ) -> list[dict[str, Any]]:

        return [
            {
                "decision": "Use modular architecture",
                "reason": (
                    "Separates system responsibilities and allows "
                    "independent development and testing."
                ),
                "evidence_basis": (
                    "Architecture synthesis from the selected solution "
                    "and research context."
                ),
                "status": "AURA_RECOMMENDATION",
            },
            {
                "decision": "Separate AI from application logic",
                "reason": (
                    "Allows models to be replaced, retrained or compared "
                    "without redesigning the user interface."
                ),
                "evidence_basis": (
                    "Supports reproducible experimentation and model iteration."
                ),
                "status": "AURA_RECOMMENDATION",
            },
            {
                "decision": "Use explicit API boundaries",
                "reason": (
                    "Allows frontend, backend, AI and device components "
                    "to evolve independently."
                ),
                "evidence_basis": (
                    "Derived from the modular solution architecture."
                ),
                "status": "AURA_RECOMMENDATION",
            },
            {
                "decision": "Track model versions",
                "reason": (
                    "Enables reproducibility and comparison between "
                    "experimental models."
                ),
                "evidence_basis": (
                    "Aligned with the experiment and validation requirements."
                ),
                "status": "AURA_RECOMMENDATION",
            },
            {
                "decision": "Preserve experiment provenance",
                "reason": (
                    "Allows datasets, configurations, models and results "
                    "to be compared later."
                ),
                "evidence_basis": (
                    "Required for evidence-aware validation."
                ),
                "status": "AURA_RECOMMENDATION",
            },
            {
                "decision": "Keep technology choices replaceable",
                "reason": (
                    "A candidate technology may be unsuitable after "
                    "implementation or benchmarking."
                ),
                "evidence_basis": (
                    "Architecture is a recommendation rather than a verified implementation."
                ),
                "status": "AURA_RECOMMENDATION",
            },
            {
                "decision": "Use evidence provenance",
                "reason": (
                    "Architectural rationale should remain traceable "
                    "to the research and solution stages."
                ),
                "evidence_basis": (
                    f"Current claim-evidence coverage: "
                    f"{evidence_context['claim_evidence_coverage_percent']}%."
                ),
                "status": "AURA_RECOMMENDATION",
            },
        ]

    # ============================================================
    # SECURITY
    # ============================================================

    def _build_security(
        self,
        project: AURAProject,
        solution: dict[str, Any],
    ) -> dict[str, Any]:

        return {
            "principles": [
                "Least privilege",
                "Secure defaults",
                "Input validation",
                "Data minimization",
                "Auditability",
                "Defense in depth",
            ],

            "controls": [
                "Authentication where required",
                "Role-based authorization",
                "HTTPS",
                "Secret management",
                "Input validation",
                "API rate limiting where required",
                "Database access control",
                "Audit logging",
                "Dependency management",
            ],

            "ai_security": [
                "Validate model inputs.",
                "Monitor abnormal requests.",
                "Track model versions.",
                "Protect model artifacts.",
                "Record important model decisions.",
                "Monitor unexpected model behavior.",
            ],

            "status": (
                "Architecture recommendation; security testing required."
            ),
        }

    # ============================================================
    # DEPLOYMENT
    # ============================================================

    def _build_deployment(
        self,
        solution: dict[str, Any],
        project: AURAProject,
    ) -> dict[str, Any]:

        return {
            "prototype": {
                "frontend": "Next.js development server",
                "backend": "Python/FastAPI service",
                "database": "SQLite or local PostgreSQL",
                "ai": "Local inference where practical",
            },

            "production_candidate": {
                "frontend": "Web application hosting",
                "backend": "Containerized API service",
                "database": "Managed PostgreSQL or equivalent",
                "ai": "Dedicated inference service where justified",
                "monitoring": "Centralized logs and metrics",
            },

            "deployment_models": [
                "Cloud",
                "On-premise",
                "Edge",
                "Edge + Cloud hybrid",
            ],

            "selection_factors": [
                "Latency",
                "Privacy",
                "Cost",
                "Connectivity",
                "Hardware availability",
                "Data volume",
                "Inference workload",
                "Security requirements",
            ],

            "selection_policy": (
                "Final deployment model must be selected after "
                "requirements, cost, performance and infrastructure validation."
            ),
        }

    # ============================================================
    # OBSERVABILITY
    # ============================================================

    def _build_observability(self) -> dict[str, Any]:

        return {
            "logs": [
                "Application events",
                "API requests",
                "Errors",
                "Model events",
                "Data-quality events",
                "Experiment events",
            ],

            "metrics": [
                "Request latency",
                "Throughput",
                "Error rate",
                "CPU usage",
                "Memory usage",
                "Storage usage",
                "Model latency",
                "Model performance",
                "Data-quality metrics",
            ],

            "alerts": [
                "Service failure",
                "High latency",
                "Abnormal error rate",
                "Model degradation",
                "Resource exhaustion",
                "Data-quality failure",
            ],
        }

    # ============================================================
    # SCALABILITY
    # ============================================================

    def _build_scalability(self) -> dict[str, Any]:

        return {
            "strategies": [
                "Stateless API services",
                "Horizontal service scaling",
                "Database indexing",
                "Caching where useful",
                "Asynchronous processing",
                "Queue-based workloads where required",
                "Separate model inference service where justified",
                "Object storage for large files where required",
            ],

            "scale_dimensions": [
                "Users",
                "Data volume",
                "Inference requests",
                "Devices",
                "Experiments",
                "Model size",
            ],
        }

    # ============================================================
    # DEVELOPMENT BOUNDARIES
    # ============================================================

    def _build_development_boundaries(
        self,
    ) -> list[dict[str, str]]:

        return [
            {
                "boundary": "Data",
                "responsibility": (
                    "Collect, validate, transform and preserve data provenance."
                ),
            },
            {
                "boundary": "AI",
                "responsibility": (
                    "Train, evaluate, version and execute intelligence models."
                ),
            },
            {
                "boundary": "Decision",
                "responsibility": (
                    "Convert model outputs into interpretable recommendations."
                ),
            },
            {
                "boundary": "Backend",
                "responsibility": (
                    "Expose business logic and AI capabilities through APIs."
                ),
            },
            {
                "boundary": "Frontend",
                "responsibility": (
                    "Provide interaction, visualization and reporting."
                ),
            },
            {
                "boundary": "Infrastructure",
                "responsibility": (
                    "Run services, storage, monitoring and deployment."
                ),
            },
        ]

    # ============================================================
    # VALIDATION
    # ============================================================

    def _build_architecture_validation(
        self,
    ) -> list[str]:

        return [
            "Verify every component has one clearly defined responsibility.",
            "Verify every input has a defined destination.",
            "Verify every output has a defined consumer.",
            "Verify API contracts independently.",
            "Verify data schemas and validation rules.",
            "Test the data pipeline independently.",
            "Compare AI performance against a baseline.",
            "Measure inference latency where relevant.",
            "Measure resource consumption where relevant.",
            "Test expected operating conditions.",
            "Test failure and recovery behavior.",
            "Validate security controls.",
            "Document architecture changes during development.",
        ]

    # ============================================================
    # VERIFICATION SCOPE
    # ============================================================

    def _build_verification_scope(
        self,
    ) -> dict[str, Any]:

        return {
            "architecture_is_ai_generated_design": True,

            "technology_choices_verified": False,

            "hardware_compatibility_verified": False,

            "dataset_compatibility_verified": False,

            "model_performance_verified": False,

            "deployment_verified": False,

            "performance_verified": False,

            "security_verified": False,

            "integration_verified": False,

            "production_readiness_verified": False,

            "expert_review_required": True,

            "next_verification_stage": (
                "Implementation, experimentation and validation."
            ),
        }

    # ============================================================
    # TRACEABILITY
    # ============================================================

    def _build_traceability(
        self,
        project: AURAProject,
        solution: dict[str, Any],
        evidence_context: dict[str, Any],
    ) -> dict[str, Any]:

        return {
            "pipeline": [
                "UNDERSTAND",
                "INVESTIGATE",
                "ANALYZE",
                "VERDICT",
                "INNOVATE",
                "SOLUTION",
                "ARCHITECT",
            ],

            "source_solution": solution.get(
                "solution_title"
            ),

            "innovation_basis": solution.get(
                "innovation_basis",
                {},
            ),

            "supporting_evidence_ids": evidence_context[
                "supporting_evidence_ids"
            ],

            "claim_evidence_coverage_percent": evidence_context[
                "claim_evidence_coverage_percent"
            ],

            "architecture_status": "AURA_RECOMMENDATION",

            "interpretation": (
                "The architecture is derived from the connected AURA "
                "research-to-solution pipeline. It is not presented as "
                "a verified implementation."
            ),
        }

    # ============================================================
    # DOMAIN HELPERS
    # ============================================================

    def _get_domains(
        self,
        project: AURAProject,
    ) -> list[str]:

        domains: list[str] = []

        understanding = (
            project.analysis.get(
                "problem_understanding",
                {},
            )
            or {}
        )

        for value in (
            project.domain,
            understanding.get("domains", []),
            understanding.get("domain", []),
        ):
            if isinstance(value, list):
                domains.extend(
                    self._string_list(value)
                )
            elif value:
                domains.append(
                    self._clean_text(value)
                )

        return self._unique_strings(domains)

    def _contains_any(
        self,
        values: list[str],
        targets: list[str],
    ) -> bool:

        normalized_values = [
            value.lower()
            for value in values
        ]

        return any(
            target.lower() in value
            for value in normalized_values
            for target in targets
        )

    # ============================================================
    # EVIDENCE ID HELPERS
    # ============================================================

    def _collect_evidence_ids(
        self,
        project: AURAProject,
        research: dict[str, Any],
        innovation: dict[str, Any],
        solution: dict[str, Any],
    ) -> list[str]:

        evidence_ids: list[str] = []

        for evidence in project.evidence:
            if not isinstance(evidence, dict):
                continue

            for key in (
                "evidence_id",
                "id",
                "paper_id",
                "source_id",
            ):
                value = evidence.get(key)

                if value:
                    evidence_ids.append(
                        self._clean_text(value)
                    )

        for paper in research.get(
            "papers",
            [],
        ):
            if not isinstance(paper, dict):
                continue

            for key in (
                "evidence_id",
                "paper_id",
                "source_id",
                "id",
                "work_id",
                "openalex_id",
                "doi",
            ):
                value = paper.get(key)

                if value:
                    evidence_ids.append(
                        self._clean_text(value)
                    )

        selected = (
            innovation.get(
                "recommended_direction",
                {},
            )
            if isinstance(innovation, dict)
            else {}
        )

        if isinstance(selected, dict):
            context = (
                selected.get(
                    "research_evidence_context",
                    {},
                )
                or {}
            )

            evidence_ids.extend(
                self._string_list(
                    context.get(
                        "evidence_ids",
                        [],
                    )
                )
            )

        innovation_context = (
            solution.get(
                "evidence_context",
                {},
            )
            or {}
        )

        evidence_ids.extend(
            self._string_list(
                innovation_context.get(
                    "supporting_evidence_ids",
                    [],
                )
            )
        )

        return self._unique_strings(
            evidence_ids
        )

    # ============================================================
    # TECHNOLOGY HELPERS
    # ============================================================

    def _count_recommended_technologies(
        self,
        technology: dict[str, Any],
    ) -> int:

        count = 0

        for key, value in technology.items():

            if key in {
                "selection_policy",
                "technology_count",
            }:
                continue

            if not isinstance(value, dict):
                continue

            recommended = value.get(
                "recommended",
                [],
            )

            if isinstance(
                recommended,
                list,
            ):
                count += len(
                    recommended
                )

            elif recommended:
                count += 1

            prototype = value.get(
                "prototype"
            )

            if prototype:
                count += 1

        return count

    # ============================================================
    # GENERIC HELPERS
    # ============================================================

    def _string_list(
        self,
        value: Any,
    ) -> list[str]:

        if value is None:
            return []

        if isinstance(value, list):
            result: list[str] = []

            for item in value:
                if isinstance(
                    item,
                    dict,
                ):
                    for key in (
                        "name",
                        "title",
                        "value",
                        "technology",
                        "model",
                        "component",
                    ):
                        if item.get(key):
                            result.append(
                                self._clean_text(
                                    item.get(key)
                                )
                            )
                            break
                else:
                    text = self._clean_text(
                        item
                    )

                    if text:
                        result.append(text)

            return self._unique_strings(
                result
            )

        text = self._clean_text(
            value
        )

        return [text] if text else []

    def _unique_strings(
        self,
        values: list[str],
    ) -> list[str]:

        seen: set[str] = set()
        result: list[str] = []

        for value in values:
            cleaned = self._clean_text(
                value
            )

            key = cleaned.lower()

            if cleaned and key not in seen:
                seen.add(key)
                result.append(cleaned)

        return result

    def _clean_text(
        self,
        value: Any,
    ) -> str:

        if value is None:
            return ""

        if isinstance(
            value,
            dict,
        ):
            for key in (
                "title",
                "name",
                "value",
                "text",
                "description",
                "technology",
                "model",
                "opportunity",
                "limitation",
                "challenge",
            ):
                if value.get(key):
                    return self._clean_text(
                        value.get(key)
                    )

            return ""

        if isinstance(
            value,
            list,
        ):
            return ", ".join(
                self._string_list(value)
            )

        return str(value).strip()

    def _number(
        self,
        value: Any,
    ) -> float:

        if isinstance(
            value,
            bool,
        ):
            return 0.0

        if isinstance(
            value,
            (int, float),
        ):
            return float(value)

        try:
            return float(
                str(value)
                .replace("%", "")
                .strip()
            )
        except (
            TypeError,
            ValueError,
        ):
            return 0.0

    def _extract_score(
        self,
        scores: dict[str, Any],
        key: str,
    ) -> float:

        if not isinstance(
            scores,
            dict,
        ):
            return 0.0

        value = scores.get(
            key,
            0,
        )

        if isinstance(
            value,
            dict,
        ):
            value = value.get(
                "score",
                value.get(
                    "value",
                    0,
                ),
            )

        return round(
            self._number(value),
            2,
        )


architect_agent = ArchitectureAgent()