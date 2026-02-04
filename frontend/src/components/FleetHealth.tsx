import { useEffect, useState } from 'react';
import { Box, Card, CardContent, Typography, Grid, Skeleton } from '@mui/material';
import { healthApi } from '../services/api';

interface FleetSummary {
  fleet_size: number;
  fleet_avg_score: number;
  by_status: {
    healthy: number;
    degraded: number;
    critical: number;
    offline: number;
  };
  worst_performers: Array<{
    device_id: string;
    serial_number: string;
    name: string;
    health_score: number;
    health_status: string;
  }>;
}

export default function FleetHealth() {
  const [summary, setSummary] = useState<FleetSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    healthApi.getFleetSummary('24h')
      .then(res => setSummary(res.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <Skeleton variant="rectangular" height={200} />;
  }

  if (!summary) {
    return null;
  }

  const { by_status, fleet_avg_score, fleet_size } = summary;

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Fleet Health
        </Typography>

        <Grid container spacing={2}>
          <Grid item xs={6}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              <Box
                sx={{
                  width: 12,
                  height: 12,
                  borderRadius: '50%',
                  bgcolor: 'success.main',
                }}
              />
              <Typography variant="body2">
                {by_status.healthy} Healthy
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              <Box
                sx={{
                  width: 12,
                  height: 12,
                  borderRadius: '50%',
                  bgcolor: 'warning.main',
                }}
              />
              <Typography variant="body2">
                {by_status.degraded} Degraded
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              <Box
                sx={{
                  width: 12,
                  height: 12,
                  borderRadius: '50%',
                  bgcolor: 'error.main',
                }}
              />
              <Typography variant="body2">
                {by_status.critical} Critical
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Box
                sx={{
                  width: 12,
                  height: 12,
                  borderRadius: '50%',
                  bgcolor: 'grey.500',
                }}
              />
              <Typography variant="body2">
                {by_status.offline} Offline
              </Typography>
            </Box>
          </Grid>

          <Grid item xs={6}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h3" color="primary">
                {fleet_avg_score}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Avg Health Score
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {fleet_size} devices
              </Typography>
            </Box>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
}
