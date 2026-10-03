from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Claim, ClaimStatus
from app.schemas import ReconciliationReport, ReconciliationRow

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/reconciliation", response_model=ReconciliationReport)
def reconciliation(start: date, end: date, db: Session = Depends(get_db)) -> ReconciliationReport:
    """Every adjudicated dollar must be owed by someone: allowed == plan paid + patient responsibility."""
    claims = list(
        db.scalars(
            select(Claim)
            .where(Claim.status == ClaimStatus.ADJUDICATED)
            .where(Claim.adjudicated_at >= datetime.combine(start, time.min))
            .where(Claim.adjudicated_at < datetime.combine(end + timedelta(days=1), time.min))
            .order_by(Claim.claim_number)
        )
    )

    discrepancies = []
    for c in claims:
        variance = c.allowed_cents - (c.plan_paid_cents + c.patient_responsibility_cents)
        if variance != 0:
            discrepancies.append(
                ReconciliationRow(
                    claim_number=c.claim_number,
                    allowed_cents=c.allowed_cents,
                    plan_paid_cents=c.plan_paid_cents,
                    patient_responsibility_cents=c.patient_responsibility_cents,
                    variance_cents=variance,
                )
            )

    return ReconciliationReport(
        start=start,
        end=end,
        claims_checked=len(claims),
        total_allowed_cents=sum(c.allowed_cents for c in claims),
        total_plan_paid_cents=sum(c.plan_paid_cents for c in claims),
        total_patient_responsibility_cents=sum(c.patient_responsibility_cents for c in claims),
        discrepancies=discrepancies,
    )
