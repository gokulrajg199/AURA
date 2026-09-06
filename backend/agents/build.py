from __future__ import annotations

from typing import Any

from models.project import AURAProject
from orchestration.contract import AURAStageResult
from orchestration.stages import AURAStage


class BuildAgent:
    """
    AURA Stage 08 — Development & Code Intelligence Engine.

    Converts the architecture into an implementation-ready blueprint.

    This stage does NOT claim that code has been generated or executed.
    It defines exactly what should be built, how it should be structured,
    what dependencies are required, how modules communicate, what tests
    are required, and which components are ready for future code generation.
    """

    stage = AURAStage.BUILD

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

            if not solution:
                return AURAStageResult(
                    stage=self.stage,
                    success=False,
                    message=(
                        "AURA cannot start development because "
                        "the Stage 06 solution specification is unavailable."
                    ),
                )

            if not architecture:
                return AURAStageResult(
                    stage=self.stage,
                    success=False,
                    message=(
                        "AURA cannot start development because "
                        "the Stage 07 architecture specification is unavailable."
                    ),
                )

            build_plan = self._build_plan(
                project=project,
                solution=solution,
                architecture=architecture,
            )

            project.development = build_plan
            project.analysis["development"] = build_plan

            project.memory.append(
                {
                    "stage": self.stage.value,
                    "type": "development_intelligence",
                    "summary": build_plan["summary"],
                    "module_count": len(
                        build_plan["modules"]
                    ),
                    "task_count": len(
                        build_plan["development_tasks"]
                    ),
                    "code_target_count": len(
                        build_plan["code_generation_targets"]
                    ),
                }
            )

            project.evidence.append(
                {
                    "stage": self.stage.value,
                    "type": "development_intelligence",
                    "status": "aura_synthesis",
                    "source": (
                        "AURA solution, architecture and evidence context"
                    ),
                    "claim": (
                        "AURA generated an implementation blueprint "
                        "derived from the selected solution and technical architecture."
                    ),
                    "evidence_ids": build_plan[
                        "evidence_context"
                    ]["supporting_evidence_ids"],
                    "verification_scope": (
                        "Implementation blueprint only. Code generation, "
                        "execution, performance and deployment require "
                        "actual implementation and testing."
                    ),
                }
            )

            return AURAStageResult(
                stage=self.stage,
                success=True,
                message=(
                    "AURA converted the architecture into a "
                    "research-aware implementation and code-generation blueprint."
                ),
                data={
                    "development": build_plan,
                },
                next_stage=AURAStage.EXPERIMENT,
            )

        except Exception as error:
            return AURAStageResult(
                stage=self.stage,
                success=False,
                message=f"Development planning failed: {error}",
            )

    # ============================================================
    # MASTER BUILD PLAN
    # ============================================================

    def _build_plan(
        self,
        project: AURAProject,
        solution: dict[str, Any],
        architecture: dict[str, Any],
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

        evidence_context = self._build_evidence_context(
            project=project,
            solution=solution,
            architecture=architecture,
        )

        modules = self._build_modules(
            project=project,
            architecture=architecture,
            solution=solution,
        )

        repository = self._build_repository(
            modules=modules,
            architecture=architecture,
        )

        tasks = self._build_tasks(
            modules=modules,
        )

        api_contract = self._build_api_contract(
            architecture=architecture,
        )

        data_pipeline = self._build_data_pipeline(
            architecture=architecture,
        )

        ai_pipeline = self._build_ai_pipeline(
            solution=solution,
            architecture=architecture,
        )

        hardware_plan = self._build_hardware_plan(
            solution=solution,
            project=project,
        )

        development_order = self._build_development_order(
            modules=modules,
        )

        testing = self._build_testing_plan(
            modules=modules,
            architecture=architecture,
        )

        code_targets = self._build_code_targets(
            modules=modules,
            api_contract=api_contract,
            ai_pipeline=ai_pipeline,
            architecture=architecture,
        )

        dependencies = self._build_dependencies(
            architecture=architecture,
            solution=solution,
            project=project,
        )

        environment = self._build_environment(
            architecture=architecture,
        )

        configuration = self._build_configuration()

        interfaces = self._build_module_interfaces(
            modules=modules,
        )

        risks = self._build_development_risks()

        milestones = self._build_milestones(
            modules=modules,
        )

        acceptance = self._build_acceptance_criteria(
            modules=modules,
            architecture=architecture,
        )

        code_readiness = self._build_code_readiness(
            modules=modules,
            code_targets=code_targets,
            architecture=architecture,
        )

        summary = (
            f"AURA prepared an implementation blueprint for "
            f"'{system_name}'. The blueprint converts the architecture "
            f"into {len(modules)} development modules, executable-style "
            f"tasks, API contracts, data and AI pipelines, dependencies, "
            f"testing requirements and code-generation targets. "
            f"Implementation remains unexecuted until the development "
            f"engine generates and tests the actual project."
        )

        return {
            "status": "development_plan_ready",

            "summary": summary,

            "system_name": system_name,

            "development_strategy": (
                "Evidence-aware incremental development with "
                "modular implementation, continuous testing, "
                "experiment tracking and progressive integration."
            ),

            "modules": modules,

            "module_interfaces": interfaces,

            "repository_structure": repository,

            "development_tasks": tasks,

            "development_order": development_order,

            "milestones": milestones,

            "api_contract": api_contract,

            "data_pipeline": data_pipeline,

            "ai_pipeline": ai_pipeline,

            "hardware_plan": hardware_plan,

            "dependencies": dependencies,

            "development_environment": environment,

            "configuration": configuration,

            "testing": testing,

            "code_generation_targets": code_targets,

            "code_generation_readiness": code_readiness,

            "risks": risks,

            "acceptance_criteria": acceptance,

            "definition_of_done": [
                "All required modules implemented.",
                "Module interfaces implemented.",
                "Input validation implemented.",
                "Error handling implemented.",
                "Logging implemented.",
                "Unit tests pass.",
                "Integration tests pass.",
                "API contracts verified.",
                "AI baseline established.",
                "AI model evaluated.",
                "Experiment results recorded.",
                "Security controls tested.",
                "Known limitations documented.",
                "Documentation updated.",
            ],

            "developer_workflow": [
                "Read the approved requirement.",
                "Inspect architecture contract.",
                "Create or update module.",
                "Implement minimum working functionality.",
                "Write unit tests.",
                "Run local validation.",
                "Integrate with adjacent module.",
                "Run integration tests.",
                "Record experiment or validation results.",
                "Update project memory.",
                "Commit versioned changes.",
            ],

            "evidence_context": evidence_context,

            "traceability": {
                "pipeline": [
                    "UNDERSTAND",
                    "INVESTIGATE",
                    "ANALYZE",
                    "VERDICT",
                    "INNOVATE",
                    "SOLUTION",
                    "ARCHITECT",
                    "BUILD",
                ],
                "solution": solution.get(
                    "solution_title"
                ),
                "architecture": architecture.get(
                    "system_name"
                ),
                "supporting_evidence_ids": evidence_context[
                    "supporting_evidence_ids"
                ],
                "claim_evidence_coverage_percent": evidence_context[
                    "claim_evidence_coverage_percent"
                ],
                "status": "AURA_DERIVED",
            },

            "verification_scope": {
                "implementation_generated": False,
                "code_generated": False,
                "code_executed": False,
                "tests_executed": False,
                "dataset_validated": False,
                "model_trained": False,
                "model_performance_verified": False,
                "integration_verified": False,
                "security_verified": False,
                "performance_verified": False,
                "deployment_verified": False,
                "production_readiness_verified": False,
                "expert_review_required": True,
            },
        }

    # ============================================================
    # EVIDENCE
    # ============================================================

    def _build_evidence_context(
        self,
        project: AURAProject,
        solution: dict[str, Any],
        architecture: dict[str, Any],
    ) -> dict[str, Any]:

        research = project.research or {}

        research_intelligence = (
            project.analysis.get(
                "research_intelligence",
                {},
            )
            or {}
        )

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

        evidence_ids = self._collect_evidence_ids(
            project=project,
            research=research,
            solution=solution,
            architecture=architecture,
        )

        return {
            "research_papers": len(
                research.get("papers", [])
                if isinstance(
                    research.get("papers", []),
                    list,
                )
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

            "architecture_status": architecture.get(
                "verification_scope",
                {},
            ),

            "interpretation": (
                "Research evidence provides the context behind "
                "the solution and architecture. It does not prove "
                "that the implementation will succeed."
            ),

            "status": "EVIDENCE_AWARE_SYNTHESIS",
        }

    def _collect_evidence_ids(
        self,
        project: AURAProject,
        research: dict[str, Any],
        solution: dict[str, Any],
        architecture: dict[str, Any],
    ) -> list[str]:

        ids: list[str] = []

        for evidence in project.evidence:
            if not isinstance(evidence, dict):
                continue

            for key in (
                "evidence_id",
                "id",
                "paper_id",
                "source_id",
            ):
                if evidence.get(key):
                    ids.append(
                        self._clean_text(
                            evidence.get(key)
                        )
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
                if paper.get(key):
                    ids.append(
                        self._clean_text(
                            paper.get(key)
                        )
                    )

        for container in (
            solution.get(
                "evidence_context",
                {},
            ),
            architecture.get(
                "evidence_context",
                {},
            ),
        ):
            if not isinstance(
                container,
                dict,
            ):
                continue

            ids.extend(
                self._string_list(
                    container.get(
                        "supporting_evidence_ids",
                        [],
                    )
                )
            )

        return self._unique_strings(ids)

    # ============================================================
    # MODULES
    # ============================================================

    def _build_modules(
        self,
        project: AURAProject,
        architecture: dict[str, Any],
        solution: dict[str, Any],
    ) -> list[dict[str, Any]]:

        architecture_components = architecture.get(
            "components",
            [],
        )

        modules: list[dict[str, Any]] = []

        component_map = {
            "Data Acquisition": (
                "Collect and validate project input data."
            ),
            "Data Processing": (
                "Clean, transform and prepare data."
            ),
            "Storage": (
                "Persist operational, experimental and provenance data."
            ),
            "AI": (
                "Train, evaluate and execute intelligence models."
            ),
            "Decision": (
                "Convert intelligence outputs into decisions."
            ),
            "Application": (
                "Expose functionality through APIs and UI."
            ),
            "Monitoring": (
                "Monitor system health and model behavior."
            ),
        }

        index = 1

        for component in architecture_components:

            if not isinstance(
                component,
                dict,
            ):
                continue

            name = self._clean_text(
                component.get(
                    "component",
                    "",
                )
            )

            layer = self._clean_text(
                component.get(
                    "layer",
                    "",
                )
            )

            if not name:
                continue

            responsibility = self._clean_text(
                component.get(
                    "responsibility",
                    "",
                )
            )

            if not responsibility:
                responsibility = component_map.get(
                    layer,
                    f"Implement the {name} component.",
                )

            modules.append(
                {
                    "id": f"MOD-{index:02d}",

                    "name": name,

                    "layer": layer,

                    "responsibility": responsibility,

                    "inputs": self._string_list(
                        component.get(
                            "input",
                            component.get(
                                "inputs",
                                [],
                            ),
                        )
                    ),

                    "outputs": self._string_list(
                        component.get(
                            "output",
                            component.get(
                                "outputs",
                                [],
                            ),
                        )
                    ),

                    "priority": (
                        "HIGH"
                        if layer in {
                            "Data Acquisition",
                            "Data Processing",
                            "AI",
                            "Decision",
                        }
                        else "MEDIUM"
                    ),

                    "implementation_status": "NOT_IMPLEMENTED",

                    "test_status": "NOT_TESTED",

                    "code_generation_status": "READY_FOR_GENERATION",
                }
            )

            index += 1

        if not modules:
            modules = self._fallback_modules()

        return modules

    def _fallback_modules(
        self,
    ) -> list[dict[str, Any]]:

        return [
            {
                "id": "MOD-01",
                "name": "Data Acquisition",
                "layer": "Data Acquisition",
                "responsibility": "Collect project input data.",
                "inputs": ["External data", "User input"],
                "outputs": ["Raw data"],
                "priority": "HIGH",
                "implementation_status": "NOT_IMPLEMENTED",
                "test_status": "NOT_TESTED",
                "code_generation_status": "READY_FOR_GENERATION",
            },
            {
                "id": "MOD-02",
                "name": "Data Processing",
                "layer": "Data Processing",
                "responsibility": "Validate and transform data.",
                "inputs": ["Raw data"],
                "outputs": ["Processed data"],
                "priority": "HIGH",
                "implementation_status": "NOT_IMPLEMENTED",
                "test_status": "NOT_TESTED",
                "code_generation_status": "READY_FOR_GENERATION",
            },
            {
                "id": "MOD-03",
                "name": "AI Engine",
                "layer": "AI",
                "responsibility": "Execute AI intelligence.",
                "inputs": ["Features"],
                "outputs": ["Predictions"],
                "priority": "HIGH",
                "implementation_status": "NOT_IMPLEMENTED",
                "test_status": "NOT_TESTED",
                "code_generation_status": "READY_FOR_GENERATION",
            },
            {
                "id": "MOD-04",
                "name": "Backend API",
                "layer": "Application",
                "responsibility": "Expose system functionality.",
                "inputs": ["Client requests"],
                "outputs": ["API responses"],
                "priority": "HIGH",
                "implementation_status": "NOT_IMPLEMENTED",
                "test_status": "NOT_TESTED",
                "code_generation_status": "READY_FOR_GENERATION",
            },
            {
                "id": "MOD-05",
                "name": "Frontend Application",
                "layer": "Application",
                "responsibility": "Provide user interaction.",
                "inputs": ["API responses"],
                "outputs": ["User interaction"],
                "priority": "HIGH",
                "implementation_status": "NOT_IMPLEMENTED",
                "test_status": "NOT_TESTED",
                "code_generation_status": "READY_FOR_GENERATION",
            },
        ]

    # ============================================================
    # MODULE INTERFACES
    # ============================================================

    def _build_module_interfaces(
        self,
        modules: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:

        interfaces: list[dict[str, Any]] = []

        for index in range(
            len(modules) - 1
        ):

            current = modules[index]
            next_module = modules[index + 1]

            interfaces.append(
                {
                    "from_module": current["id"],
                    "from": current["name"],
                    "to_module": next_module["id"],
                    "to": next_module["name"],
                    "contract": (
                        f"{current['name']} output must satisfy "
                        f"{next_module['name']} input requirements."
                    ),
                    "status": "CONTRACT_TO_BE_IMPLEMENTED",
                    "test_required": True,
                }
            )

        return interfaces

    # ============================================================
    # REPOSITORY
    # ============================================================

    def _build_repository(
        self,
        modules: list[dict[str, Any]],
        architecture: dict[str, Any],
    ) -> dict[str, Any]:

        existing = architecture.get(
            "development_boundaries",
            [],
        )

        return {
            "root": "project-root",

            "directories": [
                "frontend/",
                "backend/",
                "ai/",
                "data/",
                "experiments/",
                "tests/",
                "docs/",
                "configs/",
                "scripts/",
            ],

            "frontend": [
                "app/",
                "components/",
                "lib/",
                "hooks/",
                "services/",
                "types/",
                "tests/",
            ],

            "backend": [
                "api/",
                "services/",
                "models/",
                "schemas/",
                "database/",
                "middleware/",
                "core/",
                "tests/",
            ],

            "ai": [
                "datasets/",
                "preprocessing/",
                "features/",
                "training/",
                "models/",
                "inference/",
                "evaluation/",
                "tests/",
            ],

            "data": [
                "raw/",
                "processed/",
                "external/",
                "metadata/",
            ],

            "experiments": [
                "configs/",
                "runs/",
                "results/",
                "reports/",
            ],

            "tests": [
                "unit/",
                "integration/",
                "api/",
                "ai/",
                "system/",
                "acceptance/",
            ],

            "docs": [
                "architecture/",
                "api/",
                "research/",
                "experiments/",
                "development/",
                "deployment/",
            ],

            "configuration": [
                ".env",
                ".env.example",
                "config/",
            ],

            "architecture_boundaries": existing,

            "version_control": {
                "recommended": "Git",
                "branching": [
                    "main",
                    "develop",
                    "feature/*",
                ],
                "commit_policy": (
                    "Use small traceable commits with meaningful messages."
                ),
            },
        }

    # ============================================================
    # TASKS
    # ============================================================

    def _build_tasks(
        self,
        modules: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:

        tasks: list[dict[str, Any]] = []

        task_index = 1

        for module in modules:

            module_id = module["id"]
            name = module["name"]

            tasks.extend(
                [
                    {
                        "id": f"TASK-{task_index:03d}",
                        "module": module_id,
                        "task": f"Define {name} interface",
                        "type": "DESIGN",
                        "priority": module["priority"],
                        "status": "TODO",
                    },
                    {
                        "id": f"TASK-{task_index + 1:03d}",
                        "module": module_id,
                        "task": f"Implement {name}",
                        "type": "IMPLEMENT",
                        "priority": module["priority"],
                        "status": "TODO",
                    },
                    {
                        "id": f"TASK-{task_index + 2:03d}",
                        "module": module_id,
                        "task": f"Validate {name} inputs and outputs",
                        "type": "VALIDATION",
                        "priority": module["priority"],
                        "status": "TODO",
                    },
                    {
                        "id": f"TASK-{task_index + 3:03d}",
                        "module": module_id,
                        "task": f"Write tests for {name}",
                        "type": "TEST",
                        "priority": module["priority"],
                        "status": "TODO",
                    },
                    {
                        "id": f"TASK-{task_index + 4:03d}",
                        "module": module_id,
                        "task": f"Integrate {name}",
                        "type": "INTEGRATION",
                        "priority": module["priority"],
                        "status": "TODO",
                    },
                ]
            )

            task_index += 5

        return tasks

    # ============================================================
    # API
    # ============================================================

    def _build_api_contract(
        self,
        architecture: dict[str, Any],
    ) -> dict[str, Any]:

        existing = architecture.get(
            "api",
            {},
        )

        endpoints = existing.get(
            "endpoints",
            [],
        )

        if not isinstance(
            endpoints,
            list,
        ):
            endpoints = []

        if not endpoints:
            endpoints = [
                {
                    "method": "POST",
                    "path": "/api/data",
                    "purpose": "Submit input data.",
                },
                {
                    "method": "POST",
                    "path": "/api/predict",
                    "purpose": "Request AI inference.",
                },
                {
                    "method": "GET",
                    "path": "/api/predictions",
                    "purpose": "Retrieve predictions.",
                },
                {
                    "method": "GET",
                    "path": "/api/status",
                    "purpose": "Retrieve system status.",
                },
            ]

        return {
            "style": "REST",

            "version": "v1",

            "content_type": "application/json",

            "endpoints": endpoints,

            "contract_rules": [
                "Validate request schema.",
                "Validate response schema.",
                "Return structured errors.",
                "Use HTTP status codes consistently.",
                "Document endpoint behavior.",
                "Version breaking changes.",
                "Do not expose internal implementation details.",
            ],

            "implementation_targets": [
                "Route definitions",
                "Request schemas",
                "Response schemas",
                "Service integration",
                "Authentication where required",
                "Authorization where required",
                "Error handling",
                "API tests",
            ],
        }

    # ============================================================
    # DATA PIPELINE
    # ============================================================

    def _build_data_pipeline(
        self,
        architecture: dict[str, Any],
    ) -> list[dict[str, Any]]:

        return [
            {
                "stage": 1,
                "name": "Collection",
                "output": "Raw data",
                "validation": "Input availability and schema validation.",
            },
            {
                "stage": 2,
                "name": "Validation",
                "output": "Validated records",
                "validation": "Schema, range and quality checks.",
            },
            {
                "stage": 3,
                "name": "Cleaning",
                "output": "Clean data",
                "validation": "Missing-value and anomaly checks.",
            },
            {
                "stage": 4,
                "name": "Transformation",
                "output": "Model-ready data",
                "validation": "Transformation consistency.",
            },
            {
                "stage": 5,
                "name": "Feature Engineering",
                "output": "Features",
                "validation": "Feature leakage and distribution checks.",
            },
            {
                "stage": 6,
                "name": "Storage",
                "output": "Versioned dataset",
                "validation": "Dataset provenance and integrity.",
            },
            {
                "stage": 7,
                "name": "Training / Inference",
                "output": "AI result",
                "validation": "Model and metric validation.",
            },
            {
                "stage": 8,
                "name": "Decision",
                "output": "Recommendation or action",
                "validation": "Decision-rule validation.",
            },
            {
                "stage": 9,
                "name": "Feedback",
                "output": "Outcome data",
                "validation": "Feedback provenance.",
            },
        ]

    # ============================================================
    # AI PIPELINE
    # ============================================================

    def _build_ai_pipeline(
        self,
        solution: dict[str, Any],
        architecture: dict[str, Any],
    ) -> dict[str, Any]:

        ai = (
            solution.get(
                "ai_intelligence",
                {},
            )
            or {}
        )

        architecture_ai = (
            architecture.get(
                "ai_architecture",
                {},
            )
            or {}
        )

        candidate_models = (
            ai.get(
                "candidate_model_families",
                [],
            )
        )

        if not candidate_models:
            candidate_models = architecture_ai.get(
                "candidate_model_families",
                [],
            )

        return {
            "problem_definition": [
                "Define target variable.",
                "Define prediction or decision objective.",
                "Define input features.",
                "Define evaluation criteria.",
            ],

            "dataset": [
                "Identify required data.",
                "Check data availability.",
                "Check dataset licensing or access conditions.",
                "Check data quality.",
                "Record dataset provenance.",
                "Define dataset version.",
            ],

            "preprocessing": [
                "Handle missing values.",
                "Handle outliers where appropriate.",
                "Normalize or encode data where required.",
                "Prevent data leakage.",
                "Preserve preprocessing configuration.",
            ],

            "training": [
                "Create baseline.",
                "Create train / validation / test split.",
                "Train candidate models.",
                "Tune parameters where justified.",
                "Record training configuration.",
            ],

            "evaluation": [
                "Calculate appropriate metrics.",
                "Compare against baseline.",
                "Analyze errors.",
                "Perform robustness checks.",
                "Record experiment results.",
            ],

            "deployment": [
                "Export selected model.",
                "Create inference interface.",
                "Measure inference latency.",
                "Measure resource usage where relevant.",
                "Monitor model behavior.",
            ],

            "candidate_models": self._string_list(
                candidate_models
            ),

            "model_governance": [
                "Track model version.",
                "Track training dataset.",
                "Track preprocessing version.",
                "Track configuration.",
                "Track evaluation results.",
                "Preserve experiment provenance.",
            ],

            "status": (
                "AI implementation blueprint — model suitability "
                "must be demonstrated experimentally."
            ),
        }

    # ============================================================
    # HARDWARE
    # ============================================================

    def _build_hardware_plan(
        self,
        solution: dict[str, Any],
        project: AURAProject,
    ) -> dict[str, Any]:

        hardware = solution.get(
            "hardware",
            [],
        )

        return {
            "components": hardware,

            "integration_tasks": [
                "Identify required hardware.",
                "Confirm electrical compatibility.",
                "Confirm communication interface.",
                "Implement device communication.",
                "Validate sensor readings where applicable.",
                "Test actuator behavior where applicable.",
                "Measure communication reliability.",
                "Record hardware configuration.",
            ],

            "prototype_policy": (
                "Use representative prototype hardware before "
                "production deployment."
            ),

            "conditional": not bool(hardware),

            "status": (
                "Hardware choices remain recommendations until "
                "compatibility and feasibility testing."
            ),
        }

    # ============================================================
    # DEVELOPMENT ORDER
    # ============================================================

    def _build_development_order(
        self,
        modules: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:

        names = {
            module["name"].lower(): module["name"]
            for module in modules
        }

        def find_name(
            keywords: list[str],
            fallback: str,
        ) -> str:

            for name_lower, name in names.items():
                if any(
                    keyword in name_lower
                    for keyword in keywords
                ):
                    return name

            return fallback

        data = find_name(
            ["data acquisition", "collector", "input"],
            "Data Acquisition",
        )

        processing = find_name(
            ["processing"],
            "Data Processing",
        )

        storage = find_name(
            ["storage", "store"],
            "Data Storage",
        )

        ai = find_name(
            ["ai", "intelligence", "model"],
            "AI Intelligence Engine",
        )

        decision = find_name(
            ["decision", "recommendation"],
            "Decision Engine",
        )

        api = find_name(
            ["api"],
            "Application API",
        )

        ui = find_name(
            ["frontend", "user interface", "dashboard", "application"],
            "Frontend Application",
        )

        monitor = find_name(
            ["monitor"],
            "Monitoring",
        )

        return [
            {
                "phase": 1,
                "name": "Foundation",
                "modules": [
                    storage,
                    api,
                ],
                "exit_condition": (
                    "Project structure, storage and API foundation available."
                ),
            },
            {
                "phase": 2,
                "name": "Data Pipeline",
                "modules": [
                    data,
                    processing,
                ],
                "exit_condition": (
                    "Validated data can move through the processing pipeline."
                ),
            },
            {
                "phase": 3,
                "name": "AI Intelligence",
                "modules": [
                    ai,
                ],
                "exit_condition": (
                    "Baseline and candidate model workflow available."
                ),
            },
            {
                "phase": 4,
                "name": "Decision Support",
                "modules": [
                    decision,
                ],
                "exit_condition": (
                    "AI outputs can produce interpretable decisions."
                ),
            },
            {
                "phase": 5,
                "name": "Application",
                "modules": [
                    ui,
                ],
                "exit_condition": (
                    "Users can interact with the system through the application."
                ),
            },
            {
                "phase": 6,
                "name": "Integration",
                "modules": [
                    "Full System",
                ],
                "exit_condition": (
                    "End-to-end workflow operates across modules."
                ),
            },
            {
                "phase": 7,
                "name": "Experiments",
                "modules": [
                    "Experiment Manager",
                ],
                "exit_condition": (
                    "Experiment configurations and results are recorded."
                ),
            },
            {
                "phase": 8,
                "name": "Monitoring",
                "modules": [
                    monitor,
                ],
                "exit_condition": (
                    "Health and performance monitoring is available."
                ),
            },
            {
                "phase": 9,
                "name": "System Validation",
                "modules": [
                    "Full System",
                ],
                "exit_condition": (
                    "Acceptance criteria and validation tests are completed."
                ),
            },
        ]

    # ============================================================
    # TESTING
    # ============================================================

    def _build_testing_plan(
        self,
        modules: list[dict[str, Any]],
        architecture: dict[str, Any],
    ) -> dict[str, Any]:

        return {
            "unit_tests": [
                "Test individual functions.",
                "Test input validation.",
                "Test data transformations.",
                "Test business rules.",
                "Test model utilities.",
            ],

            "integration_tests": [
                "Test data pipeline.",
                "Test database integration.",
                "Test AI-to-backend integration.",
                "Test backend-to-frontend integration.",
                "Test device integration where required.",
            ],

            "api_tests": [
                "Valid request.",
                "Invalid request.",
                "Missing fields.",
                "Invalid data types.",
                "Unauthorized request.",
                "Service failure.",
                "Rate-limit behavior where applicable.",
            ],

            "ai_tests": [
                "Baseline comparison.",
                "Metric verification.",
                "Input boundary testing.",
                "Robustness testing.",
                "Error analysis.",
                "Data leakage checks.",
                "Reproducibility checks.",
            ],

            "system_tests": [
                "End-to-end workflow.",
                "Normal operating condition.",
                "Failure condition.",
                "Recovery behavior.",
                "Performance behavior.",
            ],

            "security_tests": [
                "Authentication testing where required.",
                "Authorization testing where required.",
                "Input security testing.",
                "Secret exposure checks.",
                "Dependency vulnerability review.",
            ],

            "acceptance_tests": [
                "Required features work.",
                "Expected outputs are produced.",
                "Defined performance targets are measured.",
                "Known limitations are documented.",
                "Evidence and experiment provenance are preserved.",
            ],
        }

    # ============================================================
    # CODE GENERATION
    # ============================================================

    def _build_code_targets(
        self,
        modules: list[dict[str, Any]],
        api_contract: dict[str, Any],
        ai_pipeline: dict[str, Any],
        architecture: dict[str, Any],
    ) -> list[dict[str, Any]]:

        return [
            {
                "target_id": "CODE-BACKEND",
                "target": "backend",
                "module_dependencies": [
                    module["id"]
                    for module in modules
                    if self._contains_any(
                        module["name"],
                        [
                            "api",
                            "backend",
                            "service",
                        ],
                    )
                ],
                "generate": [
                    "API routes",
                    "Request schemas",
                    "Response schemas",
                    "Service classes",
                    "Database layer",
                    "Validation logic",
                    "Error handling",
                    "Logging",
                ],
                "tests": [
                    "API unit tests",
                    "Service tests",
                    "Integration tests",
                ],
                "readiness": "READY_FOR_GENERATION",
            },

            {
                "target_id": "CODE-FRONTEND",
                "target": "frontend",
                "module_dependencies": [
                    module["id"]
                    for module in modules
                    if self._contains_any(
                        module["name"],
                        [
                            "frontend",
                            "dashboard",
                            "interface",
                            "application",
                            "ui",
                        ],
                    )
                ],
                "generate": [
                    "Application pages",
                    "Reusable components",
                    "API client",
                    "Forms",
                    "Charts",
                    "Status views",
                    "Error states",
                    "Loading states",
                ],
                "tests": [
                    "Component tests",
                    "UI workflow tests",
                    "API integration tests",
                ],
                "readiness": "READY_FOR_GENERATION",
            },

            {
                "target_id": "CODE-AI",
                "target": "ai",
                "module_dependencies": [
                    module["id"]
                    for module in modules
                    if self._contains_any(
                        module["name"],
                        [
                            "ai",
                            "model",
                            "intelligence",
                            "vision",
                        ],
                    )
                ],
                "generate": [
                    "Dataset loader",
                    "Data preprocessing",
                    "Feature engineering",
                    "Baseline model",
                    "Candidate model pipeline",
                    "Training script",
                    "Evaluation pipeline",
                    "Inference service",
                    "Model serialization",
                ],
                "tests": [
                    "Preprocessing tests",
                    "Model utility tests",
                    "Evaluation tests",
                    "Inference tests",
                ],
                "readiness": "READY_FOR_GENERATION",
            },

            {
                "target_id": "CODE-DATA",
                "target": "data",
                "module_dependencies": [
                    module["id"]
                    for module in modules
                    if self._contains_any(
                        module["name"],
                        [
                            "data",
                            "storage",
                            "collector",
                            "processing",
                        ],
                    )
                ],
                "generate": [
                    "Data schemas",
                    "Validation functions",
                    "Transformation functions",
                    "Database models",
                    "Data access layer",
                    "Provenance metadata",
                ],
                "tests": [
                    "Schema tests",
                    "Validation tests",
                    "Transformation tests",
                ],
                "readiness": "READY_FOR_GENERATION",
            },

            {
                "target_id": "CODE-TESTS",
                "target": "testing",
                "module_dependencies": [
                    module["id"]
                    for module in modules
                ],
                "generate": [
                    "Unit tests",
                    "API tests",
                    "Integration tests",
                    "AI evaluation tests",
                    "System tests",
                ],
                "tests": [
                    "Test suite itself must execute successfully."
                ],
                "readiness": "READY_FOR_GENERATION",
            },

            {
                "target_id": "CODE-DOCS",
                "target": "documentation",
                "module_dependencies": [
                    module["id"]
                    for module in modules
                ],
                "generate": [
                    "README",
                    "Setup guide",
                    "Architecture documentation",
                    "API documentation",
                    "Development guide",
                    "Experiment documentation",
                ],
                "tests": [
                    "Verify documentation matches implementation."
                ],
                "readiness": "READY_FOR_GENERATION",
            },
        ]

    # ============================================================
    # CODE READINESS
    # ============================================================

    def _build_code_readiness(
        self,
        modules: list[dict[str, Any]],
        code_targets: list[dict[str, Any]],
        architecture: dict[str, Any],
    ) -> dict[str, Any]:

        return {
            "status": "READY_FOR_CODE_GENERATION",

            "module_count": len(modules),

            "code_target_count": len(code_targets),

            "architecture_available": bool(
                architecture
            ),

            "module_interfaces_defined": True,

            "api_contract_defined": bool(
                architecture.get("api")
            ),

            "testing_strategy_defined": True,

            "environment_defined": True,

            "code_generated": False,

            "code_executed": False,

            "interpretation": (
                "AURA has enough architectural information to "
                "begin controlled code generation. This status "
                "does not mean the generated code has been executed "
                "or verified."
            ),
        }

    # ============================================================
    # DEPENDENCIES
    # ============================================================

    def _build_dependencies(
        self,
        architecture: dict[str, Any],
        solution: dict[str, Any],
        project: AURAProject,
    ) -> dict[str, Any]:

        stack = (
            architecture.get(
                "technology_intelligence",
                {},
            )
            or {}
        )

        return {
            "frontend": [
                "Node.js",
                "Next.js",
                "React",
                "TypeScript",
            ],

            "backend": [
                "Python",
                "FastAPI",
            ],

            "ai": [
                "Python",
                "scikit-learn",
                "PyTorch where justified",
            ],

            "database": [
                "PostgreSQL",
                "SQLite for prototype",
            ],

            "optional": [
                "OpenCV where computer vision is required",
                "MQTT client where IoT is required",
                "ROS 2 where robotics is required",
            ],

            "architecture_source": stack,

            "dependency_policy": [
                "Pin important production dependencies.",
                "Review licenses and compatibility.",
                "Scan dependencies for known vulnerabilities.",
                "Document system requirements.",
                "Avoid unnecessary dependencies.",
            ],
        }

    # ============================================================
    # ENVIRONMENT
    # ============================================================

    def _build_environment(
        self,
        architecture: dict[str, Any],
    ) -> dict[str, Any]:

        return {
            "frontend": [
                "Node.js",
                "npm",
                "Next.js",
                "TypeScript",
            ],

            "backend": [
                "Python",
                "FastAPI",
                "Virtual environment",
            ],

            "ai": [
                "Python",
                "scikit-learn",
                "PyTorch where required",
            ],

            "database": [
                "PostgreSQL",
                "SQLite for prototype",
            ],

            "development_tools": [
                "Git",
                "VS Code or equivalent IDE",
                "API testing tool",
                "Environment variable manager",
            ],

            "optional": [
                "Docker",
                "GPU/CUDA where deep-learning workload requires it",
            ],

            "configuration": [
                ".env",
                ".env.example",
                "Environment-specific configuration",
            ],
        }

    # ============================================================
    # CONFIGURATION
    # ============================================================

    def _build_configuration(
        self,
    ) -> dict[str, Any]:

        return {
            "environment_variables": [
                "DATABASE_URL",
                "API_BASE_URL",
                "SECRET_KEY",
                "MODEL_PATH",
                "DATA_PATH",
                "LOG_LEVEL",
            ],

            "files": [
                ".env",
                ".env.example",
                "config/settings",
            ],

            "rules": [
                "Never commit secrets.",
                "Provide safe example values.",
                "Separate development and production configuration.",
                "Validate required configuration at startup.",
            ],
        }

    # ============================================================
    # MILESTONES
    # ============================================================

    def _build_milestones(
        self,
        modules: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:

        return [
            {
                "milestone": "M1",
                "name": "Foundation Complete",
                "condition": "Repository, environment and storage foundation work.",
            },
            {
                "milestone": "M2",
                "name": "Data Pipeline Complete",
                "condition": "Data can be collected, validated and processed.",
            },
            {
                "milestone": "M3",
                "name": "Baseline Intelligence",
                "condition": "A measurable baseline model or algorithm exists.",
            },
            {
                "milestone": "M4",
                "name": "Decision Layer Complete",
                "condition": "Intelligence outputs produce interpretable decisions.",
            },
            {
                "milestone": "M5",
                "name": "Application Complete",
                "condition": "Users can operate the main workflow.",
            },
            {
                "milestone": "M6",
                "name": "Integrated System",
                "condition": "Major modules operate together.",
            },
            {
                "milestone": "M7",
                "name": "Experimental Validation",
                "condition": "Experiments produce recorded measurable results.",
            },
            {
                "milestone": "M8",
                "name": "Release Candidate",
                "condition": "Acceptance, security and deployment checks are complete.",
            },
        ]

    # ============================================================
    # ACCEPTANCE
    # ============================================================

    def _build_acceptance_criteria(
        self,
        modules: list[dict[str, Any]],
        architecture: dict[str, Any],
    ) -> list[dict[str, Any]]:

        return [
            {
                "criterion": "Functional correctness",
                "requirement": (
                    "Required workflows produce the expected outputs."
                ),
                "verification": "Functional testing",
            },
            {
                "criterion": "Data integrity",
                "requirement": (
                    "Input, processed and stored data remain consistent."
                ),
                "verification": "Data validation and integration testing",
            },
            {
                "criterion": "AI performance",
                "requirement": (
                    "Selected model meets the experimentally defined target."
                ),
                "verification": "Baseline comparison and experiment",
            },
            {
                "criterion": "API correctness",
                "requirement": (
                    "API requests and responses follow the defined contract."
                ),
                "verification": "Automated API tests",
            },
            {
                "criterion": "Security",
                "requirement": (
                    "Defined security controls operate correctly."
                ),
                "verification": "Security testing",
            },
            {
                "criterion": "Performance",
                "requirement": (
                    "Measured performance satisfies project requirements."
                ),
                "verification": "Benchmarking",
            },
            {
                "criterion": "Reproducibility",
                "requirement": (
                    "Important experiments can be reproduced from recorded configuration."
                ),
                "verification": "Experiment reproduction",
            },
            {
                "criterion": "Documentation",
                "requirement": (
                    "Implementation and limitations are documented."
                ),
                "verification": "Documentation review",
            },
        ]

    # ============================================================
    # RISKS
    # ============================================================

    def _build_development_risks(
        self,
    ) -> list[dict[str, Any]]:

        return [
            {
                "risk": "Insufficient data",
                "impact": "HIGH",
                "mitigation": (
                    "Assess data availability before committing "
                    "to complex models."
                ),
            },
            {
                "risk": "Poor data quality",
                "impact": "HIGH",
                "mitigation": (
                    "Implement automated data-quality validation."
                ),
            },
            {
                "risk": "Model overfitting",
                "impact": "HIGH",
                "mitigation": (
                    "Use baselines, proper validation and error analysis."
                ),
            },
            {
                "risk": "Data leakage",
                "impact": "HIGH",
                "mitigation": (
                    "Separate training and evaluation data correctly "
                    "and audit preprocessing."
                ),
            },
            {
                "risk": "Hardware incompatibility",
                "impact": "MEDIUM",
                "mitigation": (
                    "Prototype and test hardware interfaces early."
                ),
            },
            {
                "risk": "API integration failures",
                "impact": "MEDIUM",
                "mitigation": (
                    "Define and test API contracts independently."
                ),
            },
            {
                "risk": "Dependency incompatibility",
                "impact": "MEDIUM",
                "mitigation": (
                    "Pin versions and test the environment."
                ),
            },
            {
                "risk": "Deployment resource constraints",
                "impact": "MEDIUM",
                "mitigation": (
                    "Measure compute, memory, storage and latency requirements."
                ),
            },
            {
                "risk": "Generated-code defects",
                "impact": "HIGH",
                "mitigation": (
                    "Require compilation, automated tests and human review "
                    "before accepting generated code."
                ),
            },
        ]

    # ============================================================
    # GENERIC HELPERS
    # ============================================================

    def _contains_any(
        self,
        value: str,
        targets: list[str],
    ) -> bool:

        normalized = self._clean_text(
            value
        ).lower()

        return any(
            target.lower() in normalized
            for target in targets
        )

    def _string_list(
        self,
        value: Any,
    ) -> list[str]:

        if value is None:
            return []

        if isinstance(
            value,
            list,
        ):
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
                        "text",
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
                "component",
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


build_agent = BuildAgent()