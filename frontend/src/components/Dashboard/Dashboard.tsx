import { useQuery } from '@tanstack/react-query'
import {
  Grid,
  Paper,
  Typography,
  Box,
  CircularProgress,
  Card,
  CardContent,
} from '@mui/material'
import {
  Router as RouterIcon,
  People as PeopleIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
} from '@mui/icons-material'
import api from '../../services/api'
import type { GAMDevice, Subscriber } from '../../types'

export default function Dashboard() {
  const { data: devices, isLoading: devicesLoading } = useQuery<GAMDevice[]>({
    queryKey: ['devices'],
    queryFn: async () => {
      const response = await api.get('/gam/devices')
      return response.data
    },
  })

  const { data: subscribers, isLoading: subscribersLoading } = useQuery<Subscriber[]>({
    queryKey: ['subscribers'],
    queryFn: async () => {
      const response = await api.get('/subscribers')
      return response.data
    },
  })

  if (devicesLoading || subscribersLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    )
  }

  const onlineDevices = devices?.filter((d) => d.status === 'online').length || 0
  const totalDevices = devices?.length || 0
  const activeSubscribers = subscribers?.filter((s) => s.status === 'active').length || 0
  const totalSubscribers = subscribers?.length || 0

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2}>
                <RouterIcon color="primary" sx={{ fontSize: 40 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Total Devices
                  </Typography>
                  <Typography variant="h4">{totalDevices}</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2}>
                <CheckCircleIcon color="success" sx={{ fontSize: 40 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Online Devices
                  </Typography>
                  <Typography variant="h4">{onlineDevices}</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2}>
                <PeopleIcon color="primary" sx={{ fontSize: 40 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Total Subscribers
                  </Typography>
                  <Typography variant="h4">{totalSubscribers}</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2}>
                <CheckCircleIcon color="success" sx={{ fontSize: 40 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Active Subscribers
                  </Typography>
                  <Typography variant="h4">{activeSubscribers}</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Recent Devices
            </Typography>
            {devices && devices.length > 0 ? (
              <Box>
                {devices.slice(0, 5).map((device) => (
                  <Box
                    key={device.id}
                    display="flex"
                    justifyContent="space-between"
                    alignItems="center"
                    py={1}
                    borderBottom="1px solid #eee"
                  >
                    <Box>
                      <Typography variant="body1">{device.name}</Typography>
                      <Typography variant="body2" color="textSecondary">
                        {device.ip_address} - {device.model}
                      </Typography>
                    </Box>
                    <Box display="flex" alignItems="center" gap={1}>
                      {device.status === 'online' ? (
                        <CheckCircleIcon color="success" />
                      ) : (
                        <ErrorIcon color="error" />
                      )}
                      <Typography variant="body2">{device.status}</Typography>
                    </Box>
                  </Box>
                ))}
              </Box>
            ) : (
              <Typography color="textSecondary">No devices found</Typography>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  )
}
