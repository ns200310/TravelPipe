import { ColorSwatch, Group, Text, useMantineTheme } from '@mantine/core'

type LegendItem = {
  name: string
  value: number
  color: string
}

type Props = {
  items: LegendItem[]
}

function resolveColor(theme: ReturnType<typeof useMantineTheme>, colorRef: string): string {
  const match = /^([a-zA-Z]+)\.(\d+)$/.exec(colorRef)
  if (match) {
    const [, name, shade] = match
    const palette = theme.colors[name]
    if (palette) return palette[Number(shade)] ?? colorRef
  }
  return colorRef
}

export function ChartLegend({ items }: Props) {
  const theme = useMantineTheme()
  return (
    <Group gap="xs" mt="sm" wrap="wrap">
      {items.map((item) => (
        <Group key={item.name} gap={6} wrap="nowrap">
          <ColorSwatch color={resolveColor(theme, item.color)} size={10} withShadow={false} />
          <Text size="xs" c="dimmed">
            {item.name} ({item.value})
          </Text>
        </Group>
      ))}
    </Group>
  )
}
