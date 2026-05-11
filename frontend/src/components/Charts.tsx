import { SimpleGrid } from '@mantine/core'
import { AlertEffectsTreemap } from './charts/AlertEffectsTreemap'
import { ImpactedRoutesBar } from './charts/ImpactedRoutesBar'
import { FleetCompositionRadar } from './charts/FleetCompositionRadar'

const Charts = ({charts}: {charts: any}) => {
  return (
    <SimpleGrid cols={{ base: 1, md: 2 }} spacing="md">
      <AlertEffectsTreemap series={charts.alert_effects} />
      <ImpactedRoutesBar series={charts.impacted_routes} />
      <FleetCompositionRadar series={charts.fleet_composition} />
    </SimpleGrid>
  );
}

export default Charts
