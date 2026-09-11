from __future__ import annotations
import hashlib, json, platform, sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "6.1-reproducibility-lineage-1"
TRACKED = ("execution_contract.json", "artifacts/dataset_status.json", "artifacts/baseline_evaluation.json", "artifacts/evaluation.json", "artifacts/experiment_run.json", "artifacts/results_summary.json")

def _now() -> str: return datetime.now(timezone.utc).isoformat()

def _hash(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024), b""): h.update(chunk)
    return h.hexdigest()

def _json(path: Path) -> dict[str,Any]:
    try:
        v=json.loads(path.read_text(encoding="utf-8")); return v if isinstance(v,dict) else {}
    except Exception: return {}

def build_reproducibility_lineage(project: dict[str,Any], workspace: Path, executions: list[dict[str,Any]]|None=None) -> dict[str,Any]:
    executions=[e for e in (executions or []) if isinstance(e,dict)]
    files=[]
    for rel in TRACKED:
        p=workspace/rel
        if p.is_file():
            files.append({"path":rel,"sha256":_hash(p),"size":p.stat().st_size})
    contract=_json(workspace/"execution_contract.json")
    exp=project.get("experiments") if isinstance(project.get("experiments"),dict) else {}
    repro=exp.get("reproducibility") if isinstance(exp.get("reproducibility"),dict) else {}
    runs=[]
    for e in executions:
        if e.get("status")!="EXECUTED": continue
        artifact_rows=[]
        for a in e.get("artifacts") or []:
            if isinstance(a,dict): artifact_rows.append({k:a.get(k) for k in ("path","name","sha256","size") if a.get(k) is not None})
            elif isinstance(a,str): artifact_rows.append({"path":a})
        runs.append({"execution_id":e.get("execution_id"),"task":e.get("task"),"started_at":e.get("started_at"),"finished_at":e.get("finished_at"),"duration_seconds":e.get("duration_seconds"),"artifacts":artifact_rows,"artifact_count":len(artifact_rows)})
    env={"python":sys.version.split()[0],"platform":platform.platform(),"machine":platform.machine()}
    seed=repro.get("seed", contract.get("seed",42))
    requirements={"seed":seed,"environment_required":bool(repro.get("environment_required",True)),"artifact_hashes_required":bool(repro.get("artifact_hashes_required",True))}
    complete=bool(runs and files and requirements["environment_required"] and (not requirements["artifact_hashes_required"] or all(f.get("sha256") for f in files)))
    lineage_id=hashlib.sha256(json.dumps({"project_id":project.get("project_id"),"files":files,"runs":runs,"env":env,"seed":seed},sort_keys=True).encode()).hexdigest()[:16]
    return {"schema_version":SCHEMA,"generated_at":_now(),"lineage_id":lineage_id,"project_id":project.get("project_id"),"requirements":requirements,"environment":env,"tracked_files":files,"executions":runs,"reproducible_ready":complete,"reproduction_steps":["Use the recorded execution contract and environment requirements.","Use the same dataset/configuration inputs represented by the tracked artifacts.","Re-run the recorded execution tasks in lineage order.","Compare generated artifact hashes and metrics with the recorded results.","Submit reproduction evidence to the AURA validation gate for review."],"truth_status":"REPRODUCIBILITY_READY" if complete else "REPRODUCIBILITY_EVIDENCE_INCOMPLETE","truth_boundary":"A reproducibility package documents how to reproduce recorded execution; it does not establish scientific validity or replace human validation."}
