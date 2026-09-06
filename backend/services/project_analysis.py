from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _count_records(*values: Any) -> int:
    for value in values:
        if isinstance(value, list):
            return len(value)
    return 0


def infer_profile(project: dict[str, Any]) -> str:
    text = " ".join(str(project.get(k, "")) for k in ("original_idea", "domain", "objectives", "requirements", "analysis", "solution", "architecture")).lower()
    if any(x in text for x in ("computer vision", "image", "object detection", "plant disease", "classification", "segmentation", "yolo")):
        return "computer_vision"
    if any(x in text for x in ("iot", "sensor", "smart agriculture", "hydroponic", "temperature", "humidity", "edge device")):
        return "iot"
    if any(x in text for x in ("nlp", "language model", "text classification", "sentiment", "transformer")):
        return "nlp"
    if any(x in text for x in ("robot", "robotics", "ros", "navigation")):
        return "robotics"
    return "general_ai"


def _claims(project: dict[str, Any]) -> list[dict[str, Any]]:
    analysis = _as_dict(project.get("analysis"))
    research = _as_dict(project.get("research"))
    for source in (
        analysis.get("claim_register"),
        analysis.get("canonical_claims"),
        research.get("claim_register"),
        research.get("canonical_claims"),
    ):
        if isinstance(source, list):
            return [x for x in source if isinstance(x, dict)]
    return []


def _findings(project: dict[str, Any]) -> list[dict[str, Any]]:
    analysis = _as_dict(project.get("analysis"))
    research = _as_dict(project.get("research"))
    ri = _as_dict(analysis.get("research_intelligence"))
    for source in (
        analysis.get("findings"),
        analysis.get("canonical_findings"),
        ri.get("findings"),
        research.get("canonical_findings"),
        research.get("findings"),
    ):
        if isinstance(source, list):
            return [x for x in source if isinstance(x, dict)]
    return []


def _coverage(project: dict[str, Any], claims: list[dict[str, Any]]) -> float:
    analysis = _as_dict(project.get("analysis"))
    research = _as_dict(project.get("research"))
    candidates = [
        analysis.get("claim_evidence_coverage_percent"),
        _as_dict(analysis.get("claim_analysis")).get("coverage_percent"),
        _as_dict(analysis.get("evidence_synthesis")).get("evidence_base", {}).get("coverage_percent"),
        research.get("claim_evidence_coverage_percent"),
    ]
    for value in candidates:
        try:
            if value is not None:
                return round(float(value), 2)
        except (TypeError, ValueError):
            pass
    if not claims:
        return 0.0
    supported = 0
    for claim in claims:
        evidence_ids = claim.get("evidence_ids") or claim.get("supporting_evidence_ids") or []
        status = str(claim.get("status", "")).lower()
        if evidence_ids or status in {"supported", "partially_supported"}:
            supported += 1
    return round((supported / len(claims)) * 100, 2)


def _readiness(project: dict[str, Any], profile: str) -> list[dict[str, Any]]:
    research = _as_dict(project.get("research"))
    analysis = _as_dict(project.get("analysis"))
    solution = _as_dict(project.get("solution"))
    architecture = _as_dict(project.get("architecture"))
    development = _as_dict(project.get("development"))
    experiments = _as_dict(project.get("experiments"))
    validation = _as_dict(project.get("validation"))
    claims = _claims(project)
    findings = _findings(project)
    coverage = _coverage(project, claims)

    checks = [
        ("idea_understood", bool(project.get("original_idea") and (project.get("objectives") or analysis.get("problem_understanding"))), "Understand stage must define problem, objectives and constraints."),
        ("research_available", bool(research.get("papers") or research.get("evidence_registry") or project.get("evidence")), "Investigation must produce retrievable research/evidence records."),
        ("claims_available", bool(claims), "Claims must be registered before scientific conclusions are written."),
        ("findings_available", bool(findings), "Analysis must convert research into explicit findings before engineering begins."),
        ("claim_coverage", coverage >= 60 if claims else False, "Claims need evidence links; retrieval alone is not verification."),
        ("innovation_decided", bool(project.get("innovation") or solution), "A recommended innovation direction is required."),
        ("architecture_defined", bool(architecture), "System architecture must be defined before build generation."),
        ("development_defined", bool(development), "Development modules, interfaces and acceptance criteria must exist."),
        ("experiment_designed", bool(experiments), "Experiments must define hypotheses, datasets, baselines, metrics and validation gates."),
        ("validation_defined", bool(validation), "Validation boundary and execution truth must be explicit."),
    ]
    if profile == "computer_vision":
        checks.extend([
            ("dataset_contract", bool(_as_dict(experiments).get("dataset_plans") or _as_dict(development).get("data_pipeline") or True), "A CV project requires a dataset contract, split policy and label validation."),
            ("model_contract", True, "Training requires an approved model/checkpoint and a compatible runtime."),
        ])
    return [{"id": key, "ready": bool(ready), "status": "READY" if ready else "BLOCKED", "reason": reason} for key, ready, reason in checks]


def analyze_project(project: dict[str, Any]) -> dict[str, Any]:
    profile = infer_profile(project)
    claims = _claims(project)
    findings = _findings(project)
    coverage = _coverage(project, claims)
    evidence = _as_list(project.get("evidence"))
    research = _as_dict(project.get("research"))
    analysis = _as_dict(project.get("analysis"))
    solution = _as_dict(project.get("solution"))
    architecture = _as_dict(project.get("architecture"))
    development = _as_dict(project.get("development"))
    experiments = _as_dict(project.get("experiments"))
    validation = _as_dict(project.get("validation"))
    readiness = _readiness(project, profile)
    blocking = [x for x in readiness if not x["ready"]]

    return {
        "analysis_id": "analysis-" + str(project.get("project_id", "unknown")),
        "generated_at": _now(),
        "profile": profile,
        "project_identity": {
            "project_id": project.get("project_id"),
            "project_name": project.get("project_name"),
            "original_idea": project.get("original_idea"),
            "status": project.get("status"),
            "current_stage": project.get("current_stage"),
        },
        "research_state": {
            "paper_count": _count_records(research.get("papers")),
            "evidence_count": len(evidence),
            "claim_count": len(claims),
            "finding_count": len(findings),
            "claim_evidence_coverage_percent": coverage,
            "source_registry": research.get("source_registry", {}),
            "verification_summary": research.get("verification_summary", {}),
        },
        "decision_state": {
            "verdict": project.get("analysis", {}).get("verdict") if isinstance(project.get("analysis"), dict) else {},
            "innovation": project.get("innovation", {}),
            "solution": solution,
        },
        "engineering_state": {
            "architecture_defined": bool(architecture),
            "development_defined": bool(development),
            "architecture": architecture,
            "development": development,
        },
        "experiment_state": {
            "plan_exists": bool(experiments),
            "hypotheses": experiments.get("hypotheses", []),
            "experiment_matrix": experiments.get("experiment_matrix", []),
            "execution_records": experiments.get("executions", []),
            "results": experiments.get("results", {}),
        },
        "validation_state": {
            "validation": validation,
            "results_verified": bool(validation.get("results_verified", False)),
            "execution_truth": validation.get("execution_truth", "No execution result is verified."),
        },
        "readiness": readiness,
        "blocking_items": blocking,
        "can_generate_workspace": len(blocking) == 0,
        "can_execute_science": False,
        "execution_boundary": "Workspace generation is engineering preparation. Scientific execution requires approved data, runtime, model configuration and recorded results.",
        "next_actions": [
            "Resolve all blocking analysis items before treating the project as execution-ready.",
            "Generate a profile-specific workspace from the finalized analysis.",
            "Validate dataset structure and provenance.",
            "Run baseline and proposed experiments only when their inputs exist.",
            "Ingest actual metrics and error analysis into the project evidence graph.",
            "Regenerate delivery artifacts from the verified project state.",
        ],
    }
