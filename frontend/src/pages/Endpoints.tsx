import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  CircularProgress,
  Tooltip,
  IconButton,
  Snackbar,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Button,
  Typography,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material'
import {
  CheckCircle as OnlineIcon,
  Cancel as OfflineIcon,
  PowerSettingsNew as RebootIcon,
  FlashOn as PoeIcon,
  MoreVert as MoreIcon,
  Visibility as ViewIcon,
  ShowChart as SpectrumIcon,
  Router as DeviceIcon,
  OpenInNew as PortalIcon,
  Search as SearchIcon,
  ContentCopy as CopyIcon,
} from '@mui/icons-material'
import { endpointsApi, devicesApi, exportApi, downloadFile, splynxApi } from '../services/api'
import { formatDistanceToNow } from 'date-fns'

function parseUTC(dateStr: string): Date {
  if (!dateStr.endsWith('Z') && !dateStr.includes('+')) {
    return new Date(dateStr + 'Z')
  }
  return new Date(dateStr)
}
import Breadcrumb from '../components/Breadcrumb'
import ListToolbar from '../components/ListToolbar'

// Get endpoint status from state field
function getEndpointStatus(endpoint: any): { label: string; color: 'success' | 'error' | 'warning' | 'default' | 'info'; description: string } {
  const state = endpoint.state?.toLowerCase() || ''
  const alive = endpoint.alive

  if (!alive) {
    return { label: 'Disconnected', color: 'default', description: 'Endpoint is not connected' }
  }

  if (state.includes('quarantine') || state.includes('unknown')) {
    return { label: 'Unprovisioned', color: 'warning', description: 'Connected but not assigned to a subscriber' }
  }
  if (state.includes('mismatch') || state.includes('error')) {
    return { label: 'Error', color: 'error', description: state }
  }
  if (state.includes('active') || state === 'connected' || state === 'registered') {
    return { label: 'Active', color: 'success', description: 'Endpoint is connected and provisioned' }
  }
  if (alive && state) {
    return { label: 'Connected', color: 'success', description: state }
  }
  if (alive) {
    return { label: 'Connected', color: 'success', description: 'Endpoint is connected' }
  }

  return { label: 'Unknown', color: 'default', description: 'Unknown state' }
}

// All available columns
const allColumns = [
  { id: 'status', label: 'Status', visible: true },
  { id: 'name', label: 'Name', visible: true },
  { id: 'description', label: 'Description', visible: false },
  { id: 'mac', label: 'MAC', visible: true },
  { id: 'type', label: 'Type', visible: true },
  { id: 'asy', label: 'ASY', visible: false },
  { id: 'revision', label: 'Revision', visible: false },
  { id: 'serial', label: 'Serial Number', visible: false },
  { id: 'detectedPort', label: 'Detected Port', visible: true },
  { id: 'configuredPort', label: 'Configured Port', visible: false },
  { id: 'subscriber', label: 'Subscriber', visible: true },
  { id: 'bandwidth', label: 'Bandwidth Profile', visible: true },
  { id: 'state', label: 'State', visible: false },
  { id: 'systemName', label: 'System Name', visible: true },
  { id: 'gamIp', label: 'GAM IP Address', visible: false },
  { id: 'ethPort1', label: 'Ethernet Port #1', visible: false },
  { id: 'ethPort2', label: 'Ethernet Port #2', visible: false },
  { id: 'phyRate', label: 'DS/US PHY rate (Mbps)', visible: true },
  { id: 'maxBw', label: 'DS/US Max BW (Mbps)', visible: false },
  { id: 'uptime', label: 'Uptime', visible: false },
  { id: 'groups', label: 'Groups', visible: false },
  { id: 'lastSeen', label: 'Last Seen', visible: true },
  { id: 'detailsUpdate', label: 'Latest Details Update', visible: false },
]

export default function Endpoints() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [page, setPage] = useState(0)
  const [rowsPerPage, setRowsPerPage] = useState(20)
  const [search, setSearch] = useState('')
  const [deviceFilter, setDeviceFilter] = useState<string>('')
  const [aliveFilter, setAliveFilter] = useState<string>('')
  const [columns, setColumns] = useState(allColumns)

  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success',
  })

  const [confirmDialog, setConfirmDialog] = useState<{
    open: boolean
    title: string
    message: string
    action: (() => void) | null
  }>({
    open: false,
    title: '',
    message: '',
    action: null,
  })

  // Row action menu state
  const [actionAnchor, setActionAnchor] = useState<null | HTMLElement>(null)
  const [selectedEndpoint, setSelectedEndpoint] = useState<any>(null)

  // Splynx lookup dialog state
  const [splynxDialog, setSplynxDialog] = useState<{
    open: boolean
    loading: boolean
    result: any | null
    error: string | null
  }>({
    open: false,
    loading: false,
    result: null,
    error: null,
  })

  const handleOpenActionMenu = (event: React.MouseEvent<HTMLElement>, endpoint: any) => {
    event.stopPropagation()
    setActionAnchor(event.currentTarget)
    setSelectedEndpoint(endpoint)
  }

  const handleCloseActionMenu = () => {
    setActionAnchor(null)
    setSelectedEndpoint(null)
  }

  const handleViewEndpointDetails = () => {
    if (selectedEndpoint) {
      navigate(`/endpoints/${selectedEndpoint.id}`)
    }
    handleCloseActionMenu()
  }

  const handleViewSpectrumAnalysis = () => {
    if (selectedEndpoint) {
      navigate(`/endpoints/${selectedEndpoint.id}?tab=spectrum`)
    }
    handleCloseActionMenu()
  }

  const handleViewGamDetails = () => {
    if (selectedEndpoint) {
      navigate(`/devices/${selectedEndpoint.device_id}`)
    }
    handleCloseActionMenu()
  }

  const handleOpenGamPortal = () => {
    if (selectedEndpoint?.device_ip) {
      window.open(`https://${selectedEndpoint.device_ip}`, '_blank')
    } else if (selectedEndpoint?.device_id) {
      // Fetch device IP from the device data
      const device = devicesData?.items?.find((d: any) => d.id === selectedEndpoint.device_id)
      if (device?.ip_address) {
        window.open(`https://${device.ip_address}`, '_blank')
      }
    }
    handleCloseActionMenu()
  }

  const handleMenuPoeReset = () => {
    if (selectedEndpoint) {
      handlePoeReset(selectedEndpoint)
    }
    handleCloseActionMenu()
  }

  const handleMenuReboot = () => {
    if (selectedEndpoint) {
      handleReboot(selectedEndpoint)
    }
    handleCloseActionMenu()
  }

  const handleLookupInSplynx = async () => {
    if (!selectedEndpoint) return
    handleCloseActionMenu()

    setSplynxDialog({ open: true, loading: true, result: null, error: null })

    try {
      const response = await splynxApi.lookupEndpoint(selectedEndpoint.id)
      setSplynxDialog({
        open: true,
        loading: false,
        result: response.data,
        error: null,
      })
    } catch (error: any) {
      setSplynxDialog({
        open: true,
        loading: false,
        result: null,
        error: error.response?.data?.detail || 'Failed to lookup in Splynx',
      })
    }
  }

  const poeResetMutation = useMutation({
    mutationFn: (id: string) => endpointsApi.poeReset(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['endpoints'] })
      setSnackbar({ open: true, message: 'PoE reset initiated', severity: 'success' })
    },
    onError: (error: any) => {
      setSnackbar({ open: true, message: error.response?.data?.detail || 'PoE reset failed', severity: 'error' })
    },
  })

  const rebootMutation = useMutation({
    mutationFn: (id: string) => endpointsApi.reboot(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['endpoints'] })
      setSnackbar({ open: true, message: 'Reboot initiated', severity: 'success' })
    },
    onError: (error: any) => {
      setSnackbar({ open: true, message: error.response?.data?.detail || 'Reboot failed', severity: 'error' })
    },
  })

  const handlePoeReset = (endpoint: any) => {
    setConfirmDialog({
      open: true,
      title: 'Reset PoE Power',
      message: `Are you sure you want to reset PoE power for endpoint ${endpoint.mac_address}?`,
      action: () => poeResetMutation.mutate(endpoint.id),
    })
  }

  const handleReboot = (endpoint: any) => {
    setConfirmDialog({
      open: true,
      title: 'Reboot Endpoint',
      message: `Are you sure you want to reboot endpoint ${endpoint.mac_address}?`,
      action: () => rebootMutation.mutate(endpoint.id),
    })
  }

  const handleConfirm = () => {
    if (confirmDialog.action) {
      confirmDialog.action()
    }
    setConfirmDialog({ ...confirmDialog, open: false })
  }

  const handleExport = async () => {
    try {
      const response = await exportApi.endpoints(deviceFilter || undefined)
      const filename = `endpoints_${new Date().toISOString().slice(0, 10)}.csv`
      downloadFile(response.data, filename)
    } catch (error) {
      console.error('Export failed:', error)
    }
  }

  const { data: devicesData } = useQuery({
    queryKey: ['devices-list'],
    queryFn: () => devicesApi.list({ page_size: 100 }).then((res) => res.data),
  })

  const deviceMap = new Map<string, string>()
  devicesData?.items?.forEach((d: any) => {
    deviceMap.set(d.id, d.name || d.serial_number)
  })

  const { data, isLoading } = useQuery({
    queryKey: ['endpoints', page, rowsPerPage, search, deviceFilter, aliveFilter],
    queryFn: () =>
      endpointsApi
        .list({
          page: page + 1,
          page_size: rowsPerPage,
          search: search || undefined,
          device_id: deviceFilter || undefined,
          alive: aliveFilter === '' ? undefined : aliveFilter === 'true',
        })
        .then((res) => res.data),
  })

  const isColumnVisible = (columnId: string) =>
    columns.find((c) => c.id === columnId)?.visible ?? false

  const deviceFilterOptions = [
    { value: '', label: 'All Devices' },
    ...(devicesData?.items?.map((d: any) => ({
      value: d.id,
      label: d.name || d.serial_number,
    })) || []),
  ]

  const statusFilterOptions = [
    { value: '', label: 'All' },
    { value: 'true', label: 'Connected' },
    { value: 'false', label: 'Disconnected' },
  ]

  return (
    <Box>
      <Breadcrumb current="Endpoints" />

      <ListToolbar
        search={search}
        onSearchChange={(value) => {
          setSearch(value)
          setPage(0)
        }}
        searchPlaceholder="Search by MAC, name..."
        filters={[
          {
            value: deviceFilter,
            onChange: (value) => {
              setDeviceFilter(value)
              setPage(0)
            },
            options: deviceFilterOptions,
          },
          {
            value: aliveFilter,
            onChange: (value) => {
              setAliveFilter(value)
              setPage(0)
            },
            options: statusFilterOptions,
          },
        ]}
        page={page}
        pageSize={rowsPerPage}
        total={data?.total || 0}
        onPageChange={setPage}
        onPageSizeChange={(size) => {
          setRowsPerPage(size)
          setPage(0)
        }}
        pageSizeOptions={[20, 50, 100, 500]}
        actions={[
          {
            label: 'Export to CSV',
            onClick: handleExport,
          },
        ]}
        columns={columns}
        onColumnsChange={setColumns}
      />

      {data && (
        <Box sx={{ mb: 2, display: 'flex', gap: 1 }}>
          <Chip label={`Total: ${data.total}`} size="small" />
          <Chip
            icon={<OnlineIcon />}
            label={`Connected: ${data.connected_count}`}
            color="success"
            size="small"
            variant="outlined"
          />
          <Chip
            icon={<OfflineIcon />}
            label={`Disconnected: ${data.disconnected_count}`}
            size="small"
            variant="outlined"
          />
        </Box>
      )}

      <TableContainer component={Paper}>
        {isLoading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          <Table size="small">
            <TableHead>
              <TableRow>
                {isColumnVisible('status') && (
                  <TableCell>
                    <Tooltip title="Endpoint connection and provisioning status"><span>Status</span></Tooltip>
                  </TableCell>
                )}
                {isColumnVisible('name') && (
                  <TableCell>
                    <Tooltip title="Configured endpoint name"><span>Name</span></Tooltip>
                  </TableCell>
                )}
                {isColumnVisible('description') && (
                  <TableCell>
                    <Tooltip title="Endpoint description"><span>Description</span></Tooltip>
                  </TableCell>
                )}
                {isColumnVisible('mac') && (
                  <TableCell>
                    <Tooltip title="Endpoint MAC address"><span>MAC</span></Tooltip>
                  </TableCell>
                )}
                {isColumnVisible('type') && (
                  <TableCell>
                    <Tooltip title="Endpoint device type (e.g., G1001-C)"><span>Type</span></Tooltip>
                  </TableCell>
                )}
                {isColumnVisible('asy') && (
                  <TableCell>
                    <Tooltip title="Hardware assembly number"><span>ASY</span></Tooltip>
                  </TableCell>
                )}
                {isColumnVisible('revision') && (
                  <TableCell>
                    <Tooltip title="Software revision number"><span>Revision</span></Tooltip>
                  </TableCell>
                )}
                {isColumnVisible('serial') && (
                  <TableCell>
                    <Tooltip title="Endpoint serial number"><span>Serial Number</span></Tooltip>
                  </TableCell>
                )}
                {isColumnVisible('detectedPort') && (
                  <TableCell>
                    <Tooltip title="Detected G.hn port on the GAM"><span>Detected Port</span></Tooltip>
                  </TableCell>
                )}
                {isColumnVisible('configuredPort') && (
                  <TableCell>
                    <Tooltip title="Configured G.hn port on the GAM"><span>Configured Port</span></Tooltip>
                  </TableCell>
                )}
                {isColumnVisible('subscriber') && (
                  <TableCell>
                    <Tooltip title="Associated subscriber"><span>Subscriber</span></Tooltip>
                  </TableCell>
                )}
                {isColumnVisible('bandwidth') && (
                  <TableCell>
                    <Tooltip title="Applied bandwidth profile"><span>Bandwidth Profile</span></Tooltip>
                  </TableCell>
                )}
                {isColumnVisible('state') && (
                  <TableCell>
                    <Tooltip title="Endpoint operational state"><span>State</span></Tooltip>
                  </TableCell>
                )}
                {isColumnVisible('systemName') && (
                  <TableCell>
                    <Tooltip title="Associated GAM device name"><span>System Name</span></Tooltip>
                  </TableCell>
                )}
                {isColumnVisible('gamIp') && (
                  <TableCell>
                    <Tooltip title="GAM device IP address"><span>GAM IP Address</span></Tooltip>
                  </TableCell>
                )}
                {isColumnVisible('ethPort1') && (
                  <TableCell>
                    <Tooltip title="Ethernet port 1 link status"><span>Ethernet Port #1</span></Tooltip>
                  </TableCell>
                )}
                {isColumnVisible('ethPort2') && (
                  <TableCell>
                    <Tooltip title="Ethernet port 2 link status"><span>Ethernet Port #2</span></Tooltip>
                  </TableCell>
                )}
                {isColumnVisible('phyRate') && (
                  <TableCell align="center">
                    <Tooltip title="Physical layer data rate (Downstream/Upstream) in Mbps"><span>DS/US PHY rate (Mbps)</span></Tooltip>
                  </TableCell>
                )}
                {isColumnVisible('maxBw') && (
                  <TableCell align="center">
                    <Tooltip title="Maximum bandwidth (Downstream/Upstream) in Mbps"><span>DS/US Max BW (Mbps)</span></Tooltip>
                  </TableCell>
                )}
                {isColumnVisible('uptime') && (
                  <TableCell>
                    <Tooltip title="Time since endpoint last connected"><span>Uptime</span></Tooltip>
                  </TableCell>
                )}
                {isColumnVisible('groups') && (
                  <TableCell>
                    <Tooltip title="Device group assignment"><span>Groups</span></Tooltip>
                  </TableCell>
                )}
                {isColumnVisible('lastSeen') && (
                  <TableCell>
                    <Tooltip title="Last communication timestamp"><span>Last Seen</span></Tooltip>
                  </TableCell>
                )}
                {isColumnVisible('detailsUpdate') && (
                  <TableCell>
                    <Tooltip title="Last time endpoint details were updated"><span>Latest Details Update</span></Tooltip>
                  </TableCell>
                )}
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {data?.items.map((endpoint: any) => {
                const status = getEndpointStatus(endpoint)
                const device = devicesData?.items?.find((d: any) => d.id === endpoint.device_id)
                return (
                  <TableRow
                    key={endpoint.id}
                    hover
                    sx={{ cursor: 'pointer' }}
                    onClick={() => navigate(`/endpoints/${endpoint.id}`)}
                  >
                    {isColumnVisible('status') && (
                      <TableCell>
                        <Tooltip title={status.description}>
                          <Chip
                            label={status.label}
                            color={status.color}
                            size="small"
                            variant={status.color === 'default' ? 'outlined' : 'filled'}
                          />
                        </Tooltip>
                      </TableCell>
                    )}
                    {isColumnVisible('name') && (
                      <TableCell>
                        <Typography variant="body2" fontWeight={500}>
                          {endpoint.conf_endpoint_name || '-'}
                        </Typography>
                      </TableCell>
                    )}
                    {isColumnVisible('description') && (
                      <TableCell>
                        <Typography variant="body2" color="text.secondary" noWrap sx={{ maxWidth: 150 }}>
                          {endpoint.description || '-'}
                        </Typography>
                      </TableCell>
                    )}
                    {isColumnVisible('mac') && (
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                            {endpoint.mac_address}
                          </Typography>
                          <IconButton
                            size="small"
                            sx={{ p: 0.25, opacity: 0.5, '&:hover': { opacity: 1 } }}
                            onClick={(e) => {
                              e.stopPropagation()
                              navigator.clipboard.writeText(endpoint.mac_address)
                              setSnackbar({ open: true, message: 'MAC address copied', severity: 'success' })
                            }}
                          >
                            <CopyIcon sx={{ fontSize: 14 }} />
                          </IconButton>
                        </Box>
                      </TableCell>
                    )}
                    {isColumnVisible('type') && (
                      <TableCell>
                        <Typography variant="body2" color="text.secondary">
                          {endpoint.model_string || endpoint.model_type || '-'}
                        </Typography>
                      </TableCell>
                    )}
                    {isColumnVisible('asy') && (
                      <TableCell>
                        <Typography variant="body2" color="text.secondary" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                          {endpoint.hardware_version || '-'}
                        </Typography>
                      </TableCell>
                    )}
                    {isColumnVisible('revision') && (
                      <TableCell>
                        <Typography variant="body2" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
                          {endpoint.software_revision || '-'}
                        </Typography>
                      </TableCell>
                    )}
                    {isColumnVisible('serial') && (
                      <TableCell>
                        <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                          {endpoint.serial_number || '-'}
                        </Typography>
                      </TableCell>
                    )}
                    {isColumnVisible('detectedPort') && (
                      <TableCell>
                        <Typography variant="body2">
                          {endpoint.detected_port_if_index ? `G.hn ${endpoint.detected_port_if_index}` : '-'}
                        </Typography>
                      </TableCell>
                    )}
                    {isColumnVisible('configuredPort') && (
                      <TableCell>
                        <Typography variant="body2">
                          {endpoint.conf_port_if_index ? `G.hn ${endpoint.conf_port_if_index}` : '-'}
                        </Typography>
                      </TableCell>
                    )}
                    {isColumnVisible('subscriber') && (
                      <TableCell>{endpoint.conf_user_name || '-'}</TableCell>
                    )}
                    {isColumnVisible('bandwidth') && (
                      <TableCell>
                        {endpoint.conf_bw_profile_name ? (
                          <Chip
                            label={endpoint.conf_bw_profile_name}
                            size="small"
                            color="primary"
                            variant="outlined"
                          />
                        ) : (
                          '-'
                        )}
                      </TableCell>
                    )}
                    {isColumnVisible('state') && (
                      <TableCell>
                        <Typography variant="body2" color="text.secondary">
                          {endpoint.state || '-'}
                        </Typography>
                      </TableCell>
                    )}
                    {isColumnVisible('systemName') && (
                      <TableCell>
                        <Typography variant="body2">
                          {device?.name || device?.serial_number || '-'}
                        </Typography>
                      </TableCell>
                    )}
                    {isColumnVisible('gamIp') && (
                      <TableCell>
                        <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                          {device?.ip_address || '-'}
                        </Typography>
                      </TableCell>
                    )}
                    {isColumnVisible('ethPort1') && (
                      <TableCell>
                        <Typography variant="body2" color={endpoint.eth_port1_link ? 'success.main' : 'text.disabled'}>
                          {endpoint.eth_port1_speed || (endpoint.eth_port1_link ? 'Up' : 'Down')}
                        </Typography>
                      </TableCell>
                    )}
                    {isColumnVisible('ethPort2') && (
                      <TableCell>
                        <Typography variant="body2" color={endpoint.eth_port2_link ? 'success.main' : 'text.disabled'}>
                          {endpoint.eth_port2_speed || (endpoint.eth_port2_link ? 'Up' : 'Down')}
                        </Typography>
                      </TableCell>
                    )}
                    {isColumnVisible('phyRate') && (
                      <TableCell align="center">
                        <Typography
                          variant="body2"
                          sx={{ fontFamily: 'monospace' }}
                          color={(endpoint.rx_phy_rate || endpoint.tx_phy_rate) ? 'text.primary' : 'text.disabled'}
                        >
                          {(endpoint.rx_phy_rate || endpoint.tx_phy_rate)
                            ? `${endpoint.rx_phy_rate || 0}/${endpoint.tx_phy_rate || 0}`
                            : '-'}
                        </Typography>
                      </TableCell>
                    )}
                    {isColumnVisible('maxBw') && (
                      <TableCell align="center">
                        <Typography
                          variant="body2"
                          sx={{ fontFamily: 'monospace' }}
                          color={(endpoint.max_ds_bw || endpoint.max_us_bw) ? 'text.primary' : 'text.disabled'}
                        >
                          {(endpoint.max_ds_bw || endpoint.max_us_bw)
                            ? `${endpoint.max_ds_bw || 0}/${endpoint.max_us_bw || 0}`
                            : '-'}
                        </Typography>
                      </TableCell>
                    )}
                    {isColumnVisible('uptime') && (
                      <TableCell>
                        <Typography variant="body2" color="text.secondary">
                          {endpoint.uptime || '-'}
                        </Typography>
                      </TableCell>
                    )}
                    {isColumnVisible('groups') && (
                      <TableCell>
                        <Typography variant="body2" color="text.secondary">
                          {endpoint.group_name || device?.group_name || '-'}
                        </Typography>
                      </TableCell>
                    )}
                    {isColumnVisible('lastSeen') && (
                      <TableCell>
                        <Tooltip title={endpoint.last_seen ? parseUTC(endpoint.last_seen).toLocaleString() : '-'}>
                          <Typography variant="body2" color="text.secondary">
                            {endpoint.last_seen
                              ? formatDistanceToNow(parseUTC(endpoint.last_seen), { addSuffix: true })
                              : '-'}
                          </Typography>
                        </Tooltip>
                      </TableCell>
                    )}
                    {isColumnVisible('detailsUpdate') && (
                      <TableCell>
                        <Tooltip title={endpoint.details_updated_at ? parseUTC(endpoint.details_updated_at).toLocaleString() : '-'}>
                          <Typography variant="body2" color="text.secondary">
                            {endpoint.details_updated_at
                              ? formatDistanceToNow(parseUTC(endpoint.details_updated_at), { addSuffix: true })
                              : '-'}
                          </Typography>
                        </Tooltip>
                      </TableCell>
                    )}
                    <TableCell onClick={(e) => e.stopPropagation()}>
                      <Tooltip title="Actions">
                        <IconButton size="small" onClick={(e) => handleOpenActionMenu(e, endpoint)}>
                          <MoreIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                )
              })}
              {data?.items.length === 0 && (
                <TableRow>
                  <TableCell colSpan={columns.filter((c) => c.visible).length + 1} align="center">
                    No endpoints found
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        )}
      </TableContainer>

      <Dialog open={confirmDialog.open} onClose={() => setConfirmDialog({ ...confirmDialog, open: false })}>
        <DialogTitle>{confirmDialog.title}</DialogTitle>
        <DialogContent>
          <DialogContentText>{confirmDialog.message}</DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmDialog({ ...confirmDialog, open: false })}>Cancel</Button>
          <Button onClick={handleConfirm} color="primary" variant="contained">
            Confirm
          </Button>
        </DialogActions>
      </Dialog>

      {/* Row Action Menu */}
      <Menu
        anchorEl={actionAnchor}
        open={Boolean(actionAnchor)}
        onClose={handleCloseActionMenu}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        transformOrigin={{ vertical: 'top', horizontal: 'right' }}
      >
        <MenuItem onClick={handleViewEndpointDetails}>
          <ListItemIcon>
            <ViewIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>View Endpoint Details</ListItemText>
        </MenuItem>
        <MenuItem onClick={handleViewSpectrumAnalysis} disabled={!selectedEndpoint?.alive}>
          <ListItemIcon>
            <SpectrumIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>View Spectrum Analysis</ListItemText>
        </MenuItem>
        <MenuItem onClick={handleViewGamDetails}>
          <ListItemIcon>
            <DeviceIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>View GAM Details</ListItemText>
        </MenuItem>
        <MenuItem onClick={handleOpenGamPortal}>
          <ListItemIcon>
            <PortalIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Open GAM Portal</ListItemText>
        </MenuItem>
        <MenuItem onClick={handleLookupInSplynx}>
          <ListItemIcon>
            <SearchIcon fontSize="small" color="info" />
          </ListItemIcon>
          <ListItemText>Lookup in Splynx</ListItemText>
        </MenuItem>
        <MenuItem onClick={handleMenuPoeReset} disabled={!selectedEndpoint?.alive || poeResetMutation.isPending}>
          <ListItemIcon>
            <PoeIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>PoE Reset</ListItemText>
        </MenuItem>
        <MenuItem onClick={handleMenuReboot} disabled={!selectedEndpoint?.alive || rebootMutation.isPending}>
          <ListItemIcon>
            <RebootIcon fontSize="small" color="warning" />
          </ListItemIcon>
          <ListItemText>Reboot Endpoint</ListItemText>
        </MenuItem>
      </Menu>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          severity={snackbar.severity}
          variant="filled"
        >
          {snackbar.message}
        </Alert>
      </Snackbar>

      {/* Splynx Lookup Result Dialog */}
      <Dialog
        open={splynxDialog.open}
        onClose={() => setSplynxDialog({ ...splynxDialog, open: false })}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Splynx Lookup Result</DialogTitle>
        <DialogContent>
          {splynxDialog.loading && (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress />
            </Box>
          )}
          {splynxDialog.error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {splynxDialog.error}
            </Alert>
          )}
          {splynxDialog.result && !splynxDialog.result.found && (
            <Alert severity="info">
              No inventory item found in Splynx for MAC address: {splynxDialog.result.mac_address}
            </Alert>
          )}
          {splynxDialog.result?.found && (
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Inventory Item
              </Typography>
              <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
                <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1 }}>
                  <Typography variant="body2" color="text.secondary">Name:</Typography>
                  <Typography variant="body2">{splynxDialog.result.inventory?.name || '-'}</Typography>
                  <Typography variant="body2" color="text.secondary">MAC:</Typography>
                  <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>{splynxDialog.result.inventory?.mac || '-'}</Typography>
                  <Typography variant="body2" color="text.secondary">Serial:</Typography>
                  <Typography variant="body2">{splynxDialog.result.inventory?.serial_number || '-'}</Typography>
                  <Typography variant="body2" color="text.secondary">Status:</Typography>
                  <Typography variant="body2">{splynxDialog.result.inventory?.status || '-'}</Typography>
                  <Typography variant="body2" color="text.secondary">Model:</Typography>
                  <Typography variant="body2">{splynxDialog.result.inventory?.model || '-'}</Typography>
                </Box>
              </Paper>

              {splynxDialog.result.customer && (
                <>
                  <Typography variant="subtitle2" gutterBottom>
                    Customer
                  </Typography>
                  <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
                    <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1 }}>
                      <Typography variant="body2" color="text.secondary">ID:</Typography>
                      <Typography variant="body2">{splynxDialog.result.customer.id}</Typography>
                      <Typography variant="body2" color="text.secondary">Name:</Typography>
                      <Typography variant="body2" fontWeight={500}>{splynxDialog.result.customer.name}</Typography>
                      <Typography variant="body2" color="text.secondary">Email:</Typography>
                      <Typography variant="body2">{splynxDialog.result.customer.email || '-'}</Typography>
                      <Typography variant="body2" color="text.secondary">Phone:</Typography>
                      <Typography variant="body2">{splynxDialog.result.customer.phone || '-'}</Typography>
                      <Typography variant="body2" color="text.secondary">Status:</Typography>
                      <Chip
                        label={splynxDialog.result.customer.status || 'Unknown'}
                        size="small"
                        color={splynxDialog.result.customer.status === 'active' ? 'success' : 'default'}
                      />
                      <Typography variant="body2" color="text.secondary">Address:</Typography>
                      <Typography variant="body2">{splynxDialog.result.customer.address || '-'}</Typography>
                    </Box>
                  </Paper>
                </>
              )}

              {splynxDialog.result.services?.length > 0 && (
                <>
                  <Typography variant="subtitle2" gutterBottom>
                    Services
                  </Typography>
                  <Paper variant="outlined" sx={{ p: 2 }}>
                    {splynxDialog.result.services.map((svc: any, idx: number) => (
                      <Box key={idx} sx={{ mb: idx < splynxDialog.result.services.length - 1 ? 2 : 0 }}>
                        <Typography variant="body2" fontWeight={500}>{svc.description || `Service ${svc.id}`}</Typography>
                        <Typography variant="body2" color="text.secondary">
                          Tariff: {svc.tariff_name || '-'} | Speed: {svc.download_speed || 0}/{svc.upload_speed || 0} Mbps
                        </Typography>
                        <Chip
                          label={svc.status || 'Unknown'}
                          size="small"
                          color={svc.status === 'active' ? 'success' : 'default'}
                          sx={{ mt: 0.5 }}
                        />
                      </Box>
                    ))}
                  </Paper>
                </>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSplynxDialog({ ...splynxDialog, open: false })}>
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
