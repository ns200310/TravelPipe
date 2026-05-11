import { RadarChart } from '@mantine/charts'
import { Card, Text } from '@mantine/core'
import type { ChartSeries } from '../../api/dashboard'

type Props = { series: ChartSeries }

export function FleetCompositionRadar({ series }: Props) {
  const data = series.labels.map((modality, i) => ({
    modality,
    vehicles: Math.sqrt(series.data[i] ?? 0),
  }))

  const maxScaled = data.reduce((m, d) => Math.max(m, d.vehicles), 0)
  const axisMax = Math.max(5, Math.ceil(maxScaled / 5) * 5)

  return (
    <Card withBorder radius="md" padding="lg" shadow="sm">
      <Text fw={600} mb="sm">
        Fleet Modal Breakdown
      </Text>
      <Text size="xs" c="dimmed" mb="sm">
        Square-root scale of active vehicle counts — compresses the dominant modality so smaller ones stay visible.
      </Text>
      <RadarChart
        h={300}
        data={data}
        dataKey="modality"
        withPolarRadiusAxis
        polarRadiusAxisProps={{ domain: [0, axisMax], tickCount: 5 }}
        series={[{ name: 'vehicles', color: 'indigo.5', opacity: 0.35 }]}
      />
    </Card>
  )
}
