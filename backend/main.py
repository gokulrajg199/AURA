from __future__ import annotations

from typing import Any

import os
import html
import io
import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from models.project import AURAProject
from orchestration.orchestrator import aura_orchestrator
from orchestration.stages import AURAStage, STAGE_ORDER

from services.literature.search import search_literature
from services.literature.analysis import analyze_literature
from services.research_gap.gap_engine import analyze_research_gap
from services.execution_engine import build_workspace, execute as execute_task, list_executions
from services.results_engine import collect_results


# ============================================================
# AURA APPLICATION
# ============================================================

APP_NAME = "AURA"
APP_VERSION = "1.0.0"

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=(
        "AURA — AI Research, Innovation & Development Operating System. "
        "A connected autonomous project lifecycle from idea to validated delivery."
    ),
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in os.getenv(
        "AURA_CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    ).split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# TEMPORARY PROJECT MEMORY
# ============================================================
#
# This is intentionally in-memory for the first working version.
#
# Later this will be replaced with persistent project storage
# such as PostgreSQL / Supabase / SQLite depending on deployment.
#
# AURAProject itself already contains:
# - research
# - analysis
# - innovation
# - solution
# - architecture
# - development
# - experiments
# - validation
# - deliverables
# - memory
# - evidence
#

PROJECT_STORE: dict[str, AURAProject] = {}
PROJECT_DATA_DIR = Path(__file__).resolve().parent / "data"
PROJECT_DATA_FILE = PROJECT_DATA_DIR / "projects.json"


def _save_project_store() -> None:
    """Persist all active AURA projects so a backend restart does not lose them."""
    PROJECT_DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = {project_id: project_snapshot(project) for project_id, project in PROJECT_STORE.items()}
    tmp = PROJECT_DATA_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(PROJECT_DATA_FILE)


def _load_project_store() -> None:
    """Restore projects created in earlier backend sessions."""
    if not PROJECT_DATA_FILE.exists():
        return
    try:
        raw = json.loads(PROJECT_DATA_FILE.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            for project_id, data in raw.items():
                if isinstance(data, dict):
                    try:
                        project = AURAProject.model_validate(data)
                        PROJECT_STORE[project_id] = project
                    except Exception:
                        continue
    except Exception:
        # A corrupt persistence file must not prevent AURA from starting.
        return




# ============================================================
# REQUEST MODELS
# ============================================================

_load_project_store()


class ResearchRequest(BaseModel):
    question: str = Field(..., min_length=3)


class LiteratureSearchRequest(BaseModel):
    question: str = Field(..., min_length=3)
    year_from: int = 2022
    year_to: int = 2026
    max_results: int = 20


class LiteratureAnalysisRequest(BaseModel):
    question: str = Field(..., min_length=3)
    papers: list[dict[str, Any]] = Field(default_factory=list)


class ResearchGapRequest(BaseModel):
    question: str = Field(..., min_length=3)
    papers: list[dict[str, Any]] = Field(default_factory=list)


class AURAProjectCreateRequest(BaseModel):
    idea: str = Field(..., min_length=3)
    project_name: str | None = None


class AURARunRequest(BaseModel):
    stop_on_failure: bool = True


class AURARunUntilRequest(BaseModel):
    target_stage: str


# ============================================================
# HELPERS
# ============================================================


def model_to_dict(value: Any) -> Any:
    """
    Convert Pydantic/model-like objects into JSON-safe dictionaries.
    """
    if value is None:
        return None

    if isinstance(value, BaseModel):
        return value.model_dump()

    if hasattr(value, "model_dump"):
        return value.model_dump()

    if hasattr(value, "to_dict"):
        try:
            return value.to_dict()
        except Exception:
            pass

    if isinstance(value, dict):
        return {
            str(key): model_to_dict(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [model_to_dict(item) for item in value]

    if isinstance(value, tuple):
        return [model_to_dict(item) for item in value]

    if isinstance(value, set):
        return [model_to_dict(item) for item in value]

    return value


def project_snapshot(project: AURAProject) -> dict[str, Any]:
    """
    Return the complete current AURA project state.
    """
    return model_to_dict(project)


def get_stage_name(stage: Any) -> str:
    """
    Safely convert an AURA stage enum/value into a string.
    """
    if isinstance(stage, AURAStage):
        return stage.value

    return str(stage)


def get_registered_stage_names() -> list[str]:
    """
    Public helper used by local tests and the frontend.
    """
    return [stage.value for stage in STAGE_ORDER]


def get_project_or_404(project_id: str) -> AURAProject:
    project = PROJECT_STORE.get(project_id)

    if project is None:
        raise HTTPException(
            status_code=404,
            detail=f"AURA project '{project_id}' was not found.",
        )

    return project


def get_pipeline_status(project: AURAProject) -> dict[str, Any]:
    """
    Frontend-friendly pipeline status.
    """
    current_stage = get_stage_name(project.current_stage)

    stages: list[dict[str, Any]] = []

    current_index = -1

    for index, stage in enumerate(STAGE_ORDER):
        if stage.value == current_stage:
            current_index = index
            break

    for index, stage in enumerate(STAGE_ORDER):
        if project.status == "completed":
            status = "completed"

        elif index < current_index:
            status = "completed"

        elif index == current_index:
            status = "running"

        else:
            status = "pending"

        stages.append(
            {
                "id": stage.value,
                "name": stage.value.replace("_", " ").title(),
                "order": index + 1,
                "status": status,
            }
        )

    if len(STAGE_ORDER) > 0:
        if project.status == "completed":
            progress = 100

        elif current_index >= 0:
            progress = round(
                ((current_index + 1) / len(STAGE_ORDER)) * 100,
                1,
            )

        else:
            progress = 0

    else:
        progress = 0

    return {
        "current_stage": current_stage,
        "status": project.status,
        "progress": progress,
        "total_stages": len(STAGE_ORDER),
        "completed_stages": (
            len(STAGE_ORDER)
            if project.status == "completed"
            else max(current_index, 0)
        ),
        "stages": stages,
    }


def build_legacy_intelligence(project: AURAProject) -> dict[str, Any]:
    """
    Provides the older research-intelligence structure while AURA
    transitions to the complete lifecycle architecture.
    """

    return {
        "literature": project.research,
        "analysis": project.analysis.get(
            "literature_analysis",
            project.analysis,
        ),
        "research_gap": project.analysis.get(
            "research_gap",
            {},
        ),
        "verdict": project.analysis.get(
            "verdict",
            {},
        ),
    }


def build_legacy_blueprint(project: AURAProject) -> dict[str, Any]:
    """
    Compatibility structure for the previous frontend.
    """

    gap_data = project.analysis.get(
        "research_gap",
        {},
    )

    verdict_data = project.analysis.get(
        "verdict",
        {},
    )

    return {
        "project_id": project.project_id,
        "project_name": project.project_name,
        "research_question": project.original_idea,
        "domains": project.domain,
        "objectives": project.objectives,
        "requirements": project.requirements,
        "constraints": project.constraints,
        "potential_gaps": gap_data.get(
            "potential_gaps",
            gap_data.get(
                "evidence_supported_gaps",
                [],
            ),
        ),
        "aura_opportunities": gap_data.get(
            "aura_opportunities",
            [],
        ),
        "verdict": verdict_data,
        "solution": project.solution,
        "architecture": project.architecture,
        "development": project.development,
        "experiments": project.experiments,
        "validation": project.validation,
        "deliverables": project.deliverables,
    }


# ============================================================
# ROOT
# ============================================================


@app.get("/")
async def root() -> dict[str, Any]:
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "status": "online",
        "description": (
            "AI Research, Innovation & Development Operating System"
        ),
        "architecture": {
            "type": "connected_full_lifecycle",
            "mode": "autonomous_project_pipeline",
        },
        "pipeline": get_registered_stage_names(),
        "project_memory": True,
        "evidence_layer": True,
        "human_approval": True,
    }


# ============================================================
# HEALTH
# ============================================================


@app.get("/health")
async def health() -> dict[str, Any]:
    return {
        "status": "healthy",
        "service": APP_NAME,
        "version": APP_VERSION,
        "projects_in_memory": len(PROJECT_STORE),
    }


# ============================================================
# AURA PIPELINE INFORMATION
# ============================================================


@app.get("/api/aura/pipeline")
async def aura_pipeline() -> dict[str, Any]:
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "stages": [
            {
                "id": stage.value,
                "name": stage.value.replace("_", " ").title(),
                "order": index + 1,
            }
            for index, stage in enumerate(STAGE_ORDER)
        ],
        "total_stages": len(STAGE_ORDER),
    }


@app.get("/api/aura/stages")
async def aura_stages() -> dict[str, Any]:
    return {
        "stages": get_registered_stage_names(),
        "count": len(STAGE_ORDER),
    }


# ============================================================
# CREATE AURA PROJECT
# ============================================================


@app.post("/api/aura/projects")
async def create_aura_project(
    request: AURAProjectCreateRequest,
) -> dict[str, Any]:

    idea = request.idea.strip()

    if not idea:
        raise HTTPException(
            status_code=400,
            detail="Idea cannot be empty.",
        )

    try:
        project = aura_orchestrator.create_project(
            idea=idea,
            project_name=request.project_name,
        )

        PROJECT_STORE[project.project_id] = project
        _save_project_store()

        return {
            "success": True,
            "message": "AURA project created.",
            "project_id": project.project_id,
            "project": project_snapshot(project),
            "pipeline": get_pipeline_status(project),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create AURA project: {exc}",
        )


# ============================================================
# UPSERT PROJECT SNAPSHOT FROM CLIENT
# ============================================================

@app.put("/api/aura/projects/{project_id}/snapshot")
async def upsert_aura_project_snapshot(
    project_id: str,
    project: AURAProject,
) -> dict[str, Any]:
    """Restore a browser-saved project into the backend after a restart."""
    if project.project_id != project_id:
        project.project_id = project_id
    PROJECT_STORE[project_id] = project
    _save_project_store()
    return {
        "success": True,
        "message": "AURA project snapshot synchronized.",
        "project_id": project_id,
        "project": project_snapshot(project),
        "pipeline": get_pipeline_status(project),
    }


# ============================================================
# GET PROJECT
# ============================================================


@app.get("/api/aura/projects/{project_id}")
async def get_aura_project(
    project_id: str,
) -> dict[str, Any]:

    project = get_project_or_404(project_id)

    return {
        "success": True,
        "project": project_snapshot(project),
        "pipeline": get_pipeline_status(project),
    }


# ============================================================
# GET PROJECT STATUS
# ============================================================


@app.get("/api/aura/projects/{project_id}/status")
async def get_aura_project_status(
    project_id: str,
) -> dict[str, Any]:

    project = get_project_or_404(project_id)

    return {
        "success": True,
        "project_id": project.project_id,
        "project_name": project.project_name,
        "status": project.status,
        "current_stage": get_stage_name(
            project.current_stage
        ),
        "pipeline": get_pipeline_status(project),
    }


# ============================================================
# RUN COMPLETE AURA PIPELINE
# ============================================================


@app.post("/api/aura/projects/{project_id}/run")
async def run_aura_project(
    project_id: str,
    request: AURARunRequest,
) -> dict[str, Any]:

    project = get_project_or_404(project_id)

    try:
        updated_project = await aura_orchestrator.run(
            project,
            stop_on_failure=request.stop_on_failure,
        )

        PROJECT_STORE[project_id] = updated_project
        _save_project_store()

        return {
            "success": True,
            "message": "AURA pipeline execution completed.",
            "project_id": project_id,
            "project": project_snapshot(updated_project),
            "pipeline": get_pipeline_status(updated_project),
        }

    except Exception as exc:
        PROJECT_STORE[project_id] = project
        _save_project_store()

        raise HTTPException(
            status_code=500,
            detail=f"AURA pipeline execution failed: {exc}",
        )


# ============================================================
# RESUME AURA PROJECT
# ============================================================


@app.post("/api/aura/projects/{project_id}/resume")
async def resume_aura_project(
    project_id: str,
) -> dict[str, Any]:

    project = get_project_or_404(project_id)

    try:
        updated_project = await aura_orchestrator.resume(
            project
        )

        PROJECT_STORE[project_id] = updated_project
        _save_project_store()

        return {
            "success": True,
            "message": "AURA project resumed.",
            "project_id": project_id,
            "project": project_snapshot(updated_project),
            "pipeline": get_pipeline_status(updated_project),
        }

    except Exception as exc:
        PROJECT_STORE[project_id] = project
        _save_project_store()

        raise HTTPException(
            status_code=500,
            detail=f"Failed to resume AURA project: {exc}",
        )


# ============================================================
# RUN UNTIL A SPECIFIC STAGE
# ============================================================


@app.post("/api/aura/projects/{project_id}/run-until")
async def run_aura_until(
    project_id: str,
    request: AURARunUntilRequest,
) -> dict[str, Any]:

    project = get_project_or_404(project_id)

    target = request.target_stage.strip().lower()

    valid_stages = {
        stage.value
        for stage in STAGE_ORDER
    }

    if target not in valid_stages:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Invalid target stage.",
                "received": target,
                "valid_stages": sorted(valid_stages),
            },
        )

    try:
        target_stage = AURAStage(target)

        updated_project = await aura_orchestrator.run_until(
            project,
            target_stage,
        )

        PROJECT_STORE[project_id] = updated_project
        _save_project_store()

        return {
            "success": True,
            "message": (
                f"AURA pipeline executed until '{target}'."
            ),
            "project_id": project_id,
            "target_stage": target,
            "project": project_snapshot(updated_project),
            "pipeline": get_pipeline_status(updated_project),
        }

    except Exception as exc:
        PROJECT_STORE[project_id] = project
        _save_project_store()

        raise HTTPException(
            status_code=500,
            detail=(
                f"Failed to execute AURA until "
                f"stage '{target}': {exc}"
            ),
        )



class ExecutionRequest(BaseModel):
    task: str = Field(..., pattern=r"^(smoke_test|dataset_prepare|train_model|evaluate_model|baseline_evaluate|experiment_run)$")
    timeout_seconds: int = Field(120, ge=1, le=300)


@app.get("/api/aura/projects/{project_id}/build")
async def get_build_status(project_id: str):
    project = get_project_or_404(project_id)
    workspace = Path(__file__).resolve().parent / "data" / "project_workspaces" / project_id
    files = [str(p.relative_to(workspace)) for p in workspace.rglob("*") if p.is_file()] if workspace.exists() else []
    build = {
        "status": "READY" if workspace.exists() else "NOT_BUILT",
        "workspace": str(workspace),
        "profile": (project.development.get("execution_engine", {}).get("workspace", {}) or {}).get("profile", "unknown"),
        "files": files,
    }
    return {"success": True, "build": build}


@app.post("/api/aura/projects/{project_id}/build")
async def build_real_project(project_id: str):
    project = get_project_or_404(project_id)
    result = build_workspace(project_snapshot(project))
    project.development.setdefault("execution_engine", {})["workspace"] = result
    project.development["real_project_generated"] = True
    project.development["execution_boundary"] = "Controlled allowlisted Python tasks only; scientific validation requires executed experiments and human review."
    project.current_stage = AURAStage.BUILD
    PROJECT_STORE[project_id] = project
    _save_project_store()
    return {"success": True, "project": project_snapshot(project), "build": result}


@app.get("/api/aura/projects/{project_id}/intelligence")
async def get_project_intelligence(project_id: str):
    project = get_project_or_404(project_id)
    research = project.research if isinstance(project.research, dict) else {}
    analysis = project.analysis if isinstance(project.analysis, dict) else {}
    claims = analysis.get("claim_register") or research.get("claim_register") or research.get("canonical_claims") or []
    findings = analysis.get("findings") or analysis.get("canonical_findings") or analysis.get("research_intelligence", {}).get("findings") or research.get("canonical_findings") or research.get("findings") or []
    coverage = analysis.get("claim_evidence_coverage_percent")
    if coverage is None and isinstance(analysis.get("claim_analysis"), dict):
        coverage = analysis["claim_analysis"].get("coverage_percent")
    if coverage is None:
        coverage = research.get("claim_evidence_coverage_percent", 0)
    return {"success": True, "claims": claims if isinstance(claims, list) else [], "findings": findings if isinstance(findings, list) else [], "claim_coverage_percent": float(coverage or 0), "evidence_count": len(project.evidence or []), "memory_count": len(project.memory or [])}


@app.get("/api/aura/projects/{project_id}/results")
async def get_project_results(project_id: str):
    project = get_project_or_404(project_id)
    workspace = Path(__file__).resolve().parent / "data" / "project_workspaces" / project_id
    if not workspace.exists():
        return {"success": True, "results": collect_results(project_id, workspace)}
    results = collect_results(project_id, workspace)
    project.experiments["results_summary"] = results
    project.validation["measured_results_available"] = results.get("proposed_executed", False)
    project.validation["scientific_validation"] = False
    project.validation["execution_truth"] = results.get("execution_truth")
    PROJECT_STORE[project_id] = project
    _save_project_store()
    return {"success": True, "results": results, "project": project_snapshot(project)}


@app.get("/api/aura/projects/{project_id}/executions")
async def get_executions(project_id: str):
    get_project_or_404(project_id)
    return {"success": True, "executions": list_executions(project_id)}


@app.post("/api/aura/projects/{project_id}/executions")
async def run_execution(project_id: str, request: ExecutionRequest):
    project = get_project_or_404(project_id)
    result = execute_task(project_id, request.task, request.timeout_seconds)
    project.experiments.setdefault("executions", []).append(result)
    project.validation.setdefault("execution_records", []).append({"execution_id": result.get("execution_id"), "task": request.task, "status": result.get("status"), "scientific_validation": False, "review_required": True})
    project.validation["execution_status"] = result.get("status")
    project.validation["results_verified"] = False
    project.validation["execution_truth"] = "Execution record exists, but scientific performance is not verified by this run."
    try:
        project.experiments["results_summary"] = collect_results(project_id, Path(__file__).resolve().parent / "data" / "project_workspaces" / project_id)
    except Exception:
        pass
    project.memory.append({"memory_id": "exec-" + result.get("execution_id", "unknown"), "type": "execution", "content": result})
    PROJECT_STORE[project_id] = project
    _save_project_store()
    return {"success": result.get("status") in {"EXECUTED"}, "execution": result, "project": project_snapshot(project)}

# ============================================================
# REAL DELIVERY FILE GENERATION
# ============================================================

def _flat_lines(value: Any, prefix: str = "", depth: int = 0) -> list[str]:
    if depth > 3:
        return [f"{prefix}: {str(value)[:600]}" if prefix else str(value)[:600]]
    if value is None:
        return [f"{prefix}: Not available." if prefix else "Not available."]
    if isinstance(value, (str, int, float, bool)):
        return [f"{prefix}: {value}" if prefix else str(value)]
    if isinstance(value, list):
        lines = []
        for i, item in enumerate(value[:30], 1):
            lines.extend(_flat_lines(item, f"{prefix} [{i}]" if prefix else f"[{i}]", depth + 1))
        return lines or [f"{prefix}: No records." if prefix else "No records."]
    if isinstance(value, dict):
        lines = []
        for key, item in list(value.items())[:40]:
            label = f"{prefix} / {key}" if prefix else str(key)
            lines.extend(_flat_lines(item, label, depth + 1))
        return lines or [f"{prefix}: No structured data." if prefix else "No structured data."]
    return [f"{prefix}: {str(value)}"]


def _delivery_sections(project: AURAProject, kind: str) -> list[tuple[str, Any]]:
    base = [("PROJECT", project.original_idea), ("PROJECT NAME", project.project_name)]
    if kind == "paper":
        return base + [("RESEARCH", project.research), ("ANALYSIS", project.analysis), ("INNOVATION", project.innovation), ("SOLUTION", project.solution), ("VALIDATION BOUNDARY", project.validation)]
    if kind == "presentation":
        return base + [("PROBLEM", project.analysis), ("EXISTING WORK", project.research), ("AURA VERDICT", project.analysis), ("INNOVATION", project.innovation), ("SOLUTION", project.solution), ("ARCHITECTURE", project.architecture), ("BUILD", project.development), ("EXPERIMENTS", project.experiments), ("VALIDATION", project.validation)]
    if kind == "sih":
        return base + [("PROBLEM & WHY IT MATTERS", project.analysis), ("PROPOSED SOLUTION", project.solution), ("INNOVATION", project.innovation), ("ARCHITECTURE", project.architecture), ("FEASIBILITY", project.development), ("VALIDATION PLAN", project.validation)]
    if kind == "demo":
        return base + [("DEMO OBJECTIVE", project.original_idea), ("ARCHITECTURE", project.architecture), ("INTELLIGENCE", project.innovation), ("BUILD", project.development), ("EXPERIMENT / VALIDATION", project.experiments), ("EXECUTION TRUTH", "A demonstration plan is not proof of scientific performance.")]
    if kind == "viva":
        return base + [("RESEARCH", project.research), ("ANALYSIS", project.analysis), ("INNOVATION", project.innovation), ("ARCHITECTURE", project.architecture), ("EXPERIMENTS", project.experiments), ("VALIDATION", project.validation)]
    return base + [("PROBLEM UNDERSTANDING", project.analysis.get("problem_understanding", project.analysis)), ("RESEARCH", project.research), ("SOLUTION", project.solution), ("ARCHITECTURE", project.architecture), ("DEVELOPMENT", project.development), ("EXPERIMENTS", project.experiments), ("VALIDATION", project.validation), ("EVIDENCE", project.evidence), ("MEMORY", project.memory)]


def _text_content(project: AURAProject, kind: str) -> str:
    title = {"report":"PROJECT REPORT","paper":"RESEARCH PAPER","presentation":"PRESENTATION","sih":"SIH / HACKATHON","demo":"DEMO SCRIPT","viva":"VIVA PREPARATION"}.get(kind, kind.upper())
    lines = ["AURA — " + title, "=" * 70, f"Project: {project.project_name}", f"Idea: {project.original_idea}", "", "EXECUTION TRUTH", "Prepared content is not proof of execution. Code, experiments and quantitative results are not claimed unless recorded as executed and verified.", ""]
    for heading, value in _delivery_sections(project, kind):
        lines += [heading, "-" * max(10, len(heading))]
        lines += _flat_lines(model_to_dict(value))[:120]
        lines.append("")
    return "\n".join(lines)


def _xml_escape(text: str) -> str:
    return html.escape(text, quote=False)


def _make_docx(title: str, text: str) -> bytes:
    paragraphs = []
    for line in text.splitlines():
        if not line.strip(): paragraphs.append("<w:p/>")
        else: paragraphs.append(f'<w:p><w:r><w:t xml:space="preserve">{_xml_escape(line[:500])}</w:t></w:r></w:p>')
    document = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>' + ''.join(paragraphs) + '<w:sectPr><w:pgSz w:w="12240" w:h="15840"/><w:pgMar w:top="720" w:right="720" w:bottom="720" w:left="720"/></w:sectPr></w:body></w:document>'
    content_types='<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>'
    rels='<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>'
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml',content_types); z.writestr('_rels/.rels',rels); z.writestr('word/document.xml',document)
    return out.getvalue()


def _make_pdf(text: str) -> bytes:
    lines=[ln[:105] for ln in text.splitlines()][:58]
    stream='BT\n/F1 9 Tf\n40 800 Td\n'
    for i,line in enumerate(lines):
        if i: stream += '0 -13 Td\n'
        safe=line.replace('\\','\\\\').replace('(','\\(').replace(')','\\)').encode('latin-1','replace').decode('latin-1')
        stream += f'({safe}) Tj\n'
    stream += 'ET'
    objs=[b'<< /Type /Catalog /Pages 2 0 R >>',b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',f'<< /Length {len(stream.encode())} >>\nstream\n{stream}\nendstream'.encode()]
    out=bytearray(b'%PDF-1.4\n'); offs=[0]
    for n,obj in enumerate(objs,1): offs.append(len(out)); out += f'{n} 0 obj\n'.encode()+obj+b'\nendobj\n'
    xref=len(out); out += f'xref\n0 {len(objs)+1}\n0000000000 65535 f \n'.encode(); out += b''.join(f'{o:010d} 00000 n \n'.encode() for o in offs[1:]); out += f'trailer\n<< /Size {len(objs)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF'.encode(); return bytes(out)


def _make_pptx(title: str, text: str) -> bytes:
    lines=[x for x in text.splitlines() if x.strip()][:28]
    runs=''.join(f'<a:p><a:r><a:rPr lang="en-US"/><a:t>{_xml_escape(x[:180])}</a:t></a:r></a:p>' for x in lines)
    slide=f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/><p:sp><p:nvSpPr><p:cNvPr id="2" name="Title"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr><p:spPr/><p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r><a:rPr lang="en-US" b="1" sz="2800"/><a:t>{_xml_escape(title)}</a:t></a:r></a:p>{runs}</p:txBody></p:sp></p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>'
    ct='<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/><Override PartName="/ppt/slides/slide1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/></Types>'
    pres='<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:sldMasterIdLst/><p:slideIdLst><p:sldId id="256" r:id="rId1" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"/></p:slideIdLst><p:sldSz cx="12192000" cy="6858000"/><p:notesSz cx="6858000" cy="9144000"/></p:presentation>'
    rels='<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide1.xml"/></Relationships>'
    rootrels='<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/></Relationships>'
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml',ct); z.writestr('_rels/.rels',rootrels); z.writestr('ppt/presentation.xml',pres); z.writestr('ppt/_rels/presentation.xml.rels',rels); z.writestr('ppt/slides/slide1.xml',slide)
    return out.getvalue()


@app.get("/api/aura/projects/{project_id}/deliverables/{kind}")
async def generate_deliverable(project_id: str, kind: str):
    project=get_project_or_404(project_id); kind=kind.lower().strip()
    if kind not in {"report","paper","presentation","sih","demo","viva","pdf","text"}: raise HTTPException(status_code=400, detail="Unsupported deliverable type.")
    content_kind="report" if kind in {"text","pdf"} else kind; text=_text_content(project,content_kind)
    safe=re.sub(r"[^A-Za-z0-9_-]+","_",project.project_name)[:70] or "AURA_Project"
    if kind=="text": media="text/plain; charset=utf-8"; data=text.encode(); filename=f"{safe}_AURA_Report.txt"
    elif kind in {"report","paper"}: media="application/vnd.openxmlformats-officedocument.wordprocessingml.document"; data=_make_docx(kind.upper(),text); filename=f"{safe}_{'Project_Report' if kind=='report' else 'Research_Paper'}.docx"
    elif kind=="pdf": media="application/pdf"; data=_make_pdf(text); filename=f"{safe}_Project_Report.pdf"
    elif kind in {"presentation","sih"}: media="application/vnd.openxmlformats-officedocument.presentationml.presentation"; data=_make_pptx(kind.upper(),text); filename=f"{safe}_{'Presentation' if kind=='presentation' else 'SIH_Pitch'}.pptx"
    elif kind=="demo": media="application/pdf"; data=_make_pdf(text); filename=f"{safe}_Demo_Script.pdf"
    else: media="application/pdf"; data=_make_pdf(text); filename=f"{safe}_Viva_Preparation.pdf"
    project.deliverables.setdefault("actual_file_generation",{})[kind]=True; project.deliverables["last_generated_type"]=kind; PROJECT_STORE[project_id]=project; _save_project_store()
    return Response(content=data,media_type=media,headers={"Content-Disposition":f'attachment; filename="{filename}"',"X-AURA-Generated":"true"})


@app.get("/api/aura/projects/{project_id}/package")
async def generate_project_package(project_id: str):
    project=get_project_or_404(project_id); safe=re.sub(r"[^A-Za-z0-9_-]+","_",project.project_name)[:70] or "AURA_Project"; out=io.BytesIO()
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr("PROJECT_DATA/aura_project.json",json.dumps(model_to_dict(project),indent=2,ensure_ascii=False))
        for kind in ["report","paper","presentation","sih","demo","viva"]:
            text=_text_content(project,kind)
            if kind in {"report","paper"}: data=_make_docx(kind.upper(),text); ext="docx"
            elif kind in {"presentation","sih"}: data=_make_pptx(kind.upper(),text); ext="pptx"
            else: data=_make_pdf(text); ext="pdf"
            z.writestr(f"{kind.upper()}/AURA_{kind}.{ext}",data)
        z.writestr("EVIDENCE/evidence_registry.json",json.dumps(model_to_dict(project.evidence),indent=2,ensure_ascii=False))
        z.writestr("EXPERIMENTS/experiment_plan.json",json.dumps(model_to_dict(project.experiments),indent=2,ensure_ascii=False))
        # Include the actual generated project workspace and execution artifacts when available.
        workspace = Path(__file__).resolve().parent / "data" / "project_workspaces" / project.project_id
        if workspace.exists():
            for path in workspace.rglob("*"):
                if path.is_file() and "executions" not in path.parts:
                    z.write(path, f"PROJECT_WORKSPACE/{path.relative_to(workspace).as_posix()}")
            for path in (workspace / "executions").glob("*.json") if (workspace / "executions").exists() else []:
                z.write(path, f"EXECUTION_RECORDS/{path.name}")
    project.deliverables.setdefault("actual_file_generation",{})["zip"]=True; PROJECT_STORE[project_id]=project; _save_project_store()
    return Response(content=out.getvalue(),media_type="application/zip",headers={"Content-Disposition":f'attachment; filename="{safe}_AURA_Project_Package.zip"',"X-AURA-Generated":"true"})

# ============================================================
# LEGACY / COMPATIBILITY RESEARCH ENDPOINT
# ============================================================


@app.post("/api/research/analyze")
async def analyze_research(
    request: ResearchRequest,
) -> dict[str, Any]:

    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Research question cannot be empty.",
        )

    try:
        project = aura_orchestrator.create_project(
            idea=question,
            project_name=None,
        )

        PROJECT_STORE[project.project_id] = project

        completed_project = await aura_orchestrator.run(
            project,
            stop_on_failure=True,
        )

        PROJECT_STORE[
            completed_project.project_id
        ] = completed_project

        return {
            "success": True,
            "agent": "AURA",
            "mode": "full_lifecycle",
            "project_id": completed_project.project_id,
            "project": project_snapshot(
                completed_project
            ),
            "pipeline": get_pipeline_status(
                completed_project
            ),
            "intelligence": build_legacy_intelligence(
                completed_project
            ),
            "blueprint": build_legacy_blueprint(
                completed_project
            ),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"AURA analysis failed: {exc}",
        )


# ============================================================
# LITERATURE SEARCH
# ============================================================


@app.post("/api/literature/search")
async def literature_search(
    request: LiteratureSearchRequest,
) -> dict[str, Any]:

    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty.",
        )

    if request.year_from > request.year_to:
        raise HTTPException(
            status_code=400,
            detail="year_from cannot be greater than year_to.",
        )

    if request.max_results < 1:
        raise HTTPException(
            status_code=400,
            detail="max_results must be at least 1.",
        )

    try:
        result = await search_literature(
            question=question,
            year_from=request.year_from,
            year_to=request.year_to,
            max_results=request.max_results,
        )

        return {
            "success": True,
            "question": question,
            "result": model_to_dict(result),
        }

    except TypeError:
        try:
            result = await search_literature(
                question,
                request.year_from,
                request.year_to,
                request.max_results,
            )

            return {
                "success": True,
                "question": question,
                "result": model_to_dict(result),
            }

        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Literature search failed: {exc}",
            )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Literature search failed: {exc}",
        )


# ============================================================
# LITERATURE ANALYSIS
# ============================================================


@app.post("/api/literature/analyze")
async def literature_analysis(
    request: LiteratureAnalysisRequest,
) -> dict[str, Any]:

    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty.",
        )

    if not isinstance(request.papers, list):
        raise HTTPException(
            status_code=400,
            detail="papers must be a list.",
        )

    try:
        result = analyze_literature(
            papers=request.papers,
            user_question=question,
        )

        if hasattr(result, "__await__"):
            result = await result

        return {
            "success": True,
            "question": question,
            "result": model_to_dict(result),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Literature analysis failed: {exc}",
        )


# ============================================================
# RESEARCH GAP ANALYSIS
# ============================================================


@app.post("/api/research/gap")
async def research_gap(
    request: ResearchGapRequest,
) -> dict[str, Any]:

    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty.",
        )

    try:
        result = analyze_research_gap(
            question=question,
            papers=request.papers,
        )

        if hasattr(result, "__await__"):
            result = await result

        return {
            "success": True,
            "question": question,
            "result": model_to_dict(result),
        }

    except TypeError:
        try:
            result = analyze_research_gap(
                question,
                request.papers,
            )

            if hasattr(result, "__await__"):
                result = await result

            return {
                "success": True,
                "question": question,
                "result": model_to_dict(result),
            }

        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Research gap analysis failed: {exc}",
            )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Research gap analysis failed: {exc}",
        )


# ============================================================
# AURA CAPABILITIES
# ============================================================


@app.get("/api/aura/capabilities")
async def aura_capabilities() -> dict[str, Any]:

    return {
        "name": "AURA",
        "version": APP_VERSION,
        "identity": (
            "AI Research, Innovation & Development "
            "Operating System"
        ),
        "core_principle": (
            "One idea in, connected project lifecycle out."
        ),
        "capabilities": [
            {
                "id": "idea_intelligence",
                "name": "Idea Intelligence",
                "stage": "understand",
            },
            {
                "id": "search_discovery",
                "name": "Search & Discovery",
                "stage": "investigate",
            },
            {
                "id": "research_analysis",
                "name": "Research & Existing Work Analysis",
                "stage": "analyze",
            },
            {
                "id": "novelty_gap",
                "name": "Novelty & Research Gap",
                "stage": "verdict",
            },
            {
                "id": "innovation",
                "name": "Innovation Engine",
                "stage": "innovate",
            },
            {
                "id": "solution",
                "name": "Solution Architect",
                "stage": "solution",
            },
            {
                "id": "architecture",
                "name": "System Architecture",
                "stage": "architect",
            },
            {
                "id": "development",
                "name": "Development & Code Planning",
                "stage": "build",
            },
            {
                "id": "experiments",
                "name": "Experiment Engine",
                "stage": "experiment",
            },
            {
                "id": "validation",
                "name": "Validation Engine",
                "stage": "validate",
            },
            {
                "id": "delivery",
                "name": (
                    "Report, Paper, PPT, Demo, "
                    "Viva & SIH Delivery"
                ),
                "stage": "deliver",
            },
            {
                "id": "project_memory",
                "name": "Project Memory",
                "stage": "cross_stage",
            },
            {
                "id": "evidence",
                "name": "Evidence & Trust Layer",
                "stage": "cross_stage",
            },
        ],
    }


# ============================================================
# ERROR HANDLER
# ============================================================


@app.exception_handler(Exception)
async def global_exception_handler(
    request: Any,
    exc: Exception,
) -> Any:

    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "AURA_INTERNAL_ERROR",
            "message": str(exc),
        },
    )


# ============================================================
# LOCAL ENTRY POINT
# ============================================================


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )