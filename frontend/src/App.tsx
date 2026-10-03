import { useState, type FormEvent } from 'react'
import { ClaimDetail } from './views/ClaimDetail'
import { MemberView } from './views/MemberView'
import { QueueView } from './views/QueueView'
import { ReconciliationView } from './views/ReconciliationView'

type Tab = 'queue' | 'members' | 'reconciliation'

const TABS: { id: Tab; label: string }[] = [
  { id: 'queue', label: 'Work queue' },
  { id: 'members', label: 'Members' },
  { id: 'reconciliation', label: 'Reconciliation' },
]

export default function App() {
  const [tab, setTab] = useState<Tab>('queue')
  const [openClaim, setOpenClaim] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [refreshKey, setRefreshKey] = useState(0)

  function findClaim(e: FormEvent) {
    e.preventDefault()
    if (search.trim()) setOpenClaim(search.trim().toUpperCase())
  }

  return (
    <div className="app">
      <header className="topbar">
        <h1>Claims Ops</h1>
        <nav>
          {TABS.map((t) => (
            <button key={t.id} className={tab === t.id ? 'tab active' : 'tab'} onClick={() => setTab(t.id)}>
              {t.label}
            </button>
          ))}
        </nav>
        <form onSubmit={findClaim} className="search">
          <input placeholder="Find claim, e.g. CLM-2026-00018" value={search} onChange={(e) => setSearch(e.target.value)} />
        </form>
      </header>

      <main>
        {tab === 'queue' && <QueueView onOpenClaim={setOpenClaim} refreshKey={refreshKey} />}
        {tab === 'members' && <MemberView />}
        {tab === 'reconciliation' && <ReconciliationView onOpenClaim={setOpenClaim} />}
      </main>

      {openClaim && (
        <ClaimDetail
          key={openClaim}
          claimNumber={openClaim}
          onClose={() => setOpenClaim(null)}
          onAdjudicated={() => setRefreshKey((k) => k + 1)}
        />
      )}
    </div>
  )
}
