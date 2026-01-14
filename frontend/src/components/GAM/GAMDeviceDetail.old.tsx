import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  Chip,
  CircularProgress,
} from '@mui/material'
import api from '../../services/api'
import type { GAMDevice, GAMPort } from '../../types'

export default function GAMDeviceDetail() {
  const { deviceId } = useParams()

  const { data: device, isLoading: deviceLoading } = useQuery<GAMDevice>({
    queryKey: ['device', deviceId],
    queryFn: async () => {
      const response = await api.get(`/gam/devices/${deviceId}`)
      return response.data
    },
    enabled: !!deviceId,
  })

  const { data: ports, isLoading: portsLoading } = useQuery<GAMPort[]>({
    queryKey: ['device-ports', deviceId],
    queryFn: async () => {
      const response = await api.get(`/gam/devices/${deviceId}/ports`)
      return response.data
    },
    enabled: !!deviceId,
  })

  if (deviceLoading || portsLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    )
  }

  if (!device) {
    return <Typography>Device not found</Typography>
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        {device.name}
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Device Information
            </Typography>
            <Box display="flex" flexDirection="column" gap={2}>
              <Box>
                <Typography variant="body2" color="textSecondary">
                  IP Address
                </Typography>
                <Typography variant="body1">{device.ip_address}</Typography>
              </Box>
              <Box>
                <Typography variant="body2" color="textSecondary">
                  Model
                </Typography>
                <Typography variant="body1">{device.model}</Typography>
              </Box>
              <Box>
                <Typography variant="body2" color="textSecondary">
                  Status
                </Typography>
                <Chip label={device.status} color="success" size="small" />
              </Box>
              <Box>
                <Typography variant="body2" color="textSecondary">
                  Location
                </Typography>
                <Typography variant="body1">{device.location || 'Not set'}</Typography>
              </Box>
              <Box>
                <Typography variant="body2" color="textSecondary">
                  Firmware Version
                </Typography>
                <Typography variant="body1">
                  {device.firmware_version || 'Unknown'}
                </Typography>
              </Box>
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Performance Metrics
            </Typography>
            <Box display="flex" flexDirection="column" gap={2}>
              <Box>
                <Typography variant="body2" color="textSecondary">
                  Uptime
                </Typography>
                <Typography variant="body1">
                  {device.uptime ? `${Math.floor(device.uptime / 3600)} hours` : 'N/A'}
                </Typography>
              </Box>
              <Box>
                <Typography variant="body2" color="textSecondary">
                  CPU Usage
                </Typography>
                <Typography variant="body1">
                  {device.cpu_usage ? `${device.cpu_usage}%` : 'N/A'}
                </Typography>
              </Box>
              <Box>
                <Typography variant="body2" color="textSecondary">
                  Memory Usage
                </Typography>
                <Typography variant="body1">
                  {device.memory_usage ? `${device.memory_usage}%` : 'N/A'}
                </Typography>
              </Box>
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Ports
            </Typography>
            <Grid container spacing={2}>
              {ports && ports.length > 0 ? (
                ports.map((port) => (
                  <Grid item xs={6} sm={4} md={3} key={port.id}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="h6">Port {port.port_number}</Typography>
                        <Typography variant="body2" color="textSecondary">
                          {port.port_type.toUpperCase()}
                        </Typography>
                        <Chip
                          label={port.status}
                          size="small"
                          color={port.status === 'up' ? 'success' : 'default'}
                          sx={{ mt: 1 }}
                        />
                      </CardContent>
                    </Card>
                  </Grid>
                ))
              ) : (
                <Grid item xs={12}>
                  <Typography color="textSecondary">No ports available</Typography>
                </Grid>
              )}
            </Grid>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  )
}
