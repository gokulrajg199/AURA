"""
AURA — Validation Intelligence Engine

Stage:
    VALIDATE

Purpose:
    Convert AURA's research, evidence, solution, architecture,
    development and experiment plans into a rigorous validation layer.

Important:
    - Never fabricate experimental results.
    - Never convert plans into verified results.
    - Preserve claim → evidence → experiment → acceptance traceability.
    - Clearly separate metadata verification, AI synthesis,
      recommendations, planned tests and executed results.
"""

from __future__ import annotations

from typing import Any

from models.project import AURAProject
from orchestration.contract import AURAStageResult
from orchestration.stages import AURAStage


class ValidationAgent:
    stage = AURAStage.VALIDATE

    async def run(self, project: AURAProject) -> AURAStageResult:
        try:
            validation = self._build_validation_framework(project)

            project.validation = validation
            project.analysis["validation"] = validation

            self._store_memory(project, validation)
            self._store_evidence(project, validation)

            return AURAStageResult(
                stage=self.stage,
                success=True,
                message=(
                    "AURA completed evidence-aware validation planning "
                    "with claim-to-evidence-to-experiment traceability."
                ),
                data={"validation": validation},
                next_stage=AURAStage.DELIVER,
            )

        except Exception as error:
            return AURAStageResult(
                stage=self.stage,
                success=False,
                message=f"Validation framework generation failed: {error}",
            )

    # ================================================================
    # MAIN VALIDATION FRAMEWORK
    # ================================================================

    def _build_validation_framework(
        self,
        project: AURAProject,
    ) -> dict[str, Any]:

        solution = self._as_dict(project.solution)
        architecture = self._as_dict(project.architecture)
        development = self._as_dict(project.development)
        experiments = self._as_dict(project.experiments)

        research = self._as_dict(project.research)

        research_intelligence = self._as_dict(
            project.analysis.get("research_intelligence", {})
        )

        verdict = self._as_dict(
            project.analysis.get("verdict", {})
        )

        innovation = self._as_dict(project.innovation)

        papers = self._extract_papers(project)

        claim_analysis = self._extract_claim_analysis(
            research_intelligence
        )

        evidence_summary = self._build_evidence_validation(
            project,
            papers,
            research_intelligence,
            claim_analysis,
        )

        technical_validation = self._build_technical_validation(
            solution,
            architecture,
            development,
        )

        functional_validation = self._build_functional_validation(
            project,
            solution,
            development,
        )

        experimental_validation = self._build_experimental_validation(
            experiments
        )

        baseline_validation = self._build_baseline_validation(
            experiments,
            research_intelligence,
        )

        dataset_validation = self._build_dataset_validation(
            experiments,
            solution,
        )

        robustness_validation = self._build_robustness_validation(
            experiments,
            solution,
        )

        reproducibility = self._build_reproducibility_plan(
            experiments,
            development,
        )

        risks = self._build_risk_validation(
            solution,
            architecture,
            experiments,
            verdict,
            evidence_summary,
        )

        acceptance = self._build_acceptance_criteria(
            solution,
            experiments,
            technical_validation,
            evidence_summary,
        )

        claim_validation_map = self._build_claim_validation_map(
            project,
            claim_analysis,
            experimental_validation,
            acceptance,
        )

        traceability = self._build_traceability(
            project,
            research,
            research_intelligence,
            verdict,
            innovation,
            solution,
            architecture,
            development,
            experiments,
            validation_claims=claim_validation_map,
        )

        readiness = self._calculate_validation_readiness(
            evidence_summary,
            technical_validation,
            functional_validation,
            experimental_validation,
            baseline_validation,
            dataset_validation,
            robustness_validation,
            reproducibility,
            risks,
            acceptance,
        )

        execution_status = {
            "validation_framework_status": "PLANNED",
            "experiments_executed": False,
            "results_available": False,
            "results_verified": False,
            "external_validation_completed": False,
            "independent_reproduction_completed": False,
            "human_expert_review_required": True,
            "important_rule": (
                "AURA must not treat a planned experiment, expected "
                "result, recommendation or hypothesis as an actual result."
            ),
        }

        return {
            "stage": "VALIDATE",
            "status": "completed",

            "validation_verdict": readiness,

            "evidence_validation": evidence_summary,

            "technical_validation": technical_validation,

            "functional_validation": functional_validation,

            "experimental_validation": experimental_validation,

            "baseline_validation": baseline_validation,

            "dataset_validation": dataset_validation,

            "robustness_validation": robustness_validation,

            "reproducibility": reproducibility,

            "risk_validation": risks,

            "acceptance_criteria": acceptance,

            "claim_validation_map": claim_validation_map,

            "traceability": traceability,

            "execution_status": execution_status,

            "verification_scope": {
                "literature_metadata_verified": bool(papers),
                "research_synthesis_available": bool(
                    research_intelligence
                ),
                "claim_analysis_available": bool(claim_analysis),
                "claim_evidence_mapping_available": bool(
                    claim_analysis.get("claims")
                    or research.get("claim_evidence_map")
                ),
                "solution_available": bool(solution),
                "architecture_available": bool(architecture),
                "development_plan_available": bool(development),
                "experiment_plan_available": bool(experiments),
                "validation_plan_generated": True,
                "actual_experiment_results": False,
                "results_verified": False,
                "external_reproduction": False,
            },

            "aura_policy": {
                "fabricate_results": False,
                "claim_global_novelty": False,
                "treat_recommendations_as_facts": False,
                "planned_is_not_executed": True,
                "expected_is_not_observed": True,
                "metadata_is_not_full_text_verification": True,
                "require_evidence_for_major_claims": True,
                "require_baseline_comparison": True,
                "require_reproducibility": True,
                "flag_uncertainty": True,
            },
        }

    # ================================================================
    # EVIDENCE VALIDATION
    # ================================================================

    def _build_evidence_validation(
        self,
        project: AURAProject,
        papers: list[dict[str, Any]],
        research_intelligence: dict[str, Any],
        claim_analysis: dict[str, Any],
    ) -> dict[str, Any]:

        source_types: dict[str, int] = {}

        for paper in papers:
            source = str(
                paper.get("source")
                or paper.get("provider")
                or paper.get("database")
                or "Unknown"
            )

            source_types[source] = (
                source_types.get(source, 0) + 1
            )

        metadata_verified = sum(
            1
            for paper in papers
            if paper.get("title")
            or paper.get("doi")
            or paper.get("url")
            or paper.get("paper_id")
        )

        open_access = sum(
            1
            for paper in papers
            if bool(
                paper.get("is_open_access")
                or paper.get("open_access")
            )
        )

        claims = claim_analysis.get("claims", [])

        claims_with_evidence = sum(
            1
            for claim in claims
            if self._claim_has_evidence(claim)
        )

        claims_without_evidence = max(
            0,
            len(claims) - claims_with_evidence,
        )

        claim_coverage = (
            round(
                claims_with_evidence
                / len(claims)
                * 100,
                1,
            )
            if claims
            else 0.0
        )

        evidence_checks = [
            {
                "check": "Source provenance",
                "status": "PASS" if papers else "PENDING",
                "description": (
                    "Retrieved research should retain provider/source "
                    "information."
                ),
            },
            {
                "check": "Bibliographic metadata",
                "status": (
                    "PASS"
                    if metadata_verified
                    else "PENDING"
                ),
                "description": (
                    "Research records should contain identifiers, "
                    "titles or source references."
                ),
            },
            {
                "check": "Cross-source comparison",
                "status": (
                    "PASS"
                    if len(source_types) >= 2
                    else "PENDING"
                ),
                "description": (
                    "Important research conclusions should be compared "
                    "across independent source providers where possible."
                ),
            },
            {
                "check": "Claim-level evidence",
                "status": (
                    "PASS"
                    if claims and claim_coverage >= 80
                    else (
                        "PARTIAL"
                        if claims_with_evidence
                        else "PENDING"
                    )
                ),
                "description": (
                    "Major research claims should maintain explicit "
                    "links to supporting evidence."
                ),
            },
            {
                "check": "Full-text verification",
                "status": "NOT_ESTABLISHED",
                "description": (
                    "Metadata retrieval does not prove that the "
                    "full text of every paper was verified."
                ),
            },
        ]

        return {
            "papers_available": len(papers),
            "metadata_verified_records": metadata_verified,
            "open_access_records": open_access,
            "source_distribution": source_types,
            "source_count": len(source_types),

            "claims_total": len(claims),
            "claims_with_evidence": claims_with_evidence,
            "claims_without_evidence": claims_without_evidence,
            "claim_evidence_coverage_percent": claim_coverage,

            "evidence_checks": evidence_checks,

            "evidence_policy": (
                "AURA distinguishes metadata-supported evidence, "
                "claim-level evidence and full-text verified evidence."
            ),
        }

    # ================================================================
    # TECHNICAL VALIDATION
    # ================================================================

    def _build_technical_validation(
        self,
        solution: dict[str, Any],
        architecture: dict[str, Any],
        development: dict[str, Any],
    ) -> dict[str, Any]:

        checks = [
            {
                "id": "TECH-01",
                "check": "Solution completeness",
                "status": "PASS" if solution else "PENDING",
            },
            {
                "id": "TECH-02",
                "check": "Architecture defined",
                "status": "PASS" if architecture else "PENDING",
            },
            {
                "id": "TECH-03",
                "check": "Development plan defined",
                "status": "PASS" if development else "PENDING",
            },
            {
                "id": "TECH-04",
                "check": "Technology compatibility",
                "status": "REQUIRES_TEST",
            },
            {
                "id": "TECH-05",
                "check": "Resource requirements",
                "status": "REQUIRES_TEST",
            },
            {
                "id": "TECH-06",
                "check": "Deployment feasibility",
                "status": "REQUIRES_TEST",
            },
            {
                "id": "TECH-07",
                "check": "Security controls",
                "status": "REQUIRES_TEST",
            },
            {
                "id": "TECH-08",
                "check": "Performance requirements",
                "status": "REQUIRES_TEST",
            },
        ]

        return {
            "checks": checks,
            "status": self._status_from_checks(checks),
            "required_actions": [
                "Verify technology compatibility.",
                "Verify hardware and software resources.",
                "Build a minimal working prototype.",
                "Measure latency and compute requirements.",
                "Perform security testing.",
                "Perform deployment testing.",
            ],
        }

    # ================================================================
    # FUNCTIONAL VALIDATION
    # ================================================================

    def _build_functional_validation(
        self,
        project: AURAProject,
        solution: dict[str, Any],
        development: dict[str, Any],
    ) -> dict[str, Any]:

        features = self._extract_list(
            solution,
            [
                "core_features",
                "features",
                "functional_requirements",
            ],
        )

        if not features:
            features = list(project.requirements)

        if not features:
            features = [
                "Input processing",
                "Core intelligence generation",
                "Decision or prediction generation",
                "Output delivery",
                "Monitoring and feedback",
            ]

        test_cases = []

        for index, feature in enumerate(features, start=1):
            text = str(feature).strip()

            if not text:
                continue

            test_cases.append(
                {
                    "test_id": f"FUNC-{index:02d}",
                    "feature": text,
                    "test_method": (
                        "Provide representative input and compare "
                        "actual behavior against the defined requirement."
                    ),
                    "expected_result": (
                        f"The system correctly performs: {text}"
                    ),
                    "status": "NOT_EXECUTED",
                    "evidence_required": [
                        "input",
                        "configuration",
                        "actual_output",
                        "expected_output",
                        "pass_fail_result",
                    ],
                }
            )

        return {
            "test_case_count": len(test_cases),
            "test_cases": test_cases,
            "status": "PLANNED",
            "implementation_context_available": bool(
                development
            ),
        }

    # ================================================================
    # EXPERIMENTAL VALIDATION
    # ================================================================

    def _build_experimental_validation(
        self,
        experiments: dict[str, Any],
    ) -> dict[str, Any]:

        experiment_list = self._extract_list(
            experiments,
            [
                "experiments",
                "experiment_plan",
                "planned_experiments",
            ],
        )

        if not experiment_list:
            experiment_list = [
                {
                    "id": "EXP-01",
                    "name": "Baseline Evaluation",
                },
                {
                    "id": "EXP-02",
                    "name": "Proposed System Evaluation",
                },
                {
                    "id": "EXP-03",
                    "name": "System Performance Evaluation",
                },
                {
                    "id": "EXP-04",
                    "name": "Robustness Evaluation",
                },
                {
                    "id": "EXP-05",
                    "name": "Ablation Evaluation",
                },
            ]

        validations = []

        for index, experiment in enumerate(
            experiment_list,
            start=1,
        ):

            if isinstance(experiment, dict):
                experiment_id = (
                    experiment.get("id")
                    or experiment.get("experiment_id")
                    or f"EXP-{index:02d}"
                )

                name = (
                    experiment.get("name")
                    or experiment.get("title")
                    or f"Experiment {index}"
                )

                validations.append(
                    {
                        "experiment_id": str(
                            experiment_id
                        ),
                        "name": str(name),
                        "execution_status": "NOT_EXECUTED",
                        "result_status": "NOT_AVAILABLE",
                        "validation_status": "PLANNED",
                        "required_evidence": [
                            "dataset/version",
                            "configuration",
                            "baseline",
                            "metrics",
                            "results",
                            "statistical_analysis",
                            "artifacts",
                        ],
                    }
                )

            else:
                validations.append(
                    {
                        "experiment_id": f"EXP-{index:02d}",
                        "name": str(experiment),
                        "execution_status": "NOT_EXECUTED",
                        "result_status": "NOT_AVAILABLE",
                        "validation_status": "PLANNED",
                    }
                )

        return {
            "experiments": validations,
            "experiment_count": len(validations),
            "status": "PLANNED",
            "execution_status": "NOT_EXECUTED",
            "result_integrity_rule": (
                "An experiment plan is not an experimental result. "
                "Only explicitly supplied and verifiable execution "
                "results may change this status."
            ),
        }

    # ================================================================
    # BASELINE
    # ================================================================

    def _build_baseline_validation(
        self,
        experiments: dict[str, Any],
        research_intelligence: dict[str, Any],
    ) -> dict[str, Any]:

        methods = self._extract_list(
            research_intelligence,
            [
                "methods",
                "existing_methods",
                "research_methods",
            ],
        )

        return {
            "baseline_required": True,
            "baseline_status": "NOT_EXECUTED",
            "candidate_baselines": methods,
            "comparison_requirements": [
                "Select an appropriate established baseline.",
                "Use comparable evaluation data.",
                "Use comparable preprocessing.",
                "Use consistent primary metrics.",
                "Report absolute improvement.",
                "Report relative improvement.",
                "Report negative or failed cases.",
            ],
            "fair_comparison_rules": [
                "Same evaluation dataset",
                "Same preprocessing policy",
                "Comparable training conditions",
                "Comparable hardware where relevant",
                "Clearly reported hyperparameters",
                "Same evaluation protocol",
            ],
            "research_context_available": bool(
                research_intelligence
            ),
        }

    # ================================================================
    # DATASET
    # ================================================================

    def _build_dataset_validation(
        self,
        experiments: dict[str, Any],
        solution: dict[str, Any],
    ) -> dict[str, Any]:

        datasets = self._extract_list(
            experiments,
            [
                "dataset_plan",
                "datasets",
                "data_sources",
            ],
        )

        if not datasets:
            datasets = self._extract_list(
                solution,
                [
                    "datasets",
                    "data_sources",
                ],
            )

        return {
            "datasets_identified": datasets,
            "dataset_status": (
                "IDENTIFIED"
                if datasets
                else "REQUIRES_SELECTION"
            ),
            "validation_checks": [
                {
                    "check": "Dataset relevance",
                    "status": "REQUIRES_TEST",
                },
                {
                    "check": "Dataset quality",
                    "status": "REQUIRES_TEST",
                },
                {
                    "check": "Data balance",
                    "status": "REQUIRES_TEST",
                },
                {
                    "check": "Missing data",
                    "status": "REQUIRES_TEST",
                },
                {
                    "check": "Data leakage",
                    "status": "REQUIRES_TEST",
                },
                {
                    "check": "Train/test separation",
                    "status": "REQUIRES_TEST",
                },
                {
                    "check": "Bias and representativeness",
                    "status": "REQUIRES_TEST",
                },
                {
                    "check": "License and usage rights",
                    "status": "REQUIRES_VERIFICATION",
                },
            ],
        }

    # ================================================================
    # ROBUSTNESS
    # ================================================================

    def _build_robustness_validation(
        self,
        experiments: dict[str, Any],
        solution: dict[str, Any],
    ) -> dict[str, Any]:

        return {
            "status": "PLANNED",
            "required_tests": [
                {
                    "id": "ROB-01",
                    "test": "Normal input variation",
                    "purpose": (
                        "Measure performance under expected variation."
                    ),
                },
                {
                    "id": "ROB-02",
                    "test": "Noisy input",
                    "purpose": (
                        "Measure resilience to imperfect data."
                    ),
                },
                {
                    "id": "ROB-03",
                    "test": "Missing data",
                    "purpose": (
                        "Measure behavior when information is unavailable."
                    ),
                },
                {
                    "id": "ROB-04",
                    "test": "Out-of-distribution input",
                    "purpose": (
                        "Identify behavior outside the expected distribution."
                    ),
                },
                {
                    "id": "ROB-05",
                    "test": "Failure recovery",
                    "purpose": (
                        "Verify safe handling of component/service failure."
                    ),
                },
                {
                    "id": "ROB-06",
                    "test": "Stress testing",
                    "purpose": (
                        "Measure system behavior under increased load."
                    ),
                },
            ],
            "system_context_available": bool(solution),
            "experiment_context_available": bool(experiments),
        }

    # ================================================================
    # REPRODUCIBILITY
    # ================================================================

    def _build_reproducibility_plan(
        self,
        experiments: dict[str, Any],
        development: dict[str, Any],
    ) -> dict[str, Any]:

        return {
            "status": "PLANNED",
            "requirements": [
                "Version-controlled source code",
                "Pinned dependency versions",
                "Dataset version/reference",
                "Configuration files",
                "Random seed where applicable",
                "Model/checkpoint version",
                "Hardware/software environment",
                "Experiment logs",
                "Evaluation scripts",
                "Result artifacts",
            ],
            "reproduction_test": {
                "status": "NOT_EXECUTED",
                "requirement": (
                    "Independent reproduction should achieve results "
                    "within a predefined tolerance."
                ),
            },
            "development_plan_available": bool(
                development
            ),
            "experiment_plan_available": bool(
                experiments
            ),
        }

    # ================================================================
    # RISKS
    # ================================================================

    def _build_risk_validation(
        self,
        solution: dict[str, Any],
        architecture: dict[str, Any],
        experiments: dict[str, Any],
        verdict: dict[str, Any],
        evidence_summary: dict[str, Any],
    ) -> dict[str, Any]:

        risks = [
            {
                "risk_id": "RISK-01",
                "risk": "Insufficient research evidence",
                "severity": "MEDIUM",
                "mitigation": (
                    "Expand source coverage and verify important claims."
                ),
            },
            {
                "risk_id": "RISK-02",
                "risk": "Weak baseline",
                "severity": "HIGH",
                "mitigation": (
                    "Select established methods from relevant research."
                ),
            },
            {
                "risk_id": "RISK-03",
                "risk": "Dataset limitations",
                "severity": "HIGH",
                "mitigation": (
                    "Validate quality, representativeness, licensing "
                    "and leakage."
                ),
            },
            {
                "risk_id": "RISK-04",
                "risk": "Overclaiming novelty",
                "severity": "HIGH",
                "mitigation": (
                    "Use evidence-bounded novelty language."
                ),
            },
            {
                "risk_id": "RISK-05",
                "risk": "Prototype fails real-world conditions",
                "severity": "MEDIUM",
                "mitigation": (
                    "Perform robustness and deployment testing."
                ),
            },
            {
                "risk_id": "RISK-06",
                "risk": "Reproducibility failure",
                "severity": "MEDIUM",
                "mitigation": (
                    "Record code, data, configuration and environment."
                ),
            },
        ]

        coverage = evidence_summary.get(
            "claim_evidence_coverage_percent",
            0,
        )

        if coverage < 80:
            risks.append(
                {
                    "risk_id": "RISK-07",
                    "risk": "Major claims lack sufficient evidence",
                    "severity": "HIGH",
                    "mitigation": (
                        "Expand evidence mapping before making strong "
                        "research conclusions."
                    ),
                }
            )

        if not solution:
            risks.append(
                {
                    "risk_id": "RISK-08",
                    "risk": "Incomplete solution definition",
                    "severity": "HIGH",
                    "mitigation": (
                        "Complete solution design before implementation."
                    ),
                }
            )

        if not architecture:
            risks.append(
                {
                    "risk_id": "RISK-09",
                    "risk": "Architecture insufficiently defined",
                    "severity": "HIGH",
                    "mitigation": (
                        "Complete architecture validation before implementation."
                    ),
                }
            )

        return {
            "risks": risks,
            "risk_count": len(risks),
            "highest_severity": self._highest_risk(risks),
            "verdict_context_available": bool(verdict),
            "experiment_context_available": bool(experiments),
        }

    # ================================================================
    # ACCEPTANCE CRITERIA
    # ================================================================

    def _build_acceptance_criteria(
        self,
        solution: dict[str, Any],
        experiments: dict[str, Any],
        technical_validation: dict[str, Any],
        evidence_summary: dict[str, Any],
    ) -> dict[str, Any]:

        evidence_target = (
            "≥80% major claims traceable"
            if evidence_summary.get("claims_total", 0)
            else "Major claims must be traceable"
        )

        return {
            "criteria": [
                {
                    "id": "ACC-01",
                    "criterion": (
                        "Core functionality works as specified."
                    ),
                    "measurement": "Functional test pass rate",
                    "target": "100% critical-path tests pass",
                    "status": "NOT_VERIFIED",
                },
                {
                    "id": "ACC-02",
                    "criterion": (
                        "Proposed approach is meaningfully evaluated "
                        "against a baseline."
                    ),
                    "measurement": "Primary research metric",
                    "target": (
                        "Defined during experiment execution"
                    ),
                    "status": "NOT_VERIFIED",
                },
                {
                    "id": "ACC-03",
                    "criterion": (
                        "System remains reliable under expected variation."
                    ),
                    "measurement": "Robustness metrics",
                    "target": (
                        "Defined for target application"
                    ),
                    "status": "NOT_VERIFIED",
                },
                {
                    "id": "ACC-04",
                    "criterion": (
                        "System satisfies deployment constraints."
                    ),
                    "measurement": (
                        "Latency / memory / compute / cost"
                    ),
                    "target": (
                        "Defined for deployment environment"
                    ),
                    "status": "NOT_VERIFIED",
                },
                {
                    "id": "ACC-05",
                    "criterion": (
                        "Results are reproducible."
                    ),
                    "measurement": "Independent reproduction",
                    "target": "Within predefined tolerance",
                    "status": "NOT_VERIFIED",
                },
                {
                    "id": "ACC-06",
                    "criterion": (
                        "Major research claims have traceable evidence."
                    ),
                    "measurement": (
                        "Claim-evidence coverage"
                    ),
                    "target": evidence_target,
                    "status": (
                        "PARTIAL"
                        if evidence_summary.get(
                            "claims_with_evidence",
                            0,
                        )
                        else "NOT_VERIFIED"
                    ),
                },
            ],
            "status": "NOT_VERIFIED",
            "technical_validation_available": bool(
                technical_validation
            ),
            "solution_available": bool(solution),
            "experiment_plan_available": bool(experiments),
        }

    # ================================================================
    # CLAIM → VALIDATION MAP
    # ================================================================

    def _build_claim_validation_map(
        self,
        project: AURAProject,
        claim_analysis: dict[str, Any],
        experimental_validation: dict[str, Any],
        acceptance: dict[str, Any],
    ) -> list[dict[str, Any]]:

        claims = claim_analysis.get("claims", [])

        experiments = experimental_validation.get(
            "experiments",
            [],
        )

        experiment_ids = [
            str(
                item.get("experiment_id")
                or item.get("id")
                or ""
            )
            for item in experiments
            if isinstance(item, dict)
        ]

        mappings = []

        for index, claim in enumerate(
            claims,
            start=1,
        ):
            if not isinstance(claim, dict):
                continue

            claim_id = (
                claim.get("claim_id")
                or claim.get("id")
                or f"CLAIM-{index:03d}"
            )

            evidence_ids = self._extract_evidence_ids(
                claim
            )

            selected_experiment = (
                experiment_ids[index - 1]
                if experiment_ids
                and index <= len(experiment_ids)
                else (
                    experiment_ids[0]
                    if experiment_ids
                    else None
                )
            )

            mappings.append(
                {
                    "claim_id": str(claim_id),
                    "claim": str(
                        claim.get("claim")
                        or claim.get("statement")
                        or ""
                    ),
                    "evidence_ids": evidence_ids,
                    "evidence_status": (
                        "SUPPORTED"
                        if evidence_ids
                        else "UNSUPPORTED"
                    ),
                    "validation_experiment": (
                        selected_experiment
                    ),
                    "acceptance_criteria": [
                        "ACC-06"
                    ],
                    "execution_status": "NOT_EXECUTED",
                    "verification_status": "NOT_VERIFIED",
                }
            )

        if not mappings:
            mappings.append(
                {
                    "claim_id": "CLAIM-000",
                    "claim": (
                        "Major project claims must remain "
                        "traceable to evidence and validation."
                    ),
                    "evidence_ids": [],
                    "evidence_status": "PENDING",
                    "validation_experiment": (
                        experiment_ids[0]
                        if experiment_ids
                        else None
                    ),
                    "acceptance_criteria": [
                        "ACC-06"
                    ],
                    "execution_status": "NOT_EXECUTED",
                    "verification_status": "NOT_VERIFIED",
                }
            )

        return mappings

    # ================================================================
    # TRACEABILITY
    # ================================================================

    def _build_traceability(
        self,
        project: AURAProject,
        research: dict[str, Any],
        research_intelligence: dict[str, Any],
        verdict: dict[str, Any],
        innovation: dict[str, Any],
        solution: dict[str, Any],
        architecture: dict[str, Any],
        development: dict[str, Any],
        experiments: dict[str, Any],
        validation_claims: list[dict[str, Any]],
    ) -> dict[str, Any]:

        return {
            "original_idea": project.original_idea,

            "research": {
                "available": bool(research),
                "papers": len(
                    self._extract_papers(project)
                ),
            },

            "analysis": {
                "available": bool(
                    research_intelligence
                ),
            },

            "verdict": {
                "available": bool(verdict),
            },

            "innovation": {
                "available": bool(innovation),
            },

            "solution": {
                "available": bool(solution),
            },

            "architecture": {
                "available": bool(architecture),
            },

            "development": {
                "available": bool(development),
            },

            "experiments": {
                "available": bool(experiments),
            },

            "validation": {
                "available": True,
                "claims_mapped": len(validation_claims),
            },

            "chain": [
                "USER IDEA",
                "RESEARCH EVIDENCE",
                "RESEARCH ANALYSIS",
                "AURA VERDICT",
                "INNOVATION",
                "SOLUTION",
                "ARCHITECTURE",
                "DEVELOPMENT",
                "EXPERIMENTS",
                "VALIDATION",
            ],

            "traceability_rule": (
                "Every major research conclusion should be traceable "
                "from claim → evidence → validation experiment → "
                "acceptance criterion."
            ),
        }

    # ================================================================
    # READINESS
    # ================================================================

    def _calculate_validation_readiness(
        self,
        evidence_summary: dict[str, Any],
        technical_validation: dict[str, Any],
        functional_validation: dict[str, Any],
        experimental_validation: dict[str, Any],
        baseline_validation: dict[str, Any],
        dataset_validation: dict[str, Any],
        robustness_validation: dict[str, Any],
        reproducibility: dict[str, Any],
        risks: dict[str, Any],
        acceptance: dict[str, Any],
    ) -> dict[str, Any]:

        score = 0
        reasons: list[str] = []

        if evidence_summary.get(
            "papers_available",
            0,
        ) > 0:
            score += 10
            reasons.append(
                "Research evidence is available."
            )

        if evidence_summary.get(
            "source_count",
            0,
        ) >= 2:
            score += 10
            reasons.append(
                "Multiple source providers are represented."
            )

        claim_coverage = evidence_summary.get(
            "claim_evidence_coverage_percent",
            0,
        )

        if claim_coverage >= 80:
            score += 15
            reasons.append(
                "Major research claims have strong evidence coverage."
            )
        elif claim_coverage > 0:
            score += 7
            reasons.append(
                "Some research claims have evidence."
            )
        else:
            reasons.append(
                "Claim-level evidence coverage requires improvement."
            )

        if technical_validation.get(
            "status"
        ) == "READY":
            score += 15
        elif technical_validation.get(
            "status"
        ) == "PARTIAL":
            score += 8
            reasons.append(
                "Technical validation is partially prepared."
            )

        if functional_validation.get(
            "test_case_count",
            0,
        ) > 0:
            score += 10
            reasons.append(
                "Functional validation cases are defined."
            )

        if experimental_validation.get(
            "experiment_count",
            0,
        ) > 0:
            score += 10
            reasons.append(
                "Experimental validation plan is defined."
            )

        if baseline_validation.get(
            "baseline_required"
        ):
            score += 5
            reasons.append(
                "Baseline comparison is explicitly required."
            )

        if dataset_validation.get(
            "dataset_status"
        ) == "IDENTIFIED":
            score += 10
            reasons.append(
                "Candidate dataset/data sources are identified."
            )
        else:
            reasons.append(
                "Dataset selection requires verification."
            )

        if robustness_validation.get(
            "status"
        ) == "PLANNED":
            score += 5

        if reproducibility.get(
            "status"
        ) == "PLANNED":
            score += 5

        score = min(score, 100)

        if score >= 80:
            readiness = "HIGH"
        elif score >= 60:
            readiness = "MEDIUM"
        else:
            readiness = "LOW"

        return {
            "readiness_score": score,
            "readiness_level": readiness,
            "execution_required": True,
            "results_verified": False,
            "reasons": reasons,
            "important_note": (
                "Validation readiness means that a structured "
                "validation process is prepared. It does not mean "
                "that the project has been experimentally validated."
            ),
            "final_statement": (
                "AURA considers the project ready for validation "
                "execution only to the extent that the defined "
                "datasets, baselines, experiments, acceptance criteria "
                "and verification procedures can actually be executed."
            ),
        }

    # ================================================================
    # MEMORY
    # ================================================================

    def _store_memory(
        self,
        project: AURAProject,
        validation: dict[str, Any],
    ) -> None:

        verdict = validation.get(
            "validation_verdict",
            {},
        )

        project.memory.append(
            {
                "stage": "VALIDATE",
                "type": "validation_framework",
                "status": "completed",
                "readiness_score": verdict.get(
                    "readiness_score",
                    0,
                ),
                "readiness_level": verdict.get(
                    "readiness_level",
                    "LOW",
                ),
                "claim_evidence_coverage": validation[
                    "evidence_validation"
                ].get(
                    "claim_evidence_coverage_percent",
                    0,
                ),
                "experiments_executed": False,
                "results_verified": False,
            }
        )

    # ================================================================
    # EVIDENCE
    # ================================================================

    def _store_evidence(
        self,
        project: AURAProject,
        validation: dict[str, Any],
    ) -> None:

        project.evidence.append(
            {
                "stage": "VALIDATE",
                "type": "validation_framework",
                "status": "AURA_RECOMMENDATION",
                "claim": (
                    "AURA generated a structured validation framework "
                    "connecting research evidence, claims, experiments "
                    "and acceptance criteria."
                ),
                "support": {
                    "papers": validation[
                        "evidence_validation"
                    ].get("papers_available", 0),
                    "claim_coverage": validation[
                        "evidence_validation"
                    ].get(
                        "claim_evidence_coverage_percent",
                        0,
                    ),
                    "experiments": validation[
                        "experimental_validation"
                    ].get("experiment_count", 0),
                    "functional_tests": validation[
                        "functional_validation"
                    ].get("test_case_count", 0),
                    "risks": validation[
                        "risk_validation"
                    ].get("risk_count", 0),
                },
                "verification_required": True,
                "execution_status": "NOT_EXECUTED",
                "note": (
                    "This record describes a validation framework. "
                    "It is not evidence of successful experiments."
                ),
            }
        )

    # ================================================================
    # HELPERS
    # ================================================================

    def _extract_claim_analysis(
        self,
        research_intelligence: dict[str, Any],
    ) -> dict[str, Any]:

        value = research_intelligence.get(
            "claim_analysis",
            {}
        )

        return value if isinstance(value, dict) else {}

    def _claim_has_evidence(
        self,
        claim: dict[str, Any],
    ) -> bool:

        return bool(
            self._extract_evidence_ids(claim)
        )

    def _extract_evidence_ids(
        self,
        claim: dict[str, Any],
    ) -> list[str]:

        values: list[Any] = []

        for key in [
            "evidence_ids",
            "supporting_evidence",
            "supporting_evidence_ids",
            "source_ids",
        ]:
            value = claim.get(key)

            if isinstance(value, list):
                values.extend(value)

        ids: list[str] = []

        for value in values:
            if isinstance(value, dict):
                identifier = (
                    value.get("evidence_id")
                    or value.get("id")
                    or value.get("paper_id")
                    or value.get("source_id")
                )
            else:
                identifier = value

            if identifier is not None:
                identifier = str(identifier)

                if identifier and identifier not in ids:
                    ids.append(identifier)

        return ids

    def _extract_papers(
        self,
        project: AURAProject,
    ) -> list[dict[str, Any]]:

        research = self._as_dict(
            project.research
        )

        papers = research.get(
            "papers",
            [],
        )

        if isinstance(papers, list):
            return [
                paper
                for paper in papers
                if isinstance(paper, dict)
            ]

        return []

    def _extract_list(
        self,
        data: dict[str, Any],
        keys: list[str],
    ) -> list[Any]:

        for key in keys:
            value = data.get(key)

            if isinstance(value, list):
                return value

        return []

    def _as_dict(
        self,
        value: Any,
    ) -> dict[str, Any]:

        if hasattr(value, "model_dump"):
            dumped = value.model_dump()

            return (
                dumped
                if isinstance(dumped, dict)
                else {}
            )

        if isinstance(value, dict):
            return value

        return {}

    def _status_from_checks(
        self,
        checks: list[dict[str, Any]],
    ) -> str:

        if not checks:
            return "PENDING"

        statuses = [
            str(
                check.get(
                    "status",
                    "PENDING",
                )
            )
            for check in checks
        ]

        if all(
            status == "PASS"
            for status in statuses
        ):
            return "READY"

        if any(
            status == "PASS"
            for status in statuses
        ):
            return "PARTIAL"

        return "PENDING"

    def _highest_risk(
        self,
        risks: list[dict[str, Any]],
    ) -> str:

        priority = {
            "CRITICAL": 4,
            "HIGH": 3,
            "MEDIUM": 2,
            "LOW": 1,
        }

        highest = "LOW"
        highest_score = 0

        for risk in risks:
            severity = str(
                risk.get(
                    "severity",
                    "LOW",
                )
            ).upper()

            score = priority.get(
                severity,
                0,
            )

            if score > highest_score:
                highest = severity
                highest_score = score

        return highest


validation_agent = ValidationAgent()