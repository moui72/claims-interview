# Open tickets

Sample data in `scripts/seed.py` reproduces the state described in each ticket.
Re-run the seed any time to reset.

---

## CLAIMS-1182 · Claim stuck — adjudication keeps failing

**Reporter:** Jordan (Claims Ops) · **Priority:** High

Claim **CLM-2026-00074** from Summit Physical Therapy errors out every time we
try to adjudicate it. The ops tool just says "Something went wrong." It's been
sitting in the queue since yesterday and the provider's billing office has
called twice.

---

## CLAIMS-1185 · Member says she was overcharged toward her deductible

**Reporter:** Renee (Member Services) · **Priority:** High

Dana Whitfield (**M-10007**, Silver PPO) called about her EOB for her Sept 14
visit (**CLM-2026-00018**). The EOB shows **$552.35** applied to her deductible
and $0 paid by the plan. Her deductible is $500 and she says this was her
first visit of the year.

Can someone confirm what she should have owed and what happened? She also asked
whether this has happened to anyone else, and I'd like to be able to answer her.

---

## CLAIMS-1190 · September reconciliation report is off by pennies

**Reporter:** Marcus (Finance) · **Priority:** Medium

The reconciliation report for September (`/reports/reconciliation?start=2026-09-01&end=2026-09-30`)
flags 9 claims where allowed ≠ plan paid + patient responsibility. All of them
are off by 1–2 cents. We think the report has a rounding issue somewhere. Can
someone look at the report? We can't close the month until it ties out.

---

## CLAIMS-1193 · Work queue doesn't match the dashboard

**Reporter:** Jordan (Claims Ops) · **Priority:** Medium

The dashboard says **47** claims pending, but when the team works the queue
page by page they only get through about 33 before it says there's nothing
left. Is the dashboard count wrong?

Separately, Riverside Medical Group says some claims from last night's batch
haven't been processed. Might be related, might not be.

---

## CLAIMS-1196 · Adjudicated claims don't leave the queue

**Reporter:** Jordan (Claims Ops) · **Priority:** Low

After I adjudicate a claim in the ops console, it stays in the work queue and
the Pending count doesn't go down. If I click the claim again it shows the
Adjudicate button again like nothing happened. A browser refresh fixes it.

Not a huge deal, but twice this week two people on the team adjudicated the
same claim because of it. Hopefully that's harmless?
