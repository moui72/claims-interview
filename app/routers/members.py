from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Member
from app.schemas import AccumulatorOut
from app.services.accumulators import get_or_create_accumulator

router = APIRouter(prefix="/members", tags=["members"])


@router.get("/{member_number}/accumulators/{plan_year}", response_model=AccumulatorOut)
def get_accumulators(member_number: str, plan_year: int, db: Session = Depends(get_db)) -> AccumulatorOut:
    member = db.scalars(select(Member).where(Member.member_number == member_number)).one_or_none()
    if member is None:
        raise HTTPException(status_code=404, detail="Member not found")
    acc = get_or_create_accumulator(db, member.id, plan_year)
    return AccumulatorOut(
        member_number=member.member_number,
        plan_name=member.plan.name,
        plan_year=plan_year,
        deductible_cents=member.plan.deductible_cents,
        deductible_met_cents=acc.deductible_met_cents,
        oop_max_cents=member.plan.oop_max_cents,
        oop_met_cents=acc.oop_met_cents,
    )
