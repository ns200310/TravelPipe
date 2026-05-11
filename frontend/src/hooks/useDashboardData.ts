import { useEffect, useState } from 'react'
import {
  fetchCharts,
  fetchHistory,
  fetchRoutes,
  type DashboardCharts,
  type HistoryRow,
  type RouteStatus,
} from '../api/dashboard'

const POLL_INTERVAL_MS = 30_000
const HISTORY_WINDOW_MS = 24 * 60 * 60 * 1000

export type DashboardData = {
  charts: DashboardCharts | null
  routes: RouteStatus[] | null
  history: HistoryRow[] | null
  loading: boolean
  error: string | null
}

export function useDashboardData(): DashboardData {
  const [charts, setCharts] = useState<DashboardCharts | null>(null)
  const [routes, setRoutes] = useState<RouteStatus[] | null>(null)
  const [history, setHistory] = useState<HistoryRow[] | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function refresh() {
      try {
        const since = new Date(Date.now() - HISTORY_WINDOW_MS).toISOString()
        const [ c, r, h] = await Promise.all([
          fetchCharts(),
          fetchRoutes(),
          fetchHistory(since),
        ])
        if (cancelled) return
        setCharts(c)
        setRoutes(r)
        setHistory(h)
        setError(null)
      } catch (err) {
        if (cancelled) return
        setError(err instanceof Error ? err.message : String(err))
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    refresh()
    const id = setInterval(refresh, POLL_INTERVAL_MS)
    return () => {
      cancelled = true
      clearInterval(id)
    }
  }, [])

  return { charts, routes, history, loading, error }
}
