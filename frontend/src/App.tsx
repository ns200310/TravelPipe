import {
  createTheme,
  MantineProvider,
} from '@mantine/core'

import Dashboard from './pages/Dashboard'

const theme = createTheme({
  primaryColor: 'indigo',
  defaultRadius: 'md',
})

const App = () => (
  <MantineProvider theme={theme} defaultColorScheme="auto">
    <Dashboard />
  </MantineProvider>
)

export default App
