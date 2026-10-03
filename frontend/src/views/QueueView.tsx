import { useEffect, useState } from 'react'
import { api, type ClaimPage, type ClaimSummary, type QueueStats } from '../api'
import { dateTime } from '../format'

interface Props {
  onOpenClaim: (claimNumber: string) => void
  refreshKey: number
}

export function QueueView({ onOpenClaim, refreshKey }: Props) {
  const [stats, setStats] = useState<QueueStats | null>(null)
  const [claims, setClaims] = useState<ClaimSummary[]>([])
  const [cursor, setCursor] = useState<string | null>(null)
  const [done, setDone] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  function applyPage(page: ClaimPage, append: boolean) {
    setClaims((prev) => (append ? [...prev, ...page.items] : page.items))
    setCursor(page.next_cursor)
    setDone(page.next_cursor === null)
    setError(null)
  }

  useEffect(() => {
    api.stats().then(setStats).catch(() => setStats(null))
    api
      .queue(null)
      .then((page) => applyPage(page, false))
      .catch(() => setError('Something went wrong loading the queue.'))
  }, [refreshKey])

  async function loadMore() {
    setLoading(true)
    try {
      applyPage(await api.queue(cursor), true)
    } catch {
      setError('Something went wrong loading the queue.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <section>
      <div className="stats">
        <Stat label="Pending" value={stats?.pending} />
        <Stat label="Adjudicated" value={stats?.adjudicated} />
        <Stat label="Denied" value={stats?.denied} />
      </div>

      <h2>Work queue</h2>
      <p className="muted">Oldest first. Showing {claims.length} claims.</p>

      <table>
        <thead>
          <tr>
            <th>Claim</th>
            <th>Submitted</th>
            <th>Service date</th>
            <th>Source</th>
          </tr>
        </thead>
        <tbody>
          {claims.map((c) => (
            <tr key={c.claim_number} className="clickable" onClick={() => onOpenClaim(c.claim_number)}>
              <td className="mono">{c.claim_number}</td>
              <td>{dateTime(c.submitted_at)}</td>
              <td>{c.service_date}</td>
              <td>
                <span className={`tag tag-${c.source}`}>{c.source === 'edi_batch' ? 'EDI batch' : 'Portal'}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {error && <p className="error">{error}</p>}
      <div className="queue-footer">
        {done ? (
          <span className="muted">End of queue.</span>
        ) : (
          <button onClick={loadMore} disabled={loading}>
            {loading ? 'Loading…' : 'Load more'}
          </button>
        )}
      </div>
    </section>
  )
}

function Stat({ label, value }: { label: string; value: number | undefined }) {
  return (
    <div className="stat">
      <div className="stat-value">{value ?? '—'}</div>
      <div className="stat-label">{label}</div>
    </div>
  )
}
