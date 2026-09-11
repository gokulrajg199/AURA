import uuid
from pathlib import Path
from fastapi.testclient import TestClient
from main import app, PROJECT_DATA_DIR


def make_user(client):
    email = f"artifact-{uuid.uuid4().hex[:10]}@example.com"
    password = "TestPassword!123"
    assert client.post("/api/aura/auth/register", json={"email": email, "password": password}).status_code == 200
    login = client.post("/api/aura/auth/login", json={"email": email, "password": password})
    return email, {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_owned_artifacts_are_blocked_cross_user():
    c = TestClient(app)
    _, owner = make_user(c)
    _, other = make_user(c)
    created = c.post("/api/aura/projects", headers=owner, json={"idea":"Artifact security", "project_name":"Artifact Guard"})
    assert created.status_code == 200
    pid = created.json()["project"]["project_id"]

    # Create a controlled workspace fixture without invoking external execution.
    workspace = PROJECT_DATA_DIR / "project_workspaces" / pid
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "README.md").write_text("owned artifact", encoding="utf-8")
    (workspace / "executions").mkdir(exist_ok=True)
    (workspace / "executions" / "run.json").write_text("{}", encoding="utf-8")

    protected = [
        ("get", f"/api/aura/projects/{pid}/workspace"),
        ("get", f"/api/aura/projects/{pid}/workspace/archive"),
        ("get", f"/api/aura/projects/{pid}/workspace/file", {"path":"README.md"}),
        ("get", f"/api/aura/projects/{pid}/results"),
        ("get", f"/api/aura/projects/{pid}/package"),
        ("get", f"/api/aura/projects/{pid}/deliverables/report"),
        ("get", f"/api/aura/projects/{pid}/datasets"),
        ("get", f"/api/aura/projects/{pid}/evidence"),
    ]
    for method, url, *params in protected:
        response = getattr(c, method)(url, headers=other, params=params[0] if params else None)
        assert response.status_code == 403, (url, response.status_code, response.text)


def test_workspace_archive_does_not_follow_symlinks():
    c = TestClient(app)
    _, owner = make_user(c)
    created = c.post("/api/aura/projects", headers=owner, json={"idea":"Symlink archive", "project_name":"Symlink Guard"})
    assert created.status_code == 200
    pid = created.json()["project"]["project_id"]
    workspace = PROJECT_DATA_DIR / "project_workspaces" / pid
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "safe.txt").write_text("safe", encoding="utf-8")
    outside = workspace.parent / "outside-secret.txt"
    outside.write_text("must not escape", encoding="utf-8")
    link = workspace / "escape.txt"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        outside.unlink(missing_ok=True)
        return
    response = c.get(f"/api/aura/projects/{pid}/workspace/archive", headers=owner)
    assert response.status_code == 200
    import io, zipfile
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        names = z.namelist()
        assert "safe.txt" in names
        assert "escape.txt" not in names
    outside.unlink(missing_ok=True)
