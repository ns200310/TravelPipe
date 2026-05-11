const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export type ChartSeries = {
  labels: string[]
  data: number[]
}

export type DashboardCharts = {
  alert_effects: ChartSeries
  impacted_routes: ChartSeries
  fleet_composition: ChartSeries
  activity_status: ChartSeries
}

export type RouteStatus = {
  id: string
  long_name: string | null
  color: string | null
  type: number | null
  alert_count: number
  max_severity: number
  status_text: string
  status_class: 'stable' | 'minor' | 'severe'
  modality: string
}

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`)
  if (!res.ok) throw new Error(`${path} failed: ${res.status}`)
  return res.json() as Promise<T>
}

export type HistoryRow = {
  timestamp: string
  vehicles: number
  alerts: number
  routes: number
  health_pct: number
}

export const fetchCharts = () => getJson<DashboardCharts>('/api/dashboard/charts')
export const fetchRoutes = () => getJson<RouteStatus[]>('/api/dashboard/routes')

export const fetchHistory = (sinceIso?: string, limit = 1000) => {
  const qs = new URLSearchParams()
  if (sinceIso) qs.set('since', sinceIso)
  qs.set('limit', String(limit))
  return getJson<HistoryRow[]>(`/api/dashboard/history?${qs.toString()}`)
}

export type ShapeRow = {
  route_id: string
  shape_id: string
  polyline: string
  color: string | null
  max_severity: number
}

export type AlertStop = {
  stop_id: string
  name: string
  latitude: number
  longitude: number
  alert_count: number
  max_severity: number
}

export const fetchShapes = () => getJson<ShapeRow[]>('/api/dashboard/shapes')
export const fetchAlertStops = () => getJson<AlertStop[]>('/api/dashboard/alert-stops')
