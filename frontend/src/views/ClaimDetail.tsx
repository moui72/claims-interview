import { useEffect, useState } from 'react'
import { api, type Claim } from '../api'
import { dateTime, money } from '../format'

interface Props {
  claimNumber: string
  onClose: () => void
  onAdjudicated: () => void
}

export function ClaimDetail({ claimNumber, onClose, onAdjudicated }: Props) {
  const [claim, setClaim] = useState<Claim | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    api
      .claim(claimNumber)
      .then(setClaim)
      .catch((e) => setError(e.status === 404 ? `No claim ${claimNumber}.` : 'Something went wrong.'))
  }, [claimNumber])

  async function adjudicate() {
    setBusy(true)
    setError(null)
    try {
      setClaim(await api.adjudicate(claimNumber))
      onAdjudicated()
    } catch {
      setError('Something went wrong.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <aside className="drawer">
      <header className="drawer-header">
        <h2 className="mono">{claimNumber}</h2>
        <button className="ghost" onClick={onClose} aria-label="Close">
          ✕
        </button>
      </header>

      {error && <p className="error">{error}</p>}
      {!claim && !error && <p className="muted">Loading…</p>}

      {claim && (
        <>
          <dl className="facts">
            <dt>Status</dt>
            <dd>
              <span className={`tag tag-${claim.status}`}>{claim.status}</span>
              {claim.denial_reason && <span className="muted"> · {claim.denial_reason}</span>}
            </dd>
            <dt>Member</dt>
            <dd className="mono">{claim.member_number}</dd>
            <dt>Provider NPI</dt>
            <dd className="mono">{claim.provider_npi}</dd>
            <dt>Service date</dt>
            <dd>{claim.service_date}</dd>
            <dt>Submitted</dt>
            <dd>{dateTime(claim.submitted_at)}</dd>
            {claim.adjudicated_at && (
              <>
                <dt>Adjudicated</dt>
                <dd>{dateTime(claim.adjudicated_at)}</dd>
              </>
            )}
          </dl>

          <table className="lines">
            <thead>
              <tr>
                <th>#</th>
                <th>CPT</th>
                <th>Units</th>
                <th className="num">Billed</th>
                <th className="num">Allowed</th>
                <th className="num">Deductible</th>
                <th className="num">Coins.</th>
                <th className="num">Plan paid</th>
              </tr>
            </thead>
            <tbody>
              {claim.lines.map((l) => (
                <tr key={l.line_number} className={l.status === 'denied' ? 'denied' : undefined}>
                  <td>{l.line_number}</td>
                  <td className="mono" title={l.denial_reason ?? undefined}>
                    {l.cpt_code}
                  </td>
                  <td>{l.units}</td>
                  <td className="num">{money(l.billed_cents)}</td>
                  <td className="num">{money(l.allowed_cents)}</td>
                  <td className="num">{money(l.deductible_cents)}</td>
                  <td className="num">{money(l.coinsurance_cents)}</td>
                  <td className="num">{money(l.plan_paid_cents)}</td>
                </tr>
              ))}
            </tbody>
          </table>

          {claim.status !== 'pending' && (
            <dl className="totals">
              <dt>Billed</dt>
              <dd>{money(claim.billed_cents)}</dd>
              <dt>Allowed</dt>
              <dd>{money(claim.allowed_cents)}</dd>
              <dt>Plan paid</dt>
              <dd>{money(claim.plan_paid_cents)}</dd>
              <dt>Member owes</dt>
              <dd>
                {money(claim.patient_responsibility_cents)}
                <span className="muted">
                  {' '}
                  ({money(claim.deductible_cents)} deductible + {money(claim.coinsurance_cents)} coinsurance)
                </span>
              </dd>
            </dl>
          )}

          {claim.status === 'pending' && (
            <button className="primary" onClick={adjudicate} disabled={busy}>
              {busy ? 'Adjudicating…' : 'Adjudicate'}
            </button>
          )}
        </>
      )}
    </aside>
  )
}
