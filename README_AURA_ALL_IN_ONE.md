# AURA 6.1 — Complete AI Research, Innovation & Development Operating System

AURA is an evidence-driven project intelligence and development operating system that connects idea understanding, research, evidence, decisions, innovation, architecture, implementation, data, experiments, results, validation and delivery.

## One system
`IDEA → ANALYSIS → REQUIREMENTS → RESEARCH → EVIDENCE → INNOVATION → SOLUTION → ARCHITECTURE → IMPLEMENTATION → DATASET → BASELINE → MODEL → TESTING → EXPERIMENT → RESULTS → VALIDATION → DOCUMENTATION → DELIVERY → COMPLETED`

## AURA Journey
`UNDERSTAND → INVESTIGATE → ANALYZE → VERDICT → INNOVATE → SOLUTION → ARCHITECT → BUILD → EXPERIMENT → VALIDATE → DELIVER`

## 6.1 capabilities
- Dynamic project analyzer and capability contract
- Research/literature intelligence and research-gap analysis
- Evidence and claims with provenance/review truth boundary
- Project provenance graph
- Dynamic project-development lifecycle
- Real workspace generation and allowlisted execution
- Dataset upload, safe extraction, hashing and profiling
- Baseline/proposed experiment planning and comparison
- Artifact-driven results collection
- Human + evidence validation gate
- Strict Completion Engine 2.0
- Specialist-agent orchestration
- Authentication, roles, collaboration, tasks, comments and audit trail
- Version checkpoints and reproducibility manifests
- Project health scoring
- One-click delivery package and generated reports
- Cinematic Command Center UI
- 14-chapter complete project report generation
- Dataset, results, experiment, traceability and completion report outputs

## Truth boundary
AURA deliberately enforces:

`GENERATED ≠ IMPLEMENTED ≠ TESTED ≠ EXECUTED ≠ MEASURED ≠ VALIDATED ≠ COMPLETED`

The platform can be certified complete as software, but it must never invent an end-user project's scientific dataset, measured metrics, validation or human approval.

## Start locally
### Backend
```powershell
cd backend
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

### Frontend
```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

## Production
- Backend: Python/FastAPI service.
- Database: PostgreSQL using `AURA_DATABASE_URL`.
- Frontend: Next.js using `NEXT_PUBLIC_AURA_API_URL`.
- Store large datasets/models/artifacts in durable object storage or persistent volumes.
- Set a strong `AURA_AUTH_SECRET`.

## Verification
Run:
```powershell
python VERIFY_AURA_6_1.py
```
The release verification checks source completeness, backend compilation, platform certification and live API endpoints.
