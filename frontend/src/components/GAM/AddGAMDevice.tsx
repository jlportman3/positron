import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import {
  Box,
  Paper,
  TextField,
  Button,
  Typography,
  Alert,
  CircularProgress,
  Stepper,
  Step,
  StepLabel,
  Grid,
  Divider,
} from '@mui/material'
import {
  Search as SearchIcon,
  Add as AddIcon,
  ArrowBack as BackIcon,
} from '@mui/icons-material'
import api from '../../services/api'

interface DiscoveredDevice {
  ip_address: string
  model: string
  firmware_version?: string
  serial_number?: string
  mac_address?: string
  system_description?: string
  system_name?: string
  uptime?: string
  interface_count?: number
}

const AddGAMDevice = () => {
  const navigate = useNavigate()
  const [activeStep, setActiveStep] = useState(0)

  // Form fields
  const [ipAddress, setIpAddress] = useState('')
  const [snmpCommunity, setSnmpCommunity] = useState('public')
  const [deviceName, setDeviceName] = useState('')
  const [sshUsername, setSshUsername] = useState('admin')
  const [sshPassword, setSshPassword] = useState('')
  const [sshPort, setSshPort] = useState('22')

  // Discovery results
  const [discoveredDevice, setDiscoveredDevice] = useState<DiscoveredDevice | null>(null)
  const [discoveryError, setDiscoveryError] = useState<string | null>(null)

  const steps = ['Enter IP Address', 'Discover Device', 'Confirm & Add']

  // Discovery mutation
  const discoverMutation = useMutation({
    mutationFn: async (data: { ip_address: string; snmp_community: string }) => {
      const response = await api.post('/gam/devices/discover', data)
      return response.data
    },
    onSuccess: (data) => {
      if (data.success && data.device_info) {
        setDiscoveredDevice(data.device_info)
        setDeviceName(data.device_info.system_name || `GAM-${ipAddress}`)
        setDiscoveryError(null)
        setActiveStep(1)
      } else {
        setDiscoveryError(data.message || 'Failed to discover device')
      }
    },
    onError: (error: any) => {
      setDiscoveryError(
        error.response?.data?.detail ||
        'Failed to discover device. Please check IP address and SNMP community.'
      )
    },
  })

  // Add device mutation
  const addDeviceMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post('/gam/devices/discover', {
        ip_address: ipAddress,
        snmp_community: snmpCommunity,
        name: deviceName,
        ssh_username: sshUsername,
        ssh_password: sshPassword,
        ssh_port: parseInt(sshPort),
      })
      return response.data
    },
    onSuccess: (data) => {
      if (data.success) {
        navigate('/devices')
      }
    },
    onError: (error: any) => {
      setDiscoveryError(
        error.response?.data?.detail ||
        'Failed to add device to database.'
      )
    },
  })

  const handleDiscover = () => {
    if (!ipAddress) {
      setDiscoveryError('Please enter an IP address')
      return
    }

    setDiscoveryError(null)
    discoverMutation.mutate({ ip_address: ipAddress, snmp_community: snmpCommunity })
  }

  const handleAddDevice = () => {
    setActiveStep(2)
    addDeviceMutation.mutate()
  }

  const handleBack = () => {
    if (activeStep > 0) {
      setActiveStep(activeStep - 1)
      setDiscoveryError(null)
    } else {
      navigate('/devices')
    }
  }

  return (
    <Box>
      <Box display="flex" alignItems="center" mb={3}>
        <Button
          startIcon={<BackIcon />}
          onClick={() => navigate('/devices')}
          sx={{ mr: 2 }}
        >
          Back to Devices
        </Button>
        <Typography variant="h5" sx={{ fontWeight: 500 }}>
          Add GAM Device
        </Typography>
      </Box>

      <Paper sx={{ p: 4 }}>
        <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        {discoveryError && (
          <Alert severity="error" sx={{ mb: 3 }} onClose={() => setDiscoveryError(null)}>
            {discoveryError}
          </Alert>
        )}

        {/* Step 0: Enter IP Address */}
        {activeStep === 0 && (
          <Box>
            <Typography variant="h6" gutterBottom>
              Device Connection Information
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              Enter the IP address and SNMP community string of the GAM device you want to add.
            </Typography>

            <Grid container spacing={3} sx={{ mt: 2 }}>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="IP Address"
                  value={ipAddress}
                  onChange={(e) => setIpAddress(e.target.value)}
                  placeholder="192.168.1.100"
                  helperText="The management IP address of the GAM device"
                  autoFocus
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="SNMP Community"
                  value={snmpCommunity}
                  onChange={(e) => setSnmpCommunity(e.target.value)}
                  placeholder="public"
                  helperText="SNMP read community string (default: public)"
                />
              </Grid>

              {/* SSH Credentials Section */}
              <Grid item xs={12}>
                <Divider sx={{ my: 2 }} />
                <Typography variant="subtitle2" gutterBottom>
                  SSH Credentials (Optional - for CLI access)
                </Typography>
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="SSH Username"
                  value={sshUsername}
                  onChange={(e) => setSshUsername(e.target.value)}
                  placeholder="admin"
                  helperText="Default: admin"
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  type="password"
                  label="SSH Password"
                  value={sshPassword}
                  onChange={(e) => setSshPassword(e.target.value)}
                  placeholder="••••••••"
                  helperText="Leave blank if not using password auth"
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="SSH Port"
                  value={sshPort}
                  onChange={(e) => setSshPort(e.target.value)}
                  placeholder="22"
                  helperText="Default: 22"
                  type="number"
                />
              </Grid>
            </Grid>

            <Box sx={{ mt: 4, display: 'flex', justifyContent: 'flex-end' }}>
              <Button onClick={handleBack} sx={{ mr: 2 }}>
                Cancel
              </Button>
              <Button
                variant="contained"
                onClick={handleDiscover}
                startIcon={discoverMutation.isPending ? <CircularProgress size={20} /> : <SearchIcon />}
                disabled={discoverMutation.isPending || !ipAddress}
              >
                {discoverMutation.isPending ? 'Discovering...' : 'Discover Device'}
              </Button>
            </Box>
          </Box>
        )}

        {/* Step 1: Discovery Results */}
        {activeStep === 1 && discoveredDevice && (
          <Box>
            <Alert severity="success" sx={{ mb: 3 }}>
              Device discovered successfully!
            </Alert>

            <Typography variant="h6" gutterBottom>
              Discovered Device Information
            </Typography>

            <Grid container spacing={3} sx={{ mt: 2 }}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Device Name"
                  value={deviceName}
                  onChange={(e) => setDeviceName(e.target.value)}
                  helperText="Friendly name for this device"
                />
              </Grid>

              <Grid item xs={12}>
                <Divider sx={{ my: 2 }} />
                <Typography variant="subtitle2" gutterBottom>
                  Auto-Detected Information
                </Typography>
              </Grid>

              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="IP Address"
                  value={discoveredDevice.ip_address}
                  disabled
                />
              </Grid>

              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Model"
                  value={discoveredDevice.model || 'Unknown'}
                  disabled
                />
              </Grid>

              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="MAC Address"
                  value={discoveredDevice.mac_address || 'N/A'}
                  disabled
                />
              </Grid>

              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Serial Number"
                  value={discoveredDevice.serial_number || 'N/A'}
                  disabled
                />
              </Grid>

              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Firmware Version"
                  value={discoveredDevice.firmware_version || 'N/A'}
                  disabled
                />
              </Grid>

              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Interface Count"
                  value={discoveredDevice.interface_count || 'N/A'}
                  disabled
                />
              </Grid>

              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="System Description"
                  value={discoveredDevice.system_description || 'N/A'}
                  disabled
                  multiline
                  rows={2}
                />
              </Grid>
            </Grid>

            <Box sx={{ mt: 4, display: 'flex', justifyContent: 'space-between' }}>
              <Button onClick={handleBack}>
                Back
              </Button>
              <Button
                variant="contained"
                onClick={handleAddDevice}
                startIcon={<AddIcon />}
                disabled={!deviceName}
              >
                Add Device to System
              </Button>
            </Box>
          </Box>
        )}

        {/* Step 2: Adding Device */}
        {activeStep === 2 && (
          <Box textAlign="center" py={4}>
            {addDeviceMutation.isPending ? (
              <>
                <CircularProgress size={60} sx={{ mb: 3 }} />
                <Typography variant="h6" gutterBottom>
                  Adding device to system...
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Initializing ports and configuration
                </Typography>
              </>
            ) : addDeviceMutation.isSuccess ? (
              <>
                <Alert severity="success" sx={{ mb: 3 }}>
                  Device added successfully!
                </Alert>
                <Typography variant="body2" color="text.secondary">
                  Redirecting to devices list...
                </Typography>
              </>
            ) : null}
          </Box>
        )}
      </Paper>
    </Box>
  )
}

export default AddGAMDevice
