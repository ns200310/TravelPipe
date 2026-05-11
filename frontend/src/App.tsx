import { LineChart } from '@mantine/charts'
import { createTheme, MantineProvider } from '@mantine/core'
import React from 'react'

const theme = createTheme({})

const App = () => {
  return (
    <MantineProvider theme={theme}>
      <LineChart
      h={300}
      data={[
        { date: '2023-01-01', Apples: 30, Oranges: 20, Tomatoes: 10 },
        { date: '2023-01-02', Apples: 40, Oranges: 25, Tomatoes: 15 },
        { date: '2023-01-03', Apples: 35, Oranges: 30, Tomatoes: 20 },
        { date: '2023-01-04', Apples: 50, Oranges: 35, Tomatoes: 25 },
      ]}
      dataKey="date"
      series={[
        { name: 'Apples', color: 'indigo.6' },
        { name: 'Oranges', color: 'blue.6' },
        { name: 'Tomatoes', color: 'teal.6' },
      ]}
      curveType="linear"
    />
    </MantineProvider>
    
  )
}

export default App