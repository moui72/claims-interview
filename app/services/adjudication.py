import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Claim,
    ClaimStatus,
    DenialReason,
    FeeScheduleEntry,
    LineStatus,
)
from app.services.accumulators import get_or_create_accumulator
from app.services.cost_share import split_line
from app.services.eligibility import is_eligible

log = logging.getLogger(__name__)


def _load_fee_schedule(db: Session, cpt_codes: set[str]) -> dict[str, int]:
    rows = db.scalars(select(FeeScheduleEntry).where(FeeScheduleEntry.cpt_code.in_(cpt_codes)))
    return {row.cpt_code: row.allowed_cents for row in rows}


def adjudicate_claim(db: Session, claim: Claim) -> Claim:
    member = claim.member
    plan = member.plan
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    if not is_eligible(member, claim.service_date):
        claim.status = ClaimStatus.DENIED
        claim.denial_reason = DenialReason.INELIGIBLE
        for line in claim.lines:
            line.status = LineStatus.DENIED
            line.denial_reason = DenialReason.INELIGIBLE
        claim.adjudicated_at = now
        db.commit()
        return claim

    fee_schedule = _load_fee_schedule(db, {line.cpt_code for line in claim.lines})
    acc = get_or_create_accumulator(db, member.id, claim.service_date.year)

    deductible_remaining = max(plan.deductible_cents - acc.deductible_met_cents, 0)
    oop_remaining = max(plan.oop_max_cents - acc.oop_met_cents, 0)

    totals = dict(billed=0, allowed=0, deductible=0, coinsurance=0, plan_paid=0)
    for line in claim.lines:
        fee = fee_schedule.get(line.cpt_code)
        allowed = min(line.billed_cents, fee * line.units)

        split = split_line(allowed, deductible_remaining, oop_remaining, plan.coinsurance_rate)

        line.status = LineStatus.PAID
        line.allowed_cents = allowed
        line.deductible_cents = split.deductible_cents
        line.coinsurance_cents = split.coinsurance_cents
        line.plan_paid_cents = split.plan_paid_cents

        totals["billed"] += line.billed_cents
        totals["allowed"] += allowed
        totals["deductible"] += split.deductible_cents
        totals["coinsurance"] += split.coinsurance_cents
        totals["plan_paid"] += split.plan_paid_cents

    claim.billed_cents = totals["billed"]
    claim.allowed_cents = totals["allowed"]
    claim.deductible_cents = totals["deductible"]
    claim.coinsurance_cents = totals["coinsurance"]
    claim.plan_paid_cents = totals["plan_paid"]
    claim.patient_responsibility_cents = totals["deductible"] + totals["coinsurance"]
    claim.status = ClaimStatus.ADJUDICATED
    claim.adjudicated_at = now

    acc.deductible_met_cents += totals["deductible"]
    acc.oop_met_cents += claim.patient_responsibility_cents

    db.commit()
    log.info(
        "adjudicated %s allowed=%d plan_paid=%d patient=%d",
        claim.claim_number,
        claim.allowed_cents,
        claim.plan_paid_cents,
        claim.patient_responsibility_cents,
    )
    return claim
