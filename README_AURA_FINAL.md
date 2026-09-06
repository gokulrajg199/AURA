# AURA — Final Integrated Build Audit

## What is now connected

1. Idea intelligence and project understanding
2. Multi-source literature investigation
3. Evidence registry and claim traceability
4. Research analysis and findings
5. Evidence-aware AURA verdict
6. Research-backed innovation directions
7. Solution architecture
8. Technology/system architecture
9. Real project workspace generation
10. Controlled build/test/training/evaluation execution
11. Experiment result ingestion and validation truth
12. Delivery generation from the same project state

## Final-state guarantees

- Project state survives backend restarts through `backend/data/projects.json`.
- Execution uses an allowlisted task set and `shell=False`.
- Results are ingested only from files produced in the project workspace.
- No metric is invented when training/evaluation has not executed.
- Baseline comparison remains unavailable until a real baseline evaluation exists.
- Results are marked `REVIEW REQUIRED`; execution is not the same as scientific verification.
- Generated reports/papers/PPT/SIH/demo/viva include the current results section when available.

## What still depends on the user's real project inputs

AURA cannot honestly manufacture a dataset, pretrained weights, GPU runtime, ground-truth labels, or experimental measurements. For a real project, provide the approved dataset and model/runtime resources, then run dataset preparation, training, evaluation and experiments. Only after those runs can AURA display measured performance.

## Final verification commands

Backend syntax: `python -m compileall backend`
Frontend: `npm.cmd run build`

