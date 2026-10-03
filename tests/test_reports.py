from datetime import date, timedelta

from tests.conftest import claim_payload


def test_reconciliation_balances(client):
    for lines in (
        [{"cpt_code": "72148", "units": 1, "billed_cents": 90000}],
        [{"cpt_code": "99214", "units": 1, "billed_cents": 25000}],
        [{"cpt_code": "99213", "units": 1, "billed_cents": 20000}],
    ):
        number = client.post("/claims", json=claim_payload(lines=lines)).json()["claim_number"]
        client.post(f"/claims/{number}/adjudicate")

    today = date.today()
    window = {"start": (today - timedelta(days=1)).isoformat(), "end": (today + timedelta(days=1)).isoformat()}
    report = client.get("/reports/reconciliation", params=window).json()
    assert report["claims_checked"] == 3
    assert report["discrepancies"] == []
    assert report["total_allowed_cents"] == (
        report["total_plan_paid_cents"] + report["total_patient_responsibility_cents"]
    )
