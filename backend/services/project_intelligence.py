from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _truth(project: dict[str, Any], executions: list[dict[str, Any]]) -> dict[str, Any]:
    validation = project.get("validation") or {}
    experiments = project.get("experiments") or {}
    results = experiments.get("results_summary") or {}
    scientific = bool(validation.get("scientific_validation") is True or validation.get("results_verified") is True or results.get("scientific_validation") is True)
    executed = any(e.get("status") == "EXECUTED" for e in executions)
    measured = bool(results.get("metrics_available") is True or results.get("status") in {"MEASURED", "RESULTS_AVAILABLE_REVIEW_REQUIRED", "EXPERIMENT_EXECUTED_REVIEW_REQUIRED"})
    human = bool(validation.get("human_approved") is True)
    if scientific and human:
        status = "VALIDATED"
    elif measured:
        status = "MEASURED · REVIEW REQUIRED"
    elif executed:
        status = "EXECUTED · REVIEW REQUIRED"
    elif project.get("development"):
        status = "IMPLEMENTATION IN PROGRESS"
    else:
        status = "DESIGN IN PROGRESS"
    return {"status": status, "scientific_validation": scientific, "human_approved": human, "execution_recorded": executed, "measurement_available": measured}


def _stage_score(stage: dict[str, Any]) -> float:
    status = str(stage.get("status", "")).lower()
    if status == "verified":
        return 100.0
    if status in {"measured", "executed", "ready"}:
        return 75.0
    if status == "designed":
        return 55.0
    if status == "na":
        return 100.0
    return 0.0


def _status_for_twin(stage: dict[str, Any]) -> str:
    return str(stage.get("status") or "pending").upper()


def build_persisted_project_twin(project: dict[str, Any], lifecycle: dict[str, Any], executions: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build the canonical persisted logical twin and compact project context.

    The twin is a projection of persisted project state. It does not create
    scientific evidence and it deliberately preserves AURA's truth boundary.
    """
    stages = lifecycle.get("stages") or []
    stage_by_key = {str(s.get("key")): s for s in stages}
    dependencies = {
        "problem": ["requirements"],
        "requirements": ["research", "evidence", "innovation", "solution"],
        "research": ["evidence", "innovation", "solution"],
        "evidence": ["innovation", "solution", "architecture"],
        "innovation": ["solution", "architecture"],
        "solution": ["architecture"],
        "architecture": ["implementation", "dataset"],
        "implementation": ["testing", "experiment", "results"],
        "dataset": ["annotation", "baseline", "model", "experiment"],
        "annotation": ["baseline", "model"],
        "baseline": ["model", "experiment"],
        "model": ["testing", "experiment"],
        "testing": ["experiment", "results"],
        "experiment": ["results", "validation"],
        "results": ["validation", "documentation", "delivery"],
        "validation": ["documentation", "delivery"],
        "documentation": ["delivery"],
    }
    chain = ["problem", "requirements", "research", "evidence", "innovation", "solution",
             "architecture", "implementation", "dataset", "annotation", "baseline", "model",
             "testing", "experiment", "results", "validation", "documentation", "delivery"]
    nodes = []
    for key in chain:
        if key == "problem":
            status = "DEFINED" if project.get("original_idea") or project.get("project_name") else "MISSING"
            label = "Problem / Idea"
        else:
            stage = stage_by_key.get(key, {})
            status = _status_for_twin(stage) if stage else "NOT_PRESENT"
            label = stage.get("label") or key.replace("_", " ").title()
        nodes.append({"id": key, "label": label, "status": status, "dependencies": dependencies.get(key, [])})
    edges = [{"from": src, "to": dst, "type": "DEPENDENCY"} for src, dsts in dependencies.items() for dst in dsts]

    blocked = [n["id"] for n in nodes if n["status"] in {"BLOCKED", "PENDING", "REVIEW", "NOT_PRESENT"}]
    context = {
        "schema_version": "6.1-twin-1",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "source": "canonical_project_snapshot",
        "project_id": project.get("project_id"),
        "profile": lifecycle.get("profile", "general"),
        "current_stage": project.get("current_stage"),
        "active_blockers": blocked,
        "memory_count": len(project.get("memory") or []),
        "evidence_count": len(project.get("evidence") or []),
        "execution_count": len(executions),
        "decision_count": len(project.get("memory") or []),
        "uncertainty_count": sum(1 for m in (project.get("memory") or []) if isinstance(m, dict) and m.get("type") in {"uncertainty", "uncertainty_record"}),
        "conflict_count": sum(1 for m in (project.get("memory") or []) if isinstance(m, dict) and m.get("type") in {"conflict", "conflict_record"}),
        "truth_boundary": "GENERATED ≠ DESIGNED ≠ IMPLEMENTED ≠ EXECUTED ≠ MEASURED ≠ VALIDATED ≠ COMPLETED",
    }
    twin = {
        "schema_version": "6.1-twin-1",
        "generated_at": context["updated_at"],
        "project_id": project.get("project_id"),
        "project_name": project.get("project_name"),
        "profile": lifecycle.get("profile", "general"),
        "nodes": nodes,
        "edges": edges,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "active_blockers": blocked,
        "current_stage": project.get("current_stage"),
        "truth_boundary": context["truth_boundary"],
        "execution_count": len(executions),
        "dependency_impact": context.get("dependency_impact", {}),
    }
    return twin, context


def refresh_persisted_project_twin(project: dict[str, Any], lifecycle: dict[str, Any], executions: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    twin, context = build_persisted_project_twin(project, lifecycle, executions)
    project["project_twin"] = twin
    project["project_context"] = context
    return twin, context


def build_project_intelligence(project: dict[str, Any], lifecycle: dict[str, Any], executions: list[dict[str, Any]]) -> dict[str, Any]:
    stages = lifecycle.get("stages") or []
    truth = _truth(project, executions)
    research = project.get("research") or {}
    analysis = project.get("analysis") or {}
    evidence = project.get("evidence") or []
    development = project.get("development") or {}
    validation = project.get("validation") or {}
    deliverables = project.get("deliverables") or {}

    stage_map = {str(s.get("key")): s for s in stages}
    def score(*keys: str) -> float:
        selected = [stage_map[k] for k in keys if k in stage_map]
        return round(sum(_stage_score(s) for s in selected) / max(len(selected), 1), 1)

    dimensions = {
        "workflow": float(lifecycle.get("completion_percent", 0)),
        "research": score("research", "evidence", "innovation"),
        "development": score("solution", "architecture", "implementation"),
        "data": score("dataset", "data", "annotation", "hardware", "simulation"),
        "experimentation": score("baseline", "model", "testing", "experiment", "results"),
        "validation": score("validation"),
        "documentation": score("documentation"),
        "delivery": score("delivery"),
    }

    blockers: list[dict[str, Any]] = []
    for stage in stages:
        if stage.get("status") in {"blocked", "pending", "review"}:
            blockers.append({
                "stage": stage.get("key"),
                "title": stage.get("label"),
                "reason": stage.get("reason"),
                "priority": "HIGH" if stage.get("status") in {"blocked", "review"} else "MEDIUM",
            })

    # Dependency-aware next action. Prefer the first blocking prerequisite, not a cosmetic stage.
    next_action = None
    for item in blockers:
        key = str(item.get("stage"))
        if key in {"requirements", "research", "evidence", "dataset", "data", "annotation", "implementation", "testing", "baseline", "model", "experiment", "results", "validation", "documentation", "delivery"}:
            next_action = {
                "stage": key,
                "title": item.get("title"),
                "action": item.get("reason"),
                "why": "This is the earliest unresolved dependency in the active project lifecycle.",
                "where": f"Project → {item.get('title')}",
                "blocks": [s.get("key") for s in stages if s.get("order", 0) > stage_map.get(key, {}).get("order", 0)][:4],
            }
            break
    if next_action is None:
        next_action = {"stage": "complete", "title": "Review completion", "action": "Review all gates and human approvals before delivery.", "why": "AURA never self-certifies scientific completion.", "where": "Project → Validation → Delivery", "blocks": []}

    papers = research.get("papers", []) if isinstance(research.get("papers"), list) else []
    reviewed_papers = [p for p in papers if isinstance(p, dict) and (p.get("reviewed") is True or p.get("source_reviewed") is True or p.get("verification_status") in {"reviewed", "verified", "APPROVED", "VERIFIED"})]
    approved_evidence = [e for e in evidence if isinstance(e, dict) and e.get("scientific_evidence") is True and (e.get("reviewed") is True or e.get("status") == "APPROVED") and bool(e.get("provenance_hash") or e.get("sha256") or e.get("source"))]
    research_state = {
        "paper_count": len(papers),
        "reviewed_paper_count": len(reviewed_papers),
        "evidence_count": len(evidence),
        "approved_evidence_count": len(approved_evidence),
        "claims_count": len(analysis.get("claim_register", [])) if isinstance(analysis.get("claim_register"), list) else 0,
        "research_gap": research.get("research_gap") or analysis.get("research_gap") or {},
        "status": "VERIFIED SOURCES" if reviewed_papers else ("SOURCE REVIEW REQUIRED" if papers or evidence else "RESEARCH NOT STARTED"),
    }

    # Canonical Project Twin: a derived, read-only logical representation of
    # the project's connected state. It is intentionally derived from the
    # persisted project snapshot so UI/report modules cannot invent state.
    twin = {
        "problem": project.get("original_idea") or project.get("project_name"),
        "requirements": project.get("requirements") or project.get("analysis", {}).get("requirements", []),
        "research": {"papers": research_state["paper_count"], "evidence": research_state["evidence_count"], "claims": research_state["claims_count"]},
        "development": {"workspace_generated": bool(development.get("real_project_generated"))},
        "experiments": {"executions": len(executions), "measurement_available": truth["measurement_available"]},
        "validation": {"scientific": truth["scientific_validation"], "human_approved": truth["human_approved"]},
        "delivery": {"content_present": bool(deliverables), "verified": bool(deliverables.get("delivery_verified") is True)},
        "truth_status": truth["status"],
        "canonical_persisted": project.get("project_twin") or {},
        "context": project.get("project_context") or {},
    }
    dependency_map = {
        "requirements": ["research", "evidence", "innovation", "solution", "architecture"],
        "research": ["evidence", "innovation", "solution"],
        "evidence": ["innovation", "solution", "architecture"],
        "dataset": ["annotation", "baseline", "model", "experiment", "results"],
        "implementation": ["testing", "experiment", "results"],
        "results": ["validation", "documentation", "delivery"],
        "validation": ["documentation", "delivery"],
    }
    impact = []
    for b in blockers:
        key = str(b.get("stage"))
        downstream = dependency_map.get(key, [])
        if downstream:
            impact.append({"source": key, "downstream": downstream, "impact": f"Changes or missing work at {key} can invalidate downstream work: {', '.join(downstream)}."})

    risk_level = "LOW"
    if len(blockers) >= 3 or truth["status"].startswith("DESIGN"):
        risk_level = "HIGH"
    elif blockers:
        risk_level = "MEDIUM"
    risks = [{"type":"PROJECT_BLOCKER","severity":b["priority"],"stage":b["stage"],"reason":b.get("reason")} for b in blockers]
    decisions = []
    if next_action:
        decisions.append({
            "decision": next_action.get("title"),
            "selected_action": next_action.get("action"),
            "reasoning": next_action.get("why"),
            "assumptions": ["Current project snapshot is the source of truth."],
            "downstream_impact": next_action.get("blocks", []),
        })

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project_id": project.get("project_id"),
        "project_name": project.get("project_name"),
        "profile": lifecycle.get("profile", "general"),
        "mission": "Convert the project idea into an evidence-driven, executable, measurable and verifiable path to delivery.",
        "truth": truth,
        "dimensions": dimensions,
        "overall_health": round(sum(dimensions.values()) / max(len(dimensions), 1), 1),
        "blockers": blockers,
        "risk": {"level": risk_level, "items": risks},
        "decision_intelligence": decisions,
        "dependency_impact": impact,
        "next_best_action": next_action,
        "research": research_state,
        "project_twin": twin,
        "implementation": {
            "workspace_generated": bool(development.get("real_project_generated")),
            "execution_boundary": development.get("execution_boundary", "Controlled execution only; scientific claims require real project evidence."),
        },
        "validation": {
            "scientific_validation": bool(validation.get("scientific_validation")),
            "human_approved": bool(validation.get("human_approved")),
        },
        "delivery": {"content_present": bool(deliverables), "status": "REVIEW REQUIRED" if deliverables else "PENDING"},
        "principle": "GENERATED ≠ DESIGNED ≠ IMPLEMENTED ≠ EXECUTED ≠ MEASURED ≠ VALIDATED ≠ COMPLETED",
    }
