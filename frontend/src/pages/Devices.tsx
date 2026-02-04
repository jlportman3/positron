import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
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
  IconButton,
  CircularProgress,
  Typography,
  Tooltip,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material'
import {
  Visibility as ViewIcon,
  CheckCircle as OnlineIcon,
  Cancel as OfflineIcon,
  MoreVert as MoreIcon,
  Settings as ConfigIcon,
  OpenInNew as PortalIcon,
  Sync as SyncIcon,
  SyncProblem as SyncErrorIcon,
} from '@mui/icons-material'
import { devicesApi, exportApi, downloadFile } from '../services/api'
import { formatDistanceToNow } from 'date-fns'
import Breadcrumb from '../components/Breadcrumb'
import ListToolbar from '../components/ListToolbar'
import HealthScore from '../components/HealthScore'

// All available columns
const allColumns = [
  { id: 'status', label: 'Status', visible: true },
  { id: 'health', label: 'Health', visible: true },
  { id: 'sync', label: 'Sync', visible: false },
  { id: 'name', label: 'System Name', visible: true },
  { id: 'serial', label: 'Serial Number', visible: true },
  { id: 'ip', label: 'IP Address', visible: true },
  { id: 'mac', label: 'MAC', visible: false },
  { id: 'model', label: 'Model', visible: true },
  { id: 'ports', label: 'Ports', visible: false },
  { id: 'endpoints', label: 'Endpoints', visible: true },
  { id: 'subscribers', label: 'Subscribers', visible: true },
  { id: 'bandwidths', label: 'Bandwidths', visible: false },
  { id: 'groups', label: 'Groups', visible: false },
  { id: 'uptime', label: 'Uptime', visible: true },
  { id: 'asy', label: 'ASY', visible: false },
  { id: 'revision', label: 'Revision', visible: false },
  { id: 'lastSeen', label: 'Last Seen', visible: true },
  { id: 'software', label: 'Software', visible: true },
]

function parseUTC(dateStr: string): Date {
  // Backend stores naive UTC datetimes - ensure JS parses as UTC
  if (!dateStr.endsWith('Z') && !dateStr.includes('+')) {
    return new Date(dateStr + 'Z')
  }
  return new Date(dateStr)
}

function formatUptime(seconds?: number): string {
  if (!seconds) return '-'
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  const mins = Math.floor((seconds % 3600) / 60)
  if (days > 0) return `${days}d ${hours}h`
  if (hours > 0) return `${hours}h ${mins}m`
  return `${mins}m`
}

export default function Devices() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [page, setPage] = useState(0)
  const [rowsPerPage, setRowsPerPage] = useState(20)
  const [search, setSearch] = useState('')
  const [columns, setColumns] = useState(allColumns)

  // Row action menu state
  const [actionAnchor, setActionAnchor] = useState<null | HTMLElement>(null)
  const [selectedDevice, setSelectedDevice] = useState<any>(null)

  const handleOpenActionMenu = (event: React.MouseEvent<HTMLElement>, device: any) => {
    event.stopPropagation()
    setActionAnchor(event.currentTarget)
    setSelectedDevice(device)
  }

  const handleCloseActionMenu = () => {
    setActionAnchor(null)
    setSelectedDevice(null)
  }

  const handleViewDetails = () => {
    if (selectedDevice) {
      navigate(`/devices/${selectedDevice.id}`)
    }
    handleCloseActionMenu()
  }

  const handleViewConfigurations = () => {
    if (selectedDevice) {
      navigate(`/devices/${selectedDevice.id}?tab=config`)
    }
    handleCloseActionMenu()
  }

  const handleOpenPortal = () => {
    if (selectedDevice?.ip_address) {
      window.open(`https://${selectedDevice.ip_address}`, '_blank')
    }
    handleCloseActionMenu()
  }

  const { data, isLoading } = useQuery({
    queryKey: ['devices', page, rowsPerPage, search],
    queryFn: () =>
      devicesApi
        .list({
          page: page + 1,
          page_size: rowsPerPage,
          search: search || undefined,
        })
        .then((res) => res.data),
  })

  const syncAllMutation = useMutation({
    mutationFn: () => devicesApi.syncAll(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['devices'] })
    },
  })

  const handleExport = async () => {
    try {
      const response = await exportApi.devices()
      const filename = `devices_${new Date().toISOString().slice(0, 10)}.csv`
      downloadFile(response.data, filename)
    } catch (error) {
      console.error('Export failed:', error)
    }
  }

  const isColumnVisible = (columnId: string) =>
    columns.find((c) => c.id === columnId)?.visible ?? false

  return (
    <Box>
      <Breadcrumb current="GAM" />

      <ListToolbar
        search={search}
        onSearchChange={(value) => {
          setSearch(value)
          setPage(0)
        }}
        searchPlaceholder="Search devices..."
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
            label: 'Remove All Inactive Devices',
            onClick: () => {
              // TODO: Implement remove all inactive
              console.log('Remove all inactive devices')
            },
          },
          {
            label: 'Sync All Devices',
            onClick: () => syncAllMutation.mutate(),
          },
          {
            label: 'Export All Data (CSV)',
            onClick: handleExport,
          },
        ]}
        columns={columns}
        onColumnsChange={setColumns}
      />

      {/* Summary chips */}
      {data && (
        <Box sx={{ mb: 2, display: 'flex', gap: 1 }}>
          <Chip label={`Total: ${data.total}`} size="small" />
          <Chip
            icon={<OnlineIcon />}
            label={`Online: ${data.online_count}`}
            color="success"
            size="small"
            variant="outlined"
          />
          <Chip
            icon={<OfflineIcon />}
            label={`Offline: ${data.offline_count}`}
            color="error"
            size="small"
            variant="outlined"
          />
        </Box>
      )}

      {/* Table */}
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
                    <Tooltip title="Device online/offline status and read-only mode"><span>Status</span></Tooltip>
                  </TableCell>
                )}
                {isColumnVisible('health') && (
                  <TableCell>
                    <Tooltip title="Device health score based on alarms and metrics"><span>Health</span></Tooltip>
                  </TableCell>
                )}
                {isColumnVisible('sync') && (
                  <TableCell>
                    <Tooltip title="Data synchronization status with the device"><span>Sync</span></Tooltip>
                  </TableCell>
                )}
                {isColumnVisible('name') && (
                  <TableCell>
                    <Tooltip title="User-defined system name"><span>System Name</span></Tooltip>
                  </TableCell>
                )}
                {isColumnVisible('serial') && (
                  <TableCell>
                    <Tooltip title="Device serial number"><span>Serial Number</span></Tooltip>
                  </TableCell>
                )}
                {isColumnVisible('ip') && (
                  <TableCell>
                    <Tooltip title="Device IP address for management"><span>IP Address</span></Tooltip>
                  </TableCell>
                )}
                {isColumnVisible('mac') && (
                  <TableCell>
                    <Tooltip title="Device MAC address"><span>MAC Address</span></Tooltip>
                  </TableCell>
                )}
                {isColumnVisible('model') && (
                  <TableCell>
                    <Tooltip title="GAM device model (e.g., GAM-12-M, GAM-24-C)"><span>Model</span></Tooltip>
                  </TableCell>
                )}
                {isColumnVisible('ports') && (
                  <TableCell align="right">
                    <Tooltip title="Total number of G.hn ports on device"><span>Ports</span></Tooltip>
                  </TableCell>
                )}
                {isColumnVisible('endpoints') && (
                  <TableCell align="right">
                    <Tooltip title="Number of connected CPE endpoints"><span>Endpoints</span></Tooltip>
                  </TableCell>
                )}
                {isColumnVisible('subscribers') && (
                  <TableCell align="right">
                    <Tooltip title="Number of provisioned subscribers"><span>Subscribers</span></Tooltip>
                  </TableCell>
                )}
                {isColumnVisible('bandwidths') && (
                  <TableCell align="right">
                    <Tooltip title="Number of bandwidth profiles configured"><span>Bandwidths</span></Tooltip>
                  </TableCell>
                )}
                {isColumnVisible('groups') && (
                  <TableCell>
                    <Tooltip title="Device group assignment"><span>Groups</span></Tooltip>
                  </TableCell>
                )}
                {isColumnVisible('uptime') && (
                  <TableCell>
                    <Tooltip title="Time since last device reboot"><span>Uptime</span></Tooltip>
                  </TableCell>
                )}
                {isColumnVisible('asy') && (
                  <TableCell>
                    <Tooltip title="Hardware assembly number"><span>ASY</span></Tooltip>
                  </TableCell>
                )}
                {isColumnVisible('revision') && (
                  <TableCell>
                    <Tooltip title="Software build revision number"><span>Revision</span></Tooltip>
                  </TableCell>
                )}
                {isColumnVisible('lastSeen') && (
                  <TableCell>
                    <Tooltip title="Last announcement received from device"><span>Last Seen</span></Tooltip>
                  </TableCell>
                )}
                {isColumnVisible('software') && (
                  <TableCell>
                    <Tooltip title="Device firmware version"><span>Software</span></Tooltip>
                  </TableCell>
                )}
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {data?.items.map((device: any) => (
                <TableRow
                  key={device.id}
                  hover
                  onClick={() => navigate(`/devices/${device.id}`)}
                  sx={{ cursor: 'pointer' }}
                >
                  {isColumnVisible('status') && (
                    <TableCell>
                      <Box sx={{ display: 'flex', gap: 0.5, alignItems: 'center' }}>
                        {device.is_online ? (
                          <Chip
                            icon={<OnlineIcon />}
                            label="Online"
                            color="success"
                            size="small"
                          />
                        ) : (
                          <Chip
                            icon={<OfflineIcon />}
                            label="Offline"
                            color="error"
                            size="small"
                          />
                        )}
                        {device.read_only && (
                          <Chip label="RO" color="warning" size="small" variant="outlined" />
                        )}
                      </Box>
                    </TableCell>
                  )}
                  {isColumnVisible('health') && (
                    <TableCell>
                      <HealthScore
                        score={device.health_score || 100}
                        status={device.health_status || 'healthy'}
                      />
                    </TableCell>
                  )}
                  {isColumnVisible('sync') && (
                    <TableCell>
                      {device.sync_error ? (
                        <Tooltip title={device.sync_error}>
                          <Chip
                            icon={<SyncErrorIcon />}
                            label="Error"
                            color="error"
                            size="small"
                            variant="outlined"
                          />
                        </Tooltip>
                      ) : (
                        <Tooltip title="Synced">
                          <SyncIcon color="success" fontSize="small" />
                        </Tooltip>
                      )}
                    </TableCell>
                  )}
                  {isColumnVisible('name') && (
                    <TableCell>
                      <Typography variant="body2" fontWeight={500}>
                        {device.name || '-'}
                      </Typography>
                    </TableCell>
                  )}
                  {isColumnVisible('serial') && (
                    <TableCell>
                      <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                        {device.serial_number}
                      </Typography>
                    </TableCell>
                  )}
                  {isColumnVisible('ip') && (
                    <TableCell>
                      <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                        {device.ip_address || '-'}
                      </Typography>
                    </TableCell>
                  )}
                  {isColumnVisible('mac') && (
                    <TableCell>
                      <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                        {device.mac_address || '-'}
                      </Typography>
                    </TableCell>
                  )}
                  {isColumnVisible('model') && (
                    <TableCell>
                      <Typography variant="body2" color="text.secondary">
                        {device.product_class || '-'}
                      </Typography>
                    </TableCell>
                  )}
                  {isColumnVisible('ports') && (
                    <TableCell align="right">{device.port_count || 0}</TableCell>
                  )}
                  {isColumnVisible('endpoints') && (
                    <TableCell align="right">{device.endpoint_count || 0}</TableCell>
                  )}
                  {isColumnVisible('subscribers') && (
                    <TableCell align="right">{device.subscriber_count || 0}</TableCell>
                  )}
                  {isColumnVisible('bandwidths') && (
                    <TableCell align="right">{device.bandwidth_count || 0}</TableCell>
                  )}
                  {isColumnVisible('groups') && (
                    <TableCell>
                      <Typography variant="body2" color="text.secondary">
                        {device.group_name || '-'}
                      </Typography>
                    </TableCell>
                  )}
                  {isColumnVisible('uptime') && (
                    <TableCell>
                      <Typography variant="body2">
                        {formatUptime(device.uptime)}
                      </Typography>
                    </TableCell>
                  )}
                  {isColumnVisible('asy') && (
                    <TableCell>
                      <Typography variant="body2" color="text.secondary" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                        {device.hardware_version || '-'}
                      </Typography>
                    </TableCell>
                  )}
                  {isColumnVisible('revision') && (
                    <TableCell>
                      <Typography variant="body2" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
                        {device.software_revision || '-'}
                      </Typography>
                    </TableCell>
                  )}
                  {isColumnVisible('lastSeen') && (
                    <TableCell>
                      <Tooltip
                        title={device.last_seen ? parseUTC(device.last_seen).toLocaleString() : '-'}
                      >
                        <Typography variant="body2" color="text.secondary">
                          {device.last_seen
                            ? formatDistanceToNow(parseUTC(device.last_seen), { addSuffix: true })
                            : '-'}
                        </Typography>
                      </Tooltip>
                    </TableCell>
                  )}
                  {isColumnVisible('software') && (
                    <TableCell>
                      <Typography variant="body2" color="text.secondary">
                        {device.software_version || '-'}
                      </Typography>
                    </TableCell>
                  )}
                  <TableCell onClick={(e) => e.stopPropagation()}>
                    <Tooltip title="Actions">
                      <IconButton size="small" onClick={(e) => handleOpenActionMenu(e, device)}>
                        <MoreIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
              {data?.items.length === 0 && (
                <TableRow>
                  <TableCell colSpan={columns.filter((c) => c.visible).length + 1} align="center">
                    No devices found
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        )}
      </TableContainer>

      {/* Row Action Menu */}
      <Menu
        anchorEl={actionAnchor}
        open={Boolean(actionAnchor)}
        onClose={handleCloseActionMenu}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        transformOrigin={{ vertical: 'top', horizontal: 'right' }}
      >
        <MenuItem onClick={handleViewDetails}>
          <ListItemIcon>
            <ViewIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>View Details</ListItemText>
        </MenuItem>
        <MenuItem onClick={handleViewConfigurations}>
          <ListItemIcon>
            <ConfigIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>View GAM Configurations</ListItemText>
        </MenuItem>
        <MenuItem onClick={handleOpenPortal} disabled={!selectedDevice?.ip_address}>
          <ListItemIcon>
            <PortalIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Open GAM Portal</ListItemText>
        </MenuItem>
      </Menu>
    </Box>
  )
}
