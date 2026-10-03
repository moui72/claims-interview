from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models import ClaimSource, ClaimStatus, DenialReason, LineStatus


class ClaimLineIn(BaseModel):
    cpt_code: str = Field(min_length=5, max_length=5)
    units: int = Field(default=1, ge=1)
    billed_cents: int = Field(gt=0)


class ClaimIn(BaseModel):
    member_number: str
    provider_npi: str
    service_date: date
    lines: list[ClaimLineIn] = Field(min_length=1)


class ClaimLineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    line_number: int
    cpt_code: str
    units: int
    billed_cents: int
    status: LineStatus | None
    denial_reason: DenialReason | None
    allowed_cents: int
    deductible_cents: int
    coinsurance_cents: int
    plan_paid_cents: int


class ClaimOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    claim_number: str
    member_number: str
    provider_npi: str
    service_date: date
    submitted_at: datetime
    source: ClaimSource
    status: ClaimStatus
    denial_reason: DenialReason | None
    billed_cents: int
    allowed_cents: int
    deductible_cents: int
    coinsurance_cents: int
    plan_paid_cents: int
    patient_responsibility_cents: int
    adjudicated_at: datetime | None
    lines: list[ClaimLineOut]


class ClaimSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    claim_number: str
    service_date: date
    submitted_at: datetime
    source: ClaimSource
    status: ClaimStatus


class ClaimPage(BaseModel):
    items: list[ClaimSummary]
    next_cursor: str | None


class QueueStats(BaseModel):
    pending: int
    adjudicated: int
    denied: int


class AccumulatorOut(BaseModel):
    member_number: str
    plan_name: str
    plan_year: int
    deductible_cents: int
    deductible_met_cents: int
    oop_max_cents: int
    oop_met_cents: int


class ReconciliationRow(BaseModel):
    claim_number: str
    allowed_cents: int
    plan_paid_cents: int
    patient_responsibility_cents: int
    variance_cents: int


class ReconciliationReport(BaseModel):
    start: date
    end: date
    claims_checked: int
    total_allowed_cents: int
    total_plan_paid_cents: int
    total_patient_responsibility_cents: int
    discrepancies: list[ReconciliationRow]
