"""Splits an allowed amount between the member and the plan."""

from dataclasses import dataclass


@dataclass(frozen=True)
class LineSplit:
    deductible_cents: int
    coinsurance_cents: int
    plan_paid_cents: int

    @property
    def patient_cents(self) -> int:
        return self.deductible_cents + self.coinsurance_cents


def split_line(
    allowed_cents: int,
    deductible_remaining_cents: int,
    oop_remaining_cents: int,
    coinsurance_rate: float,
) -> LineSplit:
    """Apply deductible, then coinsurance, then the out-of-pocket max to one line."""
    deductible = min(allowed_cents, deductible_remaining_cents)
    after_deductible = allowed_cents - deductible

    coinsurance = round(after_deductible * coinsurance_rate)
    plan_paid = round(after_deductible * (1 - coinsurance_rate))

    # Once the member hits their out-of-pocket max, the plan picks up the rest.
    excess = deductible + coinsurance - oop_remaining_cents
    if excess > 0:
        from_coinsurance = min(excess, coinsurance)
        coinsurance -= from_coinsurance
        deductible -= excess - from_coinsurance
        plan_paid += excess

    return LineSplit(
        deductible_cents=deductible,
        coinsurance_cents=coinsurance,
        plan_paid_cents=plan_paid,
    )
