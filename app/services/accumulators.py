from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Accumulator


def get_or_create_accumulator(db: Session, member_id: int, plan_year: int) -> Accumulator:
    acc = db.scalars(
        select(Accumulator).where(
            Accumulator.member_id == member_id, Accumulator.plan_year == plan_year
        )
    ).one_or_none()
    if acc is None:
        acc = Accumulator(
            member_id=member_id, plan_year=plan_year, deductible_met_cents=0, oop_met_cents=0
        )
        db.add(acc)
        db.flush()
    return acc
