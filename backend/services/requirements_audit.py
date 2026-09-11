from __future__ import annotations

from pathlib import Path
from typing import Any
import json


AREAS = [
    ("foundation_functional_nonfunctional_traceability", ["backend/main.py", "backend/services/completeness_engine.py"]),
    ("intelligence_research_evidence_claim_chain", ["backend/services/research_intelligence.py", "backend/services/evidence/engine.py"]),
    ("frontend_research_surfaces", ["frontend/app/page.tsx", "frontend/app/globals.css"]),
    ("evidence_claim_provenance", ["backend/services/evidence/engine.py", "backend/services/project_graph_engine.py"]),
    ("agentic_ai", ["backend/agents", "backend/orchestration/orchestrator.py"]),
    ("decision_intelligence", ["backend/services/project_intelligence.py"]),
    ("innovation", ["backend/agents/innovation.py"]),
    ("execution", ["backend/services/universal_execution.py"]),
    ("validation", ["backend/services/completion_engine.py"]),
    ("project_graph", ["backend/services/project_graph_engine.py"]),
    ("database", ["backend/services/database.py"]),
    ("backend_api", ["backend/main.py"]),
    ("auth_users", ["backend/services/auth.py"]),
    ("security", ["backend/services/auth.py", "backend/main.py"]),
    ("ai_model_quality", ["backend/services/results_engine.py", "backend/services/project_intelligence.py"]),
    ("testing", ["backend/tests", "VERIFY_AURA_6_1.py"]),
    ("ui_ux", ["frontend/app/page.tsx", "frontend/app/globals.css"]),
    ("deployment", ["render.yaml", "backend/Dockerfile", "frontend/package.json"]),
    ("github", [".gitignore"]),
    ("documentation", ["AURA_6_1_MASTER_ARCHITECTURE.md", "AURA_6_1_DEVELOPMENT_STATUS.md"]),
    ("research_validation", ["backend/services/research_intelligence.py", "backend/services/evidence/engine.py"]),
    ("final_demonstration", ["backend/services/report_engine.py"]),
]


def _exists(root: Path, rel: str) -> bool:
    return (root / rel).exists()


def build_requirements_audit(root: Path) -> dict[str, Any]:
    rows = []
    for area, evidence in AREAS:
        present = [p for p in evidence if _exists(root, p)]
        missing = [p for p in evidence if p not in present]
        if not present:
            status = "MISSING"
        elif missing:
            status = "PARTIAL"
        else:
            status = "IMPLEMENTED"
        rows.append({"area": area, "status": status, "evidence": present, "missing_evidence": missing})

    atomic_source = root / "AURA_649_REQUIREMENTS_SOURCE.txt"
    atomic_available = atomic_source.exists()
    return {
        "audit_version": "6.1-requirements-audit",
        "area_count": len(rows),
        "areas": rows,
        "atomic_649": {
            "available": atomic_available,
            "status": "READY_FOR_ATOMIC_MAPPING" if atomic_available else "SOURCE_REQUIRED",
            "source": atomic_source.name if atomic_available else None,
            "message": (
                "Exact 649-item source loaded; atomic mapping can be evaluated."
                if atomic_available else
                "The exact 649-item checklist is not present. Area coverage must not be presented as 649/649."
            ),
        },
        "truth_rule": "Area implementation evidence is not equivalent to atomic requirement verification.",
        "summary": {
            "implemented": sum(r["status"] == "IMPLEMENTED" for r in rows),
            "partial": sum(r["status"] == "PARTIAL" for r in rows),
            "missing": sum(r["status"] == "MISSING" for r in rows),
        },
    }
