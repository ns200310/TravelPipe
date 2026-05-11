import { MapView } from '../components/MapView'
import { AlertsTrendArea } from '../components/charts/AlertsTrendArea'
import { useDashboardData } from '../hooks/useDashboardData'
import { 
    Alert, 
    Container,
    Stack 
} from '@mantine/core'
import Header from '../components/Header'
import LoadingScreen from '../components/LoadingScreen'
import Charts from '../components/Charts'

const Dashboard = () => {
  const { charts, history, loading, error } = useDashboardData()

  if (loading) {
    return (
      <LoadingScreen />
    )
  }

  return (
    <Container size="xl" py="lg">
      <Stack gap="lg">
        <Header />

        {error && (
          <Alert color="red" title="Failed to load dashboard data">
            {error}
          </Alert>
        )}

        <AlertsTrendArea history={history ?? []} />

        <MapView />

        {charts && (
            <Charts charts={charts} />
        )}
      </Stack>
    </Container>
  )
}

export default Dashboard