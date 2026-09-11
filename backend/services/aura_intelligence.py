from __future__ import annotations

import re
from collections import Counter
from datetime import datetime, timezone
from typing import Any

STOP = {"the","and","for","with","that","this","from","into","using","based","system","project","design","develop","development","smart","ai","model","data","application","user","users"}


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]


def _keywords(text: str, limit: int = 12) -> list[str]:
    words = re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", text.lower())
    c = Counter(w for w in words if w not in STOP)
    return [w for w, _ in c.most_common(limit)]


def _domain_tags(text: str) -> list[str]:
    t = text.lower()
    mapping = {
        "Artificial Intelligence": ["ai", "artificial intelligence", "machine learning", "deep learning"],
        "Computer Vision": ["computer vision", "image", "object detection", "yolo", "segmentation"],
        "IoT": ["iot", "sensor", "esp32", "arduino", "mqtt", "embedded"],
        "Robotics": ["robot", "ros", "robotics", "slam", "manipulator"],
        "Smart Agriculture": ["hydroponic", "agriculture", "crop", "farm", "plant", "soil"],
        "Agentic AI": ["agentic", "multi-agent", "agent", "orchestrator", "autonomous"],
        "Data Science": ["analytics", "prediction", "forecast", "data science", "classification"],
        "Cybersecurity": ["security", "cyber", "intrusion", "malware", "authentication"],
    }
    return [name for name, terms in mapping.items() if any(term in t for term in terms)] or ["General Technology"]


def analyze_idea(idea: str, project_name: str | None = None) -> dict[str, Any]:
    idea = idea.strip()
    domains = _domain_tags(idea)
    keys = _keywords(idea)
    title = project_name or " ".join(w.capitalize() for w in idea.split()[:8])
    if len(title) > 90:
        title = title[:87] + "..."
    problem = f"Address the core problem described by the idea: {idea}. AURA will convert the concept into a measurable, evidence-backed engineering and research plan."
    objective = f"Design, implement, test and validate a solution for {idea}, with explicit evidence, provenance and reproducibility gates."
    users = ["Researchers", "Students / project teams", "Developers", "Project mentors", "Decision makers"]
    scope = [f"Research and evidence analysis in {', '.join(domains[:4])}", "Requirements and architecture", "Implementation and experiment planning", "Validation and delivery artifacts"]
    expected = ["Traceable project definition", "Evidence-backed claims and findings", "Executable development/experiment plan", "Validation-ready results and documentation"]
    functional = [
        "Create and version a project from an idea",
        "Collect and analyze research sources",
        "Extract evidence, claims and findings",
        "Identify research gaps and innovation opportunities",
        "Generate architecture, tasks, experiments and validation plans",
        "Track execution, results, provenance and approvals",
        "Generate reports, presentation and viva material",
    ]
    nonfunctional = [
        "Evidence provenance for important claims",
        "No fabricated execution metrics or validation results",
        "Role-based access and auditability",
        "Responsive, accessible and reduced-motion UI",
        "Recoverable persistent project memory",
        "Controlled execution boundaries and secure secrets handling",
    ]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "agent": "AURA Project Definition Agent",
        "truth_status": "DESIGNED",
        "project_definition": {
            "project_title": title,
            "problem_statement": problem,
            "objective": objective,
            "target_users": users,
            "scope": scope,
            "expected_outcome": expected,
            "functional_requirements": functional,
            "non_functional_requirements": nonfunctional,
        },
        "research_planning": {
            "literature_market_research": "Search peer-reviewed literature, standards, repositories and relevant market/technology sources before accepting novelty claims.",
            "existing_system_analysis": "Compare existing methods, products, datasets and architectures against the project objective.",
            "gap_identification": "Use evidence-backed limitations, contradictions and unaddressed requirements to form candidate gaps.",
            "proposed_solution": f"Evidence-guided solution for {idea}.",
            "architecture_design": "Layered architecture: interface → orchestration → intelligence → evidence/memory → execution → validation → delivery.",
            "technology_selection": ["Next.js / React", "FastAPI / Python", "SQLite or PostgreSQL", "Optional LLM provider", "Research APIs / web sources"],
            "feasibility_analysis": {"technical": "Assessable", "economic": "Assessable", "operational": "Assessable", "research": "Requires evidence review"},
        },
        "ui_ux": {
            "user_flow": ["Idea → Blueprint → Research → Evidence → Decision → Build → Experiment → Validate → Deliver"],
            "wireframes": "Generated as screen-level information architecture.",
            "ui_design": "Futuristic AURA Command Center with icon-based modules and evidence states.",
            "responsive_design": True,
            "navigation": ["Command Center", "AURA Blueprint", "Research", "Evidence", "Claims", "Graph", "Execution", "Validation", "Delivery", "Team", "Admin"],
            "states": ["loading", "error", "empty", "success", "blocked by evidence"],
            "accessibility": ["keyboard navigation", "semantic controls", "visible focus", "reduced motion"],
            "mobile_desktop": True,
        },
        "development": {
            "frontend": ["screens", "API integration", "form validation", "authentication", "error handling"],
            "backend": ["REST APIs", "business logic", "authorization", "database adapter", "file/document analysis", "validation", "audit logging"],
            "ai_ml": ["dataset gate", "preprocessing plan", "model plan", "training gate", "validation gate", "metrics", "inference integration"] if any(x in domains for x in ["Artificial Intelligence", "Computer Vision", "Data Science", "Smart Agriculture"]) else ["AI/ML marked not required until project scope demands it"],
        },
        "testing": {k: "PLANNED" for k in ["unit", "integration", "api", "ui", "database", "security", "performance", "responsive", "edge_cases", "user_acceptance"]},
        "evidence_validation": {
            "required": ["experimental results", "metrics", "baseline comparison", "screenshots", "graphs/charts", "test results", "limitations", "reproducibility"],
            "truth_boundary": "Designed functionality is not execution evidence. Measured results require actual execution and review.",
        },
        "deployment": ["frontend", "backend", "database", "environment variables", "deployment config", "domain/URL", "HTTPS", "monitoring", "backup/recovery"],
        "security": ["password hashing", "authentication", "authorization", "input validation", "CORS", "secret isolation", "SQL injection/XSS controls", "rate limiting", "audit logs"],
        "documentation": ["README", "SRS", "architecture", "ER/database design", "API docs", "user manual", "developer guide", "test report", "evaluation report", "deployment guide"],
        "github_repository": ["frontend", "backend", "ai-model", "database", "docs", "tests", "assets", ".env.example", ".gitignore", "README.md", "LICENSE", "docker-compose.yml"],
        "domains": domains,
        "keywords": keys,
        "completion_gates": [
            {"gate": "Definition", "status": "READY"},
            {"gate": "Research", "status": "EVIDENCE_REQUIRED"},
            {"gate": "Build", "status": "PLAN_REQUIRED"},
            {"gate": "Experiment", "status": "EXECUTION_REQUIRED"},
            {"gate": "Validation", "status": "MEASURED_EVIDENCE_REQUIRED"},
            {"gate": "Delivery", "status": "BLOCKED_UNTIL_VALIDATED"},
        ],
    }


def analyze_document(text: str, filename: str = "document") -> dict[str, Any]:
    text = text.strip()
    sentences = _sentences(text)
    lines = [x.strip() for x in text.splitlines() if x.strip()]
    headings = [x.lstrip("# ").strip() for x in lines if x.startswith("#")]
    claim_candidates = [s for s in sentences if any(k in s.lower() for k in ["shows", "demonstrates", "improves", "achieves", "proposes", "results", "accuracy", "performance"])]
    evidence_candidates = [s for s in sentences if any(k in s.lower() for k in ["dataset", "experiment", "table", "figure", "benchmark", "measured", "%", "accuracy", "f1", "rmse"])]
    return {
        "filename": filename,
        "characters": len(text), "words": len(re.findall(r"\b\w+\b", text)), "sentences": len(sentences),
        "headings": headings[:50], "keywords": _keywords(text, 20),
        "claim_candidates": claim_candidates[:50], "evidence_candidates": evidence_candidates[:50],
        "research_signals": {"has_methods": any("method" in s.lower() for s in sentences), "has_results": any("result" in s.lower() for s in sentences), "has_limitations": any("limitation" in s.lower() for s in sentences), "has_references": any("reference" in s.lower() or "doi" in s.lower() for s in lines)},
        "truth_status": "ANALYZED_TEXT_ONLY",
    }


def claim_analysis(claims: list[Any], evidence: list[Any]) -> dict[str, Any]:
    ev_text = [str(e.get("text", e) if isinstance(e, dict) else e).lower() for e in evidence]
    rows = []
    supported = 0
    for idx, c in enumerate(claims):
        text = str(c.get("text", c.get("claim", c)) if isinstance(c, dict) else c)
        tokens = {w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP and len(w) > 3}
        scores = []
        for e in ev_text:
            et = set(re.findall(r"[a-z0-9]+", e))
            scores.append(len(tokens & et) / max(1, len(tokens)))
        score = max(scores, default=0.0)
        status = "SUPPORTED" if score >= 0.35 else "WEAK_SUPPORT" if score >= 0.15 else "UNSUPPORTED"
        if status == "SUPPORTED": supported += 1
        rows.append({"id": f"claim-{idx+1}", "claim": text, "support_score": round(score, 3), "verification": status})
    return {"claims": rows, "coverage_percent": round((supported / len(rows)) * 100, 1) if rows else 0, "unsupported_claims": [r for r in rows if r["verification"] == "UNSUPPORTED"], "truth_rule": "Support score is an analytical heuristic, not scientific verification."}


def project_graph(project: dict[str, Any]) -> dict[str, Any]:
    nodes = [{"id": "project", "type": "project", "label": project.get("project_name", "AURA Project")}]
    edges = []
    sections = [("research", "research"), ("evidence", "evidence"), ("claims", "claim"), ("findings", "finding"), ("decision", "decision"), ("innovation", "innovation"), ("experiment", "experiment"), ("execution", "execution"), ("result", "result"), ("validation", "validation")]
    prev = "project"
    for key, typ in sections:
        value = project.get(key) or (project.get("analysis", {}).get(key) if isinstance(project.get("analysis"), dict) else None)
        if value:
            nid = f"{typ}-1"
            nodes.append({"id": nid, "type": typ, "label": typ.title(), "count": len(value) if isinstance(value, list) else 1})
            edges.append({"source": prev, "target": nid, "relationship": "produces"})
            prev = nid
    for i, domain in enumerate(project.get("domain", []) or []):
        did = f"domain-{i+1}"
        nodes.append({"id": did, "type": "domain", "label": domain})
        edges.append({"source": "project", "target": did, "relationship": "belongs_to"})
    return {"nodes": nodes, "edges": edges, "filters": sorted({n["type"] for n in nodes}), "truth_boundary": "Graph relationships are only asserted when represented in project state."}


def recommendations(project: dict[str, Any]) -> dict[str, Any]:
    domains = project.get("domain") or []
    recs = []
    for d in domains[:6]:
        recs.append({"title": f"Strengthen {d} evidence layer", "reason": f"Collect authoritative sources, datasets and benchmarks for {d} before novelty or performance claims.", "priority": "HIGH"})
    recs += [
        {"title": "Establish a baseline", "reason": "Every performance-oriented experiment needs a reproducible baseline before a proposed model can be judged.", "priority": "HIGH"},
        {"title": "Create a provenance chain", "reason": "Link research → evidence → claim → finding → decision → execution → validation.", "priority": "HIGH"},
        {"title": "Add human approval gates", "reason": "Scientific decisions and final claims should be reviewable before delivery.", "priority": "MEDIUM"},
    ]
    return {"recommendations": recs, "truth_status": "RECOMMENDATIONS_ARE_NOT_EXECUTION_RESULTS"}


def viva(project: dict[str, Any]) -> dict[str, Any]:
    title = project.get("project_name", "AURA Project")
    return {"title": f"Viva Pack — {title}", "questions": [
        {"q": "What problem does the project solve?", "answer": project.get("original_idea", "Define the problem and measurable objective.")},
        {"q": "Why is the proposed approach needed?", "answer": "Explain the evidence-backed gap and compare alternatives."},
        {"q": "What is novel?", "answer": "State only novelty supported by literature comparison; do not overclaim."},
        {"q": "What dataset or evidence supports the system?", "answer": "Identify the exact source, provenance, preprocessing and limitations."},
        {"q": "How was performance evaluated?", "answer": "Describe baseline, metrics, test protocol and actual execution evidence."},
        {"q": "What are the limitations?", "answer": "Report known technical, data, evaluation and deployment limitations."},
        {"q": "How is the system reproducible?", "answer": "Give versions, dependencies, configuration, data preparation and execution steps."},
    ], "truth_status": "VIVA_CONTENT_MUST_BE_UPDATED_FROM_VERIFIED_RESULTS"}
