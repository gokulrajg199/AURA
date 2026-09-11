from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any


DEPENDENCIES: dict[str, list[str]] = {
    "problem": ["requirements"],
    "requirements": ["research", "evidence", "innovation", "solution", "architecture"],
    "research": ["evidence", "innovation", "solution"],
    "evidence": ["innovation", "solution", "architecture"],
    "innovation": ["solution", "architecture"],
    "solution": ["architecture"],
    "architecture": ["implementation", "dataset"],
    "implementation": ["testing", "experiment", "results"],
    "dataset": ["annotation", "baseline", "model", "experiment", "results"],
    "annotation": ["baseline", "model"],
    "baseline": ["model", "experiment", "results"],
    "model": ["testing", "experiment", "results"],
    "testing": ["experiment", "results"],
    "experiment": ["results", "validation"],
    "results": ["validation", "documentation", "delivery"],
    "validation": ["documentation", "delivery"],
    "documentation": ["delivery"],
}

SOURCE_FIELDS: dict[str, list[str]] = {
    "problem": ["original_idea", "project_name", "domain"],
    "requirements": ["requirements", "objectives", "constraints"],
    "research": ["research"],
    "evidence": ["evidence"],
    "innovation": ["innovation"],
    "solution": ["solution"],
    "architecture": ["architecture"],
    "implementation": ["development"],
    "dataset": ["development", "execution_contract"],
    "annotation": ["development"],
    "baseline": ["experiments"],
    "model": ["development", "experiments"],
    "testing": ["development", "experiments"],
    "experiment": ["experiments"],
    "results": ["experiments"],
    "validation": ["validation"],
    "documentation": ["deliverables"],
    "delivery": ["deliverables", "validation"],
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stable(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def _fingerprint(project: dict[str, Any], fields: list[str]) -> str:
    payload = {field: project.get(field) for field in fields}
    return hashlib.sha256(_stable(payload).encode("utf-8")).hexdigest()


def _downstream(start: str) -> list[str]:
    seen: set[str] = set()
    queue = list(DEPENDENCIES.get(start, []))
    while queue:
        node = queue.pop(0)
        if node in seen:
            continue
        seen.add(node)
        queue.extend(DEPENDENCIES.get(node, []))
    return sorted(seen, key=lambda item: list(SOURCE_FIELDS).index(item) if item in SOURCE_FIELDS else 999)


def propagate_dependency_impact(project: dict[str, Any]) -> dict[str, Any]:
    """Detect persisted project changes and record downstream impact.

    This is a deterministic dependency engine. It does not claim that an
    affected artifact is scientifically invalid; it marks it as requiring
    re-check/re-execution/review so AURA cannot silently carry stale truth.
    """
    context = project.setdefault("project_context", {})
    previous = context.get("dependency_fingerprints") if isinstance(context, dict) else {}
    previous = previous if isinstance(previous, dict) else {}
    current = {stage: _fingerprint(project, fields) for stage, fields in SOURCE_FIELDS.items()}

    changed = [stage for stage, value in current.items() if previous.get(stage) and previous.get(stage) != value]
    impacts: list[dict[str, Any]] = []
    impacted: list[str] = []
    for stage in changed:
        downstream = _downstream(stage)
        impacted.extend(downstream)
        impacts.append({
            "source": stage,
            "downstream": downstream,
            "action": "RECHECK_DOWNSTREAM",
            "reason": f"{stage} changed after the previous persisted project state.",
        })

    impacted = list(dict.fromkeys(impacted))
    now = _now()
    state = {
        "schema_version": "6.1-dependency-impact-1",
        "updated_at": now,
        "changed_nodes": changed,
        "impacted_nodes": impacted,
        "impacts": impacts,
        "requires_reexecution": any(node in impacted for node in {"testing", "experiment", "results"}),
        "requires_revalidation": any(node in impacted for node in {"validation", "documentation", "delivery"}),
        "truth": "Impact propagation identifies stale downstream work; it does not itself prove scientific invalidity.",
    }

    context["dependency_fingerprints"] = current
    context["dependency_impact"] = state

    if changed and project.get("validation", {}).get("scientific_validation"):
        validation = project.setdefault("validation", {})
        validation["scientific_validation"] = False
        validation["human_approved"] = False
        validation["results_verified"] = False
        validation["invalidated_at"] = now
        validation["invalidation_reason"] = "Upstream project state changed; downstream scientific validation requires re-review."
        validation.setdefault("review_history", []).append({
            "action": "INVALIDATED",
            "reason": validation["invalidation_reason"],
            "at": now,
            "changed_nodes": changed,
            "impacted_nodes": impacted,
        })

    return state
