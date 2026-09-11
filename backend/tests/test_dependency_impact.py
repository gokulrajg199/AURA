from services.dependency_impact import propagate_dependency_impact


def base_project():
    return {
        "project_id": "impact-1",
        "project_name": "Impact Test",
        "original_idea": "Build a classifier",
        "domain": ["ai"],
        "requirements": ["r1"],
        "objectives": ["o1"],
        "constraints": [],
        "research": {"papers": ["p1"]},
        "evidence": [{"id": "e1"}],
        "innovation": {"x": 1},
        "solution": {"x": 1},
        "architecture": {"x": 1},
        "development": {"x": 1},
        "execution_contract": {},
        "experiments": {"x": 1},
        "validation": {},
        "deliverables": {},
        "project_context": {},
    }


def test_first_persistence_establishes_baseline_without_impact():
    project = base_project()
    state = propagate_dependency_impact(project)
    assert state["changed_nodes"] == []
    assert project["project_context"]["dependency_fingerprints"]


def test_requirements_change_propagates_to_downstream_nodes():
    project = base_project()
    propagate_dependency_impact(project)
    project["requirements"].append("r2")
    state = propagate_dependency_impact(project)
    assert "requirements" in state["changed_nodes"]
    assert "research" in state["impacted_nodes"]
    assert "validation" in state["impacted_nodes"]
    assert "delivery" in state["impacted_nodes"]
    assert state["requires_reexecution"] is True


def test_upstream_change_invalidates_existing_scientific_approval():
    project = base_project()
    propagate_dependency_impact(project)
    project["validation"] = {"scientific_validation": True, "human_approved": True, "results_verified": True}
    # Validation itself is changed by adding the approval; that should not be
    # treated as an upstream scientific change. Change implementation instead.
    propagate_dependency_impact(project)
    project["development"]["x"] = 2
    state = propagate_dependency_impact(project)
    assert "implementation" in state["changed_nodes"]
    assert project["validation"]["scientific_validation"] is False
    assert project["validation"]["human_approved"] is False
    assert project["validation"]["results_verified"] is False
