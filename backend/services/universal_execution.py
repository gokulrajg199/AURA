from __future__ import annotations
"""Universal, capability-driven project execution contracts for AURA.
No domain is hard-coded into the completion model; profiles are inferred into capabilities and gates."""
from dataclasses import dataclass, asdict
from typing import Any
import re

CAPABILITIES = {
    "software": {"signals": ["web app","software","api","backend","frontend","dashboard","application"], "data": ["none","json","csv","database","api"], "metrics": ["tests_passed","coverage","latency_ms","error_rate"], "gates": ["implementation","tests","execution"]},
    "ml_regression": {"signals": ["regression","prediction","forecast","nutrient prediction","price prediction"], "data": ["csv","json","database","sensor_stream"], "metrics": ["mae","rmse","r2"], "gates": ["dataset","training","evaluation","validation"]},
    "ml_classification": {"signals": ["classification","classify","disease detection","spam detection","sentiment"], "data": ["csv","json","image","text","database"], "metrics": ["accuracy","precision","recall","f1","auc"], "gates": ["dataset","training","evaluation","validation"]},
    "computer_vision": {"signals": ["computer vision","object detection","image recognition","image classification","yolo","segmentation"], "data": ["image","video"], "metrics": ["precision","recall","map50","map50_95"], "gates": ["dataset","training","evaluation","validation"]},
    "nlp": {"signals": ["nlp","natural language","text classification","summarization","question answering","language model"], "data": ["text","json","csv","document"], "metrics": ["accuracy","precision","recall","f1","rouge"], "gates": ["dataset","evaluation","validation"]},
    "iot": {"signals": ["iot","sensor","hydroponic","smart agriculture","telemetry","embedded"], "data": ["sensor_stream","csv","json","telemetry"], "metrics": ["mae","rmse","r2","latency_ms","packet_loss","reliability"], "gates": ["data_contract","device_simulation","tests","evaluation","validation"]},
    "robotics": {"signals": ["robot","robotics","ros","navigation","control system","autonomous vehicle"], "data": ["telemetry","video","sensor_stream","rosbag"], "metrics": ["position_error","latency_ms","success_rate","stability"], "gates": ["simulation","tests","evaluation","validation"]},
    "research": {"signals": ["research","study","analysis","framework","methodology","experiment"], "data": ["document","csv","json","none"], "metrics": ["evidence_count","claim_coverage","reproducibility"], "gates": ["research","evidence","analysis","validation"]},
}

@dataclass
class CapabilityContract:
    primary: list[str]
    capabilities: list[str]
    accepted_data: list[str]
    evaluation_metrics: list[str]
    required_gates: list[str]
    rationale: list[str]

def _text(project: dict[str, Any]) -> str:
    return re.sub(r"\s+", " ", str(project.get("original_idea", "")) + " " + str(project.get("analysis", {})) + " " + str(project.get("solution", {}))).lower()

def infer_capabilities(project: dict[str, Any]) -> CapabilityContract:
    text = _text(project)
    scores = []
    for name, spec in CAPABILITIES.items():
        hits = [s for s in spec["signals"] if s in text]
        scores.append((len(hits), name, hits))
    scores.sort(reverse=True)
    selected = [name for score, name, _ in scores if score > 0][:3]
    if not selected: selected = ["research", "software"]
    primary = [scores[0][1]] if scores[0][0] else ["research"]
    accepted, metrics, gates = [], [], []
    rationale=[]
    for name in selected:
        spec=CAPABILITIES[name]
        accepted += spec["data"]; metrics += spec["metrics"]; gates += spec["gates"]
        hits = next((h for _,n,h in scores if n==name), [])
        rationale.append(f"{name}: matched {hits or ['generic research/software fallback']}")
    def uniq(x): return list(dict.fromkeys(x))
    return CapabilityContract(primary=primary, capabilities=selected, accepted_data=uniq(accepted), evaluation_metrics=uniq(metrics), required_gates=uniq(gates), rationale=rationale)

def build_contract(project: dict[str, Any]) -> dict[str, Any]:
    c=infer_capabilities(project)
    return {"version":"3.2", "capabilities":asdict(c), "truth_boundary":{"generated":False,"implemented":False,"tested":False,"executed":False,"measured":False,"validated":False,"completed":False}, "completion_rule":"ALL_REQUIRED_GATES + VALID_EVIDENCE + SUCCESSFUL_VERIFICATION + REQUIRED_HUMAN_APPROVAL = COMPLETED", "dynamic":True}
