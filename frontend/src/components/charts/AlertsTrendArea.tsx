import { CompositeChart } from '@mantine/charts'
import { Card, Text } from '@mantine/core'
import type { HistoryRow } from '../../api/dashboard'

type Props = { history: HistoryRow[] }

const MAX_POINTS = 120

function formatClock(iso: string): string {
  const d = new Date(iso)
  const hh = String(d.getHours()).padStart(2, '0')
  const mm = String(d.getMinutes()).padStart(2, '0')
  return `${hh}:${mm}`
}

export function AlertsTrendArea({ history }: Props) {
  const points = history.slice(-MAX_POINTS).map((row) => ({
    time: formatClock(row.timestamp),
    alerts: row.alerts,
    vehicles: row.vehicles,
  }))

  return (
    <Card withBorder radius="md" padding="lg" shadow="sm">
      <Text fw={600} mb="sm">
        Active Alerts & Vehicles — Last 24 Hours
      </Text>
      {points.length === 0 ? (
        <Text size="sm" c="dimmed">
          Collecting data…
        </Text>
      ) : (
        <CompositeChart
          h={260}
          data={points}
          dataKey="time"
          curveType="monotone"
          withRightYAxis
          yAxisLabel="Alerts"
          rightYAxisLabel="Vehicles"
          withLegend
          withDots={false}
          gridAxis="xy"
          series={[
            { name: 'alerts', color: 'red.6', type: 'area' },
            { name: 'vehicles', color: 'indigo.5', type: 'line', yAxisId: 'right' },
          ]}
        />
      )}
    </Card>
  )
}
