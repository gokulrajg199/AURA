"""Fast, dependency-light AURA backend verification harness."""
from __future__ import annotations
import shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "backend"))
from fastapi.testclient import TestClient
import main

client = TestClient(main.app)
checks = []
def check(name, condition):
    checks.append((name, bool(condition)))
    print(f"[{'PASS' if condition else 'FAIL'}] {name}")

check("health", client.get("/health").status_code == 200)
check("pipeline", client.get("/api/aura/pipeline").status_code == 200)
check("stages", client.get("/api/aura/stages").status_code == 200)
check("capabilities", client.get("/api/aura/capabilities").status_code == 200)

created = client.post("/api/aura/projects", json={
    "idea": "AI based early detection of plant diseases using computer vision and IoT",
    "project_name": "AURA Verification",
})
check("project creation", created.status_code == 200)
pid = created.json()["project_id"] if created.status_code == 200 else None

if pid:
    check("project get", client.get(f"/api/aura/projects/{pid}").status_code == 200)
    check("project status", client.get(f"/api/aura/projects/{pid}/status").status_code == 200)
    check("intelligence", client.get(f"/api/aura/projects/{pid}/intelligence").status_code == 200)
    check("results before execution", client.get(f"/api/aura/projects/{pid}/results").status_code == 200)
    built = client.post(f"/api/aura/projects/{pid}/build")
    check("real workspace build", built.status_code == 200 and built.json().get("build", {}).get("files"))
    smoke = client.post(f"/api/aura/projects/{pid}/executions", json={"task":"smoke_test", "timeout_seconds":30})
    check("controlled smoke execution", smoke.status_code == 200 and smoke.json().get("execution", {}).get("status") == "EXECUTED")
    blocked = client.post(f"/api/aura/projects/{pid}/executions", json={"task":"dataset_prepare", "timeout_seconds":30})
    check("missing dataset is blocked", blocked.status_code == 200 and blocked.json().get("execution", {}).get("status") == "BLOCKED")
    results = client.get(f"/api/aura/projects/{pid}/results")
    check("results observatory truth boundary", results.status_code == 200 and results.json()["results"].get("scientific_validation") is False)
    for kind in ("report", "paper", "presentation", "sih", "demo", "viva", "pdf", "text"):
        r = client.get(f"/api/aura/projects/{pid}/deliverables/{kind}")
        check(f"deliverable {kind}", r.status_code == 200 and len(r.content) > 0)
    package = client.get(f"/api/aura/projects/{pid}/package")
    check("project package", package.status_code == 200 and package.content[:2] == b"PK")

    main.PROJECT_STORE.pop(pid, None)
    main._save_project_store()
    workspace = ROOT / "backend" / "data" / "project_workspaces" / pid
    if workspace.exists():
        shutil.rmtree(workspace)

failed = [name for name, ok in checks if not ok]
print(f"\n{len(checks)-len(failed)}/{len(checks)} checks passed")
if failed:
    print("Failed:", ", ".join(failed))
    raise SystemExit(1)
