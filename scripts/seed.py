"""Reset the local database and load sample data.

    uv run python -m scripts.seed
"""

import random
from datetime import date, datetime, timedelta

from app.db import Base, SessionLocal, engine
from app.models import (
    Accumulator,
    Claim,
    ClaimLine,
    ClaimSource,
    ClaimStatus,
    FeeScheduleEntry,
    Member,
    Plan,
    Provider,
)
from app.services.adjudication import adjudicate_claim

FEE_SCHEDULE = [
    ("99213", "Office visit, established patient, low complexity", 11235),
    ("99214", "Office visit, established patient, moderate complexity", 16455),
    ("99215", "Office visit, established patient, high complexity", 21115),
    ("85025", "Complete blood count (CBC) w/ differential", 1055),
    ("80053", "Comprehensive metabolic panel", 1485),
    ("36415", "Routine venipuncture", 305),
    ("71046", "Chest x-ray, 2 views", 3215),
    ("93000", "Electrocardiogram, complete", 1745),
    ("72148", "MRI lumbar spine w/o contrast", 32450),
    ("97110", "Therapeutic exercise, each 15 min", 3165),
    ("97140", "Manual therapy, each 15 min", 2895),
    ("90834", "Psychotherapy, 45 min", 10245),
    ("87880", "Rapid strep test", 1675),
]

# (member_number, first, last, dob, plan, deductible_met, oop_met) as of Sept 1
MEMBERS = [
    ("M-10001", "Arturo", "Mendez", date(1979, 3, 14), "Bronze HDHP", 300000, 300000),
    ("M-10002", "Priya", "Raman", date(1988, 11, 2), "Gold PPO", 25000, 61040),
    ("M-10003", "Gerald", "Okafor", date(1956, 6, 30), "Silver PPO", 50000, 88215),
    ("M-10004", "Hannah", "Lindqvist", date(1995, 1, 19), "Bronze HDHP", 300000, 342585),
    ("M-10005", "Marcus", "Bell", date(1969, 8, 8), "Gold PPO", 25000, 40210),
    ("M-10006", "Sofia", "Castellano", date(2001, 4, 27), "Silver PPO", 50000, 52100),
    ("M-10007", "Dana", "Whitfield", date(1984, 9, 5), "Silver PPO", 0, 0),
    ("M-10008", "Wei", "Zhang", date(1973, 12, 11), "Bronze HDHP", 300000, 415505),
    ("M-10009", "Olivia", "Brennan", date(1990, 7, 3), "Gold PPO", 25000, 33055),
    ("M-10010", "Tomás", "Herrera", date(1962, 2, 21), "Silver PPO", 50000, 71230),
    ("M-10011", "Keisha", "Grant", date(1998, 10, 16), "Gold PPO", 25000, 27450),
    ("M-10012", "Noah", "Abernathy", date(1985, 5, 9), "Bronze HDHP", 300000, 319880),
]

PROVIDERS = [
    ("1487623905", "Riverside Medical Group"),
    ("1730291846", "Cascade Family Practice"),
    ("1265849302", "Summit Physical Therapy"),
    ("1902384751", "Northside Imaging Center"),
    ("1548203967", "Lakeview Behavioral Health"),
]

VISIT_TEMPLATES = {
    "1487623905": [["99214", "85025", "36415"], ["99213", "80053", "36415"], ["99215", "93000"]],
    "1730291846": [["99213"], ["99213", "87880"], ["99214", "71046"]],
    "1265849302": [["97110", "97140"], ["97110"]],
    "1902384751": [["71046"], ["72148"]],
    "1548203967": [["90834"]],
}


def billed_for(rng: random.Random, allowed_cents: int, units: int) -> int:
    markup = rng.uniform(1.4, 2.4)
    return int(allowed_cents * units * markup) // 100 * 100


def make_lines(rng: random.Random, fees: dict[str, int], codes: list[str]) -> list[ClaimLine]:
    lines = []
    for i, code in enumerate(codes, start=1):
        units = 2 if code.startswith("971") else 1
        lines.append(
            ClaimLine(line_number=i, cpt_code=code, units=units, billed_cents=billed_for(rng, fees[code], units))
        )
    return lines


def main() -> None:
    rng = random.Random(20260901)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    plans = {
        p.name: p
        for p in [
            Plan(name="Bronze HDHP", deductible_cents=300000, oop_max_cents=700000, coinsurance_rate=0.3),
            Plan(name="Silver PPO", deductible_cents=50000, oop_max_cents=400000, coinsurance_rate=0.2),
            Plan(name="Gold PPO", deductible_cents=25000, oop_max_cents=250000, coinsurance_rate=0.1),
        ]
    }
    db.add_all(plans.values())
    db.add_all(FeeScheduleEntry(cpt_code=c, description=d, allowed_cents=a) for c, d, a in FEE_SCHEDULE)
    fees = {c: a for c, _, a in FEE_SCHEDULE}

    providers = {npi: Provider(npi=npi, name=name) for npi, name in PROVIDERS}
    db.add_all(providers.values())

    members = {}
    for number, first, last, dob, plan_name, ded_met, oop_met in MEMBERS:
        m = Member(
            member_number=number,
            first_name=first,
            last_name=last,
            date_of_birth=dob,
            plan=plans[plan_name],
            coverage_start=date(2026, 1, 1),
        )
        members[number] = m
        db.add(m)
    db.flush()
    for number, *_, ded_met, oop_met in MEMBERS:
        db.add(Accumulator(member_id=members[number].id, plan_year=2026, deductible_met_cents=ded_met, oop_met_cents=oop_met))
    db.commit()

    seq = 0

    def next_number() -> str:
        nonlocal seq
        seq += 1
        return f"CLM-2026-{seq:05d}"

    # --- September: adjudicated history -----------------------------------
    other_members = [m for n, m in members.items() if n != "M-10007"]
    september = []
    for day in range(1, 29):
        for _ in range(rng.choice([1, 1, 2])):
            npi = rng.choice(list(VISIT_TEMPLATES))
            service = date(2026, 9, day)
            submitted = datetime(2026, 9, day, rng.randint(8, 17), rng.randint(0, 59), rng.randint(0, 59))
            september.append((submitted, rng.choice(other_members), npi, service, rng.choice(VISIT_TEMPLATES[npi])))

    # Dana Whitfield: first visit of the year, MRI + follow-up + PT eval
    september.append(
        (datetime(2026, 9, 14, 16, 2, 41), members["M-10007"], "1730291846", date(2026, 9, 14), ["72148", "99214", "97110"])
    )
    september.sort(key=lambda t: t[0])

    for submitted, member, npi, service, codes in september:
        claim = Claim(
            claim_number=next_number(),
            member=member,
            provider=providers[npi],
            service_date=service,
            submitted_at=submitted,
            source=ClaimSource.PORTAL,
            status=ClaimStatus.PENDING,
            lines=make_lines(rng, fees, codes),
        )
        db.add(claim)
        db.commit()
        adjudicate_claim(db, claim)
        claim.adjudicated_at = submitted + timedelta(days=rng.choice([1, 2]), hours=rng.randint(0, 6))
        db.commit()

    # --- October 1: today's pending work queue ----------------------------
    pending: list[tuple[datetime, ClaimSource, str, list[str]]] = []
    for i in range(10):
        npi = rng.choice(list(VISIT_TEMPLATES))
        pending.append((datetime(2026, 10, 1, 7, 12) + timedelta(minutes=7 * i, seconds=rng.randint(0, 59)), ClaimSource.PORTAL, npi, rng.choice(VISIT_TEMPLATES[npi])))
    # Riverside's nightly 837 batch file lands all at once
    batch_time = datetime(2026, 10, 1, 9, 30, 0)
    for _ in range(24):
        pending.append((batch_time, ClaimSource.EDI_BATCH, "1487623905", rng.choice(VISIT_TEMPLATES["1487623905"])))
    for i in range(13):
        npi = rng.choice(list(VISIT_TEMPLATES))
        codes = rng.choice(VISIT_TEMPLATES[npi])
        if i == 4:
            npi, codes = "1265849302", ["97110", "97140", "97799"]
        pending.append((datetime(2026, 10, 1, 10, 4) + timedelta(minutes=9 * i, seconds=rng.randint(0, 59)), ClaimSource.PORTAL, npi, codes))

    fees_with_unlisted = {**fees, "97799": 4500}
    for submitted, source, npi, codes in pending:
        db.add(
            Claim(
                claim_number=next_number(),
                member=rng.choice(other_members),
                provider=providers[npi],
                service_date=(submitted - timedelta(days=rng.randint(1, 10))).date(),
                submitted_at=submitted,
                source=source,
                status=ClaimStatus.PENDING,
                lines=make_lines(rng, fees_with_unlisted, codes),
            )
        )
    db.commit()
    db.close()
    print(f"Seeded {seq} claims ({len(september)} adjudicated, {len(pending)} pending).")


if __name__ == "__main__":
    main()
