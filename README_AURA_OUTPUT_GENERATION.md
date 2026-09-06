# AURA — Output Generation Build

This build adds real backend file generation to Delivery Studio.

## Start backend

```powershell
cd C:\Users\ragul\AURA\backend
.\venv\Scripts\python.exe main.py
```

## Start frontend

```powershell
cd C:\Users\ragul\AURA\frontend
npm.cmd run dev
```

Open http://localhost:3000

## Generate files

DELIVER → OUTPUTS → select an output.

Available actual generation controls:
- DOCX Project Report
- PDF Project Report
- PPTX Presentation
- Project ZIP package

The project package also contains Research Paper, SIH/Hackathon, Demo, Viva, evidence JSON, experiment plan and full project JSON.

Generated artifacts are derived from the current AURA project state. AURA does not claim that planned experiments or unexecuted code are verified merely because a document was generated.
