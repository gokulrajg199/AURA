from __future__ import annotations
import csv, hashlib, io, json, zipfile
from pathlib import Path
from typing import Any

SUPPORTED = {'.csv','.json','.jsonl','.txt','.yaml','.yml','.jpg','.jpeg','.png','.webp','.mp4','.zip'}

def profile_bytes(filename: str, raw: bytes) -> dict[str, Any]:
    name = filename or 'dataset.bin'
    ext = Path(name).suffix.lower()
    result: dict[str, Any] = {
        'filename': name, 'extension': ext, 'size_bytes': len(raw),
        'sha256': hashlib.sha256(raw).hexdigest(), 'supported': ext in SUPPORTED,
        'quality_status': 'UNPROFILED', 'rows': None, 'columns': [], 'missing_values': {},
        'duplicate_rows': None, 'sample': [], 'archive_members': [],
        'truth_status': 'PROFILE_ONLY_NOT_SCIENTIFIC_VALIDATION'
    }
    if ext == '.csv':
        text = raw.decode('utf-8-sig', errors='replace')
        rows = list(csv.DictReader(io.StringIO(text)))
        cols = list(rows[0].keys()) if rows else []
        missing = {c: sum(1 for r in rows if not str(r.get(c,'')).strip()) for c in cols}
        signatures = [json.dumps(r, sort_keys=True) for r in rows]
        result.update(rows=len(rows), columns=cols, missing_values=missing,
                      duplicate_rows=len(signatures)-len(set(signatures)), sample=rows[:5])
        result['quality_status'] = 'READY' if rows and cols else 'BLOCKED'
    elif ext == '.json':
        try:
            obj = json.loads(raw.decode('utf-8-sig'))
            arr = obj if isinstance(obj,list) else [obj]
            result.update(rows=len(arr), columns=sorted({k for x in arr if isinstance(x,dict) for k in x}), sample=arr[:5])
            result['quality_status'] = 'READY' if arr else 'BLOCKED'
        except Exception as exc:
            result.update(quality_status='BLOCKED', error=str(exc))
    elif ext == '.jsonl':
        rows=[]
        for line in raw.decode('utf-8-sig',errors='replace').splitlines():
            if line.strip(): rows.append(json.loads(line))
        result.update(rows=len(rows), columns=sorted({k for x in rows if isinstance(x,dict) for k in x}), sample=rows[:5])
        result['quality_status'] = 'READY' if rows else 'BLOCKED'
    elif ext == '.zip':
        try:
            with zipfile.ZipFile(io.BytesIO(raw)) as z:
                result['archive_members'] = [x.filename for x in z.infolist() if not x.is_dir()][:1000]
                result['quality_status'] = 'READY' if result['archive_members'] else 'BLOCKED'
        except zipfile.BadZipFile as exc:
            result.update(quality_status='BLOCKED', error=str(exc))
    else:
        result['quality_status'] = 'READY_FOR_DOMAIN_PROCESSOR' if result['supported'] else 'BLOCKED'
    return result


def profile_workspace(workspace: Path) -> list[dict[str, Any]]:
    data = workspace / 'data'
    if not data.exists(): return []
    out=[]
    for p in sorted(data.iterdir()):
        if p.is_file() and p.suffix.lower() in SUPPORTED:
            try: out.append(profile_bytes(p.name, p.read_bytes()))
            except Exception as exc: out.append({'filename':p.name,'quality_status':'BLOCKED','error':str(exc)})
    return out
