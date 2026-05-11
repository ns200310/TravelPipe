import polyline from '@mapbox/polyline'
import { Card, Text } from '@mantine/core'
import { CircleMarker, MapContainer, Polyline, Popup, TileLayer } from 'react-leaflet'
import { useMapData } from '../hooks/useMapData'
import type { ShapeRow } from '../api/dashboard'

const BOSTON_CENTER: [number, number] = [42.36, -71.06]
const DEFAULT_ZOOM = 12

const severityColor = (severity: number): string => {
  if (severity >= 7) return '#e03131'
  if (severity > 0) return '#f59f00'
  return '#868e96'
}

const shapeWeight = (shape: ShapeRow): number => {
  if (shape.max_severity >= 7) return 5
  if (shape.max_severity > 0) return 4
  return 2
}

const shapeColor = (shape: ShapeRow): string => {
  if (shape.max_severity > 0) return severityColor(shape.max_severity)
  if (shape.color) return `#${shape.color}`
  return '#adb5bd'
}

export function MapView() {
  const { shapes, alertStops, loading, error } = useMapData()

  return (
    <Card withBorder radius="md" padding="lg" shadow="sm">
      <Text fw={600} mb="sm">
        Network Map
      </Text>
      <Text size="xs" c="dimmed" mb="md">
        Route paths coloured by today's peak alert severity. Pins mark stops in active alerts.
      </Text>
      {error && (
        <Text size="sm" c="red" mb="sm">
          {error}
        </Text>
      )}
      <div style={{ height: 480, borderRadius: 8, overflow: 'hidden' }}>
        <MapContainer
          center={BOSTON_CENTER}
          zoom={DEFAULT_ZOOM}
          style={{ height: '100%', width: '100%' }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {shapes?.map((shape) => {
            const positions = polyline.decode(shape.polyline) as [number, number][]
            return (
              <Polyline
                key={shape.shape_id}
                positions={positions}
                pathOptions={{
                  color: shapeColor(shape),
                  weight: shapeWeight(shape),
                  opacity: shape.max_severity > 0 ? 0.95 : 0.55,
                }}
              />
            )
          })}
          {alertStops?.map((stop) => (
            <CircleMarker
              key={stop.stop_id}
              center={[stop.latitude, stop.longitude]}
              radius={7}
              pathOptions={{
                color: severityColor(stop.max_severity),
                fillColor: severityColor(stop.max_severity),
                fillOpacity: 0.8,
                weight: 2,
              }}
            >
              <Popup>
                <div style={{ fontSize: 12 }}>
                  <strong>{stop.name}</strong>
                  <br />
                  Alerts: {stop.alert_count}
                  <br />
                  Max severity: {stop.max_severity}
                </div>
              </Popup>
            </CircleMarker>
          ))}
        </MapContainer>
      </div>
      {loading && !shapes && (
        <Text size="xs" c="dimmed" mt="xs">
          Loading map data…
        </Text>
      )}
    </Card>
  )
}
