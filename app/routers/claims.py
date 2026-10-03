from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.models import Claim, ClaimLine, ClaimStatus, Member, Provider
from app.schemas import ClaimIn, ClaimOut, ClaimPage, ClaimSummary, QueueStats
from app.services.adjudication import adjudicate_claim
from app.services.pagination import decode_cursor, encode_cursor

router = APIRouter(prefix="/claims", tags=["claims"])


def _to_out(claim: Claim) -> ClaimOut:
    return ClaimOut.model_validate(
        {
            **{k: getattr(claim, k) for k in ClaimOut.model_fields if hasattr(claim, k)},
            "member_number": claim.member.member_number,
            "provider_npi": claim.provider.npi,
            "lines": claim.lines,
        }
    )


def _get_claim(db: Session, claim_number: str) -> Claim:
    claim = db.scalars(
        select(Claim)
        .where(Claim.claim_number == claim_number)
        .options(selectinload(Claim.lines), selectinload(Claim.member).selectinload(Member.plan))
    ).one_or_none()
    if claim is None:
        raise HTTPException(status_code=404, detail="Claim not found")
    return claim


def _next_claim_number(db: Session, year: int) -> str:
    count = db.scalar(select(func.count(Claim.id)).where(Claim.claim_number.like(f"CLM-{year}-%")))
    return f"CLM-{year}-{count + 1:05d}"


@router.post("", response_model=ClaimOut, status_code=201)
def submit_claim(payload: ClaimIn, db: Session = Depends(get_db)) -> ClaimOut:
    member = db.scalars(select(Member).where(Member.member_number == payload.member_number)).one_or_none()
    if member is None:
        raise HTTPException(status_code=422, detail="Unknown member")
    provider = db.scalars(select(Provider).where(Provider.npi == payload.provider_npi)).one_or_none()
    if provider is None:
        raise HTTPException(status_code=422, detail="Unknown provider")

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    claim = Claim(
        claim_number=_next_claim_number(db, now.year),
        member=member,
        provider=provider,
        service_date=payload.service_date,
        submitted_at=now,
        status=ClaimStatus.PENDING,
        lines=[
            ClaimLine(line_number=i, cpt_code=l.cpt_code, units=l.units, billed_cents=l.billed_cents)
            for i, l in enumerate(payload.lines, start=1)
        ],
    )
    db.add(claim)
    db.commit()
    return _to_out(claim)


@router.get("", response_model=ClaimPage)
def list_claims(
    status: ClaimStatus = ClaimStatus.PENDING,
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = None,
    db: Session = Depends(get_db),
) -> ClaimPage:
    """Work queue, oldest first."""
    query = select(Claim).where(Claim.status == status).order_by(Claim.submitted_at)
    if cursor:
        query = query.where(Claim.submitted_at > decode_cursor(cursor))
    rows = list(db.scalars(query.limit(limit + 1)))

    has_more = len(rows) > limit
    rows = rows[:limit]
    next_cursor = encode_cursor(rows[-1].submitted_at) if has_more else None
    return ClaimPage(items=[ClaimSummary.model_validate(c) for c in rows], next_cursor=next_cursor)


@router.get("/stats", response_model=QueueStats)
def queue_stats(db: Session = Depends(get_db)) -> QueueStats:
    counts = dict(db.execute(select(Claim.status, func.count(Claim.id)).group_by(Claim.status)).all())
    return QueueStats(
        pending=counts.get(ClaimStatus.PENDING, 0),
        adjudicated=counts.get(ClaimStatus.ADJUDICATED, 0),
        denied=counts.get(ClaimStatus.DENIED, 0),
    )


@router.get("/{claim_number}", response_model=ClaimOut)
def get_claim(claim_number: str, db: Session = Depends(get_db)) -> ClaimOut:
    return _to_out(_get_claim(db, claim_number))


@router.post("/{claim_number}/adjudicate", response_model=ClaimOut)
def adjudicate(claim_number: str, db: Session = Depends(get_db)) -> ClaimOut:
    claim = _get_claim(db, claim_number)
    return _to_out(adjudicate_claim(db, claim))
