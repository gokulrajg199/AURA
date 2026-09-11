from __future__ import annotations
import hashlib, json
from datetime import datetime, timezone
from typing import Any

def now(): return datetime.now(timezone.utc).isoformat()

def create_plan(project: dict[str,Any], capabilities: dict[str,Any] | None=None) -> dict[str,Any]:
    caps=capabilities or {}
    metrics=caps.get('evaluation_metrics') or ['accuracy','precision','recall','f1']
    profile=(caps.get('primary') or ['general'])[0]
    plan={'experiment_id':'exp-'+hashlib.sha256((project.get('project_id','')+now()).encode()).hexdigest()[:12],
          'profile':profile,'hypothesis':'The proposed approach should improve the project objective against the declared baseline.',
          'baseline':{'name':'declared_baseline','status':'REQUIRED_BEFORE_COMPARISON'},
          'proposed':{'name':'proposed_solution','status':'READY_FOR_EXECUTION'},
          'metrics':metrics,'runs':[],'reproducibility':{'seed':42,'environment_required':True,'artifact_hashes_required':True},
          'truth_status':'EXPERIMENT_PLAN_ONLY_UNTIL_EXECUTED'}
    return plan

def compare(baseline: dict[str,Any], proposed: dict[str,Any], metrics: list[str]) -> dict[str,Any]:
    rows=[]
    for m in metrics:
        b=baseline.get(m); p=proposed.get(m)
        row={'metric':m,'baseline':b,'proposed':p,'delta':None,'relative_delta_percent':None}
        try:
            if b is not None and p is not None:
                row['delta']=float(p)-float(b)
                row['relative_delta_percent']=None if float(b)==0 else (float(p)-float(b))/abs(float(b))*100
        except Exception: pass
        rows.append(row)
    return {'metrics':rows,'truth_status':'MEASURED_COMPARISON_ONLY_NOT_AUTOMATIC_VALIDATION'}
