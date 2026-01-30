import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Box,
  Typography,
  Grid,
  Chip,
  Button,
  CircularProgress,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Alert,
  Snackbar,
  Tabs,
  Tab,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
} from '@mui/material'
import {
  ArrowBack as BackIcon,
  CheckCircle as OnlineIcon,
  Cancel as OfflineIcon,
  Sync as SyncIcon,
  Link as LinkIcon,
  LinkOff as LinkOffIcon,
  Save as SaveIcon,
  Download as DownloadIcon,
  SwapHoriz as SwapIcon,
  PowerSettingsNew as RebootIcon,
  FlashOn as PoeIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material'
import { devicesApi, endpointsApi, subscribersApi, portsApi, bandwidthsApi, configBackupApi } from '../services/api'

interface TabPanelProps {
  children?: React.ReactNode
  index: number
  value: number
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props
  return (
    <div hidden={value !== index} {...other}>
      {value === index && <Box sx={{ pt: 2 }}>{children}</Box>}
    </div>
  )
}

export default function DeviceDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [tabValue, setTabValue] = useState(0)
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success',
  })

  const [editDialog, setEditDialog] = useState(false)
  const [editForm, setEditForm] = useState({ name: '', ip_address: '', location: '' })
  const [deleteDialog, setDeleteDialog] = useState(false)

  const updateMutation = useMutation({
    mutationFn: (data: any) => devicesApi.update(id!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['device', id] })
      setEditDialog(false)
      setSnackbar({ open: true, message: 'Device updated', severity: 'success' })
    },
    onError: (error: any) => {
      const detail = error.response?.data?.detail
      const message = typeof detail === 'string' ? detail : 'Update failed'
      setSnackbar({ open: true, message, severity: 'error' })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: () => devicesApi.delete(id!),
    onSuccess: () => {
      navigate('/devices')
    },
    onError: (error: any) => {
      const detail = error.response?.data?.detail
      const message = typeof detail === 'string' ? detail : 'Delete failed'
      setSnackbar({ open: true, message, severity: 'error' })
    },
  })

  const { data: device, isLoading } = useQuery({
    queryKey: ['device', id],
    queryFn: () => devicesApi.get(id!).then((res) => res.data),
  })

  const { data: endpoints } = useQuery({
    queryKey: ['device-endpoints', id],
    queryFn: () =>
      endpointsApi.list({ device_id: id, page_size: 100 }).then((res) => res.data),
    enabled: !!id,
  })

  const { data: subscribers } = useQuery({
    queryKey: ['device-subscribers', id],
    queryFn: () =>
      subscribersApi.list({ device_id: id, page_size: 100 }).then((res) => res.data),
    enabled: !!id,
  })

  const { data: ports } = useQuery({
    queryKey: ['device-ports', id],
    queryFn: () => portsApi.list({ device_id: id }).then((res) => res.data),
    enabled: !!id,
  })

  const { data: bandwidths } = useQuery({
    queryKey: ['device-bandwidths', id],
    queryFn: () => bandwidthsApi.list({ device_id: id }).then((res) => res.data),
    enabled: !!id,
  })

  const { data: configBackups } = useQuery({
    queryKey: ['config-backups', id],
    queryFn: () => configBackupApi.list(id!).then((res) => res.data),
    enabled: !!id,
  })

  const [configViewContent, setConfigViewContent] = useState<string | null>(null)

  const backupMutation = useMutation({
    mutationFn: () => configBackupApi.create(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['config-backups', id] })
      setSnackbar({ open: true, message: 'Config backup created', severity: 'success' })
    },
    onError: (error: any) => {
      setSnackbar({ open: true, message: error.response?.data?.detail || 'Backup failed', severity: 'error' })
    },
  })

  const restoreMutation = useMutation({
    mutationFn: (backupId: string) => configBackupApi.restore(backupId),
    onSuccess: () => {
      setSnackbar({ open: true, message: 'Config restored to device', severity: 'success' })
    },
    onError: (error: any) => {
      setSnackbar({ open: true, message: error.response?.data?.detail || 'Restore failed', severity: 'error' })
    },
  })

  const viewConfigContent = async (backupId: string) => {
    try {
      const res = await configBackupApi.getContent(backupId)
      setConfigViewContent(res.data.config_content)
    } catch {
      setSnackbar({ open: true, message: 'Failed to load config', severity: 'error' })
    }
  }

  const syncMutation = useMutation({
    mutationFn: () => devicesApi.sync(id!),
    onSuccess: (response) => {
      const results = response.data.results
      const successCount = [
        results.endpoints?.success,
        results.subscribers?.success,
        results.bandwidths?.success,
        results.ports?.success,
      ].filter(Boolean).length

      setSnackbar({
        open: true,
        message: `Sync complete: ${results.endpoints?.count || 0} endpoints, ${results.bandwidths?.count || 0} bandwidth profiles, ${results.ports?.count || 0} ports`,
        severity: successCount > 0 ? 'success' : 'error',
      })

      // Refresh all queries
      queryClient.invalidateQueries({ queryKey: ['device', id] })
      queryClient.invalidateQueries({ queryKey: ['device-endpoints', id] })
      queryClient.invalidateQueries({ queryKey: ['device-subscribers', id] })
      queryClient.invalidateQueries({ queryKey: ['device-ports', id] })
      queryClient.invalidateQueries({ queryKey: ['device-bandwidths', id] })
    },
    onError: (error: any) => {
      setSnackbar({
        open: true,
        message: `Sync failed: ${error.response?.data?.detail || error.message}`,
        severity: 'error',
      })
    },
  })

  const saveConfigMutation = useMutation({
    mutationFn: () => devicesApi.saveConfig(id!),
    onSuccess: () => {
      setSnackbar({
        open: true,
        message: 'Configuration saved to device startup config',
        severity: 'success',
      })
    },
    onError: (error: any) => {
      setSnackbar({
        open: true,
        message: `Save config failed: ${error.response?.data?.detail || error.message}`,
        severity: 'error',
      })
    },
  })

  const downloadConfigMutation = useMutation({
    mutationFn: () => devicesApi.downloadConfig(id!),
    onSuccess: () => {
      setSnackbar({
        open: true,
        message: 'Configuration backup downloaded from device',
        severity: 'success',
      })
    },
    onError: (error: any) => {
      setSnackbar({
        open: true,
        message: `Download config failed: ${error.response?.data?.detail || error.message}`,
        severity: 'error',
      })
    },
  })

  const firmwareSwapMutation = useMutation({
    mutationFn: () => devicesApi.firmwareSwap(id!),
    onSuccess: () => {
      setSnackbar({
        open: true,
        message: 'Firmware swap initiated - device will reboot',
        severity: 'success',
      })
    },
    onError: (error: any) => {
      setSnackbar({
        open: true,
        message: `Firmware swap failed: ${error.response?.data?.detail || error.message}`,
        severity: 'error',
      })
    },
  })

  const poeResetMutation = useMutation({
    mutationFn: (endpointId: string) => endpointsApi.poeReset(endpointId),
    onSuccess: () => {
      setSnackbar({
        open: true,
        message: 'PoE reset initiated',
        severity: 'success',
      })
      queryClient.invalidateQueries({ queryKey: ['device-endpoints', id] })
    },
    onError: (error: any) => {
      setSnackbar({
        open: true,
        message: `PoE reset failed: ${error.response?.data?.detail || error.message}`,
        severity: 'error',
      })
    },
  })

  const rebootEndpointMutation = useMutation({
    mutationFn: (endpointId: string) => endpointsApi.reboot(endpointId),
    onSuccess: () => {
      setSnackbar({
        open: true,
        message: 'Endpoint reboot initiated',
        severity: 'success',
      })
      queryClient.invalidateQueries({ queryKey: ['device-endpoints', id] })
    },
    onError: (error: any) => {
      setSnackbar({
        open: true,
        message: `Endpoint reboot failed: ${error.response?.data?.detail || error.message}`,
        severity: 'error',
      })
    },
  })

  const formatSpeed = (speed: string | null) => {
    if (!speed) return '-'
    const speedMap: Record<string, string> = {
      speed10G: '10 Gbps',
      speed2G5: '2.5 Gbps',
      speed1G: '1 Gbps',
      speed100M: '100 Mbps',
    }
    return speedMap[speed] || speed
  }

  const getPortType = (port: any) => {
    // Check port key to determine type
    const key = port.key || ''
    if (key.startsWith('G.hn')) {
      // G.hn ports - check device product class for COAX vs MIMO
      const productClass = device?.product_class?.toUpperCase() || ''
      if (productClass.includes('C')) {
        return 'Coax'
      }
      return 'MIMO' // -M models use MIMO over twisted pair
    }
    if (key.startsWith('10G') || key.startsWith('SFP')) {
      return port.fiber ? 'Fiber' : 'SFP/DAC'
    }
    return port.fiber ? 'Fiber' : 'Copper'
  }

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    )
  }

  if (!device) {
    return (
      <Box>
        <Typography>Device not found</Typography>
      </Box>
    )
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Button
          startIcon={<BackIcon />}
          onClick={() => navigate('/devices')}
        >
          Back to Devices
        </Button>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<EditIcon />}
            onClick={() => {
              setEditForm({
                name: device.name || '',
                ip_address: device.ip_address || '',
                location: device.location || '',
              })
              setEditDialog(true)
            }}
          >
            Edit
          </Button>
          <Button
            variant="outlined"
            color="error"
            startIcon={<DeleteIcon />}
            onClick={() => setDeleteDialog(true)}
          >
            Delete
          </Button>
          <Button
            variant="outlined"
            startIcon={downloadConfigMutation.isPending ? <CircularProgress size={20} /> : <DownloadIcon />}
            onClick={() => downloadConfigMutation.mutate()}
            disabled={downloadConfigMutation.isPending || !device.is_online}
          >
            Backup Config
          </Button>
          <Button
            variant="outlined"
            color="success"
            startIcon={saveConfigMutation.isPending ? <CircularProgress size={20} /> : <SaveIcon />}
            onClick={() => saveConfigMutation.mutate()}
            disabled={saveConfigMutation.isPending || !device.is_online || device.read_only}
          >
            Save Config
          </Button>
          <Button
            variant="outlined"
            color="warning"
            startIcon={firmwareSwapMutation.isPending ? <CircularProgress size={20} /> : <SwapIcon />}
            onClick={() => {
              if (confirm('Swap firmware and reboot device? This will cause a brief outage.')) {
                firmwareSwapMutation.mutate()
              }
            }}
            disabled={firmwareSwapMutation.isPending || !device.is_online || device.read_only || !device.swap_software_version}
          >
            Firmware Swap
          </Button>
          <Button
            variant="contained"
            startIcon={syncMutation.isPending ? <CircularProgress size={20} color="inherit" /> : <SyncIcon />}
            onClick={() => syncMutation.mutate()}
            disabled={syncMutation.isPending || !device.is_online}
          >
            {syncMutation.isPending ? 'Syncing...' : 'Sync Device'}
          </Button>
        </Box>
      </Box>

      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
        <Typography variant="h4">
          {device.name || device.serial_number}
        </Typography>
        {device.is_online ? (
          <Chip icon={<OnlineIcon />} label="Online" color="success" />
        ) : (
          <Chip icon={<OfflineIcon />} label="Offline" color="error" />
        )}
        {device.read_only && (
          <Chip label="Read Only" color="warning" variant="outlined" />
        )}
      </Box>

      <Grid container spacing={3}>
        {/* Device Info */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Device Information
              </Typography>
              <Table size="small">
                <TableBody>
                  <TableRow>
                    <TableCell><strong>Serial Number</strong></TableCell>
                    <TableCell>{device.serial_number}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell><strong>MAC Address</strong></TableCell>
                    <TableCell>{device.mac_address || '-'}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell><strong>IP Address</strong></TableCell>
                    <TableCell>{device.ip_address || '-'}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell><strong>Vendor</strong></TableCell>
                    <TableCell>{device.vendor || '-'}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell><strong>Product Class</strong></TableCell>
                    <TableCell>{device.product_class || '-'}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell><strong>Hardware Version</strong></TableCell>
                    <TableCell>{device.hardware_version || '-'}</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </Grid>

        {/* Software Info */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Software Information
              </Typography>
              <Table size="small">
                <TableBody>
                  <TableRow>
                    <TableCell><strong>Software Version</strong></TableCell>
                    <TableCell>{device.software_version || '-'}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell><strong>Software Revision</strong></TableCell>
                    <TableCell>{device.software_revision || '-'}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell><strong>Build Date</strong></TableCell>
                    <TableCell>{device.software_build_date || '-'}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell><strong>Firmware</strong></TableCell>
                    <TableCell>{device.firmware || device.software_version || '-'}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell><strong>Swap Version</strong></TableCell>
                    <TableCell>{device.swap_software_version || '-'}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell><strong>Uptime</strong></TableCell>
                    <TableCell>
                      {device.uptime
                        ? `${Math.floor(device.uptime / 86400)}d ${Math.floor(
                            (device.uptime % 86400) / 3600
                          )}h`
                        : '-'}
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </Grid>

        {/* VLANs in Use */}
        {subscribers?.items && subscribers.items.length > 0 && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="subtitle2" gutterBottom>
                  VLANs in Use
                </Typography>
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  {(() => {
                    const vlans = new Map<string, { tagged: boolean; count: number }>()
                    subscribers.items.forEach((sub: any) => {
                      const v = sub.port1_vlan_id
                      if (v) {
                        const existing = vlans.get(v)
                        if (existing) {
                          existing.count++
                        } else {
                          vlans.set(v, { tagged: !!sub.vlan_is_tagged, count: 1 })
                        }
                      }
                    })
                    return Array.from(vlans.entries()).sort().map(([vlan, info]) => (
                      <Chip
                        key={vlan}
                        label={`VLAN ${vlan}${info.tagged ? ' (T)' : ''} — ${info.count} subscriber${info.count > 1 ? 's' : ''}`}
                        variant="outlined"
                        color="primary"
                        size="small"
                      />
                    ))
                  })()}
                </Box>
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Tabs for Ports, Endpoints, Subscribers, Bandwidth Profiles */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)}>
                <Tab label={`Ports (${ports?.total || 0})`} />
                <Tab label={`Endpoints (${endpoints?.total || 0})`} />
                <Tab label={`Subscribers (${subscribers?.total || 0})`} />
                <Tab label={`Bandwidth Profiles (${bandwidths?.total || 0})`} />
                <Tab label={`Configuration (${configBackups?.total || 0})`} />
              </Tabs>

              {/* Ports Tab */}
              <TabPanel value={tabValue} index={0}>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Port</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell>Speed</TableCell>
                        <TableCell>Type</TableCell>
                        <TableCell>SFP Info</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {ports?.items.map((port: any) => (
                        <TableRow key={port.id}>
                          <TableCell>
                            <strong>{port.key}</strong>
                          </TableCell>
                          <TableCell>
                            {port.link ? (
                              <Chip
                                icon={<LinkIcon />}
                                label="Up"
                                color="success"
                                size="small"
                              />
                            ) : (
                              <Chip
                                icon={<LinkOffIcon />}
                                label="Down"
                                color="default"
                                size="small"
                              />
                            )}
                          </TableCell>
                          <TableCell>{formatSpeed(port.speed)}</TableCell>
                          <TableCell>
                            {getPortType(port)}
                            {port.fdx && ' (FDX)'}
                          </TableCell>
                          <TableCell>
                            {port.sfp_type && port.sfp_type !== 'none' ? (
                              <>
                                {port.sfp_vendor_name} {port.sfp_vendor_pn}
                                {port.sfp_vendor_sn && <br />}
                                {port.sfp_vendor_sn && (
                                  <Typography variant="caption" color="textSecondary">
                                    S/N: {port.sfp_vendor_sn}
                                  </Typography>
                                )}
                              </>
                            ) : (
                              '-'
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                      {(!ports?.items || ports.items.length === 0) && (
                        <TableRow>
                          <TableCell colSpan={5} align="center">
                            No ports found - click Sync to refresh
                          </TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </TableContainer>
              </TabPanel>

              {/* Endpoints Tab */}
              <TabPanel value={tabValue} index={1}>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Status</TableCell>
                        <TableCell>MAC Address</TableCell>
                        <TableCell>Model</TableCell>
                        <TableCell>Port</TableCell>
                        <TableCell>Subscriber</TableCell>
                        <TableCell>BW Profile</TableCell>
                        <TableCell>RX/TX PHY</TableCell>
                        <TableCell>Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {endpoints?.items.map((endpoint: any) => {
                        // Determine status chip based on state
                        const getStatusChip = () => {
                          const state = endpoint.state?.toLowerCase() || ''
                          if (state.includes('quarantine') || state.includes('unknown')) {
                            return <Chip label="Unprovisioned" color="warning" size="small" />
                          }
                          if (state === 'connected' || state === 'online') {
                            return <Chip label="Connected" color="success" size="small" />
                          }
                          if (!endpoint.alive) {
                            return <Chip label="Offline" color="default" size="small" />
                          }
                          if (endpoint.conf_user_name) {
                            return <Chip label="Provisioned" color="success" size="small" />
                          }
                          return <Chip label="New" color="info" size="small" />
                        }
                        return (
                          <TableRow key={endpoint.id}>
                            <TableCell>{getStatusChip()}</TableCell>
                            <TableCell>{endpoint.mac_address}</TableCell>
                            <TableCell>{endpoint.model_string || endpoint.model_type || '-'}</TableCell>
                            <TableCell>{endpoint.detected_port_if_index || endpoint.conf_port_if_index || '-'}</TableCell>
                            <TableCell>{endpoint.conf_user_name || '-'}</TableCell>
                            <TableCell>{endpoint.conf_bw_profile_name || (endpoint.conf_bw_profile_id === 0 ? 'Unthrottled' : '-')}</TableCell>
                            <TableCell>
                              {endpoint.rx_phy_rate && endpoint.tx_phy_rate
                                ? `${endpoint.rx_phy_rate}/${endpoint.tx_phy_rate} Mbps`
                                : '-'}
                            </TableCell>
                            <TableCell>
                              <Tooltip title="PoE Reset">
                                <IconButton
                                  size="small"
                                  onClick={() => poeResetMutation.mutate(endpoint.id)}
                                  disabled={!endpoint.alive || poeResetMutation.isPending}
                                >
                                  <PoeIcon fontSize="small" />
                                </IconButton>
                              </Tooltip>
                              <Tooltip title="Reboot Endpoint">
                                <IconButton
                                  size="small"
                                  color="warning"
                                  onClick={() => rebootEndpointMutation.mutate(endpoint.id)}
                                  disabled={!endpoint.alive || rebootEndpointMutation.isPending}
                                >
                                  <RebootIcon fontSize="small" />
                                </IconButton>
                              </Tooltip>
                            </TableCell>
                          </TableRow>
                        )
                      })}
                      {(!endpoints?.items || endpoints.items.length === 0) && (
                        <TableRow>
                          <TableCell colSpan={8} align="center">
                            No endpoints connected
                          </TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </TableContainer>
              </TabPanel>

              {/* Subscribers Tab */}
              <TabPanel value={tabValue} index={2}>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Name</TableCell>
                        <TableCell>Description</TableCell>
                        <TableCell>Endpoint MAC</TableCell>
                        <TableCell>VLAN Port #1</TableCell>
                        <TableCell>VLAN Port #2</TableCell>
                        <TableCell>Trunk</TableCell>
                        <TableCell>Bandwidth Profile</TableCell>
                        <TableCell>PoE</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {subscribers?.items.map((sub: any) => (
                        <TableRow key={sub.id}>
                          <TableCell sx={{ fontWeight: 500 }}>{sub.name}</TableCell>
                          <TableCell>{sub.description || '-'}</TableCell>
                          <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>
                            {sub.endpoint_mac || sub.endpoint_mac_address || '-'}
                          </TableCell>
                          <TableCell>
                            {sub.port1_vlan_id || '-'}
                            {sub.vlan_is_tagged && (
                              <Chip label="Tagged" size="small" sx={{ ml: 0.5, height: 18, fontSize: '0.7rem' }} />
                            )}
                          </TableCell>
                          <TableCell>
                            {sub.port2_vlan_id || '-'}
                            {sub.vlan_is_tagged2 && (
                              <Chip label="Tagged" size="small" sx={{ ml: 0.5, height: 18, fontSize: '0.7rem' }} />
                            )}
                          </TableCell>
                          <TableCell>
                            {sub.trunk_mode ? (
                              <Chip label="Yes" color="info" size="small" />
                            ) : '-'}
                          </TableCell>
                          <TableCell>{sub.bw_profile_name || (sub.bw_profile_id === 0 ? 'Unthrottled' : '-')}</TableCell>
                          <TableCell>{sub.poe_mode_ctrl || '-'}</TableCell>
                        </TableRow>
                      ))}
                      {(!subscribers?.items || subscribers.items.length === 0) && (
                        <TableRow>
                          <TableCell colSpan={8} align="center">
                            No subscribers configured
                          </TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </TableContainer>
              </TabPanel>

              {/* Bandwidth Profiles Tab */}
              <TabPanel value={tabValue} index={3}>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Name</TableCell>
                        <TableCell>Downstream</TableCell>
                        <TableCell>Upstream</TableCell>
                        <TableCell>Description</TableCell>
                        <TableCell>Synced</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {bandwidths?.items.map((bw: any) => (
                        <TableRow key={bw.id}>
                          <TableCell><strong>{bw.name}</strong></TableCell>
                          <TableCell>{bw.ds_mbps} Mbps</TableCell>
                          <TableCell>{bw.us_mbps} Mbps</TableCell>
                          <TableCell>{bw.description || '-'}</TableCell>
                          <TableCell>
                            {bw.sync ? (
                              <Chip label="Yes" color="success" size="small" />
                            ) : (
                              <Chip label="No" color="warning" size="small" />
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                      {(!bandwidths?.items || bandwidths.items.length === 0) && (
                        <TableRow>
                          <TableCell colSpan={5} align="center">
                            No bandwidth profiles - click Sync to refresh
                          </TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </TableContainer>
              </TabPanel>

              {/* Configuration Backups Tab */}
              <TabPanel value={tabValue} index={4}>
                <Box sx={{ mb: 2 }}>
                  <Button
                    variant="outlined"
                    size="small"
                    startIcon={<DownloadIcon />}
                    onClick={() => backupMutation.mutate()}
                    disabled={backupMutation.isPending}
                  >
                    {backupMutation.isPending ? 'Backing up...' : 'Create Backup'}
                  </Button>
                </Box>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Version</TableCell>
                        <TableCell>Type</TableCell>
                        <TableCell>Size</TableCell>
                        <TableCell>Created</TableCell>
                        <TableCell>Created By</TableCell>
                        <TableCell>Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {configBackups?.items?.map((backup: any) => (
                        <TableRow key={backup.id}>
                          <TableCell><strong>v{backup.version_number}</strong></TableCell>
                          <TableCell>{backup.config_type}</TableCell>
                          <TableCell>{backup.size ? `${(backup.size / 1024).toFixed(1)} KB` : '-'}</TableCell>
                          <TableCell>{backup.created_at ? new Date(backup.created_at).toLocaleString() : '-'}</TableCell>
                          <TableCell>{backup.created_by || '-'}</TableCell>
                          <TableCell>
                            <Tooltip title="View">
                              <IconButton size="small" onClick={() => viewConfigContent(backup.id)}>
                                <DownloadIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Restore to device">
                              <IconButton
                                size="small"
                                color="warning"
                                onClick={() => {
                                  if (window.confirm(`Restore config v${backup.version_number} to this device?`)) {
                                    restoreMutation.mutate(backup.id)
                                  }
                                }}
                              >
                                <SwapIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          </TableCell>
                        </TableRow>
                      ))}
                      {(!configBackups?.items || configBackups.items.length === 0) && (
                        <TableRow>
                          <TableCell colSpan={6} align="center">
                            No config backups - click Create Backup to start
                          </TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </TableContainer>
                {configViewContent && (
                  <Box sx={{ mt: 2, p: 2, bgcolor: '#1e1e1e', borderRadius: 1, maxHeight: 400, overflow: 'auto' }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="subtitle2" color="#ccc">Configuration Content</Typography>
                      <Button size="small" onClick={() => setConfigViewContent(null)} sx={{ color: '#ccc' }}>Close</Button>
                    </Box>
                    <pre style={{ color: '#d4d4d4', fontSize: 12, margin: 0, whiteSpace: 'pre-wrap' }}>
                      {configViewContent}
                    </pre>
                  </Box>
                )}
              </TabPanel>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Edit Device Dialog */}
      <Dialog open={editDialog} onClose={() => setEditDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Edit Device</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth size="small" label="Name" value={editForm.name}
            onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
            sx={{ mt: 1, mb: 2 }}
          />
          <TextField
            fullWidth size="small" label="IP Address" value={editForm.ip_address}
            onChange={(e) => setEditForm({ ...editForm, ip_address: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            fullWidth size="small" label="Location" value={editForm.location}
            onChange={(e) => setEditForm({ ...editForm, location: e.target.value })}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialog(false)}>Cancel</Button>
          <Button variant="contained" onClick={() => updateMutation.mutate(editForm)} disabled={updateMutation.isPending}>
            {updateMutation.isPending ? 'Saving...' : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Device Dialog */}
      <Dialog open={deleteDialog} onClose={() => setDeleteDialog(false)}>
        <DialogTitle>Delete Device</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete <strong>{device.name || device.serial_number}</strong>?
            This will remove all associated endpoints and subscribers from the database.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialog(false)}>Cancel</Button>
          <Button variant="contained" color="error" onClick={() => deleteMutation.mutate()} disabled={deleteMutation.isPending}>
            {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  )
}
