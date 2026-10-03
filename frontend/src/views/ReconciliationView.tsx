import { useEffect, useState } from 'react'
import { api, type ReconciliationReport } from '../api'
import { money } from '../format'

interface Props {
  onOpenClaim: (claimNumber: string) => void
}

export function ReconciliationView({ onOpenClaim }: Props) {
  const [start, setStart] = useState('2026-09-01')
  const [end, setEnd] = useState('2026-09-30')
  const [report, setReport] = useState<ReconciliationReport | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .reconciliation(start, end)
      .then((r) => {
        setReport(r)
        setError(null)
      })
      .catch(() => setError('Something went wrong.'))
  }, [start, end])

  return (
    <section>
      <h2>Reconciliation</h2>
      <p className="muted">Every adjudicated claim must satisfy: allowed = plan paid + member responsibility.</p>
      <div className="inline-form">
        <label>
          From <input type="date" value={start} onChange={(e) => setStart(e.target.value)} />
        </label>
        <label>
          To <input type="date" value={end} onChange={(e) => setEnd(e.target.value)} />
        </label>
      </div>

      {error && <p className="error">{error}</p>}

      {report && (
        <>
          <div className="stats">
            <Stat label="Claims checked" value={String(report.claims_checked)} />
            <Stat label="Allowed" value={money(report.total_allowed_cents)} />
            <Stat label="Plan paid" value={money(report.total_plan_paid_cents)} />
            <Stat label="Member responsibility" value={money(report.total_patient_responsibility_cents)} />
          </div>

          {report.discrepancies.length === 0 ? (
            <p className="ok">✓ All claims tie out.</p>
          ) : (
            <>
              <p className="error">{report.discrepancies.length} claims don't tie out.</p>
              <table>
                <thead>
                  <tr>
                    <th>Claim</th>
                    <th className="num">Allowed</th>
                    <th className="num">Plan paid</th>
                    <th className="num">Member resp.</th>
                    <th className="num">Variance</th>
                  </tr>
                </thead>
                <tbody>
                  {report.discrepancies.map((d) => (
                    <tr key={d.claim_number} className="clickable" onClick={() => onOpenClaim(d.claim_number)}>
                      <td className="mono">{d.claim_number}</td>
                      <td className="num">{money(d.allowed_cents)}</td>
                      <td className="num">{money(d.plan_paid_cents)}</td>
                      <td className="num">{money(d.patient_responsibility_cents)}</td>
                      <td className="num error">{money(d.variance_cents)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
        </>
      )}
    </section>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="stat">
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
    </div>
  )
}
