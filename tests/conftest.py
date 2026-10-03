import os

os.environ.setdefault("DATABASE_URL", "sqlite://")

from datetime import date  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.db import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import FeeScheduleEntry, Member, Plan, Provider  # noqa: E402


@pytest.fixture
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)()

    silver = Plan(name="Silver PPO", deductible_cents=50000, oop_max_cents=400000, coinsurance_rate=0.2)
    session.add(silver)
    session.add_all(
        [
            FeeScheduleEntry(cpt_code="99213", description="Office visit, low", allowed_cents=11000),
            FeeScheduleEntry(cpt_code="99214", description="Office visit, moderate", allowed_cents=16000),
            FeeScheduleEntry(cpt_code="72148", description="MRI lumbar", allowed_cents=60000),
            FeeScheduleEntry(cpt_code="85025", description="CBC", allowed_cents=1000),
        ]
    )
    session.add(Provider(npi="1111111111", name="Test Clinic"))
    session.add(
        Member(
            member_number="M-1",
            first_name="Test",
            last_name="Member",
            date_of_birth=date(1990, 1, 1),
            plan=silver,
            coverage_start=date(2026, 1, 1),
        )
    )
    session.add(
        Member(
            member_number="M-2",
            first_name="Former",
            last_name="Member",
            date_of_birth=date(1980, 1, 1),
            plan=silver,
            coverage_start=date(2025, 1, 1),
            coverage_end=date(2026, 3, 31),
        )
    )
    session.commit()
    yield session
    session.close()


@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    app.dependency_overrides.clear()


def claim_payload(member="M-1", service_date="2026-06-01", lines=None):
    return {
        "member_number": member,
        "provider_npi": "1111111111",
        "service_date": service_date,
        "lines": lines or [{"cpt_code": "99213", "units": 1, "billed_cents": 20000}],
    }
