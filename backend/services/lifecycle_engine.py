from __future__ import annotations
import json
from pathlib import Path
import os
from typing import Any

PROFILE_LIFECYCLES = {
    "computer_vision": [
        ("idea", "IDEA", "Project idea and scope"),
        ("analysis", "ANALYSIS", "Problem, objectives and constraints"),
        ("requirements", "REQUIREMENTS", "Functional and non-functional requirements"),
        ("research", "RESEARCH", "Literature and technical investigation"),
        ("evidence", "EVIDENCE", "Source-backed evidence and provenance"),
        ("innovation", "INNOVATION", "Gap and differentiation"),
        ("solution", "SOLUTION", "Selected technical solution"),
        ("architecture", "ARCHITECTURE", "System and model architecture"),
        ("implementation", "IMPLEMENTATION", "Actual project workspace and code"),
        ("dataset", "DATASET", "Approved image/video dataset"),
        ("annotation", "ANNOTATION", "Labels, classes and annotation quality"),
        ("baseline", "BASELINE", "Approved baseline implementation and evaluation"),
        ("model", "MODEL", "Proposed model training"),
        ("testing", "TESTING", "Automated and project-level tests"),
        ("experiment", "EXPERIMENT", "Controlled experiment execution"),
        ("results", "RESULTS", "Measured results and comparison"),
        ("validation", "VALIDATION", "Scientific/technical validation and review"),
        ("documentation", "DOCUMENTATION", "Final report, paper and technical docs"),
        ("delivery", "DELIVERY", "Verified final package and demonstration"),
    ],
    "iot": [
        ("idea", "IDEA", "Project idea and scope"), ("analysis", "ANALYSIS", "Problem and constraints"),
        ("requirements", "REQUIREMENTS", "System requirements"), ("research", "RESEARCH", "Literature and technology research"),
        ("evidence", "EVIDENCE", "Evidence and provenance"), ("innovation", "INNOVATION", "Gap and innovation"),
        ("solution", "SOLUTION", "Technical solution"), ("architecture", "ARCHITECTURE", "Hardware/software architecture"),
        ("implementation", "IMPLEMENTATION", "Firmware/software implementation"), ("hardware", "HARDWARE", "Sensor/device integration"),
        ("data", "DATA", "Approved sensor/telemetry data"), ("baseline", "BASELINE", "Baseline method"),
        ("model", "MODEL", "Proposed model"), ("testing", "TESTING", "Automated and hardware tests"),
        ("experiment", "EXPERIMENT", "Controlled experiment"), ("results", "RESULTS", "Measured results"),
        ("validation", "VALIDATION", "Field/scientific validation"), ("documentation", "DOCUMENTATION", "Final documentation"),
        ("delivery", "DELIVERY", "Deployment and final package"),
    ],
    "robotics": [
        ("idea", "IDEA", "Project idea and scope"), ("analysis", "ANALYSIS", "Problem and constraints"),
        ("requirements", "REQUIREMENTS", "System requirements"), ("research", "RESEARCH", "Research and prior art"),
        ("evidence", "EVIDENCE", "Evidence and provenance"), ("innovation", "INNOVATION", "Innovation and gap"),
        ("solution", "SOLUTION", "Selected solution"), ("architecture", "ARCHITECTURE", "Robot/software architecture"),
        ("implementation", "IMPLEMENTATION", "ROS/software/hardware implementation"), ("simulation", "SIMULATION", "Simulation and scenario tests"),
        ("dataset", "DATASET", "Approved sensor/video/telemetry data"), ("baseline", "BASELINE", "Baseline controller/model"),
        ("model", "MODEL", "Proposed perception/planning/control model"), ("testing", "TESTING", "Automated and integration tests"),
        ("experiment", "EXPERIMENT", "Controlled robot experiments"), ("results", "RESULTS", "Measured results"),
        ("validation", "VALIDATION", "Real-world validation and review"), ("documentation", "DOCUMENTATION", "Final documentation"),
        ("delivery", "DELIVERY", "Deployment/demo package"),
    ],
    "general": [
        ("idea", "IDEA", "Project idea and scope"), ("analysis", "ANALYSIS", "Problem and constraints"),
        ("requirements", "REQUIREMENTS", "Project requirements"), ("research", "RESEARCH", "Research and investigation"),
        ("evidence", "EVIDENCE", "Evidence and provenance"), ("innovation", "INNOVATION", "Gap and innovation"),
        ("solution", "SOLUTION", "Selected solution"), ("architecture", "ARCHITECTURE", "System architecture"),
        ("implementation", "IMPLEMENTATION", "Implementation"), ("data", "DATA", "Project data/input readiness"),
        ("baseline", "BASELINE", "Baseline"), ("model", "MODEL", "Proposed implementation/model"),
        ("testing", "TESTING", "Testing"), ("experiment", "EXPERIMENT", "Experiment/execution"),
        ("results", "RESULTS", "Measured results"), ("validation", "VALIDATION", "Validation and review"),
        ("documentation", "DOCUMENTATION", "Documentation"), ("delivery", "DELIVERY", "Delivery"),
    ],
}


def _profile(project: dict[str, Any]) -> str:
    idea = str(project.get("original_idea", "")).lower()
    if any(x in idea for x in ("computer vision", "plant disease", "object detection", "image classification", "image recognition", "yolo")):
        return "computer_vision"
    if any(x in idea for x in ("iot", "sensor", "hydroponic", "telemetry", "embedded")):
        return "iot"
    if any(x in idea for x in ("robot", "robotics", "ros", "navigation", "control system")):
        return "robotics"
    return "general"


def _artifact(root: Path, name: str) -> dict[str, Any]:
    path = root / "artifacts" / name
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _executed(executions: list[dict[str, Any]], task: str) -> bool:
    return any(e.get("task") == task and e.get("status") == "EXECUTED" for e in executions)


def build_lifecycle(project: dict[str, Any], executions: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    executions = executions or []
    pid = str(project.get("project_id", ""))
    root = Path(os.getenv("AURA_DATA_DIR", str(Path(__file__).resolve().parents[1] / "data"))) / "project_workspaces" / pid
    profile = _profile(project)
    stages = PROFILE_LIFECYCLES.get(profile, PROFILE_LIFECYCLES["general"])
    dataset = _artifact(root, "dataset_status.json")
    training = _artifact(root, "training_status.json")
    baseline = _artifact(root, "baseline_evaluation.json")
    evaluation = _artifact(root, "evaluation.json")
    experiment = _artifact(root, "experiment_run.json")
    validation = project.get("validation") or {}
    deliverables = project.get("deliverables") or {}
    development = project.get("development") or {}
    evidence = project.get("evidence") or []
    research = project.get("research") or {}
    analysis = project.get("analysis") or {}
    statuses: list[dict[str, Any]] = []

    def state(key: str) -> tuple[str, str, str]:
        if key == "idea": return ("verified", "VERIFIED", "Original project idea exists.") if project.get("original_idea") else ("blocked", "MISSING", "Project idea is required.")
        if key == "analysis": return ("verified", "VERIFIED", "Project analysis exists.") if analysis else ("pending", "PENDING", "Run AURA analysis.")
        if key == "requirements":
            if project.get("requirements"):
                approved = bool((analysis.get("requirements_approved") is True) or (analysis.get("requirements_status") in {"APPROVED", "VERIFIED"}))
                if approved:
                    return ("verified", "VERIFIED", "Requirements are defined and approved.")
                return ("ready", "DEFINED · REVIEW REQUIRED", "Requirements are defined but still require human approval.")
            return ("pending", "PENDING", "Requirements are not yet defined.")
        if key == "research":
            papers = research.get("papers") if isinstance(research, dict) else []
            papers = papers if isinstance(papers, list) else []
            reviewed = [p for p in papers if isinstance(p, dict) and (p.get("reviewed") is True or p.get("source_reviewed") is True or p.get("verification_status") in {"reviewed", "verified", "APPROVED", "VERIFIED"})]
            if reviewed:
                return ("verified", "VERIFIED", f"{len(reviewed)} research source(s) are marked reviewed.")
            if papers or research:
                return ("ready", "REVIEW REQUIRED", "Research context exists but source review is not verified.")
            return ("pending", "PENDING", "Research evidence is required.")
        if key == "evidence":
            approved = [e for e in evidence if isinstance(e, dict) and e.get("scientific_evidence") is True and (e.get("reviewed") is True or e.get("status") == "APPROVED") and bool(e.get("provenance_hash") or e.get("sha256") or e.get("source"))]
            if approved:
                return ("verified", "VERIFIED", f"{len(approved)} evidence record(s) passed review and provenance checks.")
            if evidence:
                return ("ready", "REVIEW REQUIRED", "Evidence records exist but are not yet verified as approved scientific evidence.")
            return ("pending", "PENDING", "Evidence records are required.")
        if key == "innovation": return ("designed", "GENERATED", "Innovation direction generated; not a measured result.") if project.get("innovation") else ("pending", "PENDING", "Innovation analysis pending.")
        if key == "solution": return ("designed", "DESIGNED", "Solution design exists.") if project.get("solution") else ("pending", "PENDING", "Solution design pending.")
        if key == "architecture": return ("designed", "DESIGNED", "Architecture exists.") if project.get("architecture") else ("pending", "PENDING", "Architecture pending.")
        if key == "implementation":
            ready = bool(development.get("real_project_generated")) or root.exists()
            return ("ready", "READY", "Real project workspace generated; runtime evidence still pending.") if ready else ("pending", "PENDING", "Generate the real project workspace.")
        if key in {"dataset", "data"}:
            if dataset.get("status") == "READY" and dataset.get("approved_dataset") is True and dataset.get("scientific_evidence") is not False:
                return ("verified", "VERIFIED", "Approved project dataset is ready.")
            if dataset.get("status") == "READY": return ("ready", "READY", "Development fixture/input is ready but is not approved scientific evidence.")
            return ("blocked", "BLOCKED", dataset.get("reason", "Approved project data is required."))
        if key == "annotation":
            if profile != "computer_vision": return ("na", "N/A", "Not applicable to this project profile.")
            if dataset.get("annotation_ready") is True: return ("verified", "VERIFIED", "Annotation readiness is recorded.")
            return ("pending", "PENDING", "Verify classes, labels and annotation quality for the dataset.")
        if key == "hardware":
            return ("verified", "VERIFIED", "Hardware integration evidence recorded.") if development.get("hardware_verified") else ("pending", "PENDING", "Hardware integration evidence is required.")
        if key == "simulation":
            return ("verified", "VERIFIED", "Simulation execution recorded.") if _executed(executions, "smoke_test") else ("pending", "PENDING", "Run the project simulation/controlled test.")
        if key == "baseline":
            if baseline.get("status") == "EXECUTED" and baseline.get("scientific_result") is not False: return ("verified", "VERIFIED", "Baseline evaluation executed on approved inputs.")
            if baseline.get("status") == "EXECUTED": return ("executed", "EXECUTED", "Baseline executed on a development fixture; not scientific evidence.")
            return ("pending", "NOT EXECUTED", "Run the project-approved baseline evaluation.")
        if key == "model":
            if training.get("status") == "EXECUTED" and training.get("scientific_result") is not False: return ("verified", "VERIFIED", "Proposed model training executed.")
            if training.get("status") == "EXECUTED": return ("executed", "EXECUTED", "Training execution used a development fixture; not scientific evidence.")
            return ("pending", "NOT EXECUTED", "Run proposed model training.")
        if key == "testing":
            if _executed(executions, "project_test"): return ("verified", "VERIFIED", "Project tests executed successfully.")
            if _executed(executions, "smoke_test"): return ("ready", "SMOKE TESTED", "Workspace smoke test passed; full project tests remain.")
            return ("pending", "PENDING", "Run project tests.")
        if key == "experiment":
            if experiment.get("status") == "EXECUTED": return ("executed", "EXECUTED", "Experiment workflow executed; scientific review remains required.")
            return ("pending", "AWAITING EXECUTION", "Run the controlled experiment.")
        if key == "results":
            if evaluation.get("status") == "EXECUTED" and evaluation.get("metrics_available"):
                if evaluation.get("scientific_result") is False: return ("executed", "MEASURED · FIXTURE", "Measured development-fixture output; not scientific evidence.")
                return ("measured", "MEASURED", "Metrics were produced by controlled execution.")
            return ("pending", "NOT AVAILABLE", "No measured project result is available yet.")
        if key == "validation":
            if validation.get("scientific_validation") is True and validation.get("human_approved") is True: return ("verified", "VERIFIED", "Scientific validation and human approval are recorded.")
            return ("review", "REVIEW REQUIRED", "AURA does not self-certify scientific validity.")
        if key == "documentation":
            if deliverables.get("documentation_verified") is True or deliverables.get("documentation_status") == "VERIFIED":
                return ("verified", "VERIFIED", "Required documentation is reviewed and verified.")
            if deliverables: return ("ready", "CONTENT READY", "Delivery content has been generated from project context but still requires review.")
            return ("pending", "PENDING", "Generate and review final documentation.")
        if key == "delivery":
            if validation.get("scientific_validation") is True and validation.get("human_approved") is True and deliverables: return ("verified", "READY", "Validated project package is ready for delivery.")
            return ("pending", "PENDING", "Delivery remains blocked until validation and required outputs are complete.")
        return ("pending", "PENDING", "Stage is pending.")

    for order, (key, label, description) in enumerate(stages, 1):
        status, display, reason = state(key)
        statuses.append({"key": key, "label": label, "order": order, "status": status, "display": display, "reason": reason, "description": description, "verified": status == "verified"})

    required = [s for s in statuses if s["status"] != "na"]
    verified = [s for s in required if s["verified"]]
    blockers = [s for s in required if s["status"] in {"blocked", "pending", "review"}]
    next_stage = blockers[0] if blockers else None
    percent = round((len(verified) / max(len(required), 1)) * 100, 1)
    completed = len(verified) == len(required) and len(required) > 0
    return {
        "profile": profile,
        "stages": statuses,
        "total_stages": len(required),
        "verified_stages": len(verified),
        "completion_percent": percent,
        "completed": completed,
        "next_blocker": next_stage,
        "truth": "Verified lifecycle completion counts only evidence-backed or successfully verified stages. Generated/design/fixture execution does not equal scientific validation.",
    }
