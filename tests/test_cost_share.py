from app.services.cost_share import split_line


def test_deductible_absorbs_whole_line():
    split = split_line(10000, deductible_remaining_cents=50000, oop_remaining_cents=400000, coinsurance_rate=0.2)
    assert split.deductible_cents == 10000
    assert split.coinsurance_cents == 0
    assert split.plan_paid_cents == 0


def test_coinsurance_after_deductible():
    split = split_line(60000, deductible_remaining_cents=50000, oop_remaining_cents=400000, coinsurance_rate=0.2)
    assert split.deductible_cents == 50000
    assert split.coinsurance_cents == 2000
    assert split.plan_paid_cents == 8000


def test_deductible_already_met():
    split = split_line(16000, deductible_remaining_cents=0, oop_remaining_cents=400000, coinsurance_rate=0.2)
    assert split.deductible_cents == 0
    assert split.coinsurance_cents == 3200
    assert split.plan_paid_cents == 12800


def test_out_of_pocket_max_caps_member_share():
    split = split_line(60000, deductible_remaining_cents=50000, oop_remaining_cents=30000, coinsurance_rate=0.2)
    assert split.patient_cents == 30000
    assert split.deductible_cents == 30000
    assert split.coinsurance_cents == 0
    assert split.plan_paid_cents == 30000


def test_out_of_pocket_max_already_met():
    split = split_line(16000, deductible_remaining_cents=0, oop_remaining_cents=0, coinsurance_rate=0.2)
    assert split.patient_cents == 0
    assert split.plan_paid_cents == 16000
