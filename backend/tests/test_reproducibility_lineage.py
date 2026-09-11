from pathlib import Path
import json
from services.reproducibility_engine import build_reproducibility_lineage

def test_lineage_hashes_files_and_orders_runs(tmp_path: Path):
    (tmp_path/'execution_contract.json').write_text(json.dumps({'seed':123}),encoding='utf-8')
    (tmp_path/'artifacts').mkdir()
    (tmp_path/'artifacts/evaluation.json').write_text('{"metrics_available":true}',encoding='utf-8')
    p={'project_id':'p1','experiments':{'reproducibility':{'seed':123,'environment_required':True,'artifact_hashes_required':True}}}
    out=build_reproducibility_lineage(p,tmp_path,[{'status':'EXECUTED','execution_id':'e1','task':'baseline_evaluate','artifacts':['a']},{'status':'FAILED','execution_id':'e2','task':'evaluate_model'}])
    assert out['lineage_id']; assert out['requirements']['seed']==123; assert len(out['tracked_files'])==2; assert len(out['executions'])==1; assert out['reproducible_ready'] is True

def test_lineage_not_ready_without_execution(tmp_path: Path):
    (tmp_path/'execution_contract.json').write_text('{}',encoding='utf-8')
    p={'project_id':'p2','experiments':{'reproducibility':{'environment_required':True,'artifact_hashes_required':True}}}
    out=build_reproducibility_lineage(p,tmp_path,[])
    assert out['reproducible_ready'] is False
    assert out['truth_status']=='REPRODUCIBILITY_EVIDENCE_INCOMPLETE'
