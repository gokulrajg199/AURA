from fastapi.testclient import TestClient
import uuid

from main import app


def _client_with_user():
    c = TestClient(app)
    email = f"test-{uuid.uuid4().hex[:10]}@example.com"
    password = "TestPassword!123"
    assert c.post("/api/aura/auth/register", json={"email": email, "password": password}).status_code == 200
    login = c.post("/api/aura/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    return c, {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_evidence_review_is_id_scoped_and_unreviewed_records_remain_unverified():
    c, headers = _client_with_user()
    created = c.post("/api/aura/projects", json={"idea": "Generic AI project", "project_name": "Review Scope Test"})
    assert created.status_code == 200
    pid = created.json()["project"]["project_id"]

    e1 = c.post(f"/api/aura/projects/{pid}/evidence", json={"title": "Evidence A", "content": "A"}).json()["evidence"]
    e2 = c.post(f"/api/aura/projects/{pid}/evidence", json={"title": "Evidence B", "content": "B"}).json()["evidence"]
    reviewed = c.post(f"/api/aura/projects/{pid}/evidence/review", headers=headers, json={"record_id": e1["evidence_id"], "approved": True})
    assert reviewed.status_code == 200
    records = {x["evidence_id"]: x for x in reviewed.json()["project"]["evidence"]}
    assert records[e1["evidence_id"]]["scientific_evidence"] is True
    assert records[e2["evidence_id"]]["scientific_evidence"] is False


def test_lifecycle_does_not_promote_defined_or_generated_state_to_verified():
    c = TestClient(app)
    created = c.post("/api/aura/projects", json={"idea": "AI computer vision project", "project_name": "Truth Boundary Test"})
    assert created.status_code == 200
    pid = created.json()["project"]["project_id"]
    overview = c.get(f"/api/aura/projects/{pid}/overview")
    assert overview.status_code == 200
    data = overview.json()["overview"]
    assert data["truth"]["status"] != "VALIDATED"
    assert "GENERATED" in data["principle"] and "VALIDATED" in data["principle"]
