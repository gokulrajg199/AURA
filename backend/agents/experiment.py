from __future__ import annotations

from typing import Any

from models.project import AURAProject
from orchestration.contract import AURAStageResult
from orchestration.stages import AURAStage


class ExperimentAgent:
    """
    AURA Stage 09
    Experiment & Validation Intelligence Engine

    Purpose:
    - Convert the proposed solution into an evidence-aware experiment plan.
    - Derive experiments from the actual project context.
    - Connect research claims to measurable experiments.
    - Distinguish planned validation from executed validation.
    - Never fabricate experimental results.
    """

    stage = AURAStage.EXPERIMENT

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

            architecture = (
                project.architecture
                or project.analysis.get("architecture", {})
                or {}
            )

            development = (
                project.development
                or project.analysis.get("development", {})
                or {}
            )

            research = project.research or {}

            research_intelligence = (
                project.analysis.get(
                    "research_intelligence",
                    {},
                )
                or {}
            )

            verdict = (
                project.analysis.get(
                    "verdict",
                    {},
                )
                or {}
            )

            problem_understanding = (
                project.analysis.get(
                    "problem_understanding",
                    {},
                )
                or {}
            )

            if not solution:
                return AURAStageResult(
                    stage=self.stage,
                    success=False,
                    message=(
                        "AURA cannot design experiments because "
                        "the solution specification is unavailable."
                    ),
                )

            if not architecture:
                return AURAStageResult(
                    stage=self.stage,
                    success=False,
                    message=(
                        "AURA cannot design experiments because "
                        "the architecture specification is unavailable."
                    ),
                )

            experiment_plan = self._build_experiment_plan(
                project=project,
                solution=solution,
                architecture=architecture,
                development=development,
                research=research,
                research_intelligence=research_intelligence,
                verdict=verdict,
                problem_understanding=problem_understanding,
            )

            project.experiments = experiment_plan
            project.analysis["experiments"] = experiment_plan

            project.memory.append(
                {
                    "stage": self.stage.value,
                    "type": "experiment_plan",
                    "summary": experiment_plan["summary"],
                    "experiment_count": len(
                        experiment_plan.get(
                            "experiments",
                            [],
                        )
                    ),
                    "validation_readiness": experiment_plan[
                        "validation_readiness"
                    ],
                }
            )

            project.evidence.append(
                {
                    "stage": self.stage.value,
                    "type": "experiment_plan",
                    "status": "aura_synthesis",
                    "source": (
                        "AURA research evidence, solution, "
                        "architecture, and development plan"
                    ),
                    "claim": (
                        "AURA proposes an experiment and validation "
                        "framework derived from the available research "
                        "and project design context."
                    ),
                    "verification_scope": (
                        "Experiment design only. "
                        "No experiment has been executed and "
                        "no experimental result has been verified."
                    ),
                    "claim_evidence_coverage": experiment_plan[
                        "evidence_context"
                    ].get(
                        "claim_evidence_coverage_percent",
                        0,
                    ),
                    "supporting_evidence_ids": experiment_plan[
                        "evidence_context"
                    ].get(
                        "supporting_evidence_ids",
                        [],
                    ),
                }
            )

            return AURAStageResult(
                stage=self.stage,
                success=True,
                message=(
                    "AURA created an evidence-aware experiment "
                    "and validation framework derived from the "
                    "research, solution, architecture, and "
                    "development context."
                ),
                data={
                    "experiments": experiment_plan,
                },
                next_stage=AURAStage.VALIDATE,
            )

        except Exception as error:
            return AURAStageResult(
                stage=self.stage,
                success=False,
                message=(
                    f"Experiment planning failed: {error}"
                ),
            )

    # ============================================================
    # MAIN EXPERIMENT PLAN
    # ============================================================

    def _build_experiment_plan(
        self,
        project: AURAProject,
        solution: dict[str, Any],
        architecture: dict[str, Any],
        development: dict[str, Any],
        research: dict[str, Any],
        research_intelligence: dict[str, Any],
        verdict: dict[str, Any],
        problem_understanding: dict[str, Any],
    ) -> dict[str, Any]:

        system_name = self._clean_text(
            architecture.get(
                "system_name",
                solution.get(
                    "solution_title",
                    "AURA Intelligent System",
                ),
            )
        )

        domains = self._unique_strings(
            self._string_list(
                problem_understanding.get(
                    "domains",
                    [],
                )
            )
            + self._string_list(
                solution.get(
                    "domains",
                    [],
                )
            )
            + self._string_list(
                project.domain
            )
        )

        research_questions = self._unique_strings(
            self._string_list(
                problem_understanding.get(
                    "research_questions",
                    [],
                )
            )
            + self._string_list(
                solution.get(
                    "research_questions",
                    [],
                )
            )
        )

        objectives = self._unique_strings(
            self._string_list(
                problem_understanding.get(
                    "objectives",
                    [],
                )
            )
            + self._string_list(
                solution.get(
                    "objectives",
                    [],
                )
            )
            + self._string_list(
                project.objectives
            )
        )

        requirements = self._unique_strings(
            self._string_list(
                problem_understanding.get(
                    "technical_requirements",
                    [],
                )
            )
            + self._string_list(
                problem_understanding.get(
                    "functional_requirements",
                    [],
                )
            )
            + self._string_list(
                solution.get(
                    "requirements",
                    [],
                )
            )
            + self._string_list(
                project.requirements
            )
        )

        constraints = self._unique_strings(
            self._string_list(
                problem_understanding.get(
                    "constraints",
                    [],
                )
            )
            + self._string_list(
                project.constraints
            )
        )

        evidence_context = self._build_evidence_context(
            project=project,
            research=research,
            research_intelligence=research_intelligence,
            verdict=verdict,
        )

        problem_context = self._build_problem_context(
            project=project,
            problem_understanding=problem_understanding,
            domains=domains,
        )

        hypotheses = self._build_hypotheses(
            system_name=system_name,
            research_questions=research_questions,
            objectives=objectives,
            solution=solution,
        )

        dataset_plan = self._build_dataset_plan(
            solution=solution,
            architecture=architecture,
            research=research,
            domains=domains,
        )

        baseline = self._build_baseline(
            solution=solution,
            research_intelligence=research_intelligence,
        )

        experiments = self._build_experiments(
            solution=solution,
            architecture=architecture,
            development=development,
            hypotheses=hypotheses,
            domains=domains,
            requirements=requirements,
            constraints=constraints,
            research_intelligence=research_intelligence,
        )

        metrics = self._build_metrics(
            solution=solution,
            architecture=architecture,
            domains=domains,
        )

        ablation = self._build_ablation_plan(
            solution=solution,
            architecture=architecture,
        )

        robustness = self._build_robustness_plan(
            solution=solution,
            architecture=architecture,
            domains=domains,
        )

        security_testing = self._build_security_testing(
            architecture=architecture,
            domains=domains,
        )

        reproducibility = self._build_reproducibility(
            project=project,
            development=development,
        )

        experiment_matrix = self._build_experiment_matrix(
            experiments
        )

        result_schema = self._build_result_schema(
            metrics=metrics
        )

        failure_analysis = self._build_failure_analysis(
            solution=solution,
            architecture=architecture,
            domains=domains,
        )

        claim_experiment_map = self._build_claim_experiment_map(
            research=research,
            research_intelligence=research_intelligence,
            experiments=experiments,
        )

        validation_gates = self._build_validation_gates(
            experiments=experiments,
            metrics=metrics,
            solution=solution,
            architecture=architecture,
        )

        readiness = self._calculate_validation_readiness(
            evidence_context=evidence_context,
            experiments=experiments,
            metrics=metrics,
            dataset_plan=dataset_plan,
            baseline=baseline,
            reproducibility=reproducibility,
        )

        execution_policy = self._build_execution_policy()

        summary = (
            f"AURA designed an evidence-aware experimental framework "
            f"for '{system_name}'. The framework contains "
            f"{len(experiments)} project-specific experiment tracks, "
            f"research-claim traceability, baseline comparison, "
            f"task-appropriate metrics, ablation testing, robustness "
            f"and security validation, reproducibility controls, "
            f"failure analysis, and explicit validation gates. "
            f"No experimental result is treated as verified until "
            f"the experiment is actually executed."
        )

        return {
            "status": "experiment_plan_ready",

            "summary": summary,

            "system_name": system_name,

            "problem_context": problem_context,

            "domains": domains,

            "research_questions": research_questions,

            "objectives": objectives,

            "requirements": requirements,

            "constraints": constraints,

            "evidence_context": evidence_context,

            "hypotheses": hypotheses,

            "dataset_plan": dataset_plan,

            "baseline": baseline,

            "experiments": experiments,

            "experiment_matrix": experiment_matrix,

            "metrics": metrics,

            "ablation_study": ablation,

            "robustness_testing": robustness,

            "security_testing": security_testing,

            "failure_analysis": failure_analysis,

            "claim_experiment_map": claim_experiment_map,

            "validation_gates": validation_gates,

            "reproducibility": reproducibility,

            "result_schema": result_schema,

            "validation_requirements": self._build_validation_requirements(
                solution=solution,
                architecture=architecture,
            ),

            "experiment_execution_policy": execution_policy,

            "validation_readiness": readiness,

            "execution_status": {
                "experiments_executed": False,
                "real_dataset_loaded": False,
                "baseline_measured": False,
                "candidate_model_measured": False,
                "ablation_executed": False,
                "robustness_tests_executed": False,
                "security_tests_executed": False,
                "statistical_significance_tested": False,
                "real_world_validation_completed": False,
                "results_verified": False,
            },

            "traceability": {
                "stage_01_understanding": bool(
                    problem_understanding
                ),
                "stage_02_investigation": bool(
                    research
                ),
                "stage_03_analysis": bool(
                    research_intelligence
                ),
                "stage_04_verdict": bool(
                    verdict
                ),
                "stage_05_innovation": bool(
                    project.innovation
                ),
                "stage_06_solution": bool(
                    solution
                ),
                "stage_07_architecture": bool(
                    architecture
                ),
                "stage_08_development": bool(
                    development
                ),
                "stage_09_experiment": True,
                "status": "AURA_DERIVED",
            },

            "verification_scope": {
                "experiment_design_generated": True,
                "experiment_design_executed": False,
                "dataset_verified": False,
                "baseline_verified": False,
                "candidate_model_verified": False,
                "metrics_verified": False,
                "statistical_results_verified": False,
                "real_world_validation_verified": False,
                "scientific_claims_validated": False,
                "expert_review_required": True,
            },
        }

    # ============================================================
    # PROBLEM CONTEXT
    # ============================================================

    def _build_problem_context(
        self,
        project: AURAProject,
        problem_understanding: dict[str, Any],
        domains: list[str],
    ) -> dict[str, Any]:

        return {
            "original_idea": self._clean_text(
                project.original_idea
            ),

            "interpreted_problem": self._clean_text(
                problem_understanding.get(
                    "problem_definition",
                    problem_understanding.get(
                        "interpreted_problem",
                        project.original_idea,
                    ),
                )
            ),

            "target_context": self._clean_text(
                problem_understanding.get(
                    "target_context",
                    "",
                )
            ),

            "domains": domains,

            "stakeholders": self._string_list(
                problem_understanding.get(
                    "stakeholders",
                    [],
                )
            ),

            "success_criteria": self._string_list(
                problem_understanding.get(
                    "success_criteria",
                    [],
                )
            ),

            "uncertainties": self._string_list(
                problem_understanding.get(
                    "uncertainties",
                    [],
                )
            ),
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
    ) -> dict[str, Any]:

        claim_analysis = (
            research_intelligence.get(
                "claim_analysis",
                {},
            )
            or research.get(
                "claim_analysis",
                {},
            )
            or {}
        )

        papers = self._as_list(
            research.get(
                "papers",
                []
            )
        )

        evidence_records = self._as_list(
            project.evidence
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
                        claim_count
                        - claims_with_evidence,
                        0,
                    ),
                )
            )
        )

        coverage = self._number(
            claim_analysis.get(
                "evidence_coverage_percent",
                0,
            )
        )

        if claim_count > 0 and coverage == 0:
            coverage = round(
                claims_with_evidence
                / claim_count
                * 100,
                2,
            )

        average_strength = self._number(
            claim_analysis.get(
                "average_evidence_strength",
                research_intelligence.get(
                    "average_evidence_strength",
                    0,
                ),
            )
        )

        supporting_ids = self._collect_evidence_ids(
            project=project,
            research=research,
            research_intelligence=research_intelligence,
        )

        return {
            "paper_count": len(papers),

            "evidence_record_count": len(
                evidence_records
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

            "supporting_evidence_ids": supporting_ids,

            "verdict_evidence_strength": self._extract_score(
                verdict,
                "evidence_strength",
            ),

            "verdict_gap_strength": self._extract_score(
                verdict,
                "research_gap_strength",
            ),

            "verdict_feasibility": self._extract_score(
                verdict,
                "technical_feasibility",
            ),

            "verdict_opportunity": self._extract_score(
                verdict,
                "opportunity_score",
            ),

            "evidence_policy": (
                "Research evidence is used to justify "
                "experiment priorities and comparison context. "
                "It does not constitute experimental validation "
                "of the proposed system."
            ),
        }

    # ============================================================
    # HYPOTHESES
    # ============================================================

    def _build_hypotheses(
        self,
        system_name: str,
        research_questions: list[str],
        objectives: list[str],
        solution: dict[str, Any],
    ) -> list[dict[str, Any]]:

        model_families = self._string_list(
            solution.get(
                "ai_intelligence",
                {},
            ).get(
                "candidate_model_families",
                [],
            )
            if isinstance(
                solution.get(
                    "ai_intelligence",
                    {},
                ),
                dict,
            )
            else []
        )

        hypotheses = [
            {
                "id": "H1",
                "statement": (
                    f"The proposed {system_name} will demonstrate "
                    "measurable improvement over an appropriate "
                    "baseline under controlled evaluation conditions."
                ),
                "type": "PRIMARY",
                "status": "TO_BE_TESTED",
                "evidence_requirement": (
                    "Requires executed baseline and proposed-system "
                    "comparison."
                ),
            },
            {
                "id": "H2",
                "statement": (
                    "The proposed intelligence mechanism will "
                    "produce task-appropriate predictive or "
                    "decision performance."
                ),
                "type": "AI_PERFORMANCE",
                "status": "TO_BE_TESTED",
                "evidence_requirement": (
                    "Requires real dataset evaluation and "
                    "task-specific metrics."
                ),
            },
            {
                "id": "H3",
                "statement": (
                    "The integrated system will operate within "
                    "the required latency, resource, reliability, "
                    "and operational constraints."
                ),
                "type": "SYSTEM_PERFORMANCE",
                "status": "TO_BE_TESTED",
                "evidence_requirement": (
                    "Requires execution on representative "
                    "hardware and operating conditions."
                ),
            },
        ]

        if model_families:
            hypotheses.append(
                {
                    "id": "H4",
                    "statement": (
                        "The selected model family will provide "
                        "an acceptable performance-efficiency "
                        "trade-off compared with alternatives."
                    ),
                    "type": "MODEL_SELECTION",
                    "status": "TO_BE_TESTED",
                    "candidate_models": model_families,
                    "evidence_requirement": (
                        "Requires controlled model comparison."
                    ),
                }
            )

        if research_questions:
            hypotheses.append(
                {
                    "id": "H5",
                    "statement": (
                        "The defined research questions can be "
                        "answered using measurable experimental evidence."
                    ),
                    "type": "RESEARCH",
                    "status": "TO_BE_TESTED",
                    "linked_research_questions": research_questions,
                    "evidence_requirement": (
                        "Requires evidence-backed interpretation "
                        "of executed experiments."
                    ),
                }
            )

        if objectives:
            hypotheses.append(
                {
                    "id": "H6",
                    "statement": (
                        "The implemented system will satisfy "
                        "the measurable objectives defined for the project."
                    ),
                    "type": "OBJECTIVE_VALIDATION",
                    "status": "TO_BE_TESTED",
                    "linked_objectives": objectives,
                    "evidence_requirement": (
                        "Requires objective-specific acceptance criteria."
                    ),
                }
            )

        return hypotheses

    # ============================================================
    # DATASET PLAN
    # ============================================================

    def _build_dataset_plan(
        self,
        solution: dict[str, Any],
        architecture: dict[str, Any],
        research: dict[str, Any],
        domains: list[str],
    ) -> dict[str, Any]:

        dataset_intelligence = solution.get(
            "dataset",
            solution.get(
                "dataset_plan",
                {},
            ),
        )

        if not isinstance(
            dataset_intelligence,
            dict,
        ):
            dataset_intelligence = {}

        data_sources = self._unique_strings(
            self._string_list(
                dataset_intelligence.get(
                    "sources",
                    [],
                )
            )
            + self._string_list(
                solution.get(
                    "data_sources",
                    [],
                )
            )
        )

        domain_text = " ".join(
            domains
        ).lower()

        if (
            "computer vision" in domain_text
            or "image" in domain_text
            or "vision" in domain_text
        ):
            preparation = [
                "Image quality inspection",
                "Resolution and format normalization",
                "Label verification",
                "Class-distribution analysis",
                "Data augmentation policy",
                "Train-validation-test separation",
            ]

            leakage_controls = [
                "Prevent subject or near-duplicate image leakage.",
                "Keep validation/test images isolated.",
                "Apply augmentation only within training workflow.",
                "Document dataset and label versions.",
            ]

        elif (
            "iot" in domain_text
            or "smart agriculture" in domain_text
            or "sensor" in domain_text
            or "robotics" in domain_text
            or "edge" in domain_text
        ):
            preparation = [
                "Sensor/data quality inspection",
                "Timestamp normalization",
                "Missing-value analysis",
                "Outlier detection",
                "Noise analysis",
                "Feature preparation",
                "Temporal ordering verification",
            ]

            leakage_controls = [
                "Prevent future observations entering training data.",
                "Preserve temporal ordering where applicable.",
                "Separate device/site conditions where required.",
                "Document calibration and sensor versions.",
            ]

        else:
            preparation = [
                "Data cleaning",
                "Missing-value analysis",
                "Outlier analysis",
                "Feature preparation",
                "Label verification where applicable",
                "Duplicate detection",
            ]

            leakage_controls = [
                "Separate training and test information.",
                "Avoid target leakage.",
                "Fit preprocessing only on training data where required.",
                "Document all preprocessing operations.",
            ]

        return {
            "data_sources": data_sources,

            "requirements": [
                "Relevant to the target problem.",
                "Sufficient coverage of expected conditions.",
                "Documented provenance.",
                "Known collection period where applicable.",
                "Quality checked.",
                "Version controlled.",
                "License or usage conditions recorded.",
            ],

            "preparation": preparation,

            "split_strategy": {
                "default": [
                    "Training set",
                    "Validation set",
                    "Test set",
                ],
                "policy": (
                    "Select the split strategy according to "
                    "task type, temporal dependency, subject "
                    "dependency, device dependency, and leakage risk."
                ),
            },

            "leakage_controls": leakage_controls,

            "dataset_card": [
                "Dataset name",
                "Source",
                "Version",
                "Collection period",
                "Number of samples",
                "Features",
                "Labels",
                "Preprocessing",
                "Known limitations",
                "License / usage conditions",
            ],

            "dataset_verification": {
                "real_dataset_available": False,
                "provenance_verified": False,
                "quality_verified": False,
                "version_verified": False,
                "license_verified": False,
            },
        }

    # ============================================================
    # BASELINE
    # ============================================================

    def _build_baseline(
        self,
        solution: dict[str, Any],
        research_intelligence: dict[str, Any],
    ) -> dict[str, Any]:

        existing_methods = self._string_list(
            research_intelligence.get(
                "methods",
                [],
            )
        )

        research_baselines = self._string_list(
            research_intelligence.get(
                "existing_methods",
                [],
            )
        )

        candidates = [
            "Simple statistical baseline",
            "Majority-class baseline where applicable",
            "Linear model where appropriate",
            "Traditional machine-learning model",
        ]

        candidates.extend(
            existing_methods[:5]
        )

        candidates.extend(
            research_baselines[:5]
        )

        return {
            "purpose": (
                "Provide a defensible reference point against "
                "which the proposed solution can be evaluated."
            ),

            "candidate_baselines": self._unique_strings(
                candidates
            ),

            "selection_policy": (
                "Select the baseline using task type, "
                "research evidence, existing approaches, "
                "data characteristics, and implementation feasibility."
            ),

            "required_comparison": [
                "Baseline metrics",
                "Proposed-system metrics",
                "Absolute improvement",
                "Relative improvement where meaningful",
                "Error analysis",
                "Resource comparison where relevant",
            ],

            "baseline_status": "NOT_SELECTED",

            "verification": (
                "No baseline performance is claimed until "
                "the selected baseline is executed."
            ),
        }

    # ============================================================
    # EXPERIMENTS
    # ============================================================

    def _build_experiments(
        self,
        solution: dict[str, Any],
        architecture: dict[str, Any],
        development: dict[str, Any],
        hypotheses: list[dict[str, Any]],
        domains: list[str],
        requirements: list[str],
        constraints: list[str],
        research_intelligence: dict[str, Any],
    ) -> list[dict[str, Any]]:

        experiments: list[dict[str, Any]] = []

        ai_layer = solution.get(
            "ai_intelligence",
            {},
        )

        if not isinstance(
            ai_layer,
            dict,
        ):
            ai_layer = {}

        candidate_models = self._string_list(
            ai_layer.get(
                "candidate_model_families",
                [],
            )
        )

        component_names = self._extract_component_names(
            architecture
        )

        # --------------------------------------------------------
        # Baseline
        # --------------------------------------------------------

        experiments.append(
            {
                "id": "EXP-01",
                "name": "Baseline Evaluation",
                "category": "BASELINE",
                "objective": (
                    "Measure the selected baseline under the "
                    "same dataset, evaluation protocol, and "
                    "operating conditions used for the proposed system."
                ),
                "linked_hypotheses": ["H1"],
                "variables": [
                    "Dataset",
                    "Preprocessing",
                    "Baseline method",
                    "Evaluation configuration",
                ],
                "controls": [
                    "Same test data",
                    "Same evaluation metrics",
                    "Same evaluation conditions",
                ],
                "status": "NOT_EXECUTED",
                "required_evidence": [
                    "Executed baseline metrics",
                    "Configuration",
                    "Dataset version",
                ],
            }
        )

        # --------------------------------------------------------
        # Proposed AI system
        # --------------------------------------------------------

        experiments.append(
            {
                "id": "EXP-02",
                "name": "Proposed Intelligence Evaluation",
                "category": "AI_PERFORMANCE",
                "objective": (
                    "Evaluate the proposed intelligence layer "
                    "using task-appropriate metrics and compare "
                    "the results against the baseline."
                ),
                "linked_hypotheses": [
                    "H1",
                    "H2",
                ],
                "variables": [
                    "Model",
                    "Features",
                    "Hyperparameters",
                    "Dataset",
                    "Preprocessing",
                ],
                "candidate_models": candidate_models,
                "controls": [
                    "Fixed test set",
                    "Versioned preprocessing",
                    "Documented configuration",
                    "Reproducible seed where applicable",
                ],
                "status": "NOT_EXECUTED",
                "required_evidence": [
                    "Model metrics",
                    "Predictions",
                    "Configuration",
                    "Model version",
                ],
            }
        )

        # --------------------------------------------------------
        # Model comparison
        # --------------------------------------------------------

        if len(candidate_models) > 1:
            experiments.append(
                {
                    "id": "EXP-03",
                    "name": "Model Comparison",
                    "category": "MODEL_SELECTION",
                    "objective": (
                        "Compare candidate model families using "
                        "the same data and evaluation protocol."
                    ),
                    "linked_hypotheses": [
                        "H4"
                    ],
                    "variables": [
                        "Model family",
                        "Training configuration",
                        "Inference configuration",
                    ],
                    "candidate_models": candidate_models,
                    "controls": [
                        "Same dataset split",
                        "Same primary metrics",
                        "Same evaluation protocol",
                    ],
                    "status": "NOT_EXECUTED",
                    "required_evidence": [
                        "Per-model metrics",
                        "Training configuration",
                        "Inference latency where relevant",
                        "Resource usage where relevant",
                    ],
                }
            )

        # --------------------------------------------------------
        # System performance
        # --------------------------------------------------------

        experiments.append(
            {
                "id": "EXP-04",
                "name": "System Performance Evaluation",
                "category": "SYSTEM_PERFORMANCE",
                "objective": (
                    "Measure latency, throughput, resource usage, "
                    "reliability, and operational behavior of the "
                    "integrated system."
                ),
                "linked_hypotheses": [
                    "H3"
                ],
                "variables": [
                    "Input volume",
                    "Hardware",
                    "Network condition",
                    "Concurrent requests",
                    "Payload size",
                ],
                "metrics": [
                    "Latency",
                    "Throughput",
                    "CPU utilization",
                    "Memory utilization",
                    "Network usage",
                    "Energy consumption where relevant",
                    "Failure rate",
                ],
                "status": "NOT_EXECUTED",
                "required_evidence": [
                    "Execution logs",
                    "Performance measurements",
                    "Hardware configuration",
                ],
            }
        )

        # --------------------------------------------------------
        # Domain-aware real-world experiment
        # --------------------------------------------------------

        domain_text = " ".join(
            domains
        ).lower()

        if (
            "iot" in domain_text
            or "smart agriculture" in domain_text
            or "sensor" in domain_text
        ):
            experiments.append(
                {
                    "id": "EXP-05",
                    "name": "Sensor / Field Condition Evaluation",
                    "category": "REAL_WORLD",
                    "objective": (
                        "Evaluate system behavior under representative "
                        "sensor, environmental, communication, or field "
                        "conditions."
                    ),
                    "linked_hypotheses": [
                        "H3",
                        "H6",
                    ],
                    "variables": [
                        "Sensor readings",
                        "Environmental conditions",
                        "Sampling frequency",
                        "Communication state",
                        "Missing readings",
                    ],
                    "status": "NOT_EXECUTED",
                    "required_evidence": [
                        "Timestamped observations",
                        "Hardware configuration",
                        "Environmental conditions",
                        "System decisions",
                    ],
                }
            )

        elif (
            "computer vision" in domain_text
            or "image" in domain_text
            or "vision" in domain_text
        ):
            experiments.append(
                {
                    "id": "EXP-05",
                    "name": "Vision Condition Evaluation",
                    "category": "REAL_WORLD",
                    "objective": (
                        "Evaluate model behavior under realistic "
                        "lighting, scale, viewpoint, occlusion, "
                        "and image-quality variations."
                    ),
                    "linked_hypotheses": [
                        "H2",
                        "H6",
                    ],
                    "variables": [
                        "Lighting",
                        "Image quality",
                        "Object scale",
                        "Viewpoint",
                        "Occlusion",
                    ],
                    "status": "NOT_EXECUTED",
                    "required_evidence": [
                        "Representative images",
                        "Predictions",
                        "Confidence values",
                        "Error analysis",
                    ],
                }
            )

        elif (
            "robotics" in domain_text
            or "ros" in domain_text
        ):
            experiments.append(
                {
                    "id": "EXP-05",
                    "name": "Robotic Operational Evaluation",
                    "category": "REAL_WORLD",
                    "objective": (
                        "Evaluate perception, decision, control, "
                        "latency, and recovery behavior under "
                        "representative robotic operating conditions."
                    ),
                    "linked_hypotheses": [
                        "H2",
                        "H3",
                        "H6",
                    ],
                    "variables": [
                        "Robot state",
                        "Sensor state",
                        "Environment",
                        "Control latency",
                        "Communication state",
                    ],
                    "status": "NOT_EXECUTED",
                    "required_evidence": [
                        "Robot configuration",
                        "Execution logs",
                        "Sensor observations",
                        "Control outputs",
                    ],
                }
            )
        else:
            experiments.append(
                {
                    "id": "EXP-05",
                    "name": "Representative Condition Evaluation",
                    "category": "REAL_WORLD",
                    "objective": (
                        "Evaluate the proposed system under "
                        "representative conditions outside the "
                        "controlled development environment."
                    ),
                    "linked_hypotheses": [
                        "H3",
                        "H6",
                    ],
                    "variables": [
                        "Input conditions",
                        "Operating environment",
                        "System load",
                        "Data quality",
                    ],
                    "status": "NOT_EXECUTED",
                    "required_evidence": [
                        "Representative test data",
                        "Execution logs",
                        "Observed outputs",
                    ],
                }
            )

        # --------------------------------------------------------
        # Ablation
        # --------------------------------------------------------

        experiments.append(
            {
                "id": "EXP-06",
                "name": "Ablation and Component Contribution",
                "category": "ABLATION",
                "objective": (
                    "Measure how important features, intelligence "
                    "components, data sources, or decision modules "
                    "contribute to the overall system."
                ),
                "linked_hypotheses": [
                    "H2",
                    "H6",
                ],
                "candidate_components": component_names,
                "variables": [
                    "Features",
                    "AI components",
                    "Data sources",
                    "Decision rules",
                    "Architecture components",
                ],
                "status": "NOT_EXECUTED",
                "required_evidence": [
                    "Full-system result",
                    "Reduced-system result",
                    "Controlled comparison",
                ],
            }
        )

        # --------------------------------------------------------
        # Robustness
        # --------------------------------------------------------

        experiments.append(
            {
                "id": "EXP-07",
                "name": "Robustness and Stress Evaluation",
                "category": "ROBUSTNESS",
                "objective": (
                    "Determine how system performance changes "
                    "when inputs or operating conditions deviate "
                    "from normal conditions."
                ),
                "linked_hypotheses": [
                    "H2",
                    "H3",
                ],
                "variables": [
                    "Noise",
                    "Missing data",
                    "Distribution shift",
                    "Boundary conditions",
                    "Input corruption",
                    "System load",
                ],
                "status": "NOT_EXECUTED",
                "required_evidence": [
                    "Controlled stress condition",
                    "Performance measurements",
                    "Failure observations",
                ],
            }
        )

        return experiments

    # ============================================================
    # METRICS
    # ============================================================

    def _build_metrics(
        self,
        solution: dict[str, Any],
        architecture: dict[str, Any],
        domains: list[str],
    ) -> dict[str, Any]:

        ai_layer = solution.get(
            "ai_intelligence",
            {},
        )

        if not isinstance(
            ai_layer,
            dict,
        ):
            ai_layer = {}

        task_type = self._clean_text(
            ai_layer.get(
                "task_type",
                "",
            )
        ).lower()

        domain_text = " ".join(
            domains
        ).lower()

        classification = [
            "Accuracy",
            "Precision",
            "Recall",
            "F1-score",
        ]

        regression = [
            "MAE",
            "MSE",
            "RMSE",
            "R²",
        ]

        detection = [
            "Precision",
            "Recall",
            "F1-score",
            "mAP where appropriate",
        ]

        if (
            "classification" in task_type
            or "classif" in task_type
        ):
            primary = classification

        elif (
            "regression" in task_type
            or "forecast" in task_type
            or "prediction" in task_type
        ):
            primary = regression

        elif (
            "detection" in task_type
            or "object detection" in domain_text
        ):
            primary = detection

        else:
            primary = [
                "Task-appropriate primary metric",
                "Task-appropriate secondary metric",
                "Error metric",
            ]

        system_metrics = [
            "Latency",
            "Throughput",
            "CPU utilization",
            "Memory utilization",
        ]

        if (
            "iot" in domain_text
            or "edge" in domain_text
            or "robotics" in domain_text
        ):
            system_metrics.extend(
                [
                    "Network usage",
                    "Energy consumption",
                    "Inference latency",
                    "Device availability",
                ]
            )

        if (
            "computer vision" in domain_text
            or "vision" in domain_text
        ):
            system_metrics.extend(
                [
                    "Inference latency",
                    "Confidence distribution",
                    "Per-class performance",
                ]
            )

        return {
            "primary_task_metrics": primary,

            "classification": classification,

            "regression": regression,

            "detection": detection,

            "system": system_metrics,

            "operational": [
                "Failure rate",
                "Availability",
                "Recovery time",
            ],

            "decision_support": [
                "Recommendation accuracy where applicable",
                "False-positive rate where applicable",
                "False-negative rate where applicable",
                "Decision confidence where applicable",
            ],

            "metric_selection_policy": (
                "Only metrics appropriate to the actual task "
                "and experiment should be reported. AURA must "
                "not report irrelevant metrics merely because "
                "they are commonly used."
            ),

            "metric_verification": (
                "Metric values remain unverified until experiments "
                "are executed on real data."
            ),
        }

    # ============================================================
    # ABLATION
    # ============================================================

    def _build_ablation_plan(
        self,
        solution: dict[str, Any],
        architecture: dict[str, Any],
    ) -> dict[str, Any]:

        components = self._extract_component_names(
            architecture
        )

        features = self._string_list(
            solution.get(
                "features",
                [],
            )
        )

        return {
            "purpose": (
                "Measure the contribution of individual "
                "features, data sources, models, or system components."
            ),

            "candidate_components": self._unique_strings(
                features
                + components
                + [
                    "Individual features",
                    "Feature groups",
                    "AI model components",
                    "Decision rules",
                    "Data sources",
                ]
            ),

            "procedure": [
                "Run the complete system.",
                "Select one component or feature group.",
                "Remove or disable only that component.",
                "Keep other experimental conditions constant.",
                "Repeat the experiment.",
                "Compare primary and secondary metrics.",
                "Record the observed contribution.",
            ],

            "controls": [
                "Same dataset",
                "Same test split",
                "Same evaluation metrics",
                "Same configuration except the ablated component",
            ],

            "status": "NOT_EXECUTED",
        }

    # ============================================================
    # ROBUSTNESS
    # ============================================================

    def _build_robustness_plan(
        self,
        solution: dict[str, Any],
        architecture: dict[str, Any],
        domains: list[str],
    ) -> dict[str, Any]:

        tests = [
            {
                "name": "Missing Data",
                "description": (
                    "Evaluate behavior when expected inputs "
                    "are unavailable."
                ),
            },
            {
                "name": "Noisy Data",
                "description": (
                    "Evaluate sensitivity to controlled input noise."
                ),
            },
            {
                "name": "Distribution Shift",
                "description": (
                    "Evaluate performance under changed "
                    "operating or data conditions."
                ),
            },
            {
                "name": "Boundary Conditions",
                "description": (
                    "Test values near defined operational limits."
                ),
            },
            {
                "name": "Failure Recovery",
                "description": (
                    "Evaluate behavior after component, "
                    "network, or communication failures."
                ),
            },
        ]

        domain_text = " ".join(
            domains
        ).lower()

        if (
            "iot" in domain_text
            or "sensor" in domain_text
            or "smart agriculture" in domain_text
        ):
            tests.extend(
                [
                    {
                        "name": "Sensor Drift",
                        "description": (
                            "Evaluate sensitivity to gradual "
                            "sensor measurement drift."
                        ),
                    },
                    {
                        "name": "Communication Loss",
                        "description": (
                            "Evaluate system behavior when "
                            "connectivity becomes unavailable."
                        ),
                    },
                ]
            )

        if (
            "computer vision" in domain_text
            or "vision" in domain_text
            or "image" in domain_text
        ):
            tests.extend(
                [
                    {
                        "name": "Lighting Variation",
                        "description": (
                            "Evaluate performance under different "
                            "lighting conditions."
                        ),
                    },
                    {
                        "name": "Occlusion",
                        "description": (
                            "Evaluate performance when target "
                            "objects are partially obscured."
                        ),
                    },
                ]
            )

        return {
            "tests": tests,

            "policy": (
                "Robustness tests must be controlled, "
                "documented, and linked to observed performance "
                "changes rather than described qualitatively only."
            ),

            "status": "NOT_EXECUTED",
        }

    # ============================================================
    # SECURITY TESTING
    # ============================================================

    def _build_security_testing(
        self,
        architecture: dict[str, Any],
        domains: list[str],
    ) -> dict[str, Any]:

        tests = [
            {
                "name": "Authentication and Authorization",
                "objective": (
                    "Verify unauthorized users cannot access "
                    "protected operations."
                ),
            },
            {
                "name": "Input Validation",
                "objective": (
                    "Verify malformed or unexpected input "
                    "is handled safely."
                ),
            },
            {
                "name": "API Abuse Resistance",
                "objective": (
                    "Evaluate behavior under repeated or "
                    "unexpected API requests."
                ),
            },
            {
                "name": "Sensitive Data Handling",
                "objective": (
                    "Verify sensitive data is not unnecessarily "
                    "exposed through logs or responses."
                ),
            },
        ]

        domain_text = " ".join(
            domains
        ).lower()

        if (
            "iot" in domain_text
            or "sensor" in domain_text
            or "edge" in domain_text
        ):
            tests.append(
                {
                    "name": "Device Communication Security",
                    "objective": (
                        "Evaluate authentication, integrity, "
                        "and failure behavior for device communication."
                    ),
                }
            )

        if (
            "ai" in domain_text
            or "machine learning" in domain_text
            or "deep learning" in domain_text
        ):
            tests.append(
                {
                    "name": "Model Input Robustness",
                    "objective": (
                        "Evaluate model behavior under malformed, "
                        "unexpected, or adversarially unusual inputs."
                    ),
                }
            )

        return {
            "tests": tests,
            "status": "NOT_EXECUTED",
            "security_results_available": False,
        }

    # ============================================================
    # REPRODUCIBILITY
    # ============================================================

    def _build_reproducibility(
        self,
        project: AURAProject,
        development: dict[str, Any],
    ) -> dict[str, Any]:

        environment = development.get(
            "environment",
            {},
        )

        if not isinstance(
            environment,
            dict,
        ):
            environment = {}

        return {
            "required_records": [
                "Project ID",
                "Code version",
                "Dataset version",
                "Configuration",
                "Random seed where applicable",
                "Python/runtime environment",
                "Hardware",
                "Software versions",
                "Model version",
                "Experiment timestamp",
                "Operator or execution context",
            ],

            "artifacts": [
                "Source code",
                "Configuration files",
                "Dataset metadata",
                "Trained model",
                "Experiment logs",
                "Metrics",
                "Plots",
                "Predictions",
                "Result files",
                "Failure logs",
            ],

            "environment": environment,

            "environment_policy": (
                "Use a reproducible environment definition "
                "such as requirements.txt, lock file, container, "
                "or equivalent environment manifest."
            ),

            "reproducibility_status": {
                "environment_locked": False,
                "dataset_version_locked": False,
                "configuration_versioned": False,
                "seed_recorded": False,
                "model_versioned": False,
            },
        }

    # ============================================================
    # EXPERIMENT MATRIX
    # ============================================================

    def _build_experiment_matrix(
        self,
        experiments: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:

        matrix = []

        for experiment in experiments:

            experiment_id = self._clean_text(
                experiment.get(
                    "id",
                    "",
                )
            )

            matrix.append(
                {
                    "experiment_id": experiment_id,

                    "name": self._clean_text(
                        experiment.get(
                            "name",
                            "",
                        )
                    ),

                    "category": self._clean_text(
                        experiment.get(
                            "category",
                            "",
                        )
                    ),

                    "status": "NOT_EXECUTED",

                    "baseline_required": (
                        experiment_id != "EXP-01"
                    ),

                    "minimum_repeat_runs": 3,

                    "record_all_runs": True,

                    "raw_results_required": True,

                    "configuration_snapshot_required": True,

                    "execution_evidence_required": True,
                }
            )

        return matrix

    # ============================================================
    # RESULT SCHEMA
    # ============================================================

    def _build_result_schema(
        self,
        metrics: dict[str, Any],
    ) -> dict[str, Any]:

        return {
            "experiment_id": "string",

            "run_id": "string",

            "timestamp": "datetime",

            "project_id": "string",

            "dataset_version": "string",

            "model_version": "string",

            "code_version": "string",

            "configuration": "object",

            "hardware": "object",

            "environment": "object",

            "input_conditions": "object",

            "metrics": {
                "primary": "object",
                "secondary": "object",
            },

            "baseline_comparison": {
                "baseline_value": "number",
                "candidate_value": "number",
                "absolute_difference": "number",
                "relative_difference": "number",
            },

            "errors": "object",

            "statistical_analysis": {
                "method": "string",
                "p_value": "number",
                "confidence_interval": "object",
            },

            "artifacts": [
                "logs",
                "plots",
                "predictions",
                "model",
                "configuration",
            ],

            "notes": "string",

            "verification": {
                "executed": "boolean",
                "reproducible": "boolean",
                "reviewed": "boolean",
            },
        }

    # ============================================================
    # FAILURE ANALYSIS
    # ============================================================

    def _build_failure_analysis(
        self,
        solution: dict[str, Any],
        architecture: dict[str, Any],
        domains: list[str],
    ) -> dict[str, Any]:

        categories = [
            "False positives",
            "False negatives",
            "Incorrect predictions",
            "Missing inputs",
            "Data quality failures",
            "Model failures",
            "API failures",
            "System failures",
            "Performance failures",
        ]

        domain_text = " ".join(
            domains
        ).lower()

        if (
            "iot" in domain_text
            or "sensor" in domain_text
            or "smart agriculture" in domain_text
        ):
            categories.extend(
                [
                    "Sensor failures",
                    "Communication failures",
                    "Calibration errors",
                ]
            )

        if (
            "computer vision" in domain_text
            or "vision" in domain_text
        ):
            categories.extend(
                [
                    "Poor lighting",
                    "Occlusion",
                    "Detection confidence failures",
                    "Class confusion",
                ]
            )

        return {
            "categories": self._unique_strings(
                categories
            ),

            "analysis_process": [
                "Identify the failure.",
                "Record input conditions.",
                "Record system configuration.",
                "Identify the responsible component.",
                "Determine probable cause.",
                "Assess impact.",
                "Determine whether the failure is reproducible.",
                "Implement corrective action where justified.",
                "Re-run the affected experiment.",
                "Record the failure in project history.",
            ],

            "status": "READY_FOR_EXECUTION",
        }

    # ============================================================
    # CLAIM → EXPERIMENT TRACEABILITY
    # ============================================================

    def _build_claim_experiment_map(
        self,
        research: dict[str, Any],
        research_intelligence: dict[str, Any],
        experiments: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:

        claim_analysis = (
            research_intelligence.get(
                "claim_analysis",
                {},
            )
            or research.get(
                "claim_analysis",
                {},
            )
            or {}
        )

        claims = self._as_list(
            claim_analysis.get(
                "claims",
                [],
            )
        )

        mapping = []

        if not claims:
            return mapping

        experiment_ids = [
            experiment.get(
                "id"
            )
            for experiment in experiments
        ]

        for index, claim in enumerate(
            claims,
            start=1,
        ):

            if isinstance(
                claim,
                dict,
            ):
                claim_id = self._clean_text(
                    claim.get(
                        "id",
                        f"CLAIM-{index:02d}",
                    )
                )

                claim_text = self._clean_text(
                    claim.get(
                        "claim",
                        claim.get(
                            "text",
                            claim.get(
                                "statement",
                                "",
                            ),
                        ),
                    )
                )

                evidence_ids = self._string_list(
                    claim.get(
                        "evidence_ids",
                        [],
                    )
                )

            else:
                claim_id = f"CLAIM-{index:02d}"
                claim_text = self._clean_text(
                    claim
                )
                evidence_ids = []

            if index == 1:
                linked_experiments = [
                    "EXP-01",
                    "EXP-02",
                ]

            elif index == 2:
                linked_experiments = [
                    "EXP-02",
                    "EXP-03",
                ]

            else:
                linked_experiments = [
                    experiment_ids[
                        min(
                            index - 1,
                            len(experiment_ids) - 1,
                        )
                    ]
                ] if experiment_ids else []

            mapping.append(
                {
                    "claim_id": claim_id,

                    "claim": claim_text,

                    "existing_evidence_ids": (
                        evidence_ids
                    ),

                    "experiments_required_to_test": (
                        linked_experiments
                    ),

                    "status": "PENDING_EXPERIMENT",

                    "interpretation_policy": (
                        "Existing literature evidence supports "
                        "the research context; only executed "
                        "project experiments can validate the "
                        "project-specific claim."
                    ),
                }
            )

        return mapping

    # ============================================================
    # VALIDATION GATES
    # ============================================================

    def _build_validation_gates(
        self,
        experiments: list[dict[str, Any]],
        metrics: dict[str, Any],
        solution: dict[str, Any],
        architecture: dict[str, Any],
    ) -> list[dict[str, Any]]:

        return [
            {
                "gate": "G1",
                "name": "Dataset Readiness",
                "requirement": (
                    "Dataset provenance, quality, version, "
                    "and preprocessing must be documented."
                ),
                "status": "PENDING",
            },
            {
                "gate": "G2",
                "name": "Baseline Readiness",
                "requirement": (
                    "A defensible baseline must be selected "
                    "and executed under comparable conditions."
                ),
                "status": "PENDING",
            },
            {
                "gate": "G3",
                "name": "Model Evaluation",
                "requirement": (
                    "The proposed intelligence layer must be "
                    "evaluated using task-appropriate metrics."
                ),
                "status": "PENDING",
            },
            {
                "gate": "G4",
                "name": "System Validation",
                "requirement": (
                    "Integrated system performance must be "
                    "measured under representative conditions."
                ),
                "status": "PENDING",
            },
            {
                "gate": "G5",
                "name": "Robustness",
                "requirement": (
                    "Important failure and boundary conditions "
                    "must be tested."
                ),
                "status": "PENDING",
            },
            {
                "gate": "G6",
                "name": "Reproducibility",
                "requirement": (
                    "The experiment must be reproducible from "
                    "recorded code, data, configuration, and environment."
                ),
                "status": "PENDING",
            },
            {
                "gate": "G7",
                "name": "Evidence-backed Conclusion",
                "requirement": (
                    "Final conclusions must be based on executed "
                    "results and must not be inferred from the "
                    "experiment plan alone."
                ),
                "status": "PENDING",
            },
        ]

    # ============================================================
    # VALIDATION READINESS
    # ============================================================

    def _calculate_validation_readiness(
        self,
        evidence_context: dict[str, Any],
        experiments: list[dict[str, Any]],
        metrics: dict[str, Any],
        dataset_plan: dict[str, Any],
        baseline: dict[str, Any],
        reproducibility: dict[str, Any],
    ) -> dict[str, Any]:

        score = 0

        if evidence_context.get(
            "paper_count",
            0,
        ) > 0:
            score += 15

        if evidence_context.get(
            "claim_evidence_coverage_percent",
            0,
        ) >= 70:
            score += 15

        if evidence_context.get(
            "evidence_synthesis_available",
            False,
        ):
            score += 10

        if experiments:
            score += 20

        if metrics.get(
            "primary_task_metrics",
        ):
            score += 10

        if baseline.get(
            "candidate_baselines",
        ):
            score += 10

        if dataset_plan.get(
            "requirements",
        ):
            score += 10

        if reproducibility.get(
            "required_records",
        ):
            score += 10

        score = min(
            score,
            100,
        )

        if score >= 80:
            level = "HIGH"

        elif score >= 60:
            level = "MEDIUM"

        else:
            level = "LOW"

        return {
            "score": score,

            "level": level,

            "status": (
                "READY_FOR_EXPERIMENT_EXECUTION"
                if score >= 70
                else "REQUIRES_PRE_EXECUTION_WORK"
            ),

            "interpretation": (
                "Readiness measures completeness of the "
                "experimental design and evidence context. "
                "It does not indicate that the system has "
                "already been validated."
            ),

            "results_verified": False,
        }

    # ============================================================
    # VALIDATION REQUIREMENTS
    # ============================================================

    def _build_validation_requirements(
        self,
        solution: dict[str, Any],
        architecture: dict[str, Any],
    ) -> dict[str, Any]:

        solution_validation = solution.get(
            "validation",
            {},
        )

        if not isinstance(
            solution_validation,
            dict,
        ):
            solution_validation = {}

        return {
            "solution_defined_requirements": solution_validation,

            "minimum_requirements": [
                "Real or appropriately representative data",
                "Defined baseline",
                "Task-appropriate metrics",
                "Controlled test protocol",
                "Repeatable execution",
                "Failure analysis",
                "Reproducible configuration",
                "Documented limitations",
            ],

            "completion_rule": (
                "The validation stage may only mark scientific "
                "claims as validated after the corresponding "
                "experiments have actually been executed and "
                "their evidence reviewed."
            ),
        }

    # ============================================================
    # EXECUTION POLICY
    # ============================================================

    def _build_execution_policy(self) -> list[str]:

        return [
            "Define the experiment before executing it.",
            "Record dataset and configuration versions.",
            "Use a reproducible random seed where applicable.",
            "Use the same evaluation conditions for fair comparisons.",
            "Compare against a defensible baseline.",
            "Record every execution, including failed runs.",
            "Store raw and processed results.",
            "Preserve experiment artifacts.",
            "Do not modify results to obtain a preferred outcome.",
            "Report uncertainty and limitations.",
            "Investigate unexpected results.",
            "Separate exploratory analysis from confirmatory conclusions.",
            "Do not claim validation from an unexecuted experiment plan.",
            "Do not claim global novelty from experiment results alone.",
        ]

    # ============================================================
    # COMPONENT EXTRACTION
    # ============================================================

    def _extract_component_names(
        self,
        architecture: dict[str, Any],
    ) -> list[str]:

        components = architecture.get(
            "components",
            [],
        )

        result = []

        for component in self._as_list(
            components
        ):

            if isinstance(
                component,
                dict,
            ):
                value = (
                    component.get("name")
                    or component.get("component")
                    or component.get("title")
                )

                if value:
                    result.append(
                        self._clean_text(
                            value
                        )
                    )

            elif component:
                result.append(
                    self._clean_text(
                        component
                    )
                )

        return self._unique_strings(
            result
        )

    # ============================================================
    # EVIDENCE IDS
    # ============================================================

    def _collect_evidence_ids(
        self,
        project: AURAProject,
        research: dict[str, Any],
        research_intelligence: dict[str, Any],
    ) -> list[str]:

        ids: list[str] = []

        for record in self._as_list(
            project.evidence
        ):

            if isinstance(
                record,
                dict,
            ):
                for key in (
                    "evidence_id",
                    "id",
                    "paper_id",
                    "source_id",
                ):
                    value = record.get(
                        key
                    )

                    if value:
                        ids.append(
                            str(value)
                        )
                        break

        for paper in self._as_list(
            research.get(
                "papers",
                [],
            )
        ):

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

        for value in self._string_list(
            research_intelligence.get(
                "supporting_evidence_ids",
                [],
            )
        ):
            ids.append(
                value
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

            if isinstance(
                item,
                dict,
            ):

                for key in (
                    "text",
                    "name",
                    "term",
                    "value",
                    "description",
                    "question",
                    "title",
                    "claim",
                    "statement",
                ):

                    if item.get(
                        key
                    ):

                        text = self._clean_text(
                            item[key]
                        )

                        if text:
                            result.append(
                                text
                            )

                        break

                else:
                    text = self._clean_text(
                        item
                    )

                    if text:
                        result.append(
                            text
                        )

            else:

                text = self._clean_text(
                    item
                )

                if text:
                    result.append(
                        text
                    )

        return result

    def _unique_strings(
        self,
        values: list[str],
    ) -> list[str]:

        result: list[str] = []
        seen: set[str] = set()

        for value in values:

            text = self._clean_text(
                value
            )

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
                "text",
                "name",
                "title",
                "value",
                "description",
                "question",
                "claim",
                "statement",
                "opportunity",
                "limitation",
                "challenge",
            ):

                if value.get(
                    key
                ) is not None:

                    return str(
                        value[key]
                    ).strip()

            return ""

        return str(
            value
        ).strip()

    def _number(
        self,
        value: Any,
    ) -> float:

        try:
            if isinstance(
                value,
                str,
            ):
                cleaned = (
                    value
                    .replace(
                        "%",
                        "",
                    )
                    .strip()
                )

                return float(
                    cleaned
                )

            return float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):
            return 0.0

    def _extract_score(
        self,
        data: dict[str, Any],
        key: str,
    ) -> float:

        if not isinstance(
            data,
            dict,
        ):
            return 0.0

        value = data.get(
            key,
            0,
        )

        if isinstance(
            value,
            dict,
        ):
            value = (
                value.get("score")
                or value.get("value")
                or 0
            )

        return round(
            self._number(
                value
            ),
            2,
        )


experiment_agent = ExperimentAgent()