from services.completion_engine import evaluate_completion
from services.project_intelligence import build_project_intelligence
from services.results_engine import build_results_observatory
from services.validation_gate import build_validation_gate


def test_unified_layers_preserve_truth_boundary():
    project = {
        "project_id": "u1",
        "project_name": "Unified test",
        "original_idea": "A general AI project",
        "analysis": {"requirements": ["evaluation"]},
        "research": {}, "evidence": [], "development": {},
        "experiments": {}, "validation": {}, "deliverables": {},
    }
    executions = []
    lifecycle = {"profile": "general", "completion_percent": 20, "stages": [
        {"key": "research", "label": "Research", "status": "pending", "order": 4, "reason": "Review required"},
        {"key": "validation", "label": "Validation", "status": "pending", "order": 17, "reason": "Execution required"},
    ]}
    intelligence = build_project_intelligence(project, lifecycle, executions)
    gate = build_validation_gate(project, executions)
    completion = evaluate_completion(project, executions)
    observatory = build_results_observatory(project, __import__('pathlib').Path('/tmp/nonexistent-aura-workspace'), executions)
    assert intelligence["truth"]["scientific_validation"] is False
    assert gate["ready"] is False
    assert completion["completed"] is False
    assert observatory["review_status"] == "REVIEW_REQUIRED"
    assert "scientific validation" in observatory["truth"].lower()
