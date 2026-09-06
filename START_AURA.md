# AURA — Complete Local Run Guide

## 1. Backend
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Health: `http://127.0.0.1:8000/health`

## 2. Frontend
```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`. Set `NEXT_PUBLIC_AURA_API_URL` when the backend is hosted elsewhere.

## 3. Real execution boundary
AURA generates a real per-project workspace and exposes only allowlisted Python tasks. Training/evaluation require user-supplied approved data and model weights. AURA never substitutes estimates for missing measurements.

## 4. Result lifecycle
IDEA → RESEARCH → EVIDENCE → CLAIMS → FINDINGS → VERDICT → INNOVATION → SOLUTION → ARCHITECTURE → BUILD → DATASET → BASELINE → PROPOSED MODEL → EVALUATION → EXPERIMENT → RESULTS → VALIDATION → DELIVERY

Execution is evidence of execution, not automatic scientific validation. Human/scientific review remains required.
