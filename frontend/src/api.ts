export type ClaimStatus = 'pending' | 'adjudicated' | 'denied'

export interface ClaimSummary {
  claim_number: string
  service_date: string
  submitted_at: string
  source: 'portal' | 'edi_batch'
  status: ClaimStatus
}

export interface ClaimPage {
  items: ClaimSummary[]
  next_cursor: string | null
}

export interface QueueStats {
  pending: number
  adjudicated: number
  denied: number
}

export interface ClaimLine {
  line_number: number
  cpt_code: string
  units: number
  billed_cents: number
  status: 'paid' | 'denied' | null
  denial_reason: string | null
  allowed_cents: number
  deductible_cents: number
  coinsurance_cents: number
  plan_paid_cents: number
}

export interface Claim {
  claim_number: string
  member_number: string
  provider_npi: string
  service_date: string
  submitted_at: string
  source: 'portal' | 'edi_batch'
  status: ClaimStatus
  denial_reason: string | null
  billed_cents: number
  allowed_cents: number
  deductible_cents: number
  coinsurance_cents: number
  plan_paid_cents: number
  patient_responsibility_cents: number
  adjudicated_at: string | null
  lines: ClaimLine[]
}

export interface Accumulators {
  member_number: string
  plan_name: string
  plan_year: number
  deductible_cents: number
  deductible_met_cents: number
  oop_max_cents: number
  oop_met_cents: number
}

export interface ReconciliationRow {
  claim_number: string
  allowed_cents: number
  plan_paid_cents: number
  patient_responsibility_cents: number
  variance_cents: number
}

export interface ReconciliationReport {
  start: string
  end: string
  claims_checked: number
  total_allowed_cents: number
  total_plan_paid_cents: number
  total_patient_responsibility_cents: number
  discrepancies: ReconciliationRow[]
}

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

// Cache GETs briefly so switching tabs doesn't refetch everything
const CACHE_TTL_MS = 5 * 60 * 1000
const cache = new Map<string, { at: number; data: unknown }>()

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const isGet = !init?.method || init.method === 'GET'
  if (isGet) {
    const hit = cache.get(path)
    if (hit && Date.now() - hit.at < CACHE_TTL_MS) return hit.data as T
  }

  const res = await fetch(`/api${path}`, init)
  if (!res.ok) {
    let detail = res.statusText
    try {
      detail = (await res.json()).detail ?? detail
    } catch {
      // non-JSON error body
    }
    throw new ApiError(res.status, detail)
  }
  const data = (await res.json()) as T
  if (isGet) cache.set(path, { at: Date.now(), data })
  return data
}

export const api = {
  queue: (cursor: string | null, limit = 20) => {
    const params = new URLSearchParams({ status: 'pending', limit: String(limit) })
    if (cursor) params.set('cursor', cursor)
    return request<ClaimPage>(`/claims?${params}`)
  },
  stats: () => request<QueueStats>('/claims/stats'),
  claim: (claimNumber: string) => request<Claim>(`/claims/${encodeURIComponent(claimNumber)}`),
  adjudicate: (claimNumber: string) =>
    request<Claim>(`/claims/${encodeURIComponent(claimNumber)}/adjudicate`, { method: 'POST' }),
  accumulators: (memberNumber: string, planYear: number) =>
    request<Accumulators>(`/members/${encodeURIComponent(memberNumber)}/accumulators/${planYear}`),
  reconciliation: (start: string, end: string) =>
    request<ReconciliationReport>(`/reports/reconciliation?${new URLSearchParams({ start, end })}`),
}
