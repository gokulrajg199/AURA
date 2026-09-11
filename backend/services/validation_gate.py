from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_validation_gate(project: dict[str, Any], executions: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    executions = executions or []
    validation = project.get("validation") or {}
    experiments = project.get("experiments") or {}
    results = experiments.get("results_summary") or {}
    if not isinstance(results, dict):
        results = {}

    proposed_executed = bool(results.get("proposed_executed") is True)
    metrics_available = bool(
        results.get("proposed", {}).get("metrics_available") is True
        if isinstance(results.get("proposed"), dict) else False
    )
    if not metrics_available:
        metrics_available = bool(results.get("comparison")) or bool(results.get("evaluation_metrics")) and proposed_executed

    experiment_executed = bool(
        results.get("experiment", {}).get("status") == "EXECUTED"
        if isinstance(results.get("experiment"), dict) else False
    ) or any(e.get("task") == "experiment_run" and e.get("status") == "EXECUTED" for e in executions)

    baseline_executed = bool(results.get("baseline_executed"))
    comparison_available = bool(results.get("comparison"))
    execution_recorded = any(e.get("status") == "EXECUTED" for e in executions) or proposed_executed

    criteria = [
        {
            "id": "execution",
            "label": "Controlled execution recorded",
            "passed": execution_recorded,
            "required": True,
            "reason": "At least one successful execution record is required." if not execution_recorded else "Execution evidence is recorded.",
        },
        {
            "id": "experiment",
            "label": "Controlled experiment executed",
            "passed": experiment_executed,
            "required": True,
            "reason": "Run the controlled experiment before scientific validation." if not experiment_executed else "Controlled experiment execution is recorded.",
        },
        {
            "id": "proposed_results",
            "label": "Proposed solution produced measured results",
            "passed": proposed_executed and metrics_available,
            "required": True,
            "reason": "Measured proposed results with project metrics are required." if not (proposed_executed and metrics_available) else "Measured proposed results are available.",
        },
        {
            "id": "baseline_comparison",
            "label": "Baseline comparison available",
            "passed": baseline_executed and comparison_available,
            "required": False,
            "reason": "A baseline comparison is recommended/required when the project contract defines a baseline." if not (baseline_executed and comparison_available) else "Measured baseline comparison is available.",
        },
        {
            "id": "review_state",
            "label": "Previous validation approval has not been invalidated",
            "passed": not bool(validation.get("invalidated_at")),
            "required": True,
            "reason": "A previous approval was invalidated by a later project change or execution." if validation.get("invalidated_at") else "No invalidation is recorded.",
        },
    ]
    required = [c for c in criteria if c["required"]]
    passed = all(c["passed"] for c in required)
    status = "READY_FOR_HUMAN_REVIEW" if passed else "BLOCKED"
    return {
        "schema_version": "6.1-validation-gate-1",
        "generated_at": _now(),
        "project_id": project.get("project_id"),
        "status": status,
        "ready": passed,
        "criteria": criteria,
        "required_passed": sum(1 for c in required if c["passed"]),
        "required_total": len(required),
        "experiment_executed": experiment_executed,
        "proposed_executed": proposed_executed,
        "metrics_available": metrics_available,
        "baseline_executed": baseline_executed,
        "comparison_available": comparison_available,
        "truth": "AURA may determine readiness for review, but only an authorized human reviewer can record scientific validation.",
    }


def invalidate_validation(project: dict[str, Any], reason: str) -> None:
    validation = project.setdefault("validation", {})
    if validation.get("scientific_validation") or validation.get("human_approved") or validation.get("reviewed_at"):
        stamp = _now()
        validation["scientific_validation"] = False
        validation["human_approved"] = False
        validation["results_verified"] = False
        validation["invalidated_at"] = stamp
        validation["invalidation_reason"] = reason
        validation.setdefault("review_history", []).append({
            "action": "INVALIDATED",
            "reason": reason,
            "at": stamp,
            "previous_reviewer": validation.get("reviewer_email"),
        })
