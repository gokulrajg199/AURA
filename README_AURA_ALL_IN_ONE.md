# AURA — Integrated Project Intelligence + Execution + Results Engine

This build connects AURA's evidence graph to a controlled real-project workspace and a measured-results layer.

## Execution lifecycle

IDEA → RESEARCH → EVIDENCE → CLAIMS → FINDINGS → VERDICT → INNOVATION → SOLUTION → ARCHITECTURE → BUILD → DATASET → BASELINE → PROPOSED MODEL → EVALUATION → EXPERIMENT → RESULTS → VALIDATION → DELIVERY

## Results truth

AURA never fabricates performance. Baseline and proposed metrics appear only when an approved dataset/model is actually executed. If a baseline is unavailable, the comparison remains unmeasured rather than using an estimate.

## New result layer

- `backend/services/results_engine.py`
- `GET /api/aura/projects/{project_id}/results`
- baseline evaluation support via `models/baseline.pt`
- proposed evaluation via executed training weights
- metric comparison: mAP50, mAP50-95, precision, recall
- persisted `artifacts/results_summary.json`
- frontend Results Observatory

## Scientific boundary

Execution is not automatically scientific validation. Measured results require human/scientific review before being treated as validated findings or publication claims.
