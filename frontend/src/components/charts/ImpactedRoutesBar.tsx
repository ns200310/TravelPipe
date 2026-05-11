import { BarChart } from '@mantine/charts'
import { Card, Text } from '@mantine/core'
import type { ChartSeries } from '../../api/dashboard'

type Props = { series: ChartSeries }

export function ImpactedRoutesBar({ series }: Props) {
  const data = series.labels.map((name, i) => ({
    route: name,
    alerts: series.data[i] ?? 0,
  }))

  return (
    <Card withBorder radius="md" padding="lg" shadow="sm">
      <Text fw={600} mb="sm">
        Top Impacted Routes
      </Text>
      <BarChart
        h={300}
        data={data}
        dataKey="route"
        orientation="vertical"
        yAxisProps={{ width: 110 }}
        series={[{ name: 'alerts', color: 'red.6' }]}
        withTooltip
      />
    </Card>
  )
}
