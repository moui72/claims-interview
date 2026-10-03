# Claims Service

FastAPI + SQLAlchemy 2.0 + SQLite. See README.md for the domain primer.

- Install: `uv sync`
- Reset local data: `uv run python -m scripts.seed`
- Run: `uv run uvicorn app.main:app --reload`
- Test: `uv run pytest`
- Frontend: `cd frontend && npm install && npm run dev` (proxies `/api` → :8000); `npm run build` typechecks

Conventions:
- Money is stored and passed around as integer cents (`*_cents` fields).
- Business logic lives in `app/services/`; routers stay thin.
