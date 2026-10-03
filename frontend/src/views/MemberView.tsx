import { useState, type FormEvent } from 'react'
import { api, type Accumulators } from '../api'
import { money } from '../format'

export function MemberView() {
  const [memberNumber, setMemberNumber] = useState('')
  const [planYear, setPlanYear] = useState(2026)
  const [acc, setAcc] = useState<Accumulators | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function lookup(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setAcc(null)
    try {
      setAcc(await api.accumulators(memberNumber.trim(), planYear))
    } catch (err) {
      setError((err as { status?: number }).status === 404 ? 'Member not found.' : 'Something went wrong.')
    }
  }

  return (
    <section>
      <h2>Member benefits</h2>
      <form className="inline-form" onSubmit={lookup}>
        <input
          placeholder="Member number, e.g. M-10007"
          value={memberNumber}
          onChange={(e) => setMemberNumber(e.target.value)}
          required
        />
        <input
          type="number"
          className="narrow"
          value={planYear}
          onChange={(e) => setPlanYear(Number(e.target.value))}
          aria-label="Plan year"
        />
        <button type="submit">Look up</button>
      </form>

      {error && <p className="error">{error}</p>}

      {acc && (
        <div className="card">
          <h3>
            <span className="mono">{acc.member_number}</span> · {acc.plan_name} · {acc.plan_year}
          </h3>
          <Meter label="Deductible" met={acc.deductible_met_cents} limit={acc.deductible_cents} />
          <Meter label="Out-of-pocket max" met={acc.oop_met_cents} limit={acc.oop_max_cents} />
        </div>
      )}
    </section>
  )
}

function Meter({ label, met, limit }: { label: string; met: number; limit: number }) {
  const pct = limit > 0 ? Math.min(100, (met / limit) * 100) : 100
  return (
    <div className="meter">
      <div className="meter-label">
        <span>{label}</span>
        <span>
          {money(met)} of {money(limit)}
        </span>
      </div>
      <div className="meter-track">
        <div className="meter-fill" style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}
