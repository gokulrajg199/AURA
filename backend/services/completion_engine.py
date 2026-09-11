from __future__ import annotations
from typing import Any
from services.lifecycle_engine import build_lifecycle

def evaluate_completion(project: dict[str, Any], executions: list[dict[str, Any]]|None=None) -> dict[str, Any]:
    executions = executions or []
    lifecycle = build_lifecycle(project, executions)
    validation = project.get("validation") or {}
    human = bool(validation.get("human_approved") or validation.get("approved"))
    scientific = bool(validation.get("scientific_validation"))
    required = [s for s in lifecycle.get("stages", []) if s.get("status") != "na"]
    gates = [{"gate": s["key"], "passed": bool(s.get("verified")), "status": s.get("display"), "reason": s.get("reason")} for s in required]
    all_gates = all(g["passed"] for g in gates) if gates else False
    completed = bool(all_gates and scientific and human)
    return {
        "status": "COMPLETED" if completed else "IN_PROGRESS",
        "completion_percent": lifecycle.get("completion_percent", 0),
        "verified_stages": lifecycle.get("verified_stages", 0),
        "total_stages": lifecycle.get("total_stages", 0),
        "gates": gates,
        "all_required_gates_passed": all_gates,
        "scientific_validation": scientific,
        "human_approval": human,
        "completed": completed,
        "next_blocker": lifecycle.get("next_blocker"),
        "truth": "COMPLETED only after every required lifecycle gate is verified, scientific validation is recorded, and required human approval is present.",
        "lifecycle": lifecycle,
    }
