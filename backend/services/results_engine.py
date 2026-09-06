from __future__ import annotations
import json
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
    metrics = ['map50', 'map50_95', 'precision', 'recall']
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
        'execution_truth': 'Measured metrics are shown only when produced by an actual controlled execution. Results require human/scientific review before being treated as validated findings.',
    }


def persist_results(project: dict[str, Any], workspace_root: Path) -> dict[str, Any]:
    result = collect_results(str(project.get('project_id', 'unknown')), workspace_root)
    out = workspace_root / 'artifacts' / 'results_summary.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    return result
