# AURA — FINAL ANALYSIS-FIRST PROJECT OPERATING SYSTEM

## What changed
AURA now enforces an **analysis gate before project workspace generation**.

The system no longer treats these as the same thing:
- research retrieval
- evidence
- claims
- findings
- decisions
- generated code
- execution records
- scientific results
- validation
- delivery

## Final lifecycle
ONE IDEA
→ UNDERSTAND
→ INVESTIGATE
→ EVIDENCE
→ ANALYZE
→ CLAIM/FINDING TRACEABILITY
→ VERDICT
→ INNOVATE
→ SOLUTION
→ ARCHITECT
→ DEVELOPMENT DESIGN
→ ANALYSIS GATE
→ PROJECT WORKSPACE
→ DATA VALIDATION
→ BASELINE
→ PROPOSED TRAINING
→ EVALUATION
→ ERROR ANALYSIS
→ EXPERIMENT AGGREGATION
→ VALIDATION
→ DELIVERY

## Why the previous workspace was not what you expected
The previous Build & Execution Core generated a scaffold, but the scaffold was not a complete project implementation. It required external dataset/model inputs and therefore often stopped at a smoke test or a blocked dataset step. That is correct execution truth, but the UX made it look like the workspace itself was the completed project.

This final build changes that contract:

1. **Complete Analysis comes first.**
2. AURA records a readiness/blocker matrix.
3. The workspace is generated from the finalized analysis.
4. The workspace is profile-specific.
5. Dataset, baseline, proposed model, evaluation and error-analysis tasks are explicit.
6. Real metrics are ingested only when an actual evaluation artifact exists.
7. Missing datasets/weights remain BLOCKED rather than being fabricated.
8. Delivery can consume the same project/evidence/result graph.

## Computer Vision profile
The CV workspace includes:
- dataset contract and provenance file
- dataset YAML validation
- proposed-model training entry point
- optional baseline evaluation
- proposed-model evaluation
- error-analysis stage
- result aggregation
- prediction utility
- pipeline smoke test
- controlled execution records

Ultralytics supports Python training/validation APIs and exposes metrics such as mAP50, mAP50-95, precision and recall. AURA uses these only when the validation run actually executes. See the official documentation for training and validation behavior.

## Execution truth
AURA will not claim:
- trained model without a training run
- benchmark performance without evaluation output
- baseline comparison without a baseline result
- scientific validation from a plan
- novelty from sparse retrieval
- successful deployment from generated code

## Final objective
The target is not a research chatbot or a document generator. AURA is a project operating system that connects research intelligence to engineering execution and keeps an auditable boundary between **planned**, **executed**, **measured**, and **verified** states.
