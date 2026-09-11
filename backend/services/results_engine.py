from __future__ import annotations
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
        return value if isinstance(value, dict) else None
    except Exception:
        return None


def _metric_value(data: dict[str, Any] | None, key: str) -> float | None:
    if not isinstance(data, dict): return None
    metrics = data.get('metrics') if isinstance(data.get('metrics'), dict) else data
    value = metrics.get(key) if isinstance(metrics, dict) else None
    try: return float(value) if value is not None else None
    except (TypeError, ValueError): return None


def collect_results(project_id: str, workspace_root: Path) -> dict[str, Any]:
    art = workspace_root / 'artifacts'
    dataset = _load(art / 'dataset_status.json')
    training = _load(art / 'training_status.json')
    proposed = _load(art / 'evaluation.json')
    baseline = _load(art / 'baseline_evaluation.json')
    experiment = _load(art / 'experiment_run.json')

    comparison: dict[str, Any] = {}
    # Evaluation is driven by the project's universal capability contract.
    # Never assume a CV metric family merely because a project is not IoT.
    contract = _load(workspace_root / "execution_contract.json") or {}
    capabilities = contract.get("capabilities") if isinstance(contract, dict) else {}
    metrics = capabilities.get("evaluation_metrics") if isinstance(capabilities, dict) else None
    if not isinstance(metrics, list) or not metrics:
        metrics = ["tests_passed", "coverage", "latency_ms", "error_rate"]
    metrics = [str(m) for m in metrics]
    if baseline and proposed and baseline.get('metrics_available') and proposed.get('metrics_available'):
        for metric in metrics:
            b = _metric_value(baseline, metric); p = _metric_value(proposed, metric)
            if b is not None and p is not None:
                comparison[metric] = {'baseline': b, 'proposed': p, 'delta': p - b, 'relative_change_percent': ((p-b)/b*100) if b != 0 else None}
    elif proposed and proposed.get('metrics_available'):
        for metric in metrics:
            p = _metric_value(proposed, metric)
            if p is not None: comparison[metric] = {'baseline': None, 'proposed': p, 'delta': None, 'relative_change_percent': None}

    status = 'NOT_EXECUTED'
    if proposed and proposed.get('status') == 'EXECUTED' and proposed.get('metrics_available'):
        status = 'RESULTS_AVAILABLE_REVIEW_REQUIRED'
    elif experiment and experiment.get('status') == 'EXECUTED':
        status = 'EXPERIMENT_EXECUTED_REVIEW_REQUIRED'
    elif training and training.get('status') == 'EXECUTED':
        status = 'TRAINING_EXECUTED_EVALUATION_PENDING'
    elif dataset and dataset.get('status') == 'READY':
        status = 'DATASET_READY_EXECUTION_PENDING'

    return {
        'project_id': project_id,
        'generated_at': _now(),
        'status': status,
        'dataset': dataset or {'status': 'NOT_AVAILABLE'},
        'training': training or {'status': 'NOT_AVAILABLE'},
        'baseline': baseline or {'status': 'NOT_EXECUTED', 'metrics_available': False},
        'proposed': proposed or {'status': 'NOT_AVAILABLE', 'metrics_available': False},
        'experiment': experiment or {'status': 'NOT_AVAILABLE'},
        'comparison': comparison,
        'baseline_executed': bool(baseline and baseline.get('status') == 'EXECUTED' and baseline.get('metrics_available')),
        'proposed_executed': bool(proposed and proposed.get('status') == 'EXECUTED' and proposed.get('metrics_available')),
        'scientific_validation': False,
        'review_required': True,
        'metric_family': 'dynamic',
        'evaluation_metrics': metrics,
        'execution_truth': 'Measured metrics are shown only when produced by an actual controlled execution. Results require human/scientific review before being treated as validated findings.',
    }


def persist_results(project: dict[str, Any], workspace_root: Path) -> dict[str, Any]:
    result = collect_results(str(project.get('project_id', 'unknown')), workspace_root)
    out = workspace_root / 'artifacts' / 'results_summary.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    return result


def _sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def build_results_observatory(project: dict[str,Any], workspace_root: Path, executions: list[dict[str,Any]]|None=None) -> dict[str,Any]:
    executions=executions or []
    results=collect_results(str(project.get("project_id","unknown")),workspace_root)
    contract=_load(workspace_root/"execution_contract.json") or {}
    caps=contract.get("capabilities") if isinstance(contract,dict) else {}
    comparison=results.get("comparison") or {}
    metrics=[]
    for name in results.get("evaluation_metrics") or []:
        row=comparison.get(name,{}) if isinstance(comparison,dict) else {}
        metrics.append({"metric":name,"baseline":row.get("baseline"),"proposed":row.get("proposed"),"delta":row.get("delta"),"relative_change_percent":row.get("relative_change_percent"),"source":"baseline_evaluation.json + evaluation.json" if row.get("baseline") is not None else "evaluation.json","measured":row.get("proposed") is not None})
    artifacts=[]
    for rel in ("dataset_status.json","training_status.json","baseline_evaluation.json","evaluation.json","experiment_run.json","results_summary.json"):
        path=workspace_root/"artifacts"/rel
        if path.is_file():
            st=path.stat(); artifacts.append({"path":f"artifacts/{rel}","size":st.st_size,"sha256":_sha256_file(path),"modified_at":datetime.fromtimestamp(st.st_mtime,timezone.utc).isoformat()})
    lineage=[{"execution_id":e.get("execution_id"),"task":e.get("task"),"started_at":e.get("started_at"),"finished_at":e.get("finished_at"),"duration_seconds":e.get("duration_seconds"),"artifact_count":len(e.get("artifacts") or [])} for e in executions if isinstance(e,dict) and e.get("status")=="EXECUTED"]
    exp=results.get("experiment") if isinstance(results.get("experiment"),dict) else {}
    repro=exp.get("reproducibility") if isinstance(exp.get("reproducibility"),dict) else {}
    validation=project.get("validation") or {}
    return {"schema_version":"6.1-results-observatory-1","generated_at":_now(),"project_id":project.get("project_id"),"profile":(caps.get("primary") or ["general"])[0] if isinstance(caps,dict) else "general","status":results.get("status"),"metric_family":results.get("metric_family","dynamic"),"metrics":metrics,"artifacts":artifacts,"execution_lineage":lineage,"reproducibility":{"seed":repro.get("seed"),"environment_required":bool(repro.get("environment_required")),"artifact_hashes_available":bool(artifacts),"execution_lineage_available":bool(lineage),"reproducible_ready":bool(artifacts and lineage and repro.get("environment_required"))},"baseline":results.get("baseline"),"proposed":results.get("proposed"),"experiment":exp,"comparison_available":bool(comparison),"measured_results":bool(results.get("proposed_executed") and results.get("proposed",{}).get("metrics_available")),"review_status":"VALIDATED" if validation.get("scientific_validation") and validation.get("human_approved") else "REVIEW_REQUIRED","truth":"Observatory values are traceable projections of persisted execution artifacts. They do not constitute scientific validation without the AURA validation gate and authorized human approval."}
