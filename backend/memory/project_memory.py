from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from models.project import AURAProject


# ============================================================
# AURA — PROJECT MEMORY ENGINE
# Stage 10: Persistent Project Intelligence & Context Layer
# ============================================================


def _utc_now() -> str:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def _ensure_memory(project: AURAProject) -> list[dict[str, Any]]:
    """Ensure the project has a valid memory collection."""
    if not isinstance(project.memory, list):
        project.memory = []

    return project.memory


def _ensure_evidence(project: AURAProject) -> list[dict[str, Any]]:
    """Ensure the project has a valid evidence collection."""
    if not isinstance(project.evidence, list):
        project.evidence = []

    return project.evidence


def add_memory(
    project: AURAProject,
    stage: str,
    event: str,
    data: dict[str, Any] | None = None,
) -> AURAProject:
    """
    Add a structured event to the project memory.

    Memory is append-only from the engine's perspective so the
    project maintains a chronological intelligence history.
    """

    memory = _ensure_memory(project)

    memory.append(
        {
            "memory_id": f"MEM-{len(memory) + 1:04d}",
            "timestamp": _utc_now(),
            "stage": stage,
            "event": event,
            "type": "stage_event",
            "data": data or {},
        }
    )

    return project


def add_evidence(
    project: AURAProject,
    source: str,
    claim: str,
    evidence_type: str,
    data: dict[str, Any] | None = None,
) -> AURAProject:
    """
    Add evidence with provenance information.
    """

    evidence = _ensure_evidence(project)

    evidence_id = None

    if isinstance(data, dict):
        evidence_id = (
            data.get("evidence_id")
            or data.get("id")
            or data.get("paper_id")
            or data.get("source_id")
        )

    if not evidence_id:
        evidence_id = f"EVD-{len(evidence) + 1:04d}"

    evidence.append(
        {
            "evidence_id": str(evidence_id),
            "timestamp": _utc_now(),
            "source": source,
            "claim": claim,
            "evidence_type": evidence_type,
            "verification_status": (
                data.get("verification_status", "recorded")
                if isinstance(data, dict)
                else "recorded"
            ),
            "evidence_level": (
                data.get("evidence_level", "unspecified")
                if isinstance(data, dict)
                else "unspecified"
            ),
            "data": data or {},
        }
    )

    return project


def record_decision(
    project: AURAProject,
    stage: str,
    decision: str,
    rationale: str,
    evidence_ids: list[str] | None = None,
    confidence: float | int | None = None,
) -> AURAProject:
    """
    Record an important AURA decision and its supporting evidence.
    """

    memory = _ensure_memory(project)

    decision_record = {
        "decision_id": f"DEC-{sum(1 for m in memory if m.get('type') == 'decision') + 1:04d}",
        "timestamp": _utc_now(),
        "stage": stage,
        "event": "decision",
        "type": "decision",
        "data": {
            "decision": decision,
            "rationale": rationale,
            "evidence_ids": evidence_ids or [],
            "confidence": confidence,
        },
    }

    memory.append(decision_record)

    return project


def record_finding(
    project: AURAProject,
    stage: str,
    finding: str,
    finding_type: str = "research_finding",
    evidence_ids: list[str] | None = None,
    confidence: float | int | None = None,
) -> AURAProject:
    """
    Store a reusable finding that later AURA stages can retrieve.
    """

    memory = _ensure_memory(project)

    finding_record = {
        "finding_id": f"FND-{sum(1 for m in memory if m.get('type') == 'finding') + 1:04d}",
        "timestamp": _utc_now(),
        "stage": stage,
        "event": "finding",
        "type": "finding",
        "data": {
            "finding": finding,
            "finding_type": finding_type,
            "evidence_ids": evidence_ids or [],
            "confidence": confidence,
        },
    }

    memory.append(finding_record)

    return project


def record_uncertainty(
    project: AURAProject,
    stage: str,
    uncertainty: str,
    reason: str,
    severity: str = "medium",
) -> AURAProject:
    """
    Record something AURA does not know or cannot currently verify.

    This is important because AURA must preserve uncertainty instead
    of converting assumptions into facts.
    """

    memory = _ensure_memory(project)

    uncertainty_record = {
        "uncertainty_id": (
            f"UNC-{sum(1 for m in memory if m.get('type') == 'uncertainty') + 1:04d}"
        ),
        "timestamp": _utc_now(),
        "stage": stage,
        "event": "uncertainty",
        "type": "uncertainty",
        "data": {
            "uncertainty": uncertainty,
            "reason": reason,
            "severity": severity,
            "requires_verification": True,
        },
    }

    memory.append(uncertainty_record)

    return project


def record_conflict(
    project: AURAProject,
    stage: str,
    conflict: str,
    sources: list[str] | None = None,
    resolution: str | None = None,
) -> AURAProject:
    """
    Preserve conflicting evidence or interpretations.

    AURA should not silently merge contradictory findings.
    """

    memory = _ensure_memory(project)

    conflict_record = {
        "conflict_id": (
            f"CNF-{sum(1 for m in memory if m.get('type') == 'conflict') + 1:04d}"
        ),
        "timestamp": _utc_now(),
        "stage": stage,
        "event": "evidence_conflict",
        "type": "conflict",
        "data": {
            "conflict": conflict,
            "sources": sources or [],
            "resolution": resolution,
            "resolved": bool(resolution),
            "requires_review": not bool(resolution),
        },
    }

    memory.append(conflict_record)

    return project


def get_stage_memory(
    project: AURAProject,
    stage: str,
) -> list[dict[str, Any]]:
    """
    Retrieve all memory records associated with a stage.
    """

    memory = _ensure_memory(project)

    return [
        item
        for item in memory
        if str(item.get("stage", "")).lower() == str(stage).lower()
    ]


def get_memory_by_type(
    project: AURAProject,
    memory_type: str,
) -> list[dict[str, Any]]:
    """
    Retrieve memory records by type.
    """

    memory = _ensure_memory(project)

    return [
        item
        for item in memory
        if str(item.get("type", "")).lower() == str(memory_type).lower()
    ]


def get_evidence(
    project: AURAProject,
    evidence_id: str,
) -> dict[str, Any] | None:
    """
    Retrieve one evidence record by evidence ID.
    """

    evidence = _ensure_evidence(project)

    for item in evidence:
        if str(item.get("evidence_id", "")) == str(evidence_id):
            return item

    return None


def get_evidence_for_claim(
    project: AURAProject,
    claim: str,
) -> list[dict[str, Any]]:
    """
    Retrieve evidence records related to a claim.

    Matching is intentionally conservative and based on textual
    overlap rather than pretending semantic verification occurred.
    """

    evidence = _ensure_evidence(project)

    claim_words = {
        word.lower().strip(".,:;!?()[]{}")
        for word in str(claim).split()
        if len(word.strip(".,:;!?()[]{}")) >= 4
    }

    if not claim_words:
        return []

    matches: list[dict[str, Any]] = []

    for item in evidence:
        item_claim = str(item.get("claim", ""))

        item_words = {
            word.lower().strip(".,:;!?()[]{}")
            for word in item_claim.split()
            if len(word.strip(".,:;!?()[]{}")) >= 4
        }

        overlap = claim_words.intersection(item_words)

        if overlap:
            matches.append(item)

    return matches


def build_project_context(
    project: AURAProject,
) -> dict[str, Any]:
    """
    Build a compact project-wide context package.

    This is the main interface future AURA agents can use to
    understand what has already happened without repeatedly
    reconstructing the entire project history.
    """

    memory = _ensure_memory(project)
    evidence = _ensure_evidence(project)

    stage_counts: dict[str, int] = {}

    for item in memory:
        stage = str(item.get("stage", "unknown"))

        stage_counts[stage] = stage_counts.get(stage, 0) + 1

    decisions = get_memory_by_type(project, "decision")
    findings = get_memory_by_type(project, "finding")
    uncertainties = get_memory_by_type(project, "uncertainty")
    conflicts = get_memory_by_type(project, "conflict")

    evidence_ids = [
        str(item.get("evidence_id"))
        for item in evidence
        if item.get("evidence_id")
    ]

    return {
        "project_id": project.project_id,
        "project_name": project.project_name,
        "original_idea": project.original_idea,
        "status": project.status,
        "current_stage": project.current_stage,
        "domain": list(project.domain),
        "objectives": list(project.objectives),
        "requirements": list(project.requirements),
        "constraints": list(project.constraints),
        "memory_statistics": {
            "total_memory_records": len(memory),
            "total_evidence_records": len(evidence),
            "total_decisions": len(decisions),
            "total_findings": len(findings),
            "total_uncertainties": len(uncertainties),
            "total_conflicts": len(conflicts),
            "stage_counts": stage_counts,
        },
        "decisions": decisions,
        "findings": findings,
        "uncertainties": uncertainties,
        "conflicts": conflicts,
        "evidence_ids": evidence_ids,
        "last_memory_event": memory[-1] if memory else None,
        "last_evidence": evidence[-1] if evidence else None,
    }


def summarize_memory(
    project: AURAProject,
) -> dict[str, Any]:
    """
    Produce a high-level memory summary for the UI and later agents.
    """

    context = build_project_context(project)

    return {
        "project_id": project.project_id,
        "project_name": project.project_name,
        "total_events": context["memory_statistics"]["total_memory_records"],
        "total_evidence": context["memory_statistics"]["total_evidence_records"],
        "decisions": context["memory_statistics"]["total_decisions"],
        "findings": context["memory_statistics"]["total_findings"],
        "uncertainties": context["memory_statistics"]["total_uncertainties"],
        "conflicts": context["memory_statistics"]["total_conflicts"],
        "stages_with_memory": list(
            context["memory_statistics"]["stage_counts"].keys()
        ),
        "current_stage": project.current_stage,
    }


def attach_memory_context(
    project: AURAProject,
) -> AURAProject:
    """
    Synchronize the current project memory summary into project.analysis.

    This keeps Stage 10 connected to the existing AURAProject model
    without requiring a new database schema immediately.
    """

    if not isinstance(project.analysis, dict):
        project.analysis = {}

    context = build_project_context(project)

    project.analysis["project_memory"] = context
    project.analysis["memory_summary"] = summarize_memory(project)

    return project


def get_recent_memory(
    project: AURAProject,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """
    Return the most recent memory records.
    """

    memory = _ensure_memory(project)

    if limit <= 0:
        return []

    return memory[-limit:]


def get_recent_evidence(
    project: AURAProject,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """
    Return the most recent evidence records.
    """

    evidence = _ensure_evidence(project)

    if limit <= 0:
        return []

    return evidence[-limit:]


def clear_runtime_memory(
    project: AURAProject,
) -> AURAProject:
    """
    Reset only the runtime memory and evidence collections.

    This helper is intentionally explicit and should only be used
    for testing/reset workflows.
    """

    project.memory = []
    project.evidence = []

    if isinstance(project.analysis, dict):
        project.analysis.pop("project_memory", None)
        project.analysis.pop("memory_summary", None)

    return project


__all__ = [
    "add_memory",
    "add_evidence",
    "record_decision",
    "record_finding",
    "record_uncertainty",
    "record_conflict",
    "get_stage_memory",
    "get_memory_by_type",
    "get_evidence",
    "get_evidence_for_claim",
    "build_project_context",
    "summarize_memory",
    "attach_memory_context",
    "get_recent_memory",
    "get_recent_evidence",
    "clear_runtime_memory",
]