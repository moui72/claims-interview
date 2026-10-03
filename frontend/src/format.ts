const usd = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' })

export function money(cents: number): string {
  return usd.format(cents / 100)
}

// API timestamps are naive UTC
export function dateTime(iso: string): string {
  return `${iso.replace('T', ' ').slice(0, 16)} UTC`
}
