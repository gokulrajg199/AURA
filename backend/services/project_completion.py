from __future__ import annotations

from typing import Any


def _count(value: Any) -> int:
    if isinstance(value, (list, tuple, set, dict)):
        return len(value)
    return 1 if value else 0


def _has(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) > 0
    return bool(value)


def build_completion_matrix(project: Any) -> dict[str, Any]:
    """Build a transparent, project-specific completion matrix.

    This is a readiness/completeness assessment, not a claim that unexecuted
    scientific work has been completed. Each item is backed by observable
    project state and keeps execution truth separate from planning.
    """
    research = project.research if isinstance(project.research, dict) else {}
    analysis = project.analysis if isinstance(project.analysis, dict) else {}
    solution = project.solution if isinstance(project.solution, dict) else {}
    architecture = project.architecture if isinstance(project.architecture, dict) else {}
    development = project.development if isinstance(project.development, dict) else {}
    experiments = project.experiments if isinstance(project.experiments, dict) else {}
    validation = project.validation if isinstance(project.validation, dict) else {}
    deliverables = project.deliverables if isinstance(project.deliverables, dict) else {}

    claims = analysis.get("claim_register") or research.get("claim_register") or research.get("canonical_claims") or []
    findings = analysis.get("findings") or analysis.get("canonical_findings") or analysis.get("research_intelligence", {}).get("findings") or []
    coverage = analysis.get("claim_evidence_coverage_percent")
    if coverage is None and isinstance(analysis.get("claim_analysis"), dict):
        coverage = analysis["claim_analysis"].get("coverage_percent")
    if coverage is None:
        coverage = research.get("claim_evidence_coverage_percent", 0)
    coverage = float(coverage or 0)

    execution_records = experiments.get("executions") or validation.get("execution_records") or []
    results = experiments.get("results") or validation.get("results") or {}
    workspace = development.get("execution_engine", {}).get("workspace", {}) if isinstance(development.get("execution_engine"), dict) else {}

    def item(id_: str, name: str, category: str, status: str, evidence: str, required: bool = True, next_action: str = "") -> dict[str, Any]:
        return {"id": id_, "name": name, "category": category, "status": status, "required": required, "evidence": evidence, "next_action": next_action}

    items = [
        item("P01", "Problem statement", "definition", "READY" if _has(project.original_idea) else "MISSING", "Original idea is stored in the project.", next_action="Clarify scope if unresolved."),
        item("P02", "Objectives and success criteria", "definition", "READY" if _has(project.objectives) else "NEEDS WORK", f"{_count(project.objectives)} objective(s) and project success criteria are carried forward.", next_action="Refine measurable acceptance criteria."),
        item("R01", "Research corpus", "research", "READY" if _count(research.get("papers") or research.get("records") or research.get("results")) else "MISSING", f"{_count(research.get('papers') or research.get('records') or research.get('results'))} research record(s) available.", next_action="Run investigation when the corpus is missing."),
        item("R02", "Evidence registry", "research", "READY" if _count(project.evidence) else "MISSING", f"{_count(project.evidence)} evidence record(s) stored.", next_action="Collect source evidence."),
        item("R03", "Claim-to-evidence coverage", "research", "READY" if coverage >= 80 else ("PARTIAL" if coverage > 0 else "MISSING"), f"Current claim coverage: {coverage:.1f}%.", next_action="Verify uncovered claims and resolve conflicts."),
        item("R04", "Research findings", "research", "READY" if _count(findings) else "MISSING", f"{_count(findings)} finding(s) recorded.", next_action="Generate/refresh evidence-backed findings."),
        item("D01", "Solution definition", "design", "READY" if _has(solution) else "MISSING", "AURA solution package is present." if _has(solution) else "No solution package is stored.", next_action="Run SOLUTION stage."),
        item("D02", "System architecture", "design", "READY" if _has(architecture) else "MISSING", "Architecture package is present." if _has(architecture) else "No architecture package is stored.", next_action="Run ARCHITECT stage."),
        item("B01", "Project workspace", "development", "READY" if _has(workspace) or development.get("real_project_generated") else "MISSING", "Project-specific workspace scaffold exists." if (_has(workspace) or development.get("real_project_generated")) else "Workspace has not been generated.", next_action="Generate BUILD workspace."),
        item("B02", "Implementation/code", "development", "EXECUTION REQUIRED", "Code scaffold/build plan is not equivalent to executed software.", next_action="Implement and execute the generated modules."),
        item("B03", "Dataset and data quality", "data", "EXECUTION REQUIRED", "Dataset preparation is only verified after a real dataset is processed.", next_action="Provide dataset and run dataset validation."),
        item("E01", "Baseline experiment", "experiments", "EXECUTION REQUIRED", "No baseline result is assumed unless a baseline run record exists.", next_action="Run an approved baseline and capture raw metrics."),
        item("E02", "Proposed experiment", "experiments", "EXECUTION REQUIRED", "No proposed-model result is assumed unless an execution record exists.", next_action="Run the proposed implementation and capture raw metrics."),
        item("E03", "Metrics and comparison", "experiments", "READY" if _has(results) and isinstance(results, dict) and _has(results.get("metrics")) else "EXECUTION REQUIRED", "Observed metrics are stored." if _has(results) and isinstance(results, dict) and _has(results.get("metrics")) else "Metrics are not yet verified from execution.", next_action="Execute evaluation and ingest metrics."),
        item("E04", "Error/failure analysis", "experiments", "READY" if isinstance(results, dict) and _has(results.get("error_analysis")) else "EXECUTION REQUIRED", "Observed failure/error analysis is stored." if isinstance(results, dict) and _has(results.get("error_analysis")) else "Failure analysis requires executed results.", next_action="Run error analysis against real outputs."),
        item("V01", "Validation", "validation", "VERIFIED" if validation.get("results_verified") is True else "NOT VERIFIED", "AURA does not mark scientific validation verified without execution evidence.", next_action="Execute, review, and verify results."),
        item("V02", "Reproducibility", "validation", "READY" if _has(experiments.get("reproducibility")) else "NEEDS WORK", "Experiment reproducibility requirements are recorded." if _has(experiments.get("reproducibility")) else "Reproducibility artifacts are not complete.", next_action="Capture environment, configuration, seeds and artifacts."),
        item("L01", "Final deliverables", "delivery", "READY" if _has(deliverables) else "MISSING", "Delivery package is connected to project state." if _has(deliverables) else "No delivery package is stored.", next_action="Generate outputs after project state is updated."),
        item("L02", "Human technical review", "delivery", "REQUIRED", "AURA preserves human review as the final gate for scientific/technical claims.", next_action="Review implementation, results, citations and submission requirements."),
    ]

    order = {"VERIFIED": 0, "READY": 1, "PARTIAL": 2, "NEEDS WORK": 3, "EXECUTION REQUIRED": 4, "MISSING": 5, "REQUIRED": 4}
    blocking = [x for x in items if x["required"] and x["status"] in {"MISSING", "EXECUTION REQUIRED", "NOT VERIFIED", "REQUIRED", "NEEDS WORK", "PARTIAL"}]
    verified = sum(1 for x in items if x["status"] in {"VERIFIED", "READY"})
    completion = round(verified / len(items) * 100, 1) if items else 0.0

    return {
        "project_id": getattr(project, "project_id", None),
        "project_name": getattr(project, "project_name", None),
        "assessment": "PROJECT_COMPLETION_READINESS",
        "completion_percent": completion,
        "verified_or_ready": verified,
        "total_items": len(items),
        "blocking_items": len(blocking),
        "scientific_validation_verified": validation.get("results_verified") is True,
        "execution_truth": "Results are verified only from real execution records and reviewed artifacts; plans are never counted as experimental results.",
        "items": items,
        "next_actions": [x["next_action"] for x in sorted(blocking, key=lambda x: order.get(x["status"], 99)) if x["next_action"]][:12],
    }
