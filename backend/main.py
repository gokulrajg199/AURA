from __future__ import annotations

from typing import Any

import os
import html
import io
import json
import re
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from models.project import AURAProject
from orchestration.orchestrator import aura_orchestrator
from orchestration.stages import AURAStage, STAGE_ORDER

from services.literature.search import search_literature
from services.literature.analysis import analyze_literature
from services.research_gap.gap_engine import analyze_research_gap
from services.execution_engine import build_workspace, execute as execute_task, list_executions, BASE_DIR as WORKSPACE_BASE
from services.results_engine import collect_results, build_results_observatory
from services.validation_gate import build_validation_gate, invalidate_validation
from services.aura_intelligence import analyze_idea, analyze_document, claim_analysis, project_graph, recommendations, viva
from services import auth as auth_service
from services.universal_execution import build_contract, infer_capabilities, CAPABILITIES
from services.completion_engine import evaluate_completion
from services.lifecycle_engine import build_lifecycle
from services.document_extractor import extract_text
from services.platform import VERSION as PLATFORM_VERSION, TEMPLATES, AGENTS, analyze_project, health_score, file_manifest, record_version, environment_snapshot, sha256_bytes
from services.dataset_engine import profile_bytes, profile_workspace
from services.research_intelligence import synthesize as synthesize_research
from services.project_graph_engine import build_graph as build_provenance_graph
from services.traceability_engine import build_traceability
from services.innovation_traceability import build_innovation_traceability
from services.experiment_engine import create_plan as create_experiment_plan, compare as compare_experiments
from services.completeness_engine import certify as certify_platform
from services.report_engine import build_report, render_report_text
from services.project_intelligence import build_project_intelligence, refresh_persisted_project_twin
from services.decision_intelligence import build_decision_intelligence
from services.dependency_impact import propagate_dependency_impact
from services.requirements_audit import build_requirements_audit
from services.reproducibility_engine import build_reproducibility_lineage
from services import database as aura_db
from fastapi import UploadFile, File, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


# ============================================================
# AURA APPLICATION
# ============================================================

APP_NAME = "AURA"
APP_VERSION = PLATFORM_VERSION

security = HTTPBearer(auto_error=False)

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=(
        "AURA — AI Research, Innovation & Development Operating System. "
        "A connected autonomous project lifecycle from idea to validated delivery."
    ),
)


@app.middleware("http")
async def project_access_guard(request: Request, call_next):
    """Central ownership guard for every project-scoped API route.

    Guest-created projects remain explicitly ownerless. Once a project has an
    owner, every project-scoped request must present a valid session belonging
    to that owner, or an admin session. This keeps the legacy guest workflow
    while preventing cross-user access to authenticated projects.
    """
    path = request.url.path
    match = re.match(r"^/api/aura/projects/([^/]+)(?:/|$)", path)
    if not match or path == "/api/aura/projects":
        return await call_next(request)

    project_id = match.group(1)
    project = PROJECT_STORE.get(project_id)
    if project is None:
        return await call_next(request)

    owner_id = getattr(project, "owner_id", None)
    if owner_id is None:
        return await call_next(request)

    auth_header = request.headers.get("authorization", "")
    if not auth_header.lower().startswith("bearer "):
        return Response(
            content=json.dumps({"detail": "Authentication required for this project."}),
            status_code=401,
            media_type="application/json",
        )

    try:
        user = auth_service.verify(auth_header[7:].strip())
    except Exception:
        return Response(
            content=json.dumps({"detail": "Invalid authentication token"}),
            status_code=401,
            media_type="application/json",
        )

    if user.get("role") != "admin" and str(user.get("sub")) != str(owner_id):
        return Response(
            content=json.dumps({"detail": "You do not have access to this project."}),
            status_code=403,
            media_type="application/json",
        )

    return await call_next(request)


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
PROJECT_DATA_DIR = Path(os.getenv("AURA_DATA_DIR", str(Path(__file__).resolve().parent / "data")))
PROJECT_DATA_FILE = PROJECT_DATA_DIR / "projects.json"


def _save_project_store() -> None:
    """Persist project state to the configured durable database and keep a JSON backup."""
    PROJECT_DATA_DIR.mkdir(parents=True, exist_ok=True)
    for project_id, project in PROJECT_STORE.items():
        snap = project_snapshot(project)
        lifecycle = snap.get("lifecycle") or build_lifecycle(snap, list_executions(project_id))
        propagate_dependency_impact(snap)
        # Mirror deterministic impact/validation changes back into the Pydantic model before persistence.
        project.project_context = snap.get("project_context", {})
        project.validation = snap.get("validation", project.validation)
        refresh_persisted_project_twin(snap, lifecycle, list_executions(project_id))
        # Keep the in-memory Pydantic model synchronized with the persisted twin.
        project.project_twin = snap.get("project_twin", {})
        project.project_context = snap.get("project_context", {})
        aura_db.upsert_project(project_id, project_snapshot(project))
    payload = {project_id: project_snapshot(project) for project_id, project in PROJECT_STORE.items()}
    tmp = PROJECT_DATA_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(PROJECT_DATA_FILE)


def _load_project_store() -> None:
    """Restore projects from durable DB; migrate the legacy JSON store when needed."""
    try:
        raw = aura_db.load_projects()
        if raw:
            for project_id, data in raw.items():
                try:
                    PROJECT_STORE[project_id] = AURAProject.model_validate(data)
                except Exception:
                    continue
            return
    except Exception:
        pass
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
            if PROJECT_STORE:
                try: _save_project_store()
                except Exception: pass
    except Exception:
        return


# ============================================================
# REQUEST MODELS
# ============================================================

aura_db.init_db()
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


class ValidationReviewRequest(BaseModel):
    approved: bool
    reviewer_note: str = Field("", max_length=2000)


class CollaborationTaskRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    assignee: str = Field("", max_length=200)
    status: str = Field("TODO", max_length=40)


class CollaborationCommentRequest(BaseModel):
    comment: str = Field(..., min_length=1, max_length=4000)


class ResearchSynthesisRequest(BaseModel):
    question: str = Field(..., min_length=3)
    papers: list[dict[str, Any]] = Field(default_factory=list)

class ExperimentPlanRequest(BaseModel):
    name: str = Field("Primary Experiment", min_length=2, max_length=200)
    hypothesis: str = Field("The proposed approach should improve the declared objective against the baseline.", max_length=2000)
    metrics: list[str] = Field(default_factory=list)

class ExperimentCompareRequest(BaseModel):
    baseline: dict[str, Any] = Field(default_factory=dict)
    proposed: dict[str, Any] = Field(default_factory=dict)
    metrics: list[str] = Field(default_factory=list)


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
    """Return the project state plus the dynamically computed development lifecycle."""
    snapshot = model_to_dict(project)
    try:
        snapshot["lifecycle"] = build_lifecycle(snapshot, list_executions(project.project_id))
    except Exception:
        snapshot["lifecycle"] = {"profile":"general","stages":[],"completion_percent":0,"verified_stages":0,"total_stages":0,"completed":False}
    return snapshot


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
        "storage": aura_db.storage_info(),
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
    http_request: Request,
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
        # Authenticated creation becomes an owned project; unauthenticated
        # creation remains a deliberate guest/ownerless project.
        auth_header = http_request.headers.get("authorization", "").strip()
        if auth_header.lower().startswith("bearer "):
            auth_header = auth_header[7:].strip()
        else:
            auth_header = ""
        if auth_header:
            try:
                user = auth_service.verify(auth_header)
                project.owner_id = int(user["sub"])
                project.owner_email = user.get("email")
            except Exception:
                pass

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
    http_request: Request,
) -> dict[str, Any]:
    """Restore a browser-saved project without allowing ownership takeover."""
    existing = get_project_or_404(project_id)
    if project.project_id != project_id:
        project.project_id = project_id

    # Never trust owner fields from a browser snapshot. Preserve the persisted
    # owner identity from the server-side project record.
    existing_owner = getattr(existing, "owner_id", None)
    existing_email = getattr(existing, "owner_email", None)
    if existing_owner is not None:
        project.owner_id = existing_owner
        project.owner_email = existing_email
    else:
        # Ownerless/guest projects remain ownerless even when a client sends
        # fabricated ownership metadata.
        project.owner_id = None
        project.owner_email = None

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
    task: str = Field(..., pattern=r"^(smoke_test|project_test|dataset_prepare|train_model|evaluate_model|baseline_evaluate|experiment_run)$")
    timeout_seconds: int = Field(120, ge=1, le=300)


class VerificationRunRequest(BaseModel):
    use_development_fixture: bool = Field(False, description="Explicitly allow AURA to create a deterministic synthetic development fixture. It is never scientific evidence.")
    timeout_seconds: int = Field(180, ge=30, le=300)


@app.post("/api/aura/projects/{project_id}/verification/run")
async def run_complete_verification(project_id: str, request: VerificationRunRequest):
    """Run AURA's complete local engineering verification flow.

    This endpoint deliberately uses a clearly labelled deterministic synthetic
    fixture when explicitly enabled. It verifies the execution plumbing and
    produces measured development metrics, but it can never become scientific
    evidence or automatic validation.
    """
    project = get_project_or_404(project_id)
    if not request.use_development_fixture:
        raise HTTPException(status_code=400, detail="Explicitly set use_development_fixture=true. The fixture is for engineering verification only, not scientific evidence.")
    workspace = WORKSPACE_BASE / project_id
    required_scripts = ["project_test.py", "dataset_prepare.py", "train_model.py", "baseline_evaluate.py", "evaluate_model.py", "experiment_runner.py"]
    if (not workspace.exists()) or any(not (workspace / "scripts" / name).exists() for name in required_scripts):
        build = build_workspace(project_snapshot(project))
        project.development.setdefault("execution_engine", {})["workspace"] = build
        project.development["real_project_generated"] = True

    # The fixture is intentionally deterministic and profile-aware. It exercises
    # AURA's engineering pipeline without polluting a computer-vision project
    # with hydroponic sensor data or presenting synthetic metrics as science.
    profile = str(project_snapshot(project).get("analysis", {}).get("profile") or "").lower()
    profile = profile or str(project.development.get("execution_engine", {}).get("workspace", {}).get("profile", "general_ai")).lower()
    if profile in {"computer_vision", "cv", "vision"}:
        fixture = workspace / "artifacts" / "verification_fixture.json"
        fixture.parent.mkdir(parents=True, exist_ok=True)
        fixture_payload = {
            "type": "DEVELOPMENT_VERIFICATION_FIXTURE",
            "profile": "computer_vision",
            "deterministic": True,
            "scientific_evidence": False,
            "approved_scientific_dataset": False,
            "purpose": "Exercise the CV engineering pathway without inventing or storing a scientific image dataset.",
            "truth_boundary": "Synthetic development verification is never scientific project evidence."
        }
        fixture.write_text(json.dumps(fixture_payload, indent=2), encoding="utf-8")
    elif profile == "iot":
        data_dir = workspace / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        fixture = data_dir / "sensor_data.csv"
        import csv, math
        rows = []
        for i in range(160):
            ph = 5.5 + 0.7 * math.sin(i / 17)
            ec = 1.0 + 0.35 * math.cos(i / 13)
            tds = 520 + 120 * math.sin(i / 11)
            temperature = 22 + 3 * math.sin(i / 19)
            humidity = 58 + 12 * math.cos(i / 23)
            target = 0.8 * ph + 0.002 * ec * 100 + 0.001 * tds + 0.03 * temperature - 0.01 * humidity
            rows.append([f"2026-01-01T{i:04d}:00:00Z", round(ph, 5), round(ec, 5), round(tds, 5), round(temperature, 5), round(humidity, 5), round(target, 5)])
        with fixture.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["timestamp", "ph", "ec", "tds", "temperature", "humidity", "nutrient_target"])
            writer.writerows(rows)
        provenance = workspace / "artifacts" / "verification_fixture.json"
        provenance.parent.mkdir(exist_ok=True)
        provenance.write_text(json.dumps({"type":"DEVELOPMENT_VERIFICATION_FIXTURE","profile":"iot","rows":len(rows),"deterministic":True,"scientific_evidence":False,"approved_scientific_dataset":False,"purpose":"Exercise the IoT engineering pathway.","truth_boundary":"Synthetic development verification is never scientific project evidence."}, indent=2), encoding="utf-8")
    else:
        fixture = workspace / "artifacts" / "verification_fixture.json"
        fixture.parent.mkdir(parents=True, exist_ok=True)
        fixture.write_text(json.dumps({"type":"DEVELOPMENT_VERIFICATION_FIXTURE","profile":profile or "general_ai","deterministic":True,"scientific_evidence":False,"approved_scientific_dataset":False,"purpose":"Exercise the generic engineering pathway.","truth_boundary":"Synthetic development verification is never scientific project evidence."}, indent=2), encoding="utf-8")

    tasks = ["project_test", "dataset_prepare", "train_model", "baseline_evaluate", "evaluate_model", "experiment_run"]
    records = []
    for task in tasks:
        result = execute_task(project_id, task, request.timeout_seconds)
        records.append(result)
        project.experiments.setdefault("executions", []).append(result)
        project.memory.append({"memory_id": "verification-" + result.get("execution_id", "unknown"), "type": "verification", "content": result})
        if result.get("status") != "EXECUTED":
            break

    project.validation["execution_status"] = records[-1].get("status") if records else "NOT_RUN"
    project.validation["scientific_validation"] = False
    project.validation["human_approved"] = False
    project.validation["results_verified"] = False
    project.validation["execution_truth"] = "Complete engineering verification used a synthetic development fixture. Metrics are measured execution outputs, not scientific evidence."
    project.experiments["verification_fixture"] = str(fixture.relative_to(workspace)).replace("\\", "/")
    project.experiments["verification_fixture_scientific"] = False
    project.experiments["verification_flow"] = [r.get("task") for r in records]
    project.experiments["verification_passed"] = bool(records) and all(r.get("status") == "EXECUTED" for r in records)
    project.execution_contract = project.execution_contract or build_contract(project_snapshot(project))
    project.completion = evaluate_completion(project_snapshot(project), list_executions(project_id))
    PROJECT_STORE[project_id] = project
    _save_project_store()
    results = collect_results(project_id, workspace)
    results["development_verification"] = {
        "passed": project.experiments["verification_passed"],
        "scientific_evidence": False,
        "fixture": str(fixture.relative_to(workspace)).replace("\\", "/"),
        "tasks": [r.get("task") for r in records],
    }
    return {"success": project.experiments["verification_passed"], "verification": results["development_verification"], "executions": records, "results": results, "completion": project.completion, "project": project_snapshot(project)}


@app.get("/api/aura/projects/{project_id}/build")
async def get_build_status(project_id: str):
    project = get_project_or_404(project_id)
    workspace = PROJECT_DATA_DIR / "project_workspaces" / project_id
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


@app.get("/api/aura/requirements/audit")
async def requirements_audit():
    root = Path(__file__).resolve().parent.parent
    return {"success": True, "audit": build_requirements_audit(root)}


@app.get("/api/aura/projects/{project_id}/overview")
async def get_project_overview(project_id: str):
    project = get_project_or_404(project_id)
    snap = project_snapshot(project)
    lifecycle = build_lifecycle(snap, list_executions(project_id))
    intelligence = build_project_intelligence(snap, lifecycle, list_executions(project_id))
    return {"success": True, "overview": intelligence, "lifecycle": lifecycle}


@app.get("/api/aura/projects/{project_id}/decision-intelligence")
async def get_decision_intelligence(project_id: str):
    project = get_project_or_404(project_id)
    snap = project_snapshot(project)
    executions = list_executions(project_id)
    lifecycle = build_lifecycle(snap, executions)
    intelligence = build_project_intelligence(snap, lifecycle, executions)
    decision = build_decision_intelligence(snap, lifecycle, intelligence)
    return {"success": True, "decision_intelligence": decision}


@app.get("/api/aura/projects/{project_id}/twin")
async def get_project_twin(project_id: str):
    project = get_project_or_404(project_id)
    snap = project_snapshot(project)
    lifecycle = build_lifecycle(snap, list_executions(project_id))
    intelligence = build_project_intelligence(snap, lifecycle, list_executions(project_id))
    return {"success": True, "project_twin": intelligence.get("project_twin", {}), "truth": intelligence.get("truth", {})}


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


@app.get("/api/aura/projects/{project_id}/workspace")
async def get_project_workspace(project_id: str):
    get_project_or_404(project_id)
    workspace = PROJECT_DATA_DIR / "project_workspaces" / project_id
    if not workspace.exists():
        raise HTTPException(status_code=404, detail="Real project workspace has not been generated yet.")
    files = [str(p.relative_to(workspace)).replace("\\", "/") for p in workspace.rglob("*") if p.is_file()]
    return {"success": True, "project_id": project_id, "workspace": str(workspace), "files": sorted(files)}


@app.get("/api/aura/projects/{project_id}/workspace/archive")
async def archive_project_workspace(project_id: str):
    get_project_or_404(project_id)
    workspace = PROJECT_DATA_DIR / "project_workspaces" / project_id
    if not workspace.exists():
        raise HTTPException(status_code=404, detail="Real project workspace has not been generated yet.")
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        root = workspace.resolve()
        for path in workspace.rglob("*"):
            # Never package symlinks or files that resolve outside the project workspace.
            if not path.is_file() or path.is_symlink():
                continue
            resolved = path.resolve()
            if resolved != root and root not in resolved.parents:
                continue
            z.write(resolved, path.relative_to(workspace).as_posix())
    safe = re.sub(r"[^A-Za-z0-9_-]+", "_", get_project_or_404(project_id).project_name)[:60] or "AURA_Project"
    return Response(content=out.getvalue(), media_type="application/zip", headers={"Content-Disposition": f'attachment; filename="{safe}_workspace.zip"', "X-AURA-Generated": "true"})


@app.get("/api/aura/projects/{project_id}/workspace/file")
async def get_project_workspace_file(project_id: str, path: str):
    get_project_or_404(project_id)
    workspace = (PROJECT_DATA_DIR / "project_workspaces" / project_id).resolve()
    target = (workspace / path).resolve()
    if workspace not in target.parents and target != workspace:
        raise HTTPException(status_code=400, detail="Invalid workspace path.")
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="Workspace file not found.")
    if target.stat().st_size > 2_000_000:
        raise HTTPException(status_code=413, detail="Workspace file is too large to preview.")
    try:
        content = target.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        content = "[Binary or non-UTF-8 file — preview unavailable.]"
    return {"success": True, "path": path, "content": content}


@app.get("/api/aura/projects/{project_id}/dependency-impact")
async def get_dependency_impact(project_id: str):
    project = get_project_or_404(project_id)
    snapshot = project_snapshot(project)
    state = propagate_dependency_impact(snapshot)
    project.project_context = snapshot.get("project_context", {})
    PROJECT_STORE[project_id] = project
    _save_project_store()
    return {"success": True, "impact": state, "project": project_snapshot(project)}


@app.get("/api/aura/projects/{project_id}/results")
async def get_project_results(project_id: str):
    project = get_project_or_404(project_id)
    workspace = PROJECT_DATA_DIR / "project_workspaces" / project_id
    if not workspace.exists():
        return {"success": True, "results": collect_results(project_id, workspace)}
    results = collect_results(project_id, workspace)
    project.experiments["results_summary"] = results
    project.validation["measured_results_available"] = results.get("proposed_executed", False)
    invalidate_validation(project, "Results were refreshed; prior validation must be re-reviewed against the current measured state.")
    project.validation["execution_truth"] = results.get("execution_truth")
    PROJECT_STORE[project_id] = project
    _save_project_store()
    return {"success": True, "results": results, "project": project_snapshot(project)}


@app.get("/api/aura/projects/{project_id}/intelligence/unified")
async def get_unified_project_intelligence(project_id: str):
    """Return one read-consistent intelligence snapshot across the 6.1 control layers.

    This endpoint composes existing engines; it does not invent evidence or upgrade
    any state. Scientific completion remains gated by measured evidence and human approval.
    """
    project = get_project_or_404(project_id)
    executions = list_executions(project_id)
    snap = project_snapshot(project)
    lifecycle = build_lifecycle(snap, executions)
    impact = propagate_dependency_impact(snap)
    intelligence = build_project_intelligence(snap, lifecycle, executions)
    observatory = build_results_observatory(snap, PROJECT_DATA_DIR / "project_workspaces" / project_id, executions)
    gate = build_validation_gate(snap, executions)
    completion = evaluate_completion(snap, executions)
    return {
        "success": True,
        "schema_version": "6.1-unified-intelligence-1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project": snap,
        "lifecycle": lifecycle,
        "intelligence": intelligence,
        "dependency_impact": impact,
        "results_observatory": observatory,
        "validation_gate": gate,
        "completion": completion,
        "truth": {
            "workflow": lifecycle.get("completion_percent", 0),
            "scientific_validation": bool((snap.get("validation") or {}).get("scientific_validation") is True),
            "human_approval": bool((snap.get("validation") or {}).get("human_approved") is True),
            "completed": bool(completion.get("completed")),
            "boundary": "AURA never upgrades generated or designed work into measured, validated, or completed truth without the required evidence and approval.",
        },
    }


@app.get("/api/aura/projects/{project_id}/results/observatory")
async def get_results_observatory(project_id: str):
    project=get_project_or_404(project_id)
    workspace=PROJECT_DATA_DIR/"project_workspaces"/project_id
    observatory=build_results_observatory(project_snapshot(project),workspace,list_executions(project_id))
    project.experiments["results_observatory"]=observatory
    PROJECT_STORE[project_id]=project; _save_project_store()
    return {"success":True,"observatory":observatory,"project":project_snapshot(project)}

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
    invalidate_validation(project, "A new execution changed the evidence state; prior validation is no longer current.")
    project.validation["results_verified"] = False
    project.validation["execution_truth"] = "Execution record exists, but scientific performance is not verified by this run."
    try:
        project.experiments["results_summary"] = collect_results(project_id, PROJECT_DATA_DIR / "project_workspaces" / project_id)
    except Exception:
        pass
    project.memory.append({"memory_id": "exec-" + result.get("execution_id", "unknown"), "type": "execution", "content": result})
    project.execution_contract = project.execution_contract or build_contract(project_snapshot(project))
    boundary = project.execution_contract.setdefault("truth_boundary", {})
    if result.get("status") == "EXECUTED":
        boundary["executed"] = True
    if result.get("task") in {"evaluate_model", "baseline_evaluate", "experiment_run"} and result.get("status") == "EXECUTED":
        boundary["measured"] = bool(result.get("result_summary"))
    project.completion = evaluate_completion(project_snapshot(project), list_executions(project_id))
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


@app.get("/api/aura/projects/{project_id}/report/complete")
async def complete_project_report(project_id: str):
    project = get_project_or_404(project_id)
    report = build_report(model_to_dict(project))
    project.deliverables["complete_project_report"] = {
        "report_version": report.get("report_version"),
        "generated_at": report.get("generated_at"),
        "truth_status": report.get("truth_status"),
        "chapter_count": len(report.get("chapters", [])),
        "scientific_completion": report.get("scientific_completion", False),
    }
    PROJECT_STORE[project_id] = project
    _save_project_store()
    return {"success": True, "report": report, "project": project_snapshot(project)}


@app.get("/api/aura/projects/{project_id}/deliverables/{kind}")
async def generate_deliverable(project_id: str, kind: str):
    project=get_project_or_404(project_id); kind=kind.lower().strip()
    supported={"report","paper","presentation","sih","demo","viva","pdf","text","dataset_report","results_report","experiment_report","traceability_report","completion_report"}
    if kind not in supported: raise HTTPException(status_code=400, detail="Unsupported deliverable type.")
    safe=re.sub(r"[^A-Za-z0-9_-]+","_",project.project_name)[:70] or "AURA_Project"

    if kind in {"report","pdf","text","dataset_report","results_report","experiment_report","traceability_report","completion_report"}:
        report=build_report(model_to_dict(project))
        if kind in {"report","pdf","text","completion_report"}:
            text=render_report_text(report)
        elif kind=="dataset_report":
            text=_text_content(project,"report") + "\n\nDATASET REPORT\n" + json.dumps(report.get("datasets",[]),indent=2,ensure_ascii=False)
        elif kind=="results_report":
            text="AURA — RESULTS REPORT\n\n" + json.dumps(report.get("results",{}),indent=2,ensure_ascii=False)
        elif kind=="experiment_report":
            text="AURA — EXPERIMENT REPORT\n\n" + json.dumps((report.get("results",{}).get("experiment") or report.get("results",{})),indent=2,ensure_ascii=False)
        else:
            text="AURA — TRACEABILITY REPORT\n\n" + json.dumps({"evidence":model_to_dict(project.evidence),"lifecycle":report.get("lifecycle"),"completion":report.get("completion")},indent=2,ensure_ascii=False)

        if kind=="text":
            media="text/plain; charset=utf-8"; data=text.encode(); filename=f"{safe}_AURA_Complete_Project_Report.txt"
        else:
            media="application/vnd.openxmlformats-officedocument.wordprocessingml.document" if kind not in {"pdf","results_report"} else "application/pdf"
            data=_make_docx(kind.upper(),text) if media.startswith("application/vnd") else _make_pdf(text)
            suffix={"report":"Complete_Project_Report.docx","pdf":"Complete_Project_Report.pdf","dataset_report":"Dataset_Report.docx","results_report":"Results_Report.pdf","experiment_report":"Experiment_Report.docx","traceability_report":"Traceability_Report.docx","completion_report":"Completion_Report.docx"}.get(kind,"Report.docx")
            filename=f"{safe}_{suffix}"
    else:
        text=_text_content(project,kind)
        if kind in {"paper","presentation","sih"}:
            media="application/vnd.openxmlformats-officedocument.wordprocessingml.document" if kind=="paper" else "application/vnd.openxmlformats-officedocument.presentationml.presentation"
            data=_make_docx(kind.upper(),text) if kind=="paper" else _make_pptx(kind.upper(),text)
            filename=f"{safe}_{'Research_Paper.docx' if kind=='paper' else ('Presentation.pptx' if kind=='presentation' else 'SIH_Pitch.pptx')}"
        elif kind=="demo": media="application/pdf"; data=_make_pdf(text); filename=f"{safe}_Demo_Script.pdf"
        else: media="application/pdf"; data=_make_pdf(text); filename=f"{safe}_Viva_Preparation.pdf"

    project.deliverables.setdefault("actual_file_generation",{})[kind]=True
    project.deliverables["last_generated_type"]=kind
    PROJECT_STORE[project_id]=project; _save_project_store()
    return Response(content=data,media_type=media,headers={"Content-Disposition":f'attachment; filename="{filename}"',"X-AURA-Generated":"true"})


@app.get("/api/aura/projects/{project_id}/package")
async def generate_project_package(project_id: str):
    project=get_project_or_404(project_id); safe=re.sub(r"[^A-Za-z0-9_-]+","_",project.project_name)[:70] or "AURA_Project"; out=io.BytesIO()
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr("PROJECT_DATA/aura_project.json",json.dumps(model_to_dict(project),indent=2,ensure_ascii=False))
        for kind in ["report","paper","presentation","sih","demo","viva","dataset_report","results_report","experiment_report","traceability_report","completion_report"]:
            text=_text_content(project,kind)
            if kind in {"report","paper","dataset_report","experiment_report","traceability_report","completion_report"}:
                if kind=="report": text=render_report_text(build_report(model_to_dict(project)))
                elif kind=="dataset_report": text="AURA — DATASET REPORT\n\n"+json.dumps(build_report(model_to_dict(project)).get("datasets",[]),indent=2,ensure_ascii=False)
                elif kind=="results_report": text="AURA — RESULTS REPORT\n\n"+json.dumps(build_report(model_to_dict(project)).get("results",{}),indent=2,ensure_ascii=False)
                elif kind=="experiment_report": text="AURA — EXPERIMENT REPORT\n\n"+json.dumps(build_report(model_to_dict(project)).get("results",{}).get("experiment",{}),indent=2,ensure_ascii=False)
                elif kind=="traceability_report": text="AURA — TRACEABILITY REPORT\n\n"+json.dumps({"evidence":model_to_dict(project.evidence),"lifecycle":build_report(model_to_dict(project)).get("lifecycle"),"completion":build_report(model_to_dict(project)).get("completion")},indent=2,ensure_ascii=False)
                elif kind=="completion_report": text="AURA — COMPLETION REPORT\n\n"+json.dumps(build_report(model_to_dict(project)).get("completion",{}),indent=2,ensure_ascii=False)
                data=_make_docx(kind.upper(),text); ext="docx"
            elif kind=="results_report": data=_make_pdf(text); ext="pdf"
            elif kind in {"presentation","sih"}: data=_make_pptx(kind.upper(),text); ext="pptx"
            else: data=_make_pdf(text); ext="pdf"
            z.writestr(f"{kind.upper()}/AURA_{kind}.{ext}",data)
        z.writestr("EVIDENCE/evidence_registry.json",json.dumps(model_to_dict(project.evidence),indent=2,ensure_ascii=False))
        z.writestr("EXPERIMENTS/experiment_plan.json",json.dumps(model_to_dict(project.experiments),indent=2,ensure_ascii=False))
        # Include the actual generated project workspace and execution artifacts when available.
        workspace = PROJECT_DATA_DIR / "project_workspaces" / project.project_id
        if workspace.exists():
            root = workspace.resolve()
            for path in workspace.rglob("*"):
                if not path.is_file() or path.is_symlink() or "executions" in path.parts:
                    continue
                resolved = path.resolve()
                if resolved != root and root not in resolved.parents:
                    continue
                z.write(resolved, f"PROJECT_WORKSPACE/{path.relative_to(workspace).as_posix()}")
            execution_dir = workspace / "executions"
            if execution_dir.exists():
                for path in execution_dir.glob("*.json"):
                    if path.is_file() and not path.is_symlink():
                        resolved = path.resolve()
                        if resolved != root and root not in resolved.parents:
                            continue
                        z.write(resolved, f"EXECUTION_RECORDS/{path.name}")
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




@app.get("/api/aura/capabilities/registry")
async def capability_registry() -> dict[str, Any]:
    return {"version":"3.2", "capabilities":CAPABILITIES, "dynamic":True}

@app.post("/api/aura/projects/{project_id}/contract")
async def project_execution_contract(project_id: str) -> dict[str, Any]:
    project=get_project_or_404(project_id)
    contract=build_contract(project_snapshot(project))
    project.execution_contract=contract
    project.analysis["execution_contract"]=contract
    _save_project_store()
    return {"success":True,"project_id":project_id,"contract":contract}

@app.get("/api/aura/projects/{project_id}/health")
async def project_health(project_id: str) -> dict[str, Any]:
    project=get_project_or_404(project_id)
    executions=list_executions(project_id)
    failures=[e for e in executions if e.get("status") not in {"EXECUTED"}]
    return {"project_id":project_id,"status":"healthy" if not failures else "attention_required","execution_count":len(executions),"failed_or_blocked":len(failures),"latest_execution":executions[0] if executions else None}


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



# ============================================================
# AURA 2.0 — INTELLIGENCE / COLLABORATION / TRUST APIs
# ============================================================

class BlueprintRequest(BaseModel):
    idea: str = Field(..., min_length=3)
    project_name: str | None = None

class DocumentTextRequest(BaseModel):
    text: str = Field(..., min_length=20)
    filename: str = "document.txt"

class ClaimAnalysisRequest(BaseModel):
    claims: list[Any] = Field(default_factory=list)
    evidence: list[Any] = Field(default_factory=list)

class AuthRequest(BaseModel):
    email: str
    password: str = Field(..., min_length=8)
    role: str = "researcher"


def _auth_user(credentials: HTTPAuthorizationCredentials | None = Depends(security)):
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        return auth_service.verify(credentials.credentials)
    except Exception:
        # Never expose token parsing/signature internals to clients.
        raise HTTPException(status_code=401, detail="Invalid authentication token")


@app.post("/api/aura/blueprint")
async def generate_blueprint(request: BlueprintRequest):
    return {"success": True, "blueprint": analyze_idea(request.idea, request.project_name)}


@app.post("/api/aura/projects/{project_id}/blueprint")
async def project_blueprint(project_id: str):
    project = get_project_or_404(project_id)
    blueprint = analyze_idea(project.original_idea, project.project_name)
    project.memory.append({"type": "blueprint", "created_at": blueprint["generated_at"], "agent": blueprint["agent"]})
    project.analysis["aura_blueprint"] = blueprint
    PROJECT_STORE[project_id] = project
    _save_project_store()
    return {"success": True, "project_id": project_id, "blueprint": blueprint, "project": project_snapshot(project)}


@app.post("/api/aura/document/analyze")
async def document_analysis(request: DocumentTextRequest):
    return {"success": True, "analysis": analyze_document(request.text, request.filename)}


@app.post("/api/aura/document/upload")
async def document_upload(file: UploadFile = File(...)):
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Uploaded document is empty.")
    if len(raw) > 25 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Document upload exceeds the 25 MB safety limit.")
    try:
        text, extraction = extract_text(raw, file.filename or "document")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text extraction returned no readable text.")
    analysis = analyze_document(text, file.filename or "document")
    analysis["extraction"] = extraction
    analysis["truth_status"] = "ANALYZED_EXTRACTED_TEXT_ONLY"
    return {"success": True, "analysis": analysis}


@app.post("/api/aura/claims/analyze")
async def advanced_claim_analysis(request: ClaimAnalysisRequest):
    return {"success": True, "analysis": claim_analysis(request.claims, request.evidence)}


@app.get("/api/aura/projects/{project_id}/graph")
async def aura_project_graph(project_id: str):
    project = get_project_or_404(project_id)
    return {"success": True, "graph": project_graph(project_snapshot(project))}


@app.get("/api/aura/projects/{project_id}/recommendations")
async def aura_recommendations(project_id: str):
    project = get_project_or_404(project_id)
    return {"success": True, **recommendations(project_snapshot(project))}


@app.get("/api/aura/projects/{project_id}/viva")
async def aura_viva(project_id: str):
    project = get_project_or_404(project_id)
    return {"success": True, "viva": viva(project_snapshot(project))}


@app.get("/api/aura/projects/{project_id}/truth")
async def aura_truth(project_id: str):
    project = get_project_or_404(project_id)
    snapshot = project_snapshot(project)
    results = project.experiments.get("results_summary", {}) if isinstance(project.experiments, dict) else {}
    execution = bool(results.get("proposed_executed"))
    return {"success": True, "truth": {
        "execution_evidence": execution,
        "validation_verified": bool(project.validation.get("scientific_validation")),
        "measured_results": execution,
        "delivery_allowed": execution and bool(project.validation.get("scientific_validation")),
        "boundary": "AURA never upgrades designed plans into verified results without execution evidence and review.",
    }}


@app.post("/api/aura/auth/register")
async def aura_register(request: AuthRequest):
    # Public registration can never self-assign privileged roles.
    role = "researcher"
    try:
        return {"success": True, "user": auth_service.register(request.email, request.password, role)}
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@app.post("/api/aura/auth/login")
async def aura_login(request: AuthRequest):
    try:
        return {"success": True, **auth_service.login(request.email, request.password)}
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))


@app.get("/api/aura/auth/me")
async def aura_me(user=Depends(_auth_user)):
    return {"success": True, "user": user}


@app.get("/api/aura/collaboration/roles")
async def collaboration_roles():
    return {"success": True, "roles": [
        {"id":"admin","name":"Admin","permissions":["manage_users","manage_projects","approve_delivery"]},
        {"id":"researcher","name":"Researcher","permissions":["research","evidence","claims","findings","experiments"]},
        {"id":"project_manager","name":"Project Manager","permissions":["projects","tasks","milestones","delivery"]},
        {"id":"developer","name":"Developer","permissions":["build","execution","artifacts"]},
    ]}


@app.get("/api/aura/projects/{project_id}/validation/gate")
async def project_validation_gate(project_id: str, user=Depends(_auth_user)):
    project = get_project_or_404(project_id)
    gate = build_validation_gate(project_snapshot(project), list_executions(project_id))
    return {"success": True, "gate": gate, "validation": project.validation}


@app.post("/api/aura/projects/{project_id}/validation/review")
async def review_project_validation(project_id: str, request: ValidationReviewRequest, user=Depends(_auth_user)):
    project = get_project_or_404(project_id)
    if user.get("role") not in {"admin", "project_manager", "researcher"}:
        raise HTTPException(status_code=403, detail="Your role cannot approve validation.")
    gate = build_validation_gate(project_snapshot(project), list_executions(project_id))
    if request.approved and not gate.get("ready"):
        failed = [c["label"] for c in gate.get("criteria", []) if c.get("required") and not c.get("passed")]
        raise HTTPException(status_code=409, detail={"message": "Validation gate is not ready for scientific approval.", "failed_criteria": failed, "gate": gate})
    if not request.approved:
        invalidate_validation(project, "Human reviewer rejected validation or requested further work.")
    stamp = datetime.now(timezone.utc).isoformat()
    project.validation["scientific_validation"] = bool(request.approved)
    project.validation["human_approved"] = bool(request.approved)
    project.validation["reviewer_id"] = user.get("sub")
    project.validation["reviewer_email"] = user.get("email")
    project.validation["reviewer_note"] = request.reviewer_note
    project.validation["reviewed_at"] = stamp
    project.validation["results_verified"] = bool(request.approved and gate.get("ready"))
    project.validation.pop("invalidated_at", None)
    project.validation.pop("invalidation_reason", None)
    project.validation.setdefault("review_history", []).append({"action": "APPROVED" if request.approved else "REJECTED", "reviewer": user.get("email"), "note": request.reviewer_note, "at": stamp, "gate": gate})
    project.audit_log.append({"action": "validation_review", "approved": request.approved, "reviewer": user.get("email"), "at": stamp, "gate_ready": gate.get("ready")})
    project.completion = evaluate_completion(project_snapshot(project), list_executions(project_id))
    if project.completion.get("completed"):
        project.status = "completed"
        project.current_stage = AURAStage.DELIVER
    PROJECT_STORE[project_id] = project
    _save_project_store()
    return {"success": True, "validation": project.validation, "completion": project.completion, "project": project_snapshot(project)}


@app.get("/api/aura/projects/{project_id}/collaboration")
async def collaboration_state(project_id: str):
    project = get_project_or_404(project_id)
    return {"success": True, "tasks": project.deliverables.get("team_tasks", []), "comments": project.deliverables.get("team_comments", []), "members": project.deliverables.get("team_members", []), "roles": {"admin": ["manage_users", "approve_delivery"], "project_manager": ["manage_tasks", "manage_milestones", "delivery"], "researcher": ["research", "evidence", "experiments"], "developer": ["build", "execution", "artifacts"]}}


@app.post("/api/aura/projects/{project_id}/collaboration/tasks")
async def collaboration_task(project_id: str, request: CollaborationTaskRequest, user=Depends(_auth_user)):
    project = get_project_or_404(project_id)
    if user.get("role") not in {"admin", "project_manager", "researcher"}:
        raise HTTPException(status_code=403, detail="Your role cannot create project tasks.")
    task={"id":"task-" + uuid.uuid4().hex[:10], "title":request.title, "assignee":request.assignee, "status":request.status, "created_by":user.get("email"), "created_at":datetime.now(timezone.utc).isoformat()}
    project.deliverables.setdefault("team_tasks", []).append(task)
    project.audit_log.append({"action":"task_created", "task_id":task["id"], "actor":user.get("email"), "at":task["created_at"]})
    PROJECT_STORE[project_id]=project; _save_project_store()
    return {"success":True,"task":task,"tasks":project.deliverables["team_tasks"]}


@app.post("/api/aura/projects/{project_id}/collaboration/comments")
async def collaboration_comment(project_id: str, request: CollaborationCommentRequest, user=Depends(_auth_user)):
    project = get_project_or_404(project_id)
    comment={"id":"comment-" + uuid.uuid4().hex[:10], "comment":request.comment, "author":user.get("email"), "created_at":datetime.now(timezone.utc).isoformat()}
    project.deliverables.setdefault("team_comments", []).append(comment)
    PROJECT_STORE[project_id]=project; _save_project_store()
    return {"success":True,"comment":comment,"comments":project.deliverables["team_comments"]}


@app.get("/api/aura/projects/{project_id}/completion")
async def project_completion_status(project_id: str):
    project=get_project_or_404(project_id)
    completion=evaluate_completion(project_snapshot(project), list_executions(project_id))
    project.completion=completion
    PROJECT_STORE[project_id]=project; _save_project_store()
    return {"success":True,"completion":completion}


@app.get("/api/aura/projects/{project_id}/lifecycle")
async def project_lifecycle_status(project_id: str):
    project = get_project_or_404(project_id)
    lifecycle = build_lifecycle(model_to_dict(project), list_executions(project_id))
    return {"success": True, "lifecycle": lifecycle}


@app.get("/api/aura/capabilities/v2")
async def aura_capabilities_v2():
    return {"version":"2.0.0", "features": [
        "project-definition-agent","research-literature-intelligence","advanced-evidence-claim-analysis","interactive-research-graph","multi-agent-collaboration","experiment-validation","real-time-project-dashboard","document-analysis","innovation-gap-discovery","scientific-truth-boundary","project-recommendations","project-package-generation","viva-presentation-generation","web-research-integration","team-collaboration","role-based-authentication","persistent-memory","futuristic-ui"
    ]}


# ============================================================
# AURA 6.1 — COMPLETE PLATFORM / DATA / PROVENANCE / REPRODUCIBILITY
# ============================================================

class EvidenceCreateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=300)
    source: str = Field("user", max_length=500)
    evidence_type: str = Field("project", max_length=80)
    content: str = Field(..., min_length=1, max_length=12000)
    strength: str = Field("unreviewed", max_length=40)

class VersionRequest(BaseModel):
    reason: str = Field("manual checkpoint", min_length=2, max_length=300)

class TemplateApplyRequest(BaseModel):
    template_id: str = Field(..., min_length=2, max_length=80)

class DeliveryManifestRequest(BaseModel):
    include_workspace: bool = True

class ReviewRequest(BaseModel):
    approved: bool
    note: str = Field("", max_length=2000)
    record_id: str | None = Field(None, min_length=2, max_length=200)

@app.get("/api/aura/platform")
async def platform_status() -> dict[str, Any]:
    return {
        "name": APP_NAME, "version": APP_VERSION, "release": "AURA 6.1 INTELLIGENCE PLATFORM",
        "status": "operational", "environment": environment_snapshot(),
        "truth_boundary": "GENERATED != IMPLEMENTED != TESTED != EXECUTED != MEASURED != VALIDATED != COMPLETED",
        "completion_rule": "ALL_REQUIRED_PROJECT_GATES + VALID_EVIDENCE + SUCCESSFUL_VERIFICATION + REQUIRED_HUMAN_APPROVAL = COMPLETED",
    }

@app.get("/api/aura/agents")
async def agent_registry() -> dict[str, Any]:
    return {"success": True, "version": APP_VERSION, "agents":[{"id":a,"name":n,"stage":s,"status":"REGISTERED"} for a,n,s in AGENTS], "count":len(AGENTS)}

@app.get("/api/aura/templates")
async def project_templates() -> dict[str, Any]:
    return {"success":True,"templates":TEMPLATES,"count":len(TEMPLATES)}

@app.post("/api/aura/projects/{project_id}/analyzer")
async def project_analyzer(project_id: str):
    project=get_project_or_404(project_id)
    result=analyze_project(project_snapshot(project))
    project.analysis["project_analyzer"]=result
    project.execution_contract=build_contract(project_snapshot(project))
    project.analysis["execution_contract"]=project.execution_contract
    project.audit_log.append({"action":"project_analyzer","at":datetime.now(timezone.utc).isoformat(),"profile":result["profile"]})
    PROJECT_STORE[project_id]=project; _save_project_store()
    return {"success":True,"analysis":result,"contract":project.execution_contract,"project":project_snapshot(project)}

@app.post("/api/aura/projects/{project_id}/template")
async def apply_project_template(project_id: str, request: TemplateApplyRequest):
    project=get_project_or_404(project_id)
    template=TEMPLATES.get(request.template_id)
    if not template: raise HTTPException(status_code=404, detail=f"Unknown template '{request.template_id}'.")
    project.analysis["template"]={"id":request.template_id,**template,"applied_at":datetime.now(timezone.utc).isoformat()}
    project.analysis.setdefault("required_lifecycle_gates",template["stages"])
    project.audit_log.append({"action":"template_applied","template":request.template_id,"at":datetime.now(timezone.utc).isoformat()})
    PROJECT_STORE[project_id]=project; _save_project_store()
    return {"success":True,"template":template,"project":project_snapshot(project)}

@app.post("/api/aura/projects/{project_id}/dataset/upload")
async def upload_project_dataset(project_id: str, file: UploadFile = File(...)):
    project=get_project_or_404(project_id)
    raw=await file.read()
    if not raw: raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(raw)>250*1024*1024: raise HTTPException(status_code=413, detail="Dataset upload exceeds the 250 MB safety limit.")
    workspace=WORKSPACE_BASE/project_id
    if not workspace.exists(): build_workspace(project_snapshot(project))
    data_dir=workspace/"data"; data_dir.mkdir(parents=True,exist_ok=True)
    name=re.sub(r"[^A-Za-z0-9._-]","_",file.filename or "dataset.bin")
    ext=Path(name).suffix.lower()
    if ext not in {".csv",".json",".jsonl",".yaml",".yml",".zip",".jpg",".jpeg",".png",".webp",".mp4",".txt"}:
        raise HTTPException(status_code=400, detail=f"Unsupported dataset format: {ext or 'unknown'}")
    target=data_dir/name; target.write_bytes(raw)
    extracted=[]
    if ext == ".zip":
        # Safe extraction: never allow archive members to escape the workspace.
        try:
            with zipfile.ZipFile(io.BytesIO(raw)) as zf:
                root_resolved=data_dir.resolve()
                members = zf.infolist()
                if len(members) > 10000:
                    raise HTTPException(status_code=400, detail="Dataset archive contains too many files.")
                total_uncompressed = 0
                for member in members:
                    # Reject traversal and Unix symlink entries; a symlink inside an archive
                    # can otherwise redirect extraction outside the workspace.
                    mode = (member.external_attr >> 16) & 0o170000
                    if mode == 0o120000:
                        raise HTTPException(status_code=400, detail="Symlink entries are not allowed in dataset archives.")
                    if member.file_size > 500 * 1024 * 1024:
                        raise HTTPException(status_code=400, detail="Dataset archive contains an oversized file.")
                    total_uncompressed += member.file_size
                    if total_uncompressed > 500 * 1024 * 1024:
                        raise HTTPException(status_code=400, detail="Dataset archive expands beyond the 500 MB safety limit.")
                    member_target=(data_dir/member.filename).resolve()
                    if root_resolved != member_target and root_resolved not in member_target.parents:
                        raise HTTPException(status_code=400, detail="Unsafe archive path detected.")
                zf.extractall(data_dir)
                extracted=[m.filename for m in zf.infolist() if not m.is_dir()]
        except zipfile.BadZipFile:
            raise HTTPException(status_code=400, detail="Uploaded ZIP dataset is invalid.")
    manifest={"dataset_id":"ds-"+uuid.uuid4().hex[:12],"filename":name,"path":target.relative_to(workspace).as_posix(),"size":len(raw),"sha256":sha256_bytes(raw),"uploaded_at":datetime.now(timezone.utc).isoformat(),"approved_dataset":False,"scientific_evidence":False,"review_required":True,"extracted_files":extracted,"truth_status":"USER_UPLOADED_UNREVIEWED"}
    project.development.setdefault("datasets",[]).append(manifest)
    project.evidence.append({"evidence_id":"ev-"+uuid.uuid4().hex[:12],"type":"dataset_upload","title":name,"source":"user_upload","sha256":manifest["sha256"],"status":"UNREVIEWED","scientific_evidence":False,"created_at":manifest["uploaded_at"]})
    project.audit_log.append({"action":"dataset_uploaded","filename":name,"sha256":manifest["sha256"],"at":manifest["uploaded_at"]})
    PROJECT_STORE[project_id]=project; _save_project_store()
    return {"success":True,"dataset":manifest,"message":"Dataset stored as unreviewed input. Scientific approval is intentionally separate.","project":project_snapshot(project)}

@app.post("/api/aura/projects/{project_id}/datasets/review")
async def review_project_dataset(project_id: str, request: ReviewRequest, user=Depends(_auth_user)):
    project=get_project_or_404(project_id)
    if user.get("role") not in {"admin","project_manager","researcher"}: raise HTTPException(status_code=403, detail="Your role cannot review datasets.")
    datasets=project.development.get("datasets",[])
    if not datasets: raise HTTPException(status_code=404, detail="No uploaded dataset exists.")
    dataset = next((d for d in datasets if request.record_id and d.get("dataset_id") == request.record_id), None) if request.record_id else datasets[-1]
    if dataset is None:
        raise HTTPException(status_code=404, detail=f"Dataset '{request.record_id}' was not found.")
    dataset["approved_dataset"]=bool(request.approved); dataset["scientific_evidence"]=bool(request.approved); dataset["reviewed"]=True; dataset["reviewer"] = user.get("email"); dataset["review_note"]=request.note; dataset["reviewed_at"]=datetime.now(timezone.utc).isoformat()
    project.audit_log.append({"action":"dataset_review","approved":request.approved,"filename":dataset.get("filename"),"reviewer":user.get("email"),"at":dataset["reviewed_at"]})
    PROJECT_STORE[project_id]=project; _save_project_store()
    return {"success":True,"dataset":dataset,"project":project_snapshot(project)}

@app.get("/api/aura/projects/{project_id}/datasets")
async def list_project_datasets(project_id: str):
    project=get_project_or_404(project_id)
    return {"success":True,"datasets":project.development.get("datasets",[]),"count":len(project.development.get("datasets",[]))}

@app.post("/api/aura/projects/{project_id}/evidence")
async def register_project_evidence(project_id: str, request: EvidenceCreateRequest):
    project=get_project_or_404(project_id)
    record={"evidence_id":"ev-"+uuid.uuid4().hex[:12],"title":request.title,"source":request.source,"evidence_type":request.evidence_type,"content":request.content,"strength":request.strength,"created_at":datetime.now(timezone.utc).isoformat(),"reviewed":False,"scientific_evidence":False,"provenance_hash":sha256_bytes(request.content.encode())}
    project.evidence.append(record); project.audit_log.append({"action":"evidence_registered","evidence_id":record["evidence_id"],"at":record["created_at"]})
    PROJECT_STORE[project_id]=project; _save_project_store()
    return {"success":True,"evidence":record,"project":project_snapshot(project)}

@app.post("/api/aura/projects/{project_id}/evidence/review")
async def review_project_evidence(project_id: str, request: ReviewRequest, user=Depends(_auth_user)):
    project=get_project_or_404(project_id)
    if user.get("role") not in {"admin","project_manager","researcher"}: raise HTTPException(status_code=403, detail="Your role cannot review evidence.")
    evidence=project.evidence
    if not evidence: raise HTTPException(status_code=404, detail="No evidence records exist.")
    record = next((e for e in evidence if request.record_id and e.get("evidence_id") == request.record_id), None) if request.record_id else evidence[-1]
    if record is None:
        raise HTTPException(status_code=404, detail=f"Evidence '{request.record_id}' was not found.")
    record["reviewed"]=True; record["reviewed_at"]=datetime.now(timezone.utc).isoformat(); record["reviewer"]=user.get("email"); record["review_note"]=request.note; record["scientific_evidence"]=bool(request.approved); record["status"]="APPROVED" if request.approved else "REJECTED"
    project.audit_log.append({"action":"evidence_review","approved":request.approved,"evidence_id":record.get("evidence_id"),"reviewer":user.get("email"),"at":record["reviewed_at"]})
    PROJECT_STORE[project_id]=project; _save_project_store()
    return {"success":True,"evidence":record,"project":project_snapshot(project)}

@app.get("/api/aura/projects/{project_id}/evidence")
async def list_project_evidence(project_id: str):
    project=get_project_or_404(project_id)
    return {"success":True,"evidence":project.evidence,"count":len(project.evidence),"truth_status":"Evidence records are candidates until reviewed and provenance-verified."}

@app.post("/api/aura/projects/{project_id}/versions")
async def create_project_version(project_id: str, request: VersionRequest):
    project=get_project_or_404(project_id); snapshot=model_to_dict(project); version=record_version(snapshot,request.reason)
    project.deliverables.setdefault("versions",[]).append(version)
    project.audit_log.append({"action":"version_checkpoint","version_id":version["version_id"],"reason":request.reason,"at":version["created_at"]})
    PROJECT_STORE[project_id]=project; _save_project_store()
    return {"success":True,"version":version,"count":len(project.deliverables["versions"])}

@app.get("/api/aura/projects/{project_id}/versions")
async def list_project_versions(project_id: str):
    project=get_project_or_404(project_id)
    versions=project.deliverables.get("versions",[])
    return {"success":True,"versions":versions,"count":len(versions)}

@app.get("/api/aura/projects/{project_id}/reproducibility")
async def reproducibility_manifest(project_id: str):
    project=get_project_or_404(project_id); workspace=WORKSPACE_BASE/project_id
    return {"success":True,"manifest":{"generated_at":datetime.now(timezone.utc).isoformat(),"environment":environment_snapshot(),"project_id":project_id,"workspace":file_manifest(workspace),"executions":list_executions(project_id),"contract":project.execution_contract,"truth_status":"REPRODUCIBILITY_MANIFEST_OF_CURRENT_STATE"}}

@app.get("/api/aura/projects/{project_id}/reproducibility/lineage")
async def reproducibility_lineage(project_id: str):
    project=get_project_or_404(project_id)
    workspace=WORKSPACE_BASE/project_id
    lineage=build_reproducibility_lineage(project_snapshot(project), workspace, list_executions(project_id))
    project.experiments["reproducibility_lineage"]=lineage
    PROJECT_STORE[project_id]=project
    _save_project_store()
    return {"success":True,"lineage":lineage}

@app.get("/api/aura/projects/{project_id}/health-score")
async def project_health_score(project_id: str):
    project=get_project_or_404(project_id); lifecycle=build_lifecycle(model_to_dict(project),list_executions(project_id)); score=health_score(model_to_dict(project),lifecycle,list_executions(project_id))
    return {"success":True,"health":score,"lifecycle":lifecycle}

@app.post("/api/aura/projects/{project_id}/run-project")
async def run_project_engine(project_id: str, request: ExecutionRequest):
    project=get_project_or_404(project_id)
    profile=(project.analysis.get("project_analyzer",{}) or {}).get("profile") or (build_contract(project_snapshot(project)).get("capabilities",{}).get("primary") or ["research"])[0]
    task_order=["project_test","dataset_prepare","train_model","baseline_evaluate","evaluate_model","experiment_run"]
    records=[]
    for task in task_order:
        result=execute_task(project_id,task,request.timeout_seconds); records.append(result)
        if result.get("status")!="EXECUTED": break
    project.experiments["last_project_run"]={"profile":profile,"tasks":[r.get("task") for r in records],"completed":bool(records) and all(r.get("status")=="EXECUTED" for r in records),"at":datetime.now(timezone.utc).isoformat(),"scientific_validation":False}
    project.validation["execution_status"]=records[-1].get("status") if records else "NOT_RUN"
    project.completion=evaluate_completion(project_snapshot(project),list_executions(project_id))
    PROJECT_STORE[project_id]=project; _save_project_store()
    return {"success":bool(records) and all(r.get("status")=="EXECUTED" for r in records),"profile":profile,"executions":records,"completion":project.completion,"project":project_snapshot(project)}

@app.post("/api/aura/projects/{project_id}/delivery/manifest")
async def create_delivery_manifest(project_id: str, request: DeliveryManifestRequest):
    project=get_project_or_404(project_id); workspace=WORKSPACE_BASE/project_id
    lifecycle=build_lifecycle(model_to_dict(project),list_executions(project_id)); health=health_score(model_to_dict(project),lifecycle,list_executions(project_id))
    required=[s for s in lifecycle.get("stages",[]) if s.get("status")!="na"]
    manifest={"generated_at":datetime.now(timezone.utc).isoformat(),"project_id":project_id,"project_name":project.project_name,"profile":lifecycle.get("profile"),"health":health,"completion":project.completion,"required_gates":required,"artifacts":file_manifest(workspace) if request.include_workspace else [],"scientific_validation":bool(project.validation.get("scientific_validation")),"human_approved":bool(project.validation.get("human_approved")),"delivery_status":"APPROVED" if lifecycle.get("completed") and project.validation.get("scientific_validation") and project.validation.get("human_approved") else "BLOCKED_REVIEW_REQUIRED","truth_status":"Delivery manifest is not a scientific certificate."}
    project.deliverables["delivery_manifest"]=manifest; PROJECT_STORE[project_id]=project; _save_project_store()
    return {"success":True,"manifest":manifest}


@app.get("/api/aura/platform/certification")
async def platform_certification():
    return {"success": True, "certification": certify_platform(Path(__file__).resolve().parents[1])}

@app.get("/api/aura/projects/{project_id}/data/profile")
async def profile_project_data(project_id: str):
    project=get_project_or_404(project_id); workspace=WORKSPACE_BASE/project_id
    return {"success":True,"profiles":profile_workspace(workspace),"truth_status":"DATASET_PROFILING_IS_ENGINEERING_ANALYSIS_NOT_SCIENTIFIC_VALIDATION"}

@app.get("/api/aura/projects/{project_id}/research/intelligence")
async def research_intelligence(project_id: str):
    project=get_project_or_404(project_id)
    papers=project.research.get("papers",[]) if isinstance(project.research,dict) else []
    question=project.original_idea
    return {"success":True,"intelligence":synthesize_research(question,papers)}

@app.post("/api/aura/research/synthesize")
async def research_synthesis(request: ResearchSynthesisRequest):
    return {"success":True,"intelligence":synthesize_research(request.question,request.papers)}



@app.get("/api/aura/projects/{project_id}/innovation-traceability")
async def project_innovation_traceability(project_id: str):
    project = get_project_or_404(project_id)
    trace = build_innovation_traceability(model_to_dict(project), list_executions(project_id))
    return {"success": True, "traceability": trace}

@app.get("/api/aura/projects/{project_id}/traceability")
async def project_traceability(project_id: str):
    project = get_project_or_404(project_id)
    trace = build_traceability(model_to_dict(project), list_executions(project_id))
    return {"success": True, "traceability": trace}

@app.get("/api/aura/projects/{project_id}/graph/provenance")
async def provenance_graph(project_id: str):
    project=get_project_or_404(project_id); snap=model_to_dict(project); lifecycle=build_lifecycle(snap,list_executions(project_id))
    return {"success":True,"graph":build_provenance_graph(snap,lifecycle,list_executions(project_id))}

@app.post("/api/aura/projects/{project_id}/experiments/plan")
async def experiment_plan(project_id: str, request: ExperimentPlanRequest):
    project=get_project_or_404(project_id); contract=project.execution_contract or build_contract(project_snapshot(project))
    plan=create_experiment_plan(model_to_dict(project), contract.get("capabilities",{})); plan["name"]=request.name; plan["hypothesis"]=request.hypothesis
    if request.metrics: plan["metrics"]=list(dict.fromkeys(request.metrics))
    project.experiments.setdefault("plans",[]).append(plan); project.audit_log.append({"action":"experiment_plan_created","experiment_id":plan["experiment_id"],"at":datetime.now(timezone.utc).isoformat()})
    PROJECT_STORE[project_id]=project; _save_project_store()
    return {"success":True,"plan":plan,"project":project_snapshot(project)}

@app.post("/api/aura/projects/{project_id}/experiments/compare")
async def experiment_compare(project_id: str, request: ExperimentCompareRequest):
    get_project_or_404(project_id)
    metrics=request.metrics or list(dict.fromkeys(list(request.baseline.keys())+list(request.proposed.keys())))
    return {"success":True,"comparison":compare_experiments(request.baseline,request.proposed,metrics)}

@app.post("/api/aura/projects/{project_id}/run-complete-lifecycle")
async def run_complete_lifecycle(project_id: str):
    project=get_project_or_404(project_id)
    build=build_workspace(project_snapshot(project))
    tasks=["smoke_test","project_test","dataset_prepare","train_model","baseline_evaluate","evaluate_model","experiment_run"]
    records=[]
    for task in tasks:
        rec=execute_task(project_id,task)
        records.append(rec)
        if rec.get("status") not in {"EXECUTED"}:
            break
    lifecycle=build_lifecycle(model_to_dict(project),list_executions(project_id)); completion=evaluate_completion(model_to_dict(project),list_executions(project_id))
    return {"success":True,"workspace":build,"executions":records,"lifecycle":lifecycle,"completion":completion,"truth_status":"AUTOMATED_ENGINEERING_RUN_COMPLETES_ONLY_EXECUTABLE_GATES; SCIENTIFIC_COMPLETION_REQUIRES_REAL_EVIDENCE_AND_HUMAN_APPROVAL"}

@app.get("/api/aura/projects/{project_id}/readiness")
async def project_readiness(project_id: str):
    project=get_project_or_404(project_id); snap=model_to_dict(project); executions=list_executions(project_id); lifecycle=build_lifecycle(snap,executions); completion=evaluate_completion(snap,executions); health=health_score(snap,lifecycle,executions); workspace=WORKSPACE_BASE/project_id
    return {"success":True,"platform":certify_platform(Path(__file__).resolve().parents[1]),"project":{"id":project_id,"profile":lifecycle.get("profile"),"lifecycle":lifecycle,"completion":completion,"health":health,"datasets":profile_workspace(workspace),"executions":len(executions)},"truth_status":"READINESS IS NOT A SCIENTIFIC RESULT"}

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
# ============================================================
# AURA 2.0 — WEB RESEARCH ADAPTER
# ============================================================

class WebResearchRequest(BaseModel):
    query: str = Field(..., min_length=3)
    limit: int = Field(8, ge=1, le=20)


@app.post("/api/aura/research/web")
async def aura_web_research(request: WebResearchRequest):
    """Small provider-neutral public-web adapter. Sources are evidence candidates, not verified truth."""
    import urllib.parse
    import urllib.request
    query = urllib.parse.quote(request.query)
    url = f"https://api.crossref.org/works?query={query}&rows={request.limit}"
    try:
        with urllib.request.urlopen(url, timeout=12) as response:
            payload = json.loads(response.read().decode("utf-8"))
        items = []
        for item in payload.get("message", {}).get("items", []):
            title = (item.get("title") or ["Untitled"])[0]
            items.append({"title": title, "doi": item.get("DOI"), "published": item.get("published-print") or item.get("published-online"), "publisher": item.get("publisher"), "type": item.get("type"), "url": item.get("URL"), "source": "Crossref"})
        return {"success": True, "query": request.query, "results": items, "truth_status": "SOURCE_DISCOVERY_ONLY"}
    except Exception as exc:
        return {"success": False, "query": request.query, "results": [], "error": str(exc), "truth_status": "SOURCE_DISCOVERY_UNAVAILABLE"}
