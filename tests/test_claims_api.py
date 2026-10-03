from datetime import datetime, timedelta

from sqlalchemy import update

from app.models import Claim
from tests.conftest import claim_payload


def test_submit_and_fetch_claim(client):
    r = client.post("/claims", json=claim_payload())
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "pending"
    assert body["claim_number"].startswith("CLM-")
    assert len(body["lines"]) == 1

    r = client.get(f"/claims/{body['claim_number']}")
    assert r.status_code == 200
    assert r.json()["member_number"] == "M-1"


def test_submit_rejects_unknown_member(client):
    r = client.post("/claims", json=claim_payload(member="M-404"))
    assert r.status_code == 422


def test_adjudicate_applies_deductible(client):
    number = client.post("/claims", json=claim_payload()).json()["claim_number"]
    r = client.post(f"/claims/{number}/adjudicate")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "adjudicated"
    assert body["allowed_cents"] == 11000
    assert body["deductible_cents"] == 11000
    assert body["plan_paid_cents"] == 0
    assert body["patient_responsibility_cents"] == 11000

    acc = client.get("/members/M-1/accumulators/2026").json()
    assert acc["deductible_met_cents"] == 11000
    assert acc["oop_met_cents"] == 11000


def test_adjudicate_crosses_deductible_across_claims(client):
    first = client.post(
        "/claims", json=claim_payload(lines=[{"cpt_code": "72148", "units": 1, "billed_cents": 90000}])
    ).json()["claim_number"]
    body = client.post(f"/claims/{first}/adjudicate").json()
    assert body["deductible_cents"] == 50000
    assert body["coinsurance_cents"] == 2000
    assert body["plan_paid_cents"] == 8000

    second = client.post("/claims", json=claim_payload()).json()["claim_number"]
    body = client.post(f"/claims/{second}/adjudicate").json()
    assert body["deductible_cents"] == 0
    assert body["coinsurance_cents"] == 2200
    assert body["plan_paid_cents"] == 8800


def test_allowed_is_lesser_of_billed_and_fee_schedule(client):
    number = client.post(
        "/claims", json=claim_payload(lines=[{"cpt_code": "99213", "units": 1, "billed_cents": 9000}])
    ).json()["claim_number"]
    body = client.post(f"/claims/{number}/adjudicate").json()
    assert body["allowed_cents"] == 9000


def test_ineligible_member_is_denied(client):
    number = client.post("/claims", json=claim_payload(member="M-2")).json()["claim_number"]
    body = client.post(f"/claims/{number}/adjudicate").json()
    assert body["status"] == "denied"
    assert body["denial_reason"] == "INELIGIBLE"


def test_work_queue_pages_oldest_first(client, db):
    numbers = [client.post("/claims", json=claim_payload()).json()["claim_number"] for _ in range(5)]
    base = datetime(2026, 10, 1, 9, 0)
    for i, n in enumerate(numbers):
        db.execute(update(Claim).where(Claim.claim_number == n).values(submitted_at=base + timedelta(minutes=i)))
    db.commit()

    seen = []
    cursor = None
    while True:
        params = {"limit": 2, **({"cursor": cursor} if cursor else {})}
        page = client.get("/claims", params=params).json()
        seen += [c["claim_number"] for c in page["items"]]
        cursor = page["next_cursor"]
        if cursor is None:
            break
    assert seen == numbers


def test_queue_stats(client):
    for _ in range(3):
        client.post("/claims", json=claim_payload())
    number = client.post("/claims", json=claim_payload()).json()["claim_number"]
    client.post(f"/claims/{number}/adjudicate")
    assert client.get("/claims/stats").json() == {"pending": 3, "adjudicated": 1, "denied": 0}
