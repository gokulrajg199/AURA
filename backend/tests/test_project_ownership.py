import uuid
from fastapi.testclient import TestClient
from main import app


def user(client):
    email=f"owner-{uuid.uuid4().hex[:10]}@example.com"
    password="TestPassword!123"
    assert client.post("/api/aura/auth/register", json={"email":email,"password":password}).status_code == 200
    login=client.post("/api/aura/auth/login", json={"email":email,"password":password})
    return email, {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_authenticated_project_is_owned_and_cross_user_access_is_blocked():
    c=TestClient(app)
    email_a, h_a=user(c)
    created=c.post("/api/aura/projects", headers=h_a, json={"idea":"Owned AI project","project_name":"Owned"})
    assert created.status_code == 200
    pid=created.json()["project"]["project_id"]
    assert created.json()["project"]["owner_email"] == email_a

    assert c.get(f"/api/aura/projects/{pid}", headers=h_a).status_code == 200
    assert c.get(f"/api/aura/projects/{pid}").status_code == 401

    email_b, h_b=user(c)
    assert email_b != email_a
    assert c.get(f"/api/aura/projects/{pid}", headers=h_b).status_code == 403
    assert c.get(f"/api/aura/projects/{pid}/status", headers=h_b).status_code == 403


def test_guest_project_remains_ownerless_and_legacy_accessible():
    c=TestClient(app)
    created=c.post("/api/aura/projects", json={"idea":"Guest AI project","project_name":"Guest"})
    assert created.status_code == 200
    pid=created.json()["project"]["project_id"]
    assert created.json()["project"]["owner_id"] is None
    assert c.get(f"/api/aura/projects/{pid}").status_code == 200


def test_snapshot_cannot_transfer_owned_project_to_attacker_or_remove_owner():
    c=TestClient(app)
    email_a, h_a=user(c)
    created=c.post("/api/aura/projects", headers=h_a, json={"idea":"Protected project","project_name":"Protected"})
    assert created.status_code == 200
    pid=created.json()["project"]["project_id"]

    _, h_b=user(c)
    snapshot=created.json()["project"]
    snapshot["owner_id"] = 999999
    snapshot["owner_email"] = "attacker@example.com"
    snapshot["project_name"] = "Tampered"

    response=c.put(f"/api/aura/projects/{pid}/snapshot", headers=h_a, json=snapshot)
    assert response.status_code == 200
    restored=response.json()["project"]
    assert restored["owner_email"] == email_a
    assert restored["owner_id"] != 999999

    # The persisted owner must still block the other user after the snapshot.
    assert c.get(f"/api/aura/projects/{pid}", headers=h_b).status_code == 403

    snapshot["owner_id"] = None
    snapshot["owner_email"] = None
    response=c.put(f"/api/aura/projects/{pid}/snapshot", headers=h_a, json=snapshot)
    assert response.status_code == 200
    restored=response.json()["project"]
    assert restored["owner_email"] == email_a
