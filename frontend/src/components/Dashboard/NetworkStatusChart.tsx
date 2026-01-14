import { Card, CardHeader, CardContent, Box } from '@mui/material'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'

interface NetworkStatusChartProps {
  data: Array<{
    time: string
    online: number
    offline: number
    total: number
  }>
}

const NetworkStatusChart = ({ data }: NetworkStatusChartProps) => {
  return (
    <Card>
      <CardHeader title="Network Status" titleTypographyProps={{ variant: 'h6' }} />
      <CardContent>
        <Box sx={{ width: '100%', height: 300 }}>
          <ResponsiveContainer>
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
              <XAxis
                dataKey="time"
                tick={{ fontSize: 12 }}
                tickMargin={10}
              />
              <YAxis tick={{ fontSize: 12 }} tickMargin={10} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#fff',
                  border: '1px solid #ddd',
                  borderRadius: 4,
                }}
              />
              <Legend
                wrapperStyle={{ paddingTop: 20 }}
                iconType="line"
              />
              <Line
                type="monotone"
                dataKey="online"
                stroke="#4caf50"
                strokeWidth={2}
                name="Online Devices"
                dot={{ fill: '#4caf50', r: 3 }}
                activeDot={{ r: 5 }}
              />
              <Line
                type="monotone"
                dataKey="offline"
                stroke="#f44336"
                strokeWidth={2}
                name="Offline Devices"
                dot={{ fill: '#f44336', r: 3 }}
                activeDot={{ r: 5 }}
              />
              <Line
                type="monotone"
                dataKey="total"
                stroke="#2196f3"
                strokeWidth={2}
                name="Total Devices"
                dot={{ fill: '#2196f3', r: 3 }}
                activeDot={{ r: 5 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </Box>
      </CardContent>
    </Card>
  )
}

export default NetworkStatusChart
