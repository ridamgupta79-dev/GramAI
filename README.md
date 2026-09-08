# Rural AI Business Advisory Assistant (SIH 20200)

Hyper-local business feasibility reports + smart scheme calculator for rural
micro-entrepreneurs availing concessional credit (10% margin / 90% loan).

## Modules

1. **Feasibility Report** — market reach, opportunity analysis, SWOT, threats,
   competitor mapping, pricing insights (`/api/feasibility/report`).
2. **Smart Financial Calculator** — margin → project cost → scheme routing →
   quarterly EMI schedule with moratorium (`/api/finance/plan`). Fully deterministic.

## Schemes

| Scheme | Project Cost | Rate | Tenure | Moratorium | Max Loan |
|---|---|---|---|---|---|
| Micro Finance | ≤ ₹1.40 lakh | 6.5% p.a. | 3 yrs | 3 months | ₹1.25 lakh |
| Term Loan | ₹1.40–50 lakh | 8% p.a. | 7 yrs | 6 months | ₹45 lakh |

## Run

Backend:
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. API docs at http://localhost:8000/docs.

Or with Docker: `docker compose up --build`

## Optional LLM

Set `LLM_API_KEY` (and optionally `LLM_MODEL`, `LLM_BASE_URL`) to enable
AI-generated feasibility narratives and chat. Without a key the app falls back
to a deterministic template report — everything works offline.

## Tests

```bash
cd backend && pytest -q
```
