import { useEffect, useState } from 'react'
import {
  fetchAlertStops,
  fetchShapes,
  type AlertStop,
  type ShapeRow,
} from '../api/dashboard'
import type { MapData } from '../types/hookTypes'

const POLL_INTERVAL_MS = 30_000



export function useMapData(): MapData {
  const [shapes, setShapes] = useState<ShapeRow[] | null>(null)
  const [alertStops, setAlertStops] = useState<AlertStop[] | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function refresh() {
      try {
        const [s, a] = await Promise.all([fetchShapes(), fetchAlertStops()])
        if (cancelled) return
        setShapes(s)
        setAlertStops(a)
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

  return { shapes, alertStops, loading, error }
}
