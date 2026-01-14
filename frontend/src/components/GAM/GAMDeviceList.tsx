import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Button,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Chip,
  CircularProgress,
  Grid,
  Card,
  CardContent,
  IconButton,
  Tooltip,
  TextField,
  InputAdornment,
  Alert,
} from '@mui/material'
import {
  Add as AddIcon,
  Refresh as RefreshIcon,
  Search as SearchIcon,
  Edit as EditIcon,
  Settings as SettingsIcon,
  Sync as SyncIcon,
} from '@mui/icons-material'
import api from '../../services/api'
import type { GAMDevice } from '../../types'
import { useState } from 'react'

export default function GAMDeviceList() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')

  const { data: devices, isLoading, refetch } = useQuery<GAMDevice[]>({
    queryKey: ['devices'],
    queryFn: async () => {
      const response = await api.get('/gam/devices')
      return response.data
    },
  })

  const syncPortsMutation = useMutation({
    mutationFn: async (deviceId: string) => {
      const response = await api.post(`/gam/devices/${deviceId}/sync-ports`)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['devices'] })
    },
  })

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online':
        return 'success'
      case 'offline':
        return 'default'
      case 'error':
        return 'error'
      case 'maintenance':
        return 'warning'
      default:
        return 'default'
    }
  }

  // Filter devices
  const filteredDevices = devices?.filter((device) => {
    const matchesSearch =
      device.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      device.ip_address.includes(searchTerm) ||
      device.model.toLowerCase().includes(searchTerm.toLowerCase())

    const matchesStatus = statusFilter === 'all' || device.status === statusFilter

    return matchesSearch && matchesStatus
  })

  // Calculate stats
  const stats = {
    total: devices?.length || 0,
    online: devices?.filter((d) => d.status === 'online').length || 0,
    offline: devices?.filter((d) => d.status === 'offline').length || 0,
    error: devices?.filter((d) => d.status === 'error').length || 0,
  }

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">GAM Devices</Typography>
        <Box display="flex" gap={2}>
          <Tooltip title="Refresh">
            <IconButton onClick={() => refetch()}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => navigate('/devices/new')}
          >
            Add Device
          </Button>
        </Box>
      </Box>

      {/* Stats Cards */}
      <Grid container spacing={2} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom variant="body2">
                Total Devices
              </Typography>
              <Typography variant="h4">{stats.total}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom variant="body2">
                Online
              </Typography>
              <Typography variant="h4" color="success.main">
                {stats.online}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom variant="body2">
                Offline
              </Typography>
              <Typography variant="h4" color="text.secondary">
                {stats.offline}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom variant="body2">
                Errors
              </Typography>
              <Typography variant="h4" color="error.main">
                {stats.error}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Search and Filters */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              placeholder="Search by name, IP, or model..."
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
          </Grid>
          <Grid item xs={12} md={6}>
            <Box display="flex" gap={1}>
              <Chip
                label="All"
                onClick={() => setStatusFilter('all')}
                color={statusFilter === 'all' ? 'primary' : 'default'}
                variant={statusFilter === 'all' ? 'filled' : 'outlined'}
              />
              <Chip
                label="Online"
                onClick={() => setStatusFilter('online')}
                color={statusFilter === 'online' ? 'success' : 'default'}
                variant={statusFilter === 'online' ? 'filled' : 'outlined'}
              />
              <Chip
                label="Offline"
                onClick={() => setStatusFilter('offline')}
                color={statusFilter === 'offline' ? 'default' : 'default'}
                variant={statusFilter === 'offline' ? 'filled' : 'outlined'}
              />
              <Chip
                label="Error"
                onClick={() => setStatusFilter('error')}
                color={statusFilter === 'error' ? 'error' : 'default'}
                variant={statusFilter === 'error' ? 'filled' : 'outlined'}
              />
            </Box>
          </Grid>
        </Grid>
      </Paper>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>IP Address</TableCell>
              <TableCell>Model</TableCell>
              <TableCell>Ports</TableCell>
              <TableCell>Location</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Firmware</TableCell>
              <TableCell>SSH</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredDevices && filteredDevices.length > 0 ? (
              filteredDevices.map((device) => (
                <TableRow key={device.id} hover>
                  <TableCell>
                    <Typography variant="body2" fontWeight="medium">
                      {device.name}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" fontFamily="monospace">
                      {device.ip_address}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip label={device.model} size="small" variant="outlined" />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" color="textSecondary">
                      {device.model.includes('-4-') ? '4' : device.model.includes('-12-') ? '12' : '24'}{' '}
                      ports
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">{device.location || '-'}</Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={device.status}
                      color={getStatusColor(device.status)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">{device.firmware_version || '-'}</Typography>
                  </TableCell>
                  <TableCell>
                    {device.ssh_username ? (
                      <Tooltip title={`SSH: ${device.ssh_username}@${device.ip_address}:${device.ssh_port}`}>
                        <Chip label="Configured" size="small" color="success" variant="outlined" />
                      </Tooltip>
                    ) : (
                      <Chip label="Not set" size="small" color="default" variant="outlined" />
                    )}
                  </TableCell>
                  <TableCell align="right">
                    <Box display="flex" gap={0.5} justifyContent="flex-end">
                      <Tooltip title="Sync Ports">
                        <IconButton
                          size="small"
                          onClick={(e) => {
                            e.stopPropagation()
                            syncPortsMutation.mutate(device.id)
                          }}
                          disabled={syncPortsMutation.isPending}
                        >
                          <SyncIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Configure">
                        <IconButton
                          size="small"
                          onClick={(e) => {
                            e.stopPropagation()
                            navigate(`/devices/${device.id}/edit`)
                          }}
                        >
                          <SettingsIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Button
                        size="small"
                        variant="outlined"
                        onClick={() => navigate(`/devices/${device.id}`)}
                      >
                        View
                      </Button>
                    </Box>
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={9} align="center">
                  <Box py={4}>
                    <Typography color="textSecondary" gutterBottom>
                      {searchTerm || statusFilter !== 'all'
                        ? 'No devices match your search criteria'
                        : 'No devices found'}
                    </Typography>
                    {(!searchTerm && statusFilter === 'all') && (
                      <Button
                        variant="contained"
                        startIcon={<AddIcon />}
                        onClick={() => navigate('/devices/new')}
                        sx={{ mt: 2 }}
                      >
                        Add Your First Device
                      </Button>
                    )}
                  </Box>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  )
}
