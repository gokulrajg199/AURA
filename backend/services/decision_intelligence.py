from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


STAGE_ORDER = {
    "problem": 1, "requirements": 2, "research": 3, "evidence": 4,
    "innovation": 5, "solution": 6, "architecture": 7, "implementation": 8,
    "dataset": 9, "annotation": 10, "baseline": 11, "model": 12,
    "testing": 13, "experiment": 14, "results": 15, "validation": 16,
    "documentation": 17, "delivery": 18,
}


def _stage_map(lifecycle: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(s.get("key")): s for s in lifecycle.get("stages") or []}


def _evidence_quality(project: dict[str, Any]) -> dict[str, int]:
    evidence = project.get("evidence") or []
    approved = 0
    reviewed = 0
    sourced = 0
    for item in evidence:
        if not isinstance(item, dict):
            continue
        reviewed += int(item.get("reviewed") is True)
        sourced += int(bool(item.get("source") or item.get("provenance_hash") or item.get("sha256")))
        approved += int(item.get("scientific_evidence") is True and item.get("reviewed") is True and bool(item.get("provenance_hash") or item.get("sha256") or item.get("source")))
    return {"total": len(evidence), "reviewed": reviewed, "sourced": sourced, "approved": approved}


def build_decision_intelligence(project: dict[str, Any], lifecycle: dict[str, Any], intelligence: dict[str, Any] | None = None) -> dict[str, Any]:
    """Deterministic decision/risk layer. It ranks actions from persisted state;
    it does not invent evidence, scientific conclusions, or execution results.
    """
    stages = _stage_map(lifecycle)
    evidence = _evidence_quality(project)
    validation = project.get("validation") or {}
    experiments = project.get("experiments") or {}
    results = experiments.get("results_summary") or {}
    impact = (project.get("project_context") or {}).get("dependency_impact") or {}

    blockers: list[dict[str, Any]] = []
    for key, stage in stages.items():
        status = str(stage.get("status") or "pending").lower()
        if status in {"blocked", "pending", "review"}:
            severity = "CRITICAL" if status == "blocked" else ("HIGH" if status == "review" else "MEDIUM")
            blockers.append({"stage": key, "title": stage.get("label") or key.replace("_", " ").title(), "status": status.upper(), "severity": severity, "reason": stage.get("reason") or "Stage requires completion or review."})
    blockers.sort(key=lambda x: (STAGE_ORDER.get(x["stage"], 999), {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2}.get(x["severity"], 3)))

    risks: list[dict[str, Any]] = []
    for b in blockers:
        risks.append({"id": f"RISK-{b['stage'].upper()}", "source": b["stage"], "severity": b["severity"], "likelihood": "HIGH" if b["status"] in {"BLOCKED", "REVIEW"} else "MEDIUM", "impact": "HIGH", "reason": b["reason"], "mitigation": f"Resolve or review {b['title']} before relying on downstream work."})
    if impact.get("requires_reexecution"):
        risks.append({"id": "RISK-STALE-EXECUTION", "source": "dependency_impact", "severity": "HIGH", "likelihood": "HIGH", "impact": "HIGH", "reason": "An upstream change has marked downstream execution state as stale.", "mitigation": "Re-execute affected work before validation or delivery."})
    if impact.get("requires_revalidation"):
        risks.append({"id": "RISK-STALE-VALIDATION", "source": "dependency_impact", "severity": "HIGH", "likelihood": "HIGH", "impact": "HIGH", "reason": "Downstream validation/delivery may no longer represent the current project state.", "mitigation": "Re-review the validation gate and affected deliverables."})
    if results.get("metrics_available") and not validation.get("scientific_validation"):
        risks.append({"id": "RISK-UNVERIFIED-MEASUREMENT", "source": "results", "severity": "MEDIUM", "likelihood": "MEDIUM", "impact": "HIGH", "reason": "Measured results exist but scientific validation is not recorded.", "mitigation": "Route the measured result through the Validation Gate and required human review."})

    actions: list[dict[str, Any]] = []
    for b in blockers[:8]:
        priority = 1000 - STAGE_ORDER.get(b["stage"], 999) * 10 + (100 if b["severity"] == "CRITICAL" else 50 if b["severity"] == "HIGH" else 0)
        actions.append({"id": f"ACTION-{b['stage'].upper()}", "stage": b["stage"], "title": f"Resolve: {b['title']}", "action": b["reason"], "priority_score": priority, "why_now": "It is an unresolved prerequisite in the current lifecycle.", "blocks": [k for k in STAGE_ORDER if STAGE_ORDER[k] > STAGE_ORDER.get(b["stage"], 0)][:4]})
    if impact.get("requires_reexecution"):
        actions.insert(0, {"id": "ACTION-REEXECUTE", "stage": "experiment", "title": "Re-execute impacted work", "action": "Repeat the affected execution path using the current upstream state and preserve new lineage/artifacts.", "priority_score": 1200, "why_now": "Dependency impact has explicitly flagged downstream execution as stale.", "blocks": ["results", "validation", "delivery"]})
    if impact.get("requires_revalidation"):
        actions.insert(0, {"id": "ACTION-REVALIDATE", "stage": "validation", "title": "Re-run validation review", "action": "Re-check the Validation Gate against the current results, dependencies and evidence.", "priority_score": 1150, "why_now": "A downstream dependency changed after the previous validation state.", "blocks": ["documentation", "delivery"]})
    if not actions:
        actions.append({"id": "ACTION-REVIEW-COMPLETION", "stage": "validation", "title": "Review completion gates", "action": "Review required gates, scientific validation and human approval before delivery.", "priority_score": 100, "why_now": "No unresolved lifecycle blocker was detected.", "blocks": ["delivery"]})
    actions.sort(key=lambda x: -int(x.get("priority_score", 0)))

    confidence = "LOW"
    if evidence["approved"] >= 3:
        confidence = "HIGH"
    elif evidence["reviewed"] or evidence["sourced"]:
        confidence = "MEDIUM"
    if not project.get("original_idea") and not project.get("project_name"):
        confidence = "LOW"

    level = "LOW"
    if any(r["severity"] == "CRITICAL" for r in risks) or len(risks) >= 4:
        level = "CRITICAL"
    elif any(r["severity"] == "HIGH" for r in risks):
        level = "HIGH"
    elif risks:
        level = "MEDIUM"

    return {
        "schema_version": "6.1-decision-intelligence-1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "decision_confidence": confidence,
        "risk_level": level,
        "active_blocker_count": len(blockers),
        "blockers": blockers,
        "risks": risks,
        "next_best_actions": actions[:8],
        "recommended_action": actions[0],
        "evidence_basis": evidence,
        "dependency_impact": impact,
        "human_review_required": True,
        "truth": "Decision Intelligence ranks actions from project state and evidence metadata; it does not create scientific evidence or certify completion.",
    }
