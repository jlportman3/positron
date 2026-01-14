import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Tabs,
  Tab,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Tooltip,
  Alert,
  List,
  ListItem,
  ListItemText,
  Divider,
} from '@mui/material'
import {
  ArrowBack as ArrowBackIcon,
  Refresh as RefreshIcon,
  Sync as SyncIcon,
  Edit as EditIcon,
  Cable as CableIcon,
  Router as RouterIcon,
  DeviceHub as DeviceHubIcon,
} from '@mui/icons-material'
import api from '../../services/api'
import type { GAMDevice, GAMPort } from '../../types'

interface TabPanelProps {
  children?: React.ReactNode
  index: number
  value: number
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props
  return (
    <div role="tabpanel" hidden={value !== index} {...other}>
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  )
}

export default function GAMDeviceDetailEnhanced() {
  const { deviceId } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [tabValue, setTabValue] = useState(0)

  const { data: device, isLoading: deviceLoading } = useQuery<GAMDevice>({
    queryKey: ['device', deviceId],
    queryFn: async () => {
      const response = await api.get(`/gam/devices/${deviceId}`)
      return response.data
    },
    enabled: !!deviceId,
  })

  const { data: ports, isLoading: portsLoading, refetch: refetchPorts } = useQuery<GAMPort[]>({
    queryKey: ['device-ports', deviceId],
    queryFn: async () => {
      const response = await api.get(`/gam/devices/${deviceId}/ports`)
      return response.data
    },
    enabled: !!deviceId,
  })

  const { data: discoveredCPE, isLoading: cpeLoading, refetch: refetchCPE } = useQuery({
    queryKey: ['discovered-cpe', deviceId],
    queryFn: async () => {
      const response = await api.get(`/gam/devices/${deviceId}/discovered-cpe`)
      return response.data
    },
    enabled: !!deviceId && tabValue === 2,
  })

  const syncPortsMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post(`/gam/devices/${deviceId}/sync-ports`)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['device-ports', deviceId] })
      refetchPorts()
    },
  })

  if (deviceLoading || portsLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    )
  }

  if (!device) {
    return (
      <Box>
        <Alert severity="error">Device not found</Alert>
        <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/devices')} sx={{ mt: 2 }}>
          Back to Devices
        </Button>
      </Box>
    )
  }

  const portStats = {
    total: ports?.length || 0,
    up: ports?.filter((p) => p.status === 'up').length || 0,
    down: ports?.filter((p) => p.status === 'down').length || 0,
    disabled: ports?.filter((p) => !p.enabled).length || 0,
  }

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box display="flex" alignItems="center" gap={2}>
          <IconButton onClick={() => navigate('/devices')}>
            <ArrowBackIcon />
          </IconButton>
          <Box>
            <Typography variant="h4">{device.name}</Typography>
            <Typography variant="body2" color="textSecondary">
              {device.model} • {device.ip_address}
            </Typography>
          </Box>
        </Box>
        <Box display="flex" gap={2}>
          <Tooltip title="Sync Ports">
            <IconButton
              onClick={() => syncPortsMutation.mutate()}
              disabled={syncPortsMutation.isPending}
            >
              <SyncIcon />
            </IconButton>
          </Tooltip>
          <Button
            variant="outlined"
            startIcon={<EditIcon />}
            onClick={() => navigate(`/devices/${deviceId}/edit`)}
          >
            Edit
          </Button>
        </Box>
      </Box>

      {/* Status Alert */}
      {device.status === 'offline' && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          This device is currently offline. Some information may be outdated.
        </Alert>
      )}

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)}>
          <Tab label="Overview" icon={<RouterIcon />} iconPosition="start" />
          <Tab label="Ports" icon={<CableIcon />} iconPosition="start" />
          <Tab label="Connected CPE" icon={<DeviceHubIcon />} iconPosition="start" />
        </Tabs>
      </Paper>

      {/* Tab Panels */}
      <TabPanel value={tabValue} index={0}>
        <Grid container spacing={3}>
          {/* Device Information */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3, height: '100%' }}>
              <Typography variant="h6" gutterBottom>
                Device Information
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemText primary="IP Address" secondary={device.ip_address} />
                </ListItem>
                <Divider />
                <ListItem>
                  <ListItemText primary="Model" secondary={device.model} />
                </ListItem>
                <Divider />
                <ListItem>
                  <ListItemText
                    primary="Status"
                    secondary={<Chip label={device.status} color={device.status === 'online' ? 'success' : 'default'} size="small" />}
                  />
                </ListItem>
                <Divider />
                <ListItem>
                  <ListItemText primary="Firmware Version" secondary={device.firmware_version || 'Unknown'} />
                </ListItem>
                <Divider />
                <ListItem>
                  <ListItemText primary="Location" secondary={device.location || 'Not set'} />
                </ListItem>
                <Divider />
                <ListItem>
                  <ListItemText
                    primary="SSH Access"
                    secondary={
                      device.ssh_username
                        ? `${device.ssh_username}@${device.ip_address}:${device.ssh_port || 22}`
                        : 'Not configured'
                    }
                  />
                </ListItem>
              </List>
            </Paper>
          </Grid>

          {/* Performance Metrics */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3, height: '100%' }}>
              <Typography variant="h6" gutterBottom>
                Performance Metrics
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemText
                    primary="Uptime"
                    secondary={device.uptime ? `${Math.floor(device.uptime / 3600)} hours` : 'N/A'}
                  />
                </ListItem>
                <Divider />
                <ListItem>
                  <ListItemText
                    primary="CPU Usage"
                    secondary={device.cpu_usage ? `${device.cpu_usage}%` : 'N/A'}
                  />
                </ListItem>
                <Divider />
                <ListItem>
                  <ListItemText
                    primary="Memory Usage"
                    secondary={device.memory_usage ? `${device.memory_usage}%` : 'N/A'}
                  />
                </ListItem>
              </List>
            </Paper>
          </Grid>

          {/* Port Statistics */}
          <Grid item xs={12}>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6} md={3}>
                <Card>
                  <CardContent>
                    <Typography color="textSecondary" gutterBottom variant="body2">
                      Total Ports
                    </Typography>
                    <Typography variant="h4">{portStats.total}</Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Card>
                  <CardContent>
                    <Typography color="textSecondary" gutterBottom variant="body2">
                      Ports Up
                    </Typography>
                    <Typography variant="h4" color="success.main">
                      {portStats.up}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Card>
                  <CardContent>
                    <Typography color="textSecondary" gutterBottom variant="body2">
                      Ports Down
                    </Typography>
                    <Typography variant="h4" color="text.secondary">
                      {portStats.down}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Card>
                  <CardContent>
                    <Typography color="textSecondary" gutterBottom variant="body2">
                      Disabled
                    </Typography>
                    <Typography variant="h4" color="text.secondary">
                      {portStats.disabled}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">Port Configuration</Typography>
          <Button
            startIcon={<RefreshIcon />}
            onClick={() => refetchPorts()}
            disabled={portsLoading}
          >
            Refresh
          </Button>
        </Box>

        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Port</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Name</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Enabled</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {ports && ports.length > 0 ? (
                ports.map((port) => (
                  <TableRow key={port.id}>
                    <TableCell>
                      <Typography variant="body2" fontWeight="medium">
                        Port {port.port_number}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={port.port_type.toUpperCase()}
                        size="small"
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">{port.name || '-'}</Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={port.status}
                        size="small"
                        color={port.status === 'up' ? 'success' : 'default'}
                      />
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={port.enabled ? 'Yes' : 'No'}
                        size="small"
                        color={port.enabled ? 'success' : 'default'}
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell align="right">
                      <Button size="small" variant="outlined">
                        Configure
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={6} align="center">
                    <Typography color="textSecondary">No ports available</Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">Discovered CPE Devices</Typography>
          <Button
            startIcon={<RefreshIcon />}
            onClick={() => refetchCPE()}
            disabled={cpeLoading}
          >
            Scan Now
          </Button>
        </Box>

        {cpeLoading ? (
          <Box display="flex" justifyContent="center" p={4}>
            <CircularProgress />
          </Box>
        ) : discoveredCPE ? (
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Total Endpoints
                  </Typography>
                  <Typography variant="h4">{discoveredCPE.total_endpoints || 0}</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Unconfigured
                  </Typography>
                  <Typography variant="h4" color="warning.main">
                    {discoveredCPE.unconfigured_count || 0}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Configured
                  </Typography>
                  <Typography variant="h4" color="success.main">
                    {discoveredCPE.configured_count || 0}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12}>
              <Paper sx={{ p: 2 }}>
                <Typography variant="subtitle1" gutterBottom>
                  Details coming soon...
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  CPE discovery requires SSH CLI integration which is currently being implemented.
                </Typography>
              </Paper>
            </Grid>
          </Grid>
        ) : (
          <Alert severity="info">
            Enable CPE discovery by configuring SSH credentials for this device.
          </Alert>
        )}
      </TabPanel>
    </Box>
  )
}
