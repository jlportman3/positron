import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  MenuItem,
  Alert,
  CircularProgress,
} from '@mui/material'
import api from '../../services/api'
import type { Subscriber, GAMDevice, GAMPort, BandwidthPlan } from '../../types'

export default function ProvisioningPage() {
  const [selectedSubscriber, setSelectedSubscriber] = useState('')
  const [selectedDevice, setSelectedDevice] = useState('')
  const [selectedPort, setSelectedPort] = useState('')
  const [selectedPlan, setSelectedPlan] = useState('')

  const { data: subscribers } = useQuery<Subscriber[]>({
    queryKey: ['subscribers'],
    queryFn: async () => {
      const response = await api.get('/subscribers?status=pending')
      return response.data
    },
  })

  const { data: devices } = useQuery<GAMDevice[]>({
    queryKey: ['devices'],
    queryFn: async () => {
      const response = await api.get('/gam/devices?status=online')
      return response.data
    },
  })

  const { data: ports } = useQuery<GAMPort[]>({
    queryKey: ['device-ports', selectedDevice],
    queryFn: async () => {
      const response = await api.get(`/gam/devices/${selectedDevice}/ports`)
      return response.data
    },
    enabled: !!selectedDevice,
  })

  const provisionMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post('/provisioning/provision', {
        subscriber_id: selectedSubscriber,
        gam_port_id: selectedPort,
        bandwidth_plan_id: selectedPlan,
      })
      return response.data
    },
    onSuccess: () => {
      // Reset form
      setSelectedSubscriber('')
      setSelectedDevice('')
      setSelectedPort('')
      setSelectedPlan('')
    },
  })

  const handleProvision = () => {
    provisionMutation.mutate()
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Subscriber Provisioning
      </Typography>

      <Paper sx={{ p: 3, maxWidth: 600 }}>
        <Box display="flex" flexDirection="column" gap={3}>
          <TextField
            select
            label="Subscriber"
            value={selectedSubscriber}
            onChange={(e) => setSelectedSubscriber(e.target.value)}
            fullWidth
          >
            {subscribers?.map((sub) => (
              <MenuItem key={sub.id} value={sub.id}>
                {sub.name} - {sub.email}
              </MenuItem>
            ))}
          </TextField>

          <TextField
            select
            label="GAM Device"
            value={selectedDevice}
            onChange={(e) => {
              setSelectedDevice(e.target.value)
              setSelectedPort('')
            }}
            fullWidth
          >
            {devices?.map((device) => (
              <MenuItem key={device.id} value={device.id}>
                {device.name} - {device.ip_address}
              </MenuItem>
            ))}
          </TextField>

          <TextField
            select
            label="Port"
            value={selectedPort}
            onChange={(e) => setSelectedPort(e.target.value)}
            disabled={!selectedDevice}
            fullWidth
          >
            {ports?.map((port) => (
              <MenuItem key={port.id} value={port.id}>
                Port {port.port_number} - {port.port_type} ({port.status})
              </MenuItem>
            ))}
          </TextField>

          <TextField
            select
            label="Bandwidth Plan"
            value={selectedPlan}
            onChange={(e) => setSelectedPlan(e.target.value)}
            fullWidth
          >
            <MenuItem value="plan1">100/100 Mbps</MenuItem>
            <MenuItem value="plan2">500/500 Mbps</MenuItem>
            <MenuItem value="plan3">1000/1000 Mbps</MenuItem>
          </TextField>

          {provisionMutation.isError && (
            <Alert severity="error">
              Provisioning failed. Please try again.
            </Alert>
          )}

          {provisionMutation.isSuccess && (
            <Alert severity="success">
              Subscriber provisioned successfully!
            </Alert>
          )}

          <Button
            variant="contained"
            onClick={handleProvision}
            disabled={
              !selectedSubscriber ||
              !selectedPort ||
              !selectedPlan ||
              provisionMutation.isPending
            }
          >
            {provisionMutation.isPending ? <CircularProgress size={24} /> : 'Provision'}
          </Button>
        </Box>
      </Paper>
    </Box>
  )
}
