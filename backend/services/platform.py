from __future__ import annotations
import hashlib, json, os, platform, re, sys, time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.universal_execution import infer_capabilities, CAPABILITIES

VERSION = "6.1.0"
TEMPLATES = {
    "final_year_ai_ml": {"name":"Final-Year AI/ML Project", "profile":"ml_classification", "stages":["requirements","research","dataset","baseline","model","testing","experiment","validation","documentation","delivery"]},
    "computer_vision": {"name":"Computer Vision / YOLO", "profile":"computer_vision", "stages":["requirements","research","evidence","dataset","annotation","baseline","model","testing","experiment","results","validation","documentation","delivery"]},
    "iot": {"name":"IoT / Smart Agriculture", "profile":"iot", "stages":["requirements","research","evidence","data","hardware","testing","baseline","model","experiment","results","validation","documentation","delivery"]},
    "robotics": {"name":"Robotics / ROS", "profile":"robotics", "stages":["requirements","research","evidence","simulation","implementation","testing","experiment","results","validation","documentation","delivery"]},
    "research": {"name":"Research / Thesis", "profile":"research", "stages":["requirements","research","evidence","analysis","innovation","experiment","results","validation","documentation","delivery"]},
    "software": {"name":"Software / Web / API", "profile":"software", "stages":["requirements","architecture","implementation","testing","execution","security","performance","validation","documentation","delivery"]},
}

AGENTS = [
    ("project-definition-agent","Project Definition","requirements"),("research-literature-intelligence","Research Intelligence","research"),("evidence-claim-agent","Evidence & Claims","evidence"),("decision-agent","Decision Intelligence","verdict"),("innovation-agent","Innovation Discovery","innovate"),("solution-agent","Solution Design","solution"),("architecture-agent","Architecture","architect"),("build-agent","Build & Execution","build"),("experiment-agent","Experiment & Reproducibility","experiment"),("validation-agent","Validation & Quality","validate"),("delivery-agent","Delivery & Documentation","deliver"),("project-memory-agent","Project Memory","cross_stage"),("security-agent","Security & Risk","cross_stage")
]

def now() -> str: return datetime.now(timezone.utc).isoformat()

def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024), b""): h.update(chunk)
    return h.hexdigest()

def sha256_bytes(data: bytes) -> str: return hashlib.sha256(data).hexdigest()

def analyze_project(project: dict[str, Any]) -> dict[str, Any]:
    contract=infer_capabilities(project)
    profile=contract.primary[0] if contract.primary else "research"
    if profile not in CAPABILITIES: profile="research"
    matching=[(k,v) for k,v in CAPABILITIES.items() if k in contract.capabilities]
    return {"profile":profile,"capabilities":contract.capabilities,"accepted_data":contract.accepted_data,"metrics":contract.evaluation_metrics,"required_gates":contract.required_gates,"rationale":contract.rationale,"template_candidates":[k for k,v in TEMPLATES.items() if v["profile"] in contract.capabilities],"confidence":round(min(1.0,0.45+0.15*len(matching)),2),"truth_status":"ANALYSIS_ONLY"}

def health_score(project: dict[str, Any], lifecycle: dict[str, Any], executions: list[dict[str,Any]]) -> dict[str,Any]:
    stages=lifecycle.get("stages",[]); required=[s for s in stages if s.get("status")!="na"]
    verified=sum(bool(s.get("verified")) for s in required)
    executed=sum(e.get("status")=="EXECUTED" for e in executions)
    failed=sum(e.get("status") in {"FAILED","BLOCKED","BLOCKED_OR_FAILED"} for e in executions)
    evidence=len(project.get("evidence") or [])
    research=bool(project.get("research")); tests=any(e.get("task")=="project_test" and e.get("status")=="EXECUTED" for e in executions)
    validation=bool((project.get("validation") or {}).get("scientific_validation"))
    human=bool((project.get("validation") or {}).get("human_approved"))
    components={"lifecycle":round(35*verified/max(1,len(required)),1),"execution":min(20,executed*4),"evidence":min(15,evidence*1.5),"research":10 if research else 0,"testing":10 if tests else 0,"validation":5 if validation else 0,"human_approval":5 if human else 0}
    score=round(sum(components.values())-min(10,failed*2),1)
    if validation and human and lifecycle.get("completed"): score=100.0
    grade="A" if score>=90 else "B" if score>=75 else "C" if score>=60 else "D" if score>=40 else "E"
    return {"score":max(0,score),"grade":grade,"components":components,"executions":executed,"failures":failed,"scientific_validation":validation,"human_approval":human,"truth_status":"PROJECT_HEALTH_ESTIMATE_NOT_SCIENTIFIC_VALIDATION"}

def environment_snapshot() -> dict[str,Any]:
    return {"python":sys.version.split()[0],"platform":platform.platform(),"aura_version":VERSION,"pid":os.getpid()}

def file_manifest(root: Path) -> list[dict[str,Any]]:
    if not root.exists(): return []
    out=[]
    for p in sorted(root.rglob("*")):
        if p.is_file() and ".git" not in p.parts:
            out.append({"path":p.relative_to(root).as_posix(),"size":p.stat().st_size,"sha256":sha256_file(p)})
    return out

def record_version(project: dict[str,Any], reason: str) -> dict[str,Any]:
    snapshot={k:v for k,v in project.items() if k not in {"completion","lifecycle"}}
    record={"version_id":"v-"+hashlib.sha256((reason+now()).encode()).hexdigest()[:12],"created_at":now(),"reason":reason,"snapshot_sha256":hashlib.sha256(json.dumps(snapshot,sort_keys=True,default=str).encode()).hexdigest(),"snapshot":snapshot}
    return record
