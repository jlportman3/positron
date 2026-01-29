import { useState, useEffect } from 'react'
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
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Checkbox,
  FormControlLabel,
  IconButton,
  Tooltip,
  Grid,
  Typography,
  Alert,
} from '@mui/material'
import { Edit as EditIcon, Refresh as RefreshIcon } from '@mui/icons-material'
import Breadcrumb from '../components/Breadcrumb'
import ListToolbar from '../components/ListToolbar'
import { devicesApi, getErrorMessage } from '../services/api'

// Common timezone options
const timezoneOptions = [
  { value: '(UTC-12:00)', label: '(UTC-12:00) International Date Line West' },
  { value: '(UTC-11:00)', label: '(UTC-11:00) Midway Island' },
  { value: '(UTC-10:00)', label: '(UTC-10:00) Hawaii' },
  { value: '(UTC-09:00)', label: '(UTC-09:00) Alaska' },
  { value: '(UTC-08:00)', label: '(UTC-08:00) Pacific Time (US & Canada)' },
  { value: '(UTC-07:00)', label: '(UTC-07:00) Mountain Time (US & Canada)' },
  { value: '(UTC-06:00)', label: '(UTC-06:00) Central Time (US & Canada)' },
  { value: '(UTC-05:00)', label: '(UTC-05:00) Eastern Time (US & Canada)' },
  { value: '(UTC-04:00)', label: '(UTC-04:00) Atlantic Time (Canada)' },
  { value: '(UTC-03:00)', label: '(UTC-03:00) Buenos Aires' },
  { value: '(UTC-02:00)', label: '(UTC-02:00) Mid-Atlantic' },
  { value: '(UTC-01:00)', label: '(UTC-01:00) Azores' },
  { value: '(UTC00:00)', label: '(UTC00:00) London, Dublin' },
  { value: '(UTC+01:00)', label: '(UTC+01:00) Paris, Berlin' },
  { value: '(UTC+02:00)', label: '(UTC+02:00) Cairo, Athens' },
  { value: '(UTC+03:00)', label: '(UTC+03:00) Moscow, Kuwait' },
  { value: '(UTC+04:00)', label: '(UTC+04:00) Abu Dhabi, Muscat' },
  { value: '(UTC+05:00)', label: '(UTC+05:00) Islamabad, Karachi' },
  { value: '(UTC+05:30)', label: '(UTC+05:30) Mumbai, Chennai' },
  { value: '(UTC+06:00)', label: '(UTC+06:00) Dhaka' },
  { value: '(UTC+07:00)', label: '(UTC+07:00) Bangkok, Jakarta' },
  { value: '(UTC+08:00)', label: '(UTC+08:00) Beijing, Singapore' },
  { value: '(UTC+09:00)', label: '(UTC+09:00) Tokyo, Seoul' },
  { value: '(UTC+10:00)', label: '(UTC+10:00) Sydney, Melbourne' },
  { value: '(UTC+11:00)', label: '(UTC+11:00) Solomon Islands' },
  { value: '(UTC+12:00)', label: '(UTC+12:00) Auckland, Fiji' },
]

// All available columns
const allColumns = [
  { id: 'systemName', label: 'System Name', visible: true },
  { id: 'serial', label: 'Serial Number', visible: true },
  { id: 'ip', label: 'GAM IP Address', visible: true },
  { id: 'ntpServers', label: 'NTP Servers', visible: true },
  { id: 'timezone', label: 'Timezone', visible: true },
  { id: 'summerTime', label: 'Summer Time', visible: true },
]

interface DeviceTimezoneData {
  device_id: string
  serial_number: string
  name: string
  timezone: any
  ntp_servers: any
  error?: string
}

interface TimezoneFormData {
  timezone: string
  dst_enabled: boolean
  dst_start: string
  dst_end: string
  ntp_servers: string[]
  ntp_enabled: boolean
}

const defaultFormData: TimezoneFormData = {
  timezone: '(UTC-06:00)',
  dst_enabled: false,
  dst_start: '',
  dst_end: '',
  ntp_servers: ['', ''],
  ntp_enabled: true,
}

// Convert offset in minutes to timezone label
function offsetToLabel(offsetMinutes: number): string {
  const hours = Math.floor(Math.abs(offsetMinutes) / 60)
  const mins = Math.abs(offsetMinutes) % 60
  const sign = offsetMinutes <= 0 ? '-' : '+'
  const hStr = String(hours).padStart(2, '0')
  const mStr = String(mins).padStart(2, '0')
  return `(UTC${sign}${hStr}:${mStr})`
}

// Extract timezone display string from RPC response
function parseTimezone(tzData: any): string {
  if (!tzData) return '-'
  const offset = tzData?.TimeZoneOffset
  if (offset !== undefined && offset !== null) {
    const acronym = tzData?.TimeZoneAcronym
    const label = offsetToLabel(offset)
    return acronym ? `${label} ${acronym}` : label
  }
  return '-'
}

// Extract timezone offset value for the select dropdown
function parseTimezoneValue(tzData: any): string {
  if (!tzData) return '(UTC-06:00)'
  const offset = tzData?.TimeZoneOffset
  if (offset !== undefined && offset !== null) {
    return offsetToLabel(offset)
  }
  return '(UTC-06:00)'
}

// Extract DST enabled from RPC response
function parseDstEnabled(tzData: any): boolean {
  if (!tzData) return false
  return tzData?.SummerTimeMode === 'enable'
}

// Extract NTP servers from RPC response ({key, val} format)
function parseNtpServers(ntpData: any): string[] {
  if (!ntpData || !Array.isArray(ntpData)) return []
  return ntpData
    .map((s: any) => s?.val || s?.Address || s?.address || '')
    .filter((v: string) => v && v !== '<no-address>')
}

export default function Timezones() {
  const queryClient = useQueryClient()
  const [columns, setColumns] = useState(allColumns)
  const [page, setPage] = useState(0)
  const [rowsPerPage, setRowsPerPage] = useState(50)

  // Dialog state
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingDevice, setEditingDevice] = useState<any>(null)
  const [formData, setFormData] = useState<TimezoneFormData>(defaultFormData)

  // Per-device timezone data fetched via RPC
  const [tzDataMap, setTzDataMap] = useState<Record<string, DeviceTimezoneData>>({})
  const [loadingTz, setLoadingTz] = useState(false)

  // Fetch device list
  const { data, isLoading } = useQuery({
    queryKey: ['devices-timezones', page, rowsPerPage],
    queryFn: () =>
      devicesApi.list({
        page: page + 1,
        page_size: rowsPerPage,
      }).then((res) => res.data),
  })

  // Fetch timezone data from each device via RPC
  const fetchTimezoneData = async (devices: any[]) => {
    setLoadingTz(true)
    const results: Record<string, DeviceTimezoneData> = {}
    await Promise.all(
      devices.map(async (device: any) => {
        try {
          const res = await devicesApi.getTimezone(device.id)
          results[device.id] = res.data
        } catch {
          results[device.id] = {
            device_id: device.id,
            serial_number: device.serial_number,
            name: device.name || device.serial_number,
            timezone: null,
            ntp_servers: null,
            error: 'Failed to fetch',
          }
        }
      })
    )
    setTzDataMap(results)
    setLoadingTz(false)
  }

  // Fetch timezone data when device list loads
  useEffect(() => {
    if (data?.items?.length) {
      fetchTimezoneData(data.items)
    }
  }, [data?.items])

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) =>
      devicesApi.updateTimezone(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['devices-timezones'] })
      setDialogOpen(false)
      setEditingDevice(null)
      // Re-fetch timezone data
      if (data?.items?.length) {
        fetchTimezoneData(data.items)
      }
    },
  })

  const openEditDialog = (device: any) => {
    const tzInfo = tzDataMap[device.id]
    const servers = parseNtpServers(tzInfo?.ntp_servers)
    setEditingDevice(device)
    setFormData({
      timezone: parseTimezoneValue(tzInfo?.timezone),
      dst_enabled: parseDstEnabled(tzInfo?.timezone),
      dst_start: '',
      dst_end: '',
      ntp_servers: [servers[0] || '', servers[1] || ''],
      ntp_enabled: true,
    })
    setDialogOpen(true)
  }

  const handleSubmit = () => {
    if (editingDevice) {
      updateMutation.mutate({
        id: editingDevice.id,
        data: {
          timezone: formData.timezone,
          dst_enabled: formData.dst_enabled,
          dst_start: formData.dst_start,
          dst_end: formData.dst_end,
          ntp_servers: formData.ntp_servers.filter(Boolean),
          ntp_enabled: formData.ntp_enabled,
        },
      })
    }
  }

  const isColumnVisible = (columnId: string) =>
    columns.find((c) => c.id === columnId)?.visible ?? false

  return (
    <Box>
      <Breadcrumb current="Timezones" />

      <ListToolbar
        page={page}
        pageSize={rowsPerPage}
        total={data?.total || 0}
        onPageChange={setPage}
        onPageSizeChange={(size) => {
          setRowsPerPage(size)
          setPage(0)
        }}
        pageSizeOptions={[20, 50, 100]}
        columns={columns}
        onColumnsChange={setColumns}
        actions={[
          {
            label: 'Refresh',
            icon: <RefreshIcon />,
            onClick: () => {
              if (data?.items?.length) fetchTimezoneData(data.items)
            },
          },
        ]}
      />

      <Paper>
        {isLoading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  {isColumnVisible('systemName') && <TableCell>System Name</TableCell>}
                  {isColumnVisible('serial') && <TableCell>Serial Number</TableCell>}
                  {isColumnVisible('ip') && <TableCell>GAM IP Address</TableCell>}
                  {isColumnVisible('ntpServers') && <TableCell>NTP Servers</TableCell>}
                  {isColumnVisible('timezone') && <TableCell>Timezone</TableCell>}
                  {isColumnVisible('summerTime') && <TableCell>Summer Time</TableCell>}
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {data?.items?.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={columns.filter((c) => c.visible).length + 1} align="center">
                      No devices found
                    </TableCell>
                  </TableRow>
                ) : (
                  data?.items?.map((device: any) => {
                    const tzInfo = tzDataMap[device.id]
                    const tzLoading = loadingTz && !tzInfo
                    const servers = parseNtpServers(tzInfo?.ntp_servers)

                    return (
                      <TableRow key={device.id} hover>
                        {isColumnVisible('systemName') && (
                          <TableCell>
                            <Typography variant="body2" fontWeight="medium">
                              {device.name || device.serial_number}
                            </Typography>
                          </TableCell>
                        )}
                        {isColumnVisible('serial') && (
                          <TableCell>{device.serial_number}</TableCell>
                        )}
                        {isColumnVisible('ip') && (
                          <TableCell>{device.ip_address}</TableCell>
                        )}
                        {isColumnVisible('ntpServers') && (
                          <TableCell>
                            {tzLoading ? (
                              <CircularProgress size={14} />
                            ) : tzInfo?.error ? (
                              <Typography variant="caption" color="error">{tzInfo.error}</Typography>
                            ) : servers.length > 0 ? (
                              servers.join(', ')
                            ) : (
                              '-'
                            )}
                          </TableCell>
                        )}
                        {isColumnVisible('timezone') && (
                          <TableCell>
                            {tzLoading ? (
                              <CircularProgress size={14} />
                            ) : tzInfo?.error ? (
                              '-'
                            ) : (
                              parseTimezone(tzInfo?.timezone)
                            )}
                          </TableCell>
                        )}
                        {isColumnVisible('summerTime') && (
                          <TableCell>
                            {tzLoading ? (
                              <CircularProgress size={14} />
                            ) : tzInfo?.error ? (
                              '-'
                            ) : parseDstEnabled(tzInfo?.timezone) ? (
                              'Yes'
                            ) : (
                              'No'
                            )}
                          </TableCell>
                        )}
                        <TableCell>
                          <Tooltip title="Edit Timezone Settings">
                            <IconButton
                              size="small"
                              onClick={() => openEditDialog(device)}
                              disabled={!!tzInfo?.error}
                            >
                              <EditIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        </TableCell>
                      </TableRow>
                    )
                  })
                )}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>

      {/* Edit Timezone Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          Edit Timezone Settings - {editingDevice?.name || editingDevice?.serial_number}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ pt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                size="small"
                label="NTP Server 1"
                value={formData.ntp_servers[0]}
                onChange={(e) => {
                  const s = [...formData.ntp_servers]
                  s[0] = e.target.value
                  setFormData({ ...formData, ntp_servers: s })
                }}
                placeholder="e.g., 10.0.4.2"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                size="small"
                label="NTP Server 2"
                value={formData.ntp_servers[1]}
                onChange={(e) => {
                  const s = [...formData.ntp_servers]
                  s[1] = e.target.value
                  setFormData({ ...formData, ntp_servers: s })
                }}
                placeholder="Optional secondary NTP server"
              />
            </Grid>
            <Grid item xs={12}>
              <FormControl fullWidth size="small">
                <InputLabel>Timezone</InputLabel>
                <Select
                  value={formData.timezone}
                  label="Timezone"
                  onChange={(e) => setFormData({ ...formData, timezone: e.target.value })}
                >
                  {timezoneOptions.map((opt) => (
                    <MenuItem key={opt.value} value={opt.value}>
                      {opt.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={formData.dst_enabled}
                    onChange={(e) => setFormData({ ...formData, dst_enabled: e.target.checked })}
                  />
                }
                label="Enable Summer Time (DST)"
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={formData.ntp_enabled}
                    onChange={(e) => setFormData({ ...formData, ntp_enabled: e.target.checked })}
                  />
                }
                label="Enable NTP"
              />
            </Grid>
          </Grid>
          {updateMutation.isError && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {getErrorMessage(updateMutation.error, 'Failed to update timezone settings. Check device connectivity.')}
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleSubmit}
            disabled={updateMutation.isPending}
          >
            {updateMutation.isPending ? 'Saving...' : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
