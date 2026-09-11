from io import BytesIO
from zipfile import ZipFile
from fastapi.testclient import TestClient
from main import app


def _project(c):
    r = c.post('/api/aura/projects', json={'idea':'Upload limit test','project_name':'Limits'})
    assert r.status_code == 200
    return r.json()['project']['project_id']


def test_zip_rejects_too_many_members():
    c = TestClient(app)
    pid = _project(c)
    buf = BytesIO()
    with ZipFile(buf, 'w') as z:
        for i in range(10001):
            z.writestr(f'f{i}.txt', '')
    r = c.post(f'/api/aura/projects/{pid}/dataset/upload', files={'file': ('many.zip', buf.getvalue(), 'application/zip')})
    assert r.status_code == 400
    assert 'too many files' in r.json()['detail'].lower()
