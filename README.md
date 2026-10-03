# Claims Service

Intake and adjudication for medical claims. Providers submit claims (via our
portal or nightly EDI 837 batch files), and the claims ops team works them
through the adjudication queue. Adjudication prices each line against the fee
schedule and splits the cost between the plan and the member.

## Setup

Requires [uv](https://docs.astral.sh/uv/) and Node 20+.

```sh
uv sync
uv run python -m scripts.seed      # reset ./claims.db with sample data
uv run uvicorn app.main:app --reload
```

API docs: http://127.0.0.1:8000/docs

The ops console (React + Vite) proxies `/api/*` to the API on port 8000:

```sh
cd frontend
npm install
npm run dev          # http://localhost:5173
```

```sh
uv run pytest
```

## Domain primer

| Term | Meaning |
| --- | --- |
| **CPT code** | 5-character code for a medical service (e.g. `99213` = routine office visit). Each claim line has one. |
| **Billed amount** | What the provider charges. Usually much higher than what gets paid. |
| **Fee schedule / allowed amount** | The contracted rate for a CPT code. A line's allowed amount is the lesser of billed and fee schedule × units. |
| **Deductible** | What the member pays in full each plan year before the plan starts sharing costs. |
| **Coinsurance** | After the deductible, the member's percentage of each allowed amount (e.g. 20%). The plan pays the rest. |
| **Out-of-pocket (OOP) max** | Cap on what the member pays in a plan year (deductible + coinsurance). Past it, the plan pays 100%. |
| **Accumulators** | Running per-member, per-plan-year totals of deductible and OOP met. |
| **EOB** | Explanation of Benefits — the statement a member gets showing how a claim was paid. |

Every adjudicated dollar is owed by someone:
`allowed = plan paid + patient responsibility`, where
`patient responsibility = deductible + coinsurance`.

## Layout

```
app/
  main.py               FastAPI app
  models.py             SQLAlchemy models
  schemas.py            API request/response models
  routers/
    claims.py           submit, fetch, adjudicate, work queue
    members.py          accumulators
    reports.py          finance reconciliation
  services/
    adjudication.py     prices a claim and applies benefits
    cost_share.py       deductible / coinsurance / OOP math for one line
    eligibility.py      coverage date checks
    accumulators.py
    pagination.py       work-queue cursors
scripts/seed.py         sample data
tests/
frontend/               claims ops console (React + TypeScript + Vite)
  src/api.ts            typed API client
  src/views/            work queue, claim detail, members, reconciliation
```

## Useful endpoints

- `GET  /claims?status=pending&limit=20&cursor=…` — work queue, oldest first
- `GET  /claims/stats` — counts by status (feeds the ops dashboard)
- `GET  /claims/{claim_number}`
- `POST /claims/{claim_number}/adjudicate`
- `GET  /members/{member_number}/accumulators/{plan_year}`
- `GET  /reports/reconciliation?start=2026-09-01&end=2026-09-30`

## Open tickets

See [TICKETS.md](TICKETS.md).
