import { Group, Stack, Title } from '@mantine/core'
import { ColorSchemeToggle } from './ColorSchemeToggle'

const Header = () => {
  return (
    <Group justify="space-between" align="flex-end">
              <Stack gap={2}>
                <Title order={2}>MBTA Analytical Dashboard</Title>
              </Stack>
              <ColorSchemeToggle />
    </Group>
  )
}

export default Header
