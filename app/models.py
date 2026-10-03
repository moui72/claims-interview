import enum
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class ClaimStatus(str, enum.Enum):
    PENDING = "pending"
    ADJUDICATED = "adjudicated"
    DENIED = "denied"


class LineStatus(str, enum.Enum):
    PAID = "paid"
    DENIED = "denied"


class DenialReason(str, enum.Enum):
    INELIGIBLE = "INELIGIBLE"
    NOT_COVERED = "NOT_COVERED"


class ClaimSource(str, enum.Enum):
    PORTAL = "portal"
    EDI_BATCH = "edi_batch"


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    deductible_cents: Mapped[int] = mapped_column(Integer)
    oop_max_cents: Mapped[int] = mapped_column(Integer)
    # Member's share after the deductible is met, e.g. 0.2 = 20% coinsurance
    coinsurance_rate: Mapped[float] = mapped_column(Float)


class Member(Base):
    __tablename__ = "members"

    id: Mapped[int] = mapped_column(primary_key=True)
    member_number: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    date_of_birth: Mapped[date] = mapped_column(Date)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id"))
    coverage_start: Mapped[date] = mapped_column(Date)
    coverage_end: Mapped[date | None] = mapped_column(Date, nullable=True)

    plan: Mapped[Plan] = relationship()


class Provider(Base):
    __tablename__ = "providers"

    id: Mapped[int] = mapped_column(primary_key=True)
    npi: Mapped[str] = mapped_column(String(10), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))


class FeeScheduleEntry(Base):
    __tablename__ = "fee_schedule"

    id: Mapped[int] = mapped_column(primary_key=True)
    cpt_code: Mapped[str] = mapped_column(String(5), unique=True, index=True)
    description: Mapped[str] = mapped_column(String(200))
    allowed_cents: Mapped[int] = mapped_column(Integer)


class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[int] = mapped_column(primary_key=True)
    claim_number: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"))
    provider_id: Mapped[int] = mapped_column(ForeignKey("providers.id"))
    service_date: Mapped[date] = mapped_column(Date)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    source: Mapped[ClaimSource] = mapped_column(Enum(ClaimSource), default=ClaimSource.PORTAL)
    status: Mapped[ClaimStatus] = mapped_column(Enum(ClaimStatus), default=ClaimStatus.PENDING, index=True)
    denial_reason: Mapped[DenialReason | None] = mapped_column(Enum(DenialReason), nullable=True)

    billed_cents: Mapped[int] = mapped_column(Integer, default=0)
    allowed_cents: Mapped[int] = mapped_column(Integer, default=0)
    deductible_cents: Mapped[int] = mapped_column(Integer, default=0)
    coinsurance_cents: Mapped[int] = mapped_column(Integer, default=0)
    plan_paid_cents: Mapped[int] = mapped_column(Integer, default=0)
    patient_responsibility_cents: Mapped[int] = mapped_column(Integer, default=0)
    adjudicated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    member: Mapped[Member] = relationship()
    provider: Mapped[Provider] = relationship()
    lines: Mapped[list["ClaimLine"]] = relationship(
        back_populates="claim", order_by="ClaimLine.line_number", cascade="all, delete-orphan"
    )


class ClaimLine(Base):
    __tablename__ = "claim_lines"

    id: Mapped[int] = mapped_column(primary_key=True)
    claim_id: Mapped[int] = mapped_column(ForeignKey("claims.id"))
    line_number: Mapped[int] = mapped_column(Integer)
    cpt_code: Mapped[str] = mapped_column(String(5))
    units: Mapped[int] = mapped_column(Integer, default=1)
    billed_cents: Mapped[int] = mapped_column(Integer)

    status: Mapped[LineStatus | None] = mapped_column(Enum(LineStatus), nullable=True)
    denial_reason: Mapped[DenialReason | None] = mapped_column(Enum(DenialReason), nullable=True)
    allowed_cents: Mapped[int] = mapped_column(Integer, default=0)
    deductible_cents: Mapped[int] = mapped_column(Integer, default=0)
    coinsurance_cents: Mapped[int] = mapped_column(Integer, default=0)
    plan_paid_cents: Mapped[int] = mapped_column(Integer, default=0)

    claim: Mapped[Claim] = relationship(back_populates="lines")


class Accumulator(Base):
    """Running deductible / out-of-pocket totals for a member in a plan year."""

    __tablename__ = "accumulators"
    __table_args__ = (UniqueConstraint("member_id", "plan_year"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"))
    plan_year: Mapped[int] = mapped_column(Integer)
    deductible_met_cents: Mapped[int] = mapped_column(Integer, default=0)
    oop_met_cents: Mapped[int] = mapped_column(Integer, default=0)
