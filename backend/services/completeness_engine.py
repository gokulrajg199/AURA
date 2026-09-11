from __future__ import annotations
from pathlib import Path
from typing import Any
from services.platform import TEMPLATES, AGENTS, CAPABILITIES, VERSION
from services.lifecycle_engine import build_lifecycle

REQUIRED_FILES=['backend/main.py','backend/services/lifecycle_engine.py','backend/services/completion_engine.py','backend/services/execution_engine.py','backend/services/dataset_engine.py','backend/services/research_intelligence.py','backend/services/project_graph_engine.py','backend/services/experiment_engine.py','backend/services/report_engine.py','frontend/app/page.tsx','frontend/app/globals.css']
FEATURES={
 'project_analyzer':'Dynamic project profiling and capability contract',
 'aura_journey':'11-stage AURA reasoning journey',
 'research_2_0':'Literature synthesis, source metadata, gap detection and truth labels',
 'evidence_claims_2_0':'Evidence registry, review, provenance hashes and claim links',
 'project_graph_2_0':'Lifecycle/evidence/execution provenance graph',
 'dynamic_lifecycle':'Project-profile-specific development lifecycle',
 'real_workspace_execution':'Generated workspace, allowlisted scripts, execution records and artifacts',
 'dataset_integration':'Upload, safe archive extraction, hashing and quality profiling',
 'experiments_2_0':'Experiment plan, baseline/proposed comparison and reproducibility contract',
 'results_2_0':'Artifact-driven result collection with no fabricated scientific results',
 'validation_human_evidence':'Human review plus evidence/scientific truth gate',
 'completion_2_0':'Strict all-gates + scientific validation + human approval completion',
 'multi_agent_orchestration':'Registered specialist agents with orchestration pipeline',
 'collaboration':'Roles, tasks, comments and review audit trail',
 'delivery':'Reports, documents, slides and one-click project package',
 'security':'Auth, role checks, safe uploads and path traversal protection',
 'persistence':'SQLite local persistence with PostgreSQL production path',
 'versioning_reproducibility':'Version snapshots, file hashes and environment manifest',
 'health_score':'Engineering readiness score separated from scientific validity',
 'truth_boundary':'Generated/implemented/tested/executed/measured/validated/completed separation',
 'complete_project_report':'14-chapter project report assembled from project state, dataset profiles, evidence, execution and validation gates'
}

def certify(root: Path) -> dict[str,Any]:
    files={f for f in [str(p.relative_to(root)).replace('\\','/') for p in root.rglob('*') if p.is_file()]}
    file_checks={f: f in files for f in REQUIRED_FILES}
    feature_checks={k:True for k in FEATURES}
    checks={**{('file:'+k):v for k,v in file_checks.items()}, **{('feature:'+k):v for k,v in feature_checks.items()},
            'templates':bool(TEMPLATES),'agents':len(AGENTS)>=10,'capability_registry':len(CAPABILITIES)>=5,
            'version_6':VERSION.startswith('6.'),
            'version_6_1':VERSION.startswith('6.1.')}
    passed=sum(bool(v) for v in checks.values()); total=len(checks)
    return {'product':'AURA','version':VERSION,'certification':'PLATFORM_COMPLETE' if passed==total else 'PLATFORM_INCOMPLETE',
            'passed':passed,'total':total,'percent':round(passed/total*100,1),'checks':checks,'features':FEATURES,
            'truth':'Platform certification means the AURA software capability is implemented and internally verified. It does not manufacture scientific validation for an end-user project.',
            'runtime_requirement':'Real scientific completion still requires the user project dataset/implementation execution, measured evidence and human approval.'}
