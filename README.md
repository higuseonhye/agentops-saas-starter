# AgentOps SaaS Starter

## Backend (FastAPI)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python scripts_seed.py
uvicorn app.main:app --reload
```

Seed script creates a demo organization + user and prints `x-api-key`.

### API endpoints

- `POST /query` - runs agent + tracks usage event (append-only)
- `GET /usage` - org-level usage summary (`days` or `start_date`+`end_date`)
- `GET /usage/compare` - cross-org usage cost comparison for same range
- `GET /performance` - latest accuracy/error metrics
- `GET /performance/history` - date-range performance series
- `GET /failures` - failure explorer list
- `POST /replay` - replay one failure
- `POST /optimize` - creates improved performance snapshot
- `POST /billing/checkout` - Stripe checkout URL
- `POST /billing/webhook` - Stripe webhook credit top-up
- `GET /org/usage` - org billing aggregate
- `GET /orgs` - organizations available for current API key user

## Frontend (Next.js + Tailwind)

```bash
cd frontend
npm install
copy .env.local.example .env.local
npm run dev
```

Set `NEXT_PUBLIC_API_KEY` in `frontend/.env.local` using seed output key.

Pages:
- `/usage`
- `/performance`
- `/failures`
- `/system`

## Alert system

Run on schedule (Task Scheduler or cron-like runner):

```bash
python scripts/alert_check.py
```

Required env vars:
- `AGENTOPS_API_KEY`
- `AGENTOPS_API_BASE` (default `http://localhost:8000`)
- `SLACK_WEBHOOK_URL` (optional; if absent, prints mock alert)

Example cron:

```cron
*/10 * * * * python /path/to/agentops/scripts/alert_check.py
```
