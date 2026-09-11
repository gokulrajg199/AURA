from io import BytesIO
from zipfile import ZipFile
from fastapi.testclient import TestClient
from main import app


def test_dataset_zip_rejects_symlink_entries():
    c = TestClient(app)
    project = c.post('/api/aura/projects', json={'idea':'Security upload test','project_name':'Archive Safety'}).json()['project']
    pid = project['project_id']
    buf = BytesIO()
    with ZipFile(buf, 'w') as z:
        info = z.getinfo(z.writestr('safe.txt', 'ok')) if False else None
        symlink = __import__('zipfile').ZipInfo('link')
        symlink.create_system = 3
        symlink.external_attr = (0o120777 << 16)
        z.writestr(symlink, '../../outside.txt')
    resp = c.post(f'/api/aura/projects/{pid}/dataset/upload', files={'file': ('bad.zip', buf.getvalue(), 'application/zip')})
    assert resp.status_code == 400
    assert 'Symlink' in resp.json()['detail']
