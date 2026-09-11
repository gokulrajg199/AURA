# START AURA 6.1

1. Open PowerShell.
2. `cd C:\Users\ragul\AURA\backend`
3. `python -m pip install -r requirements.txt`
4. `python -m uvicorn main:app --reload --port 8000`
5. Open a second PowerShell.
6. `cd C:\Users\ragul\AURA\frontend`
7. `npm install`
8. `npm run dev`
9. Open `http://localhost:3000`.

If the browser shows `Failed to fetch`, first verify `http://127.0.0.1:8000/health` and ensure `NEXT_PUBLIC_AURA_API_URL=http://127.0.0.1:8000`.

For a complete controlled engineering run, use the AURA Command Center's complete verification control or `POST /api/aura/projects/{project_id}/run-complete-lifecycle`.

## Complete project report outputs
Open the Delivery Studio after creating a project. AURA can generate a 14-chapter complete project report plus dataset, results, experiment, traceability, completion, presentation, paper, viva, demo and SIH outputs.

The report remains truth-aware: unexecuted scientific stages are marked as pending rather than populated with invented metrics.
