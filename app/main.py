import logging

from fastapi import FastAPI

from app.db import Base, engine
from app.routers import claims, members, reports

logging.basicConfig(level=logging.INFO)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Claims Service", version="0.4.2")
app.include_router(claims.router)
app.include_router(members.router)
app.include_router(reports.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
