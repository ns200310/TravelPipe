import { Treemap } from '@mantine/charts'
import { Card, Text } from '@mantine/core'
import type { ChartSeries } from '../../api/dashboard'
import { ChartLegend } from './ChartLegend'

type Props = { series: ChartSeries }

const PALETTE = [
  'indigo.6',
  'teal.6',
  'orange.6',
  'pink.6',
  'cyan.6',
  'grape.6',
  'lime.6',
  'red.6',
  'blue.6',
  'yellow.7',
]

export function AlertEffectsTreemap({ series }: Props) {
  const data = series.labels.map((name, i) => ({
    name: name.replace(/_/g, ' '),
    value: series.data[i] ?? 0,
    color: PALETTE[i % PALETTE.length],
  }))

  return (
    <Card withBorder radius="md" padding="lg" shadow="sm">
      <Text fw={600} mb="sm">
        Alert Effects Distribution
      </Text>
      <Treemap data={data} h={260} withTooltip />
      <ChartLegend items={data} />
    </Card>
  )
}
