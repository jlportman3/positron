import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Chip,
  Button,
  TextField,
  InputAdornment,
  CircularProgress,
  Alert,
} from '@mui/material'
import {
  Add as AddIcon,
  Search as SearchIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material'
import api from '../../services/api'

interface UnconfiguredCPE {
  id: string
  mac_address: string
  gam_device_name: string
  gam_port: number
  port_type: string
  link_speed_down?: number
  link_speed_up?: number
  snr_downstream?: number
  snr_upstream?: number
  last_seen?: string
  model?: string
}

const UnconfiguredCPEList = () => {
  const [searchTerm, setSearchTerm] = useState('')

  const { data: unconfiguredDevices, isLoading, error, refetch } = useQuery<UnconfiguredCPE[]>({
    queryKey: ['unconfigured-cpe'],
    queryFn: async () => {
      const response = await api.get('/cpe/unconfigured')
      return response.data
    },
  })

  const filteredDevices = unconfiguredDevices?.filter(
    (device) =>
      device.mac_address.toLowerCase().includes(searchTerm.toLowerCase()) ||
      device.gam_device_name.toLowerCase().includes(searchTerm.toLowerCase())
  ) || []

  const getSignalQuality = (snr?: number): { label: string; color: 'success' | 'info' | 'warning' | 'error' } => {
    if (!snr) return { label: 'Unknown', color: 'error' }
    if (snr >= 40) return { label: 'Excellent', color: 'success' }
    if (snr >= 35) return { label: 'Good', color: 'info' }
    if (snr >= 25) return { label: 'Fair', color: 'warning' }
    return { label: 'Poor', color: 'error' }
  }

  const handleProvision = (device: UnconfiguredCPE) => {
    // Navigate to provisioning page with device pre-filled
    console.log('Provision device:', device)
  }

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    )
  }

  if (error) {
    return (
      <Box>
        <Typography variant="h5" sx={{ mb: 3, fontWeight: 500 }}>
          Unconfigured CPE Devices
        </Typography>
        <Alert severity="error">
          Failed to load unconfigured CPE devices. Please try again later.
        </Alert>
      </Box>
    )
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h5" sx={{ fontWeight: 500 }}>
            Unconfigured CPE Devices
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
            Customer premises equipment connected to GAM devices but not yet assigned to subscribers
          </Typography>
        </Box>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={() => refetch()}
        >
          Refresh
        </Button>
      </Box>

      <Paper>
        <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
          <TextField
            fullWidth
            size="small"
            placeholder="Search by MAC address or GAM device..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
          />
        </Box>

        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>MAC Address</TableCell>
                <TableCell>Model</TableCell>
                <TableCell>GAM Device</TableCell>
                <TableCell>Port</TableCell>
                <TableCell>Port Type</TableCell>
                <TableCell>Link Speed</TableCell>
                <TableCell>SNR (dB)</TableCell>
                <TableCell>Signal Quality</TableCell>
                <TableCell>Last Seen</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredDevices.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={10} align="center" sx={{ py: 8 }}>
                    <Typography variant="body2" color="text.secondary">
                      {searchTerm
                        ? 'No unconfigured devices match your search'
                        : 'No unconfigured CPE devices found'}
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                filteredDevices.map((device) => {
                  const signalQuality = getSignalQuality(device.snr_downstream)
                  const linkSpeed = device.link_speed_down && device.link_speed_up
                    ? `${device.link_speed_down}/${device.link_speed_up} Mbps`
                    : 'N/A'

                  return (
                    <TableRow key={device.id} hover>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                          {device.mac_address}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">{device.model || 'Unknown'}</Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">{device.gam_device_name}</Typography>
                      </TableCell>
                      <TableCell>
                        <Chip label={`Port ${device.gam_port}`} size="small" />
                      </TableCell>
                      <TableCell>
                        <Chip label={device.port_type} size="small" variant="outlined" />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>
                          {linkSpeed}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {device.snr_downstream ?? 'N/A'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={signalQuality.label}
                          size="small"
                          color={signalQuality.color}
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" color="text.secondary">
                          {device.last_seen || 'Unknown'}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Button
                          size="small"
                          variant="contained"
                          startIcon={<AddIcon />}
                          onClick={() => handleProvision(device)}
                        >
                          Provision
                        </Button>
                      </TableCell>
                    </TableRow>
                  )
                })
              )}
            </TableBody>
          </Table>
        </TableContainer>

        {filteredDevices.length > 0 && (
          <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              Showing {filteredDevices.length} unconfigured {filteredDevices.length === 1 ? 'device' : 'devices'}
            </Typography>
          </Box>
        )}
      </Paper>
    </Box>
  )
}

export default UnconfiguredCPEList
