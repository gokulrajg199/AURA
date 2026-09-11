from __future__ import annotations
from hashlib import sha256
from typing import Any


def _as_items(value: Any, keys: tuple[str, ...]) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [x if isinstance(x, dict) else {"text": str(x)} for x in value]
    if isinstance(value, dict):
        for key in keys:
            v = value.get(key)
            if isinstance(v, list):
                return [x if isinstance(x, dict) else {"text": str(x)} for x in v]
        if value:
            return [value]
    return []


def _text(x: dict[str, Any]) -> str:
    for k in ("text", "title", "name", "description", "requirement", "component", "module", "result"):
        if x.get(k):
            return str(x[k])
    return ""


def _id(prefix: str, x: dict[str, Any], i: int) -> str:
    raw = x.get("id") or x.get(f"{prefix}_id") or i
    return f"{prefix}:{raw}"


def _refs(x: dict[str, Any], names: tuple[str, ...]) -> list[str]:
    out: list[str] = []
    for k in names:
        v = x.get(k)
        vals = v if isinstance(v, list) else [v] if v else []
        out.extend(str(z) for z in vals)
    return out


def build_innovation_traceability(project: dict[str, Any], executions: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    executions = executions or []
    innovation = _as_items(project.get("innovation"), ("items", "innovations", "proposals", "features"))
    requirements = _as_items(project.get("requirements"), ("items", "requirements"))
    architecture = _as_items(project.get("architecture"), ("components", "modules", "architecture", "items"))
    development = _as_items(project.get("development"), ("components", "modules", "implementation", "files", "items"))
    dataset = _as_items(project.get("dataset") or project.get("data"), ("datasets", "items", "sources"))
    experiments = _as_items(project.get("experiments"), ("plans", "experiments", "runs", "items"))
    results = []
    for e in executions:
        if isinstance(e, dict) and (e.get("metrics") or e.get("results") or e.get("artifact_hashes")):
            results.append(e)
    if not results:
        results = _as_items(project.get("experiments"), ("results", "results_summary"))
    validation = _as_items(project.get("validation"), ("criteria", "checks", "items"))

    buckets = [("innovation", innovation), ("requirement", requirements), ("architecture", architecture),
               ("implementation", development), ("dataset", dataset), ("experiment", experiments),
               ("result", results), ("validation", validation)]
    nodes: list[dict[str, Any]] = []
    ids: dict[str, list[str]] = {}
    for typ, items in buckets:
        ids[typ] = []
        for i, item in enumerate(items):
            nid = _id(typ, item, i)
            text = _text(item)
            status = str(item.get("status") or item.get("verification") or "DEFINED")
            if typ == "implementation":
                status = "IMPLEMENTED" if text or item else "MISSING"
            elif typ == "result":
                status = "MEASURED" if item.get("metrics") or item.get("results") or item.get("artifact_hashes") else "PENDING"
            elif typ == "validation":
                status = "VALIDATED" if item.get("verified") is True or item.get("status") == "VERIFIED" else status
            nodes.append({"id": nid, "type": typ, "label": text[:180] or nid, "status": status,
                          "provenance_hash": sha256(text.encode()).hexdigest() if text else None})
            ids[typ].append(nid)

    edges: list[dict[str, Any]] = []
    rel_fields = {
        "innovation": (("requirement_ids", "requirement_id"), "requirement"),
        "requirement": (("innovation_ids", "innovation_id"), "innovation"),
    }
    chain = [("innovation", "requirement"), ("requirement", "architecture"), ("architecture", "implementation"),
             ("implementation", "dataset"), ("dataset", "experiment"), ("experiment", "result"), ("result", "validation")]
    # Explicit references only; conservative same-index linkage is used only when both sides are singleton records.
    for src_typ, dst_typ in chain:
        for i, item in enumerate(dict(buckets)[src_typ]):
            src = ids[src_typ][i]
            refs = _refs(item, (f"{dst_typ}_ids", f"{dst_typ}_id", "component_ids", "module_ids", "experiment_ids", "result_ids"))
            for ref in refs:
                for dst in ids[dst_typ]:
                    if ref in dst:
                        edges.append({"source": src, "target": dst, "relationship": f"{src_typ}_to_{dst_typ}", "basis": "EXPLICIT_REFERENCE"})
        if len(ids[src_typ]) == 1 and len(ids[dst_typ]) == 1:
            # A singleton record is a safe structural container, but still not scientific proof.
            edges.append({"source": ids[src_typ][0], "target": ids[dst_typ][0], "relationship": f"{src_typ}_to_{dst_typ}", "basis": "SINGLETON_STRUCTURAL_LINK"})

    linked = {x for e in edges for x in (e["source"], e["target"])}
    counts = {typ: len(ids[typ]) for typ, _ in buckets}
    coverage = round(len(linked) / len(nodes) * 100, 1) if nodes else 0.0
    missing = []
    for src_typ, dst_typ in chain:
        for sid in ids[src_typ]:
            if not any(e["source"] == sid and e["target"].startswith(dst_typ + ":") for e in edges):
                missing.append({"source": sid, "expected": dst_typ})
    return {
        "schema": "6.1-innovation-traceability-1", "nodes": nodes, "edges": edges,
        "counts": counts, "coverage_percent": coverage, "missing_links": missing,
        "implementation_traceability": {"innovations_to_requirements": len(ids["innovation"]) > 0 and len(ids["requirement"]) > 0,
                                         "requirements_to_architecture": len(ids["requirement"]) > 0 and len(ids["architecture"]) > 0,
                                         "architecture_to_implementation": len(ids["architecture"]) > 0 and len(ids["implementation"]) > 0,
                                         "implementation_to_experiment": len(ids["implementation"]) > 0 and len(ids["experiment"]) > 0,
                                         "experiment_to_result": len(ids["experiment"]) > 0 and len(ids["result"]) > 0,
                                         "result_to_validation": len(ids["result"]) > 0 and len(ids["validation"]) > 0},
        "truth_status": "TRACEABILITY_ONLY; IMPLEMENTATION_LINKS_DO_NOT_PROVE_EXECUTION_OR_SCIENTIFIC_VALIDATION",
        "review_required": True,
    }
