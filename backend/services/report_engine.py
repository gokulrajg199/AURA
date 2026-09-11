from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.lifecycle_engine import build_lifecycle
from services.results_engine import collect_results
from services.dataset_engine import profile_workspace


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _text(value: Any) -> str:
    if value is None:
        return "Not available."
    if isinstance(value, str):
        return value.strip() or "Not available."
    return json.dumps(value, indent=2, ensure_ascii=False, default=str)


def _items(value: Any) -> list[str]:
    if value is None:
        return ["Not available."]
    if isinstance(value, list):
        return [str(x) for x in value] or ["No records available."]
    if isinstance(value, dict):
        return [f"{k}: {_text(v)}" for k, v in value.items()]
    return [str(value)]


def build_report(project: dict[str, Any], workspace_root: Path | None = None) -> dict[str, Any]:
    project_id = str(project.get("project_id", "unknown"))
    workspace = workspace_root or Path(os.getenv("AURA_DATA_DIR", str(Path(__file__).resolve().parent.parent / "data"))) / "project_workspaces" / project_id
    executions: list[dict[str, Any]] = []
    try:
        # Import lazily to avoid circular imports at module load time.
        from services.execution_engine import list_executions
        executions = list_executions(project_id)
    except Exception:
        executions = []

    lifecycle = build_lifecycle(project, executions)
    results = collect_results(project_id, workspace)
    datasets = profile_workspace(workspace) if workspace.exists() else []
    validation = project.get("validation") or {}
    evidence = project.get("evidence") or []
    research = project.get("research") or {}
    analysis = project.get("analysis") or {}
    architecture = project.get("architecture") or {}
    development = project.get("development") or {}
    experiments = project.get("experiments") or {}
    completion = project.get("completion") or {}

    metrics = results.get("comparison") or {}
    scientific_complete = bool(completion.get("completed")) and bool(validation.get("scientific_validation")) and bool(validation.get("human_approved"))

    chapters: list[dict[str, Any]] = []

    def add(number: str, title: str, sections: list[tuple[str, Any]]) -> None:
        chapters.append({"number": number, "title": title, "sections": [{"title": h, "content": _items(v)} for h, v in sections]})

    add("1", "INTRODUCTION", [
        ("Project Title", project.get("project_name") or project.get("original_idea")),
        ("Background / Context", analysis.get("background") or analysis.get("problem_understanding") or analysis),
        ("Problem Statement", analysis.get("problem_statement") or analysis.get("problem_understanding") or "Not explicitly recorded yet."),
        ("Motivation", analysis.get("motivation") or "Not explicitly recorded yet."),
        ("Objectives", project.get("objectives")),
        ("Scope", analysis.get("scope") or project.get("constraints")),
        ("Contributions", innovation := project.get("innovation")),
    ])
    add("2", "LITERATURE REVIEW", [
        ("Research Records", research),
        ("Research Question", research.get("question") if isinstance(research, dict) else None),
        ("Research Gaps", research.get("research_gaps") if isinstance(research, dict) else None),
        ("Source Coverage", research.get("coverage") if isinstance(research, dict) else None),
        ("Evidence / Review Status", "Source review is required before literature metadata is treated as verified evidence."),
    ])
    add("3", "SYSTEM ANALYSIS", [
        ("Existing System / Baseline Context", analysis.get("existing_system") or analysis),
        ("Requirements", project.get("requirements")),
        ("Constraints", project.get("constraints")),
        ("Project Profile", project.get("domain")),
        ("AURA Verdict", analysis.get("verdict") or analysis.get("recommendation") or "Not recorded."),
    ])
    add("4", "SYSTEM DESIGN", [
        ("Proposed Solution", project.get("solution")),
        ("Architecture", architecture),
        ("Innovation", project.get("innovation")),
        ("Data Flow / Components", architecture.get("data_flow") if isinstance(architecture, dict) else None),
    ])
    add("5", "DATASET", [
        ("Dataset Status", results.get("dataset")),
        ("Workspace Dataset Profiles", datasets),
        ("Dataset Truth Boundary", "Dataset profiling establishes file/data quality signals; it does not prove scientific validity."),
    ])
    add("6", "METHODOLOGY", [
        ("Development Plan", development),
        ("Execution Contract", project.get("execution_contract")),
        ("Experiment Design", experiments),
        ("Evaluation Metrics", results.get("evaluation_metrics")),
    ])
    add("7", "IMPLEMENTATION", [
        ("Implementation State", development),
        ("Workspace", str(workspace) if workspace.exists() else "Workspace not generated."),
        ("Execution Records", executions),
    ])
    add("8", "EXPERIMENTATION", [
        ("Experiment Plan", experiments),
        ("Baseline", results.get("baseline")),
        ("Proposed", results.get("proposed")),
        ("Experiment Run", results.get("experiment")),
    ])
    add("9", "RESULTS", [
        ("Result Status", results.get("status")),
        ("Measured Metrics", metrics),
        ("Baseline Executed", results.get("baseline_executed")),
        ("Proposed Executed", results.get("proposed_executed")),
        ("Execution Truth", results.get("execution_truth")),
    ])
    add("10", "VALIDATION", [
        ("Lifecycle", lifecycle),
        ("Validation Record", validation),
        ("Scientific Validation", validation.get("scientific_validation", False)),
        ("Human Approval", validation.get("human_approved", False)),
        ("Evidence Records", evidence),
    ])
    add("11", "DISCUSSION", [
        ("Findings", results.get("comparison") or "No measured comparison is available yet."),
        ("Limitations", validation.get("limitations") or analysis.get("limitations") or "Not recorded."),
        ("Research Implications", research.get("implications") if isinstance(research, dict) else "Not recorded."),
    ])
    add("12", "CONCLUSION", [
        ("Current Project State", lifecycle.get("next_blocker") or lifecycle.get("completed")),
        ("Completion Status", "SCIENTIFICALLY COMPLETED" if scientific_complete else "PROJECT IN PROGRESS — SCIENTIFIC COMPLETION NOT YET VERIFIED"),
        ("Future Work", project.get("deliverables", {}).get("future_work") if isinstance(project.get("deliverables"), dict) else None),
    ])
    add("13", "REFERENCES & EVIDENCE", [
        ("Literature Sources", research.get("sources") if isinstance(research, dict) else None),
        ("Evidence Registry", evidence),
        ("Provenance Rule", "Every scientific claim should remain traceable to its source, execution record, measured artifact, or human review."),
    ])
    add("14", "APPENDICES", [
        ("Execution Records", executions),
        ("Dataset Profiles", datasets),
        ("Results Summary", results),
        ("Completion Gates", completion),
    ])

    return {
        "report_version": "AURA-COMPLETE-PROJECT-REPORT-1.0",
        "generated_at": _now(),
        "project_id": project_id,
        "project_title": project.get("project_name") or project.get("original_idea") or "AURA Project",
        "scientific_completion": scientific_complete,
        "truth_status": "SCIENTIFICALLY_COMPLETE" if scientific_complete else "DESIGNED_OR_IN_PROGRESS",
        "chapters": chapters,
        "lifecycle": lifecycle,
        "results": results,
        "datasets": datasets,
        "evidence_count": len(evidence),
        "execution_count": len(executions),
        "completion": completion,
    }


def render_report_text(report: dict[str, Any]) -> str:
    lines = [
        "AURA — COMPLETE PROJECT REPORT",
        "=" * 80,
        f"Project: {report.get('project_title')}",
        f"Report Version: {report.get('report_version')}",
        f"Generated: {report.get('generated_at')}",
        f"Scientific Completion: {report.get('truth_status')}",
        "",
        "TRUTH CONTRACT",
        "GENERATED != IMPLEMENTED != TESTED != EXECUTED != MEASURED != VALIDATED != COMPLETED",
        "",
    ]
    for chapter in report.get("chapters", []):
        lines += [f"CHAPTER {chapter['number']}: {chapter['title']}", "-" * 80]
        for section in chapter.get("sections", []):
            lines += [section["title"], "~" * max(12, len(section["title"]))]
            for item in section.get("content", []):
                lines.append(str(item))
            lines.append("")
    return "\n".join(lines)
