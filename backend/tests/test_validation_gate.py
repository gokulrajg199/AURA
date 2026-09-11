from fastapi.testclient import TestClient
import uuid
from main import app
from services.validation_gate import build_validation_gate, invalidate_validation


def test_validation_gate_blocks_without_controlled_experiment():
    project = {
        "project_id": "vg-1",
        "validation": {},
        "experiments": {"results_summary": {
            "proposed_executed": True,
            "proposed": {"metrics_available": True},
            "experiment": {"status": "NOT_AVAILABLE"},
        }},
    }
    gate = build_validation_gate(project, [{"status": "EXECUTED", "task": "evaluate_model"}])
    assert gate["ready"] is False
    assert any(c["id"] == "experiment" and not c["passed"] for c in gate["criteria"])


def test_validation_gate_ready_after_experiment_and_measurement():
    project = {
        "project_id": "vg-2",
        "validation": {},
        "experiments": {"results_summary": {
            "proposed_executed": True,
            "proposed": {"metrics_available": True},
            "experiment": {"status": "EXECUTED"},
        }},
    }
    gate = build_validation_gate(project, [
        {"status": "EXECUTED", "task": "experiment_run"},
        {"status": "EXECUTED", "task": "evaluate_model"},
    ])
    assert gate["ready"] is True


def test_new_execution_invalidates_previous_validation():
    project = {"validation": {"scientific_validation": True, "human_approved": True, "reviewed_at": "old", "reviewer_email": "a@example.com"}}
    invalidate_validation(project, "new execution")
    assert project["validation"]["scientific_validation"] is False
    assert project["validation"]["human_approved"] is False
    assert project["validation"]["invalidation_reason"] == "new execution"
    assert project["validation"]["review_history"][-1]["action"] == "INVALIDATED"
