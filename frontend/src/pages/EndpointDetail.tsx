import { useState, useEffect } from 'react'
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
  Alert,
  Snackbar,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
} from '@mui/material'
import {
  ArrowBack as BackIcon,
  CheckCircle as OnlineIcon,
  Cancel as OfflineIcon,
  FlashOn as PoeIcon,
  PowerSettingsNew as RebootIcon,
  ContentCopy as CopyIcon,
  Router as DeviceIcon,
  Search as SearchIcon,
  Refresh as RefreshIcon,
  PersonAdd as ProvisionIcon,
  PersonRemove as UnprovisionIcon,
} from '@mui/icons-material'
import { endpointsApi, devicesApi, splynxApi, subscribersApi } from '../services/api'
import Breadcrumb from '../components/Breadcrumb'

function InfoRow({ label, value, mono }: { label: string; value: any; mono?: boolean }) {
  return (
    <Box sx={{ display: 'flex', py: 0.5 }}>
      <Typography variant="body2" color="text.secondary" sx={{ width: 180, flexShrink: 0 }}>
        {label}
      </Typography>
      <Typography variant="body2" sx={mono ? { fontFamily: 'monospace' } : undefined}>
        {value ?? '-'}
      </Typography>
    </Box>
  )
}

export default function EndpointDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success',
  })
  const [confirmDialog, setConfirmDialog] = useState<{
    open: boolean; title: string; message: string; action: (() => void) | null
  }>({ open: false, title: '', message: '', action: null })

  // Splynx lookup dialog
  const [splynxDialog, setSplynxDialog] = useState<{
    open: boolean; loading: boolean; result: any; error: string | null
  }>({ open: false, loading: false, result: null, error: null })

  const { data: endpoint, isLoading } = useQuery({
    queryKey: ['endpoint', id],
    queryFn: () => endpointsApi.get(id!).then((res) => res.data),
  })

  // Auto-refresh details from device on page load
  const [autoRefreshed, setAutoRefreshed] = useState(false)
  useEffect(() => {
    if (endpoint && !autoRefreshed && !isLoading) {
      setAutoRefreshed(true)
      endpointsApi.refreshDetails(id!).then((res) => {
        queryClient.setQueryData(['endpoint', id], res.data)
      }).catch(() => {
        // Silently fail - device may be unreachable
      })
    }
  }, [endpoint, autoRefreshed, isLoading, id, queryClient])

  const { data: device } = useQuery({
    queryKey: ['device', endpoint?.device_id],
    queryFn: () => devicesApi.get(endpoint!.device_id).then((res) => res.data),
    enabled: !!endpoint?.device_id,
  })

  const poeResetMutation = useMutation({
    mutationFn: () => endpointsApi.poeReset(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['endpoint', id] })
      setSnackbar({ open: true, message: 'PoE reset initiated', severity: 'success' })
    },
    onError: (error: any) => {
      setSnackbar({ open: true, message: error.response?.data?.detail || 'PoE reset failed', severity: 'error' })
    },
  })

  const rebootMutation = useMutation({
    mutationFn: () => endpointsApi.reboot(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['endpoint', id] })
      setSnackbar({ open: true, message: 'Reboot initiated', severity: 'success' })
    },
    onError: (error: any) => {
      setSnackbar({ open: true, message: error.response?.data?.detail || 'Reboot failed', severity: 'error' })
    },
  })

  const refreshMutation = useMutation({
    mutationFn: () => endpointsApi.refreshDetails(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['endpoint', id] })
      setSnackbar({ open: true, message: 'Endpoint details refreshed', severity: 'success' })
    },
    onError: (error: any) => {
      setSnackbar({ open: true, message: error.response?.data?.detail || 'Refresh failed', severity: 'error' })
    },
  })

  // Auto-lookup Splynx for unprovisioned endpoints
  const [autoLooked, setAutoLooked] = useState(false)
  const [splynxData, setSplynxData] = useState<any>(null)
  const [splynxLoading, setSplynxLoading] = useState(false)

  useEffect(() => {
    if (endpoint && !autoLooked && !isLoading) {
      const epState = endpoint.state?.toLowerCase() || ''
      const unprovisioned = epState.includes('quarantine') || epState.includes('unknown') || !endpoint.conf_user_name
      if (unprovisioned) {
        setAutoLooked(true)
        setSplynxLoading(true)
        splynxApi.lookupEndpoint(id!).then((res) => {
          setSplynxData(res.data)
          setSplynxLoading(false)
        }).catch(() => {
          setSplynxLoading(false)
        })
      }
    }
  }, [endpoint, autoLooked, isLoading, id])

  const handleLookupInSplynx = async () => {
    setSplynxDialog({ open: true, loading: true, result: null, error: null })
    try {
      const response = await splynxApi.lookupEndpoint(id!)
      setSplynxData(response.data)
      setSplynxDialog({ open: true, loading: false, result: response.data, error: null })
    } catch (error: any) {
      setSplynxDialog({ open: true, loading: false, result: null, error: error.response?.data?.detail || 'Failed to lookup in Splynx' })
    }
  }

  const [provisioning, setProvisioning] = useState(false)
  const [provisionStatus, setProvisionStatus] = useState('')

  const handleProvision = async () => {
    if (!splynxData?.found || !endpoint) return
    setProvisioning(true)
    try {
      // Step 1: Configure endpoint if not already configured
      if (!endpoint.conf_endpoint_id) {
        setProvisionStatus('Configuring endpoint...')
        if (endpoint.detected_port_if_index) {
          try {
            await endpointsApi.autoConfigure(id!)
          } catch (e: any) {
            // 400 "already configured" is OK - continue to step 2
            if (e.response?.status !== 400) throw e
          }
        } else {
          throw new Error('Endpoint has no detected port. Configure it manually first.')
        }
      }

      // Step 2: Create subscriber on device
      setProvisionStatus('Creating subscriber...')
      await subscribersApi.createOnDevice({
        device_id: endpoint.device_id,
        endpoint_mac_address: endpoint.mac_address,
        name: splynxData.customer?.name || '',
        description: splynxData.customer?.address || '',
      })

      queryClient.invalidateQueries({ queryKey: ['endpoint', id] })
      setSplynxDialog({ ...splynxDialog, open: false })
      setSnackbar({ open: true, message: 'Endpoint configured and subscriber provisioned', severity: 'success' })
    } catch (error: any) {
      const detail = error.response?.data?.detail
      const message = typeof detail === 'string' ? detail : Array.isArray(detail) ? detail.map((e: any) => e.msg).join('; ') : (error.message || 'Provision failed')
      setSnackbar({ open: true, message, severity: 'error' })
    } finally {
      setProvisioning(false)
      setProvisionStatus('')
    }
  }

  const copyMac = () => {
    if (endpoint?.mac_address) {
      navigator.clipboard.writeText(endpoint.mac_address)
      setSnackbar({ open: true, message: 'MAC address copied', severity: 'success' })
    }
  }

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    )
  }

  if (!endpoint) {
    return <Alert severity="error">Endpoint not found</Alert>
  }

  const isAlive = endpoint.alive
  const state = endpoint.state?.toLowerCase() || ''
  const isProvisioned = !state.includes('quarantine') && !state.includes('unknown') && endpoint.conf_user_name

  return (
    <Box>
      <Breadcrumb
        items={[{ label: 'Endpoints', path: '/endpoints' }]}
        current={endpoint.conf_endpoint_name || endpoint.mac_address}
      />

      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
        <IconButton onClick={() => navigate('/endpoints')}>
          <BackIcon />
        </IconButton>
        <Box sx={{ flex: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="h5">
              {endpoint.conf_endpoint_name || endpoint.mac_address}
            </Typography>
            <Chip
              icon={isAlive ? <OnlineIcon /> : <OfflineIcon />}
              label={isAlive ? 'Connected' : 'Disconnected'}
              color={isAlive ? 'success' : 'default'}
              size="small"
            />
            {isAlive && !isProvisioned && (
              <Chip label="Unprovisioned" color="warning" size="small" />
            )}
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: 0.5 }}>
            <Typography variant="body2" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
              {endpoint.mac_address}
            </Typography>
            <IconButton size="small" onClick={copyMac} sx={{ p: 0.25 }}>
              <CopyIcon sx={{ fontSize: 14 }} />
            </IconButton>
          </Box>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="contained"
            size="small"
            startIcon={<RefreshIcon />}
            onClick={() => refreshMutation.mutate()}
            disabled={refreshMutation.isPending}
          >
            {refreshMutation.isPending ? 'Refreshing...' : 'Refresh Details'}
          </Button>
          <Button
            variant="outlined"
            size="small"
            startIcon={<SearchIcon />}
            onClick={handleLookupInSplynx}
          >
            Splynx Lookup
          </Button>
          <Button
            variant="outlined"
            size="small"
            startIcon={<DeviceIcon />}
            onClick={() => navigate(`/devices/${endpoint.device_id}`)}
          >
            View GAM
          </Button>
          <Button
            variant="outlined"
            size="small"
            startIcon={<PoeIcon />}
            disabled={!isAlive || poeResetMutation.isPending}
            onClick={() => setConfirmDialog({
              open: true,
              title: 'Reset PoE Power',
              message: `Reset PoE power for ${endpoint.mac_address}?`,
              action: () => poeResetMutation.mutate(),
            })}
          >
            PoE Reset
          </Button>
          <Button
            variant="outlined"
            size="small"
            color="warning"
            startIcon={<RebootIcon />}
            disabled={!isAlive || rebootMutation.isPending}
            onClick={() => setConfirmDialog({
              open: true,
              title: 'Reboot Endpoint',
              message: `Reboot endpoint ${endpoint.mac_address}?`,
              action: () => rebootMutation.mutate(),
            })}
          >
            Reboot
          </Button>
          {isProvisioned && (
            <Button
              variant="outlined"
              size="small"
              color="error"
              startIcon={<UnprovisionIcon />}
              onClick={() => setConfirmDialog({
                open: true,
                title: 'Unprovision Endpoint',
                message: `Remove subscriber from ${endpoint.mac_address}? This will delete the subscriber from the GAM device.`,
                action: () => {
                  endpointsApi.unprovision(id!).then(() => {
                    queryClient.invalidateQueries({ queryKey: ['endpoint', id] })
                    setSnackbar({ open: true, message: 'Endpoint unprovisioned', severity: 'success' })
                  }).catch((error: any) => {
                    const detail = error.response?.data?.detail
                    const message = typeof detail === 'string' ? detail : 'Unprovision failed'
                    setSnackbar({ open: true, message, severity: 'error' })
                  })
                },
              })}
            >
              Unprovision
            </Button>
          )}
        </Box>
      </Box>

      {/* Provision Card - one click does both configure + create subscriber */}
      {!isProvisioned && splynxData?.found && (
        <Card sx={{ mb: 2, border: '2px solid', borderColor: 'success.main' }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Box>
                <Typography variant="subtitle1" fontWeight="bold" color="success.main">
                  Ready to Provision
                </Typography>
                <Typography variant="body2">
                  Customer: <strong>{splynxData.customer?.name}</strong>
                  {splynxData.services?.[0] && (
                    <> | Plan: <strong>{splynxData.services[0].tariff_name}</strong> ({splynxData.services[0].download_speed}/{splynxData.services[0].upload_speed} Mbps)</>
                  )}
                </Typography>
                {provisionStatus && (
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                    <CircularProgress size={14} />
                    <Typography variant="body2" color="text.secondary">{provisionStatus}</Typography>
                  </Box>
                )}
              </Box>
              <Button
                variant="contained"
                color="success"
                startIcon={<ProvisionIcon />}
                onClick={handleProvision}
                disabled={provisioning}
              >
                {provisioning ? 'Provisioning...' : 'Provision Subscriber'}
              </Button>
            </Box>
          </CardContent>
        </Card>
      )}
      {!isProvisioned && !splynxData && splynxLoading && (
        <Card sx={{ mb: 2 }}>
          <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <CircularProgress size={20} />
            <Typography variant="body2" color="text.secondary">Looking up in Splynx...</Typography>
          </CardContent>
        </Card>
      )}

      <Grid container spacing={2}>
        {/* Identity */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="subtitle2" gutterBottom>Identity</Typography>
              <InfoRow label="Name" value={endpoint.conf_endpoint_name} />
              <InfoRow label="MAC Address" value={endpoint.mac_address} mono />
              <InfoRow label="Model" value={endpoint.model_string || endpoint.model_type} />
              <InfoRow label="Serial Number" value={endpoint.serial_number} mono />
              <InfoRow label="Firmware" value={endpoint.fw_version} />
              {endpoint.fw_mismatch && (
                <Alert severity="warning" sx={{ mt: 1 }}>Firmware mismatch detected</Alert>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Status */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="subtitle2" gutterBottom>Status</Typography>
              <InfoRow label="State" value={endpoint.state} />
              <InfoRow label="Alive" value={isAlive ? 'Yes' : 'No'} />
              <InfoRow label="Uptime" value={endpoint.uptime} />
              <InfoRow label="Last Updated" value={endpoint.updated_at ? new Date(endpoint.updated_at).toLocaleString() : '-'} />
              <InfoRow label="Last Details Update" value={endpoint.last_details_update ? new Date(endpoint.last_details_update).toLocaleString() : '-'} />
            </CardContent>
          </Card>
        </Grid>

        {/* Port Configuration */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="subtitle2" gutterBottom>Port Configuration</Typography>
              <InfoRow label="Detected Port" value={endpoint.detected_port_if_index} />
              <InfoRow label="Configured Port" value={endpoint.conf_port_if_index} />
              <InfoRow label="Auto Port" value={endpoint.conf_auto_port ? 'Yes' : 'No'} />
              <InfoRow label="Mode" value={endpoint.mode} />
            </CardContent>
          </Card>
        </Grid>

        {/* Subscriber */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="subtitle2" gutterBottom>Subscriber</Typography>
              <InfoRow label="Subscriber Name" value={endpoint.conf_user_name} />
              <InfoRow label="Subscriber ID" value={endpoint.conf_user_id} />
              <InfoRow label="Bandwidth Profile" value={endpoint.conf_bw_profile_name || (endpoint.conf_bw_profile_id === 0 ? 'Default BW Profile' : null)} />
            </CardContent>
          </Card>
        </Grid>

        {/* Performance */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="subtitle2" gutterBottom>Performance</Typography>
              <InfoRow label="RX PHY Rate" value={endpoint.rx_phy_rate ? `${endpoint.rx_phy_rate} Mbps` : null} />
              <InfoRow label="TX PHY Rate" value={endpoint.tx_phy_rate ? `${endpoint.tx_phy_rate} Mbps` : null} />
              <InfoRow label="RX Max Throughput" value={endpoint.rx_max_xput ? `${endpoint.rx_max_xput} Mbps` : null} />
              <InfoRow label="TX Max Throughput" value={endpoint.tx_max_xput ? `${endpoint.tx_max_xput} Mbps` : null} />
              <InfoRow label="RX Usage" value={endpoint.rx_usage != null ? `${endpoint.rx_usage}%` : null} />
              <InfoRow label="TX Usage" value={endpoint.tx_usage != null ? `${endpoint.tx_usage}%` : null} />
              <InfoRow label="Wire Length" value={endpoint.wire_length_feet ? `${endpoint.wire_length_feet} ft (${endpoint.wire_length_meters} m)` : null} />
            </CardContent>
          </Card>
        </Grid>

        {/* Ethernet Ports */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="subtitle2" gutterBottom>Ethernet Ports</Typography>
              <InfoRow label="Port 1 Link" value={endpoint.port1_link ? 'Up' : 'Down'} />
              <InfoRow label="Port 1 Speed" value={endpoint.port1_speed} />
              <InfoRow label="Port 2 Link" value={endpoint.port2_link ? 'Up' : 'Down'} />
              <InfoRow label="Port 2 Speed" value={endpoint.port2_speed} />
            </CardContent>
          </Card>
        </Grid>

        {/* Device Info */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="subtitle2" gutterBottom>GAM Device</Typography>
              <InfoRow label="Device" value={device?.name || device?.serial_number} />
              <InfoRow label="IP Address" value={device?.ip_address} mono />
              <InfoRow label="Model" value={device?.model} />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Confirm Dialog */}
      <Dialog open={confirmDialog.open} onClose={() => setConfirmDialog({ ...confirmDialog, open: false })}>
        <DialogTitle>{confirmDialog.title}</DialogTitle>
        <DialogContent>
          <DialogContentText>{confirmDialog.message}</DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmDialog({ ...confirmDialog, open: false })}>Cancel</Button>
          <Button variant="contained" onClick={() => { confirmDialog.action?.(); setConfirmDialog({ ...confirmDialog, open: false }) }}>
            Confirm
          </Button>
        </DialogActions>
      </Dialog>

      {/* Splynx Lookup Dialog */}
      <Dialog open={splynxDialog.open} onClose={() => setSplynxDialog({ ...splynxDialog, open: false })} maxWidth="sm" fullWidth>
        <DialogTitle>Splynx Lookup Result</DialogTitle>
        <DialogContent>
          {splynxDialog.loading && (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}><CircularProgress /></Box>
          )}
          {splynxDialog.error && <Alert severity="error">{splynxDialog.error}</Alert>}
          {splynxDialog.result && !splynxDialog.result.found && (
            <Alert severity="info">No inventory item found in Splynx for MAC: {splynxDialog.result.mac_address}</Alert>
          )}
          {splynxDialog.result?.found && (
            <Box>
              <Typography variant="subtitle2" gutterBottom>Inventory</Typography>
              <InfoRow label="Name" value={splynxDialog.result.inventory?.name} />
              <InfoRow label="MAC" value={splynxDialog.result.inventory?.mac} mono />
              <InfoRow label="Status" value={splynxDialog.result.inventory?.status} />
              <InfoRow label="Model" value={splynxDialog.result.inventory?.model} />
              {splynxDialog.result.customer && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>Customer</Typography>
                  <InfoRow label="ID" value={splynxDialog.result.customer.id} />
                  <InfoRow label="Name" value={splynxDialog.result.customer.name} />
                  <InfoRow label="Email" value={splynxDialog.result.customer.email} />
                  <InfoRow label="Phone" value={splynxDialog.result.customer.phone} />
                  <InfoRow label="Status" value={splynxDialog.result.customer.status} />
                  <InfoRow label="Address" value={splynxDialog.result.customer.address} />
                </Box>
              )}
              {splynxDialog.result.services?.length > 0 && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>Services</Typography>
                  {splynxDialog.result.services.map((svc: any, i: number) => (
                    <Box key={i} sx={{ mb: 1 }}>
                      <InfoRow label="Tariff" value={svc.tariff_name} />
                      <InfoRow label="Speed" value={`${svc.download_speed || 0}/${svc.upload_speed || 0} Mbps`} />
                      <InfoRow label="Status" value={svc.status} />
                    </Box>
                  ))}
                </Box>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSplynxDialog({ ...splynxDialog, open: false })}>Close</Button>
          {splynxDialog.result?.found && !isProvisioned && (
            <Button
              variant="contained"
              color="success"
              onClick={handleProvision}
              disabled={provisioning}
            >
              {provisioning ? 'Provisioning...' : 'Provision Subscriber'}
            </Button>
          )}
        </DialogActions>
      </Dialog>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={3000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert onClose={() => setSnackbar({ ...snackbar, open: false })} severity={snackbar.severity} variant="filled">
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  )
}
