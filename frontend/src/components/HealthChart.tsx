import { useEffect, useState } from 'react';
import { Box, Card, CardContent, Typography, ToggleButton, ToggleButtonGroup, Skeleton } from '@mui/material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { healthApi } from '../services/api';

interface HealthChartProps {
  deviceId: string;
}

interface DataPoint {
  timestamp: string;
  score: number;
}

export default function HealthChart({ deviceId }: HealthChartProps) {
  const [period, setPeriod] = useState('7d');
  const [data, setData] = useState<DataPoint[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    healthApi.getDeviceHistory(deviceId, period)
      .then(res => {
        setData(res.data.data_points.map((p: any) => ({
          timestamp: new Date(p.timestamp).toLocaleDateString(),
          score: p.score,
        })));
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [deviceId, period]);

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">Health History</Typography>
          <ToggleButtonGroup
            value={period}
            exclusive
            onChange={(_, v) => v && setPeriod(v)}
            size="small"
          >
            <ToggleButton value="24h">24h</ToggleButton>
            <ToggleButton value="7d">7d</ToggleButton>
            <ToggleButton value="30d">30d</ToggleButton>
          </ToggleButtonGroup>
        </Box>

        {loading ? (
          <Skeleton variant="rectangular" height={200} />
        ) : (
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timestamp" fontSize={12} />
              <YAxis domain={[0, 100]} fontSize={12} />
              <Tooltip />
              <Line
                type="monotone"
                dataKey="score"
                stroke="#1976d2"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}
