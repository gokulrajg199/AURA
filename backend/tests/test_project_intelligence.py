from services.project_intelligence import build_project_intelligence


def test_project_intelligence_exposes_truth_twin_risk_and_next_action():
    project = {
        "project_id": "p1",
        "project_name": "CV test",
        "original_idea": "AI plant disease detection using computer vision",
        "analysis": {"requirements": ["dataset", "evaluation"]},
        "research": {},
        "evidence": [],
        "development": {},
        "validation": {},
        "deliverables": {},
    }
    lifecycle = {"profile": "computer_vision", "completion_percent": 20, "stages": [
        {"key":"research","label":"Research","status":"pending","order":4,"reason":"Source review required"},
        {"key":"implementation","label":"Implementation","status":"designed","order":9},
        {"key":"validation","label":"Validation","status":"pending","order":17,"reason":"Execution required"},
    ]}
    out = build_project_intelligence(project, lifecycle, [])
    assert out["project_twin"]["truth_status"] == "DESIGN IN PROGRESS"
    assert out["risk"]["level"] == "HIGH"
    assert out["next_best_action"]["stage"] == "research"
    assert out["decision_intelligence"]


def test_project_twin_persists_canonical_nodes_edges_and_context():
    from services.project_intelligence import build_persisted_project_twin
    project = {
        "project_id": "p-twin",
        "project_name": "IoT test",
        "original_idea": "Sensor monitoring",
        "current_stage": "research",
        "memory": [{"type": "uncertainty"}],
        "evidence": [{"id": "e1"}],
    }
    lifecycle = {"profile": "iot", "stages": [
        {"key": "research", "label": "Research", "status": "review"},
        {"key": "dataset", "label": "Dataset", "status": "pending"},
        {"key": "implementation", "label": "Implementation", "status": "designed"},
    ]}
    twin, context = build_persisted_project_twin(project, lifecycle, [{"status": "EXECUTED"}])
    assert twin["schema_version"] == "6.1-twin-1"
    assert twin["node_count"] == 18
    assert any(e["from"] == "research" and e["to"] == "evidence" for e in twin["edges"])
    assert "research" in twin["active_blockers"]
    assert context["profile"] == "iot"
    assert context["execution_count"] == 1
    assert context["uncertainty_count"] == 1
