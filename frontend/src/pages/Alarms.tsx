import { useState } from 'react'
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
  Tooltip,
  Card,
  CardContent,
  Grid,
  Snackbar,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Stack,
  Divider,
  Button,
  Typography,
} from '@mui/material'
import {
  Info as InfoIcon,
  CheckCircle as AckIcon,
  Close as CloseIcon,
} from '@mui/icons-material'
import { alarmsApi, devicesApi, exportApi, downloadFile } from '../services/api'
import Breadcrumb from '../components/Breadcrumb'
import ListToolbar from '../components/ListToolbar'

const severityColors: Record<string, 'error' | 'warning' | 'info' | 'default'> = {
  CR: 'error',
  MJ: 'warning',
  MN: 'info',
  NA: 'default',
}

const severityLabels: Record<string, string> = {
  CR: 'Critical',
  MJ: 'Major',
  MN: 'Minor',
  NA: 'Normal',
}

// All available columns
const allColumns = [
  { id: 'systemName', label: 'System Name', visible: true },
  { id: 'productClass', label: 'Product Class', visible: true },
  { id: 'severity', label: 'Severity', visible: true },
  { id: 'condition', label: 'Condition', visible: true },
  { id: 'serviceAffecting', label: 'Service Affecting', visible: true },
  { id: 'description', label: 'Description', visible: true },
  { id: 'occurred', label: 'Occured', visible: true },
  { id: 'received', label: 'Received', visible: true },
  { id: 'cleared', label: 'Cleared', visible: true },
]

export default function Alarms() {
  const queryClient = useQueryClient()
  const [page, setPage] = useState(0)
  const [rowsPerPage, setRowsPerPage] = useState(20)
  const [activeOnly, setActiveOnly] = useState(true)
  const [deviceFilter, setDeviceFilter] = useState<string>('')
  const [severityFilter, setSeverityFilter] = useState<string>('')
  const [selectedAlarm, setSelectedAlarm] = useState<any>(null)
  const [detailDialogOpen, setDetailDialogOpen] = useState(false)
  const [columns, setColumns] = useState(allColumns)
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success',
  })

  const { data: alarmCounts } = useQuery({
    queryKey: ['alarm-counts'],
    queryFn: () => alarmsApi.getCounts().then((res) => res.data),
  })

  const { data: devicesData } = useQuery({
    queryKey: ['devices-list'],
    queryFn: () => devicesApi.list({ page_size: 100 }).then((res) => res.data),
  })

  const { data, isLoading } = useQuery({
    queryKey: ['alarms', page, rowsPerPage, activeOnly, deviceFilter, severityFilter],
    queryFn: () =>
      alarmsApi
        .list({
          page: page + 1,
          page_size: rowsPerPage,
          active_only: activeOnly,
          device_id: deviceFilter || undefined,
          severity: severityFilter || undefined,
        })
        .then((res) => res.data),
  })

  const acknowledgeMutation = useMutation({
    mutationFn: (id: string) => alarmsApi.acknowledge(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alarms'] })
      queryClient.invalidateQueries({ queryKey: ['alarm-counts'] })
      setSnackbar({ open: true, message: 'Alarm acknowledged', severity: 'success' })
    },
    onError: (error: any) => {
      setSnackbar({ open: true, message: error.response?.data?.detail || 'Failed to acknowledge alarm', severity: 'error' })
    },
  })

  const closeMutation = useMutation({
    mutationFn: (id: string) => alarmsApi.close(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alarms'] })
      queryClient.invalidateQueries({ queryKey: ['alarm-counts'] })
      setSnackbar({ open: true, message: 'Alarm closed', severity: 'success' })
    },
    onError: (error: any) => {
      setSnackbar({ open: true, message: error.response?.data?.detail || 'Failed to close alarm', severity: 'error' })
    },
  })

  const handleViewDetails = (alarm: any) => {
    setSelectedAlarm(alarm)
    setDetailDialogOpen(true)
  }

  const handleExport = async () => {
    try {
      const response = await exportApi.alarms({
        device_id: deviceFilter || undefined,
        active_only: activeOnly,
      })
      const filename = `alarms_${new Date().toISOString().slice(0, 10)}.csv`
      downloadFile(response.data, filename)
    } catch (error) {
      console.error('Export failed:', error)
    }
  }

  const isColumnVisible = (columnId: string) =>
    columns.find((c) => c.id === columnId)?.visible ?? false

  const deviceFilterOptions = [
    { value: '', label: 'All Devices' },
    ...(devicesData?.items?.map((d: any) => ({
      value: d.id,
      label: d.name || d.serial_number,
    })) || []),
  ]

  const severityFilterOptions = [
    { value: '', label: 'All' },
    { value: 'CR', label: 'Critical' },
    { value: 'MJ', label: 'Major' },
    { value: 'MN', label: 'Minor' },
    { value: 'NA', label: 'Normal' },
  ]

  const statusFilterOptions = [
    { value: 'true', label: 'Active Only' },
    { value: 'false', label: 'All Alarms' },
  ]

  return (
    <Box>
      <Breadcrumb current="Alarms" />

      {/* Alarm Counts Summary */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={6} sm={3} md={2}>
          <Card sx={{ borderLeft: 4, borderColor: 'error.main' }}>
            <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
              <Typography color="error.main" variant="overline">Critical</Typography>
              <Typography variant="h4" color="error.main">{alarmCounts?.critical || 0}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} sm={3} md={2}>
          <Card sx={{ borderLeft: 4, borderColor: 'warning.main' }}>
            <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
              <Typography color="warning.main" variant="overline">Major</Typography>
              <Typography variant="h4" color="warning.main">{alarmCounts?.major || 0}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} sm={3} md={2}>
          <Card sx={{ borderLeft: 4, borderColor: 'info.main' }}>
            <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
              <Typography color="info.main" variant="overline">Minor</Typography>
              <Typography variant="h4" color="info.main">{alarmCounts?.minor || 0}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} sm={3} md={2}>
          <Card sx={{ borderLeft: 4, borderColor: 'success.main' }}>
            <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
              <Typography color="success.main" variant="overline">Normal</Typography>
              <Typography variant="h4" color="success.main">{alarmCounts?.normal || 0}</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <ListToolbar
        filters={[
          {
            value: activeOnly ? 'true' : 'false',
            onChange: (value) => {
              setActiveOnly(value === 'true')
              setPage(0)
            },
            options: statusFilterOptions,
          },
          {
            value: deviceFilter,
            onChange: (value) => {
              setDeviceFilter(value)
              setPage(0)
            },
            options: deviceFilterOptions,
          },
          {
            value: severityFilter,
            onChange: (value) => {
              setSeverityFilter(value)
              setPage(0)
            },
            options: severityFilterOptions,
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

      <TableContainer component={Paper}>
        {isLoading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          <Table size="small">
            <TableHead>
              <TableRow>
                {isColumnVisible('systemName') && (
                  <TableCell>
                    <Tooltip title="GAM device name"><span>System Name</span></Tooltip>
                  </TableCell>
                )}
                {isColumnVisible('productClass') && (
                  <TableCell>
                    <Tooltip title="Device model"><span>Product Class</span></Tooltip>
                  </TableCell>
                )}
                {isColumnVisible('severity') && (
                  <TableCell>
                    <Tooltip title="Alarm severity (CR/MJ/MN/NA)"><span>Severity</span></Tooltip>
                  </TableCell>
                )}
                {isColumnVisible('condition') && (
                  <TableCell>
                    <Tooltip title="Alarm condition type"><span>Condition</span></Tooltip>
                  </TableCell>
                )}
                {isColumnVisible('serviceAffecting') && (
                  <TableCell>
                    <Tooltip title="Whether alarm affects service"><span>Service Affecting</span></Tooltip>
                  </TableCell>
                )}
                {isColumnVisible('description') && (
                  <TableCell>
                    <Tooltip title="Alarm description"><span>Description</span></Tooltip>
                  </TableCell>
                )}
                {isColumnVisible('occurred') && (
                  <TableCell>
                    <Tooltip title="When alarm occurred"><span>Occured</span></Tooltip>
                  </TableCell>
                )}
                {isColumnVisible('received') && (
                  <TableCell>
                    <Tooltip title="When alarm was received"><span>Received</span></Tooltip>
                  </TableCell>
                )}
                {isColumnVisible('cleared') && (
                  <TableCell>
                    <Tooltip title="When alarm was cleared"><span>Cleared</span></Tooltip>
                  </TableCell>
                )}
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {data?.items.map((alarm: any) => (
                <TableRow key={alarm.id} hover>
                  {isColumnVisible('systemName') && (
                    <TableCell>
                      {alarm.device_name || alarm.device_serial || '-'}
                    </TableCell>
                  )}
                  {isColumnVisible('productClass') && (
                    <TableCell>
                      {alarm.device_model || '-'}
                    </TableCell>
                  )}
                  {isColumnVisible('severity') && (
                    <TableCell>
                      <Chip
                        label={alarm.severity}
                        color={severityColors[alarm.severity] || 'default'}
                        size="small"
                      />
                    </TableCell>
                  )}
                  {isColumnVisible('condition') && (
                    <TableCell>{alarm.cond_type}</TableCell>
                  )}
                  {isColumnVisible('serviceAffecting') && (
                    <TableCell>
                      {alarm.is_service_affecting ? 'Yes' : 'No'}
                    </TableCell>
                  )}
                  {isColumnVisible('description') && (
                    <TableCell>
                      <Typography
                        variant="body2"
                        color="text.secondary"
                        sx={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis' }}
                        title={alarm.details}
                      >
                        {alarm.details || '-'}
                      </Typography>
                    </TableCell>
                  )}
                  {isColumnVisible('occurred') && (
                    <TableCell>
                      {new Date(alarm.occurred_at).toLocaleString()}
                    </TableCell>
                  )}
                  {isColumnVisible('received') && (
                    <TableCell>
                      {alarm.received_at ? new Date(alarm.received_at).toLocaleString() : new Date(alarm.occurred_at).toLocaleString()}
                    </TableCell>
                  )}
                  {isColumnVisible('cleared') && (
                    <TableCell>
                      {alarm.closing_date ? new Date(alarm.closing_date).toLocaleString() : '-'}
                    </TableCell>
                  )}
                  <TableCell>
                    <Tooltip title="View Details">
                      <IconButton size="small" onClick={() => handleViewDetails(alarm)}>
                        <InfoIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    {alarm.is_active && (
                      <>
                        {!alarm.acknowledged_at && (
                          <Tooltip title="Acknowledge">
                            <IconButton
                              size="small"
                              onClick={() => acknowledgeMutation.mutate(alarm.id)}
                              disabled={acknowledgeMutation.isPending}
                              color="primary"
                            >
                              <AckIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        )}
                        <Tooltip title="Close">
                          <IconButton
                            size="small"
                            onClick={() => closeMutation.mutate(alarm.id)}
                            disabled={closeMutation.isPending}
                            color="error"
                          >
                            <CloseIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </>
                    )}
                  </TableCell>
                </TableRow>
              ))}
              {data?.items.length === 0 && (
                <TableRow>
                  <TableCell colSpan={columns.filter((c) => c.visible).length + 1} align="center">
                    No alarms found
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        )}
      </TableContainer>

      {/* Alarm Detail Dialog */}
      <Dialog
        open={detailDialogOpen}
        onClose={() => setDetailDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Stack direction="row" spacing={2} alignItems="center">
            <Chip
              label={severityLabels[selectedAlarm?.severity] || selectedAlarm?.severity}
              color={severityColors[selectedAlarm?.severity] || 'default'}
            />
            <Typography variant="h6">Alarm Details</Typography>
          </Stack>
        </DialogTitle>
        <DialogContent>
          {selectedAlarm && (
            <Stack spacing={2} sx={{ mt: 1 }}>
              <Box>
                <Typography variant="subtitle2" color="text.secondary">Device</Typography>
                <Typography>{selectedAlarm.device_name || selectedAlarm.device_serial || 'Unknown'}</Typography>
              </Box>
              <Divider />
              <Box>
                <Typography variant="subtitle2" color="text.secondary">Condition Type</Typography>
                <Typography>{selectedAlarm.cond_type}</Typography>
              </Box>
              <Box>
                <Typography variant="subtitle2" color="text.secondary">Interface</Typography>
                <Typography>{selectedAlarm.if_descr || '-'}</Typography>
              </Box>
              <Box>
                <Typography variant="subtitle2" color="text.secondary">Details</Typography>
                <Typography>{selectedAlarm.details || 'No additional details'}</Typography>
              </Box>
              <Divider />
              <Box>
                <Typography variant="subtitle2" color="text.secondary">Service Affecting</Typography>
                <Typography>{selectedAlarm.is_service_affecting ? 'Yes' : 'No'}</Typography>
              </Box>
              <Box>
                <Typography variant="subtitle2" color="text.secondary">Occurred At</Typography>
                <Typography>{new Date(selectedAlarm.occurred_at).toLocaleString()}</Typography>
              </Box>
              {selectedAlarm.acknowledged_at && (
                <Box>
                  <Typography variant="subtitle2" color="text.secondary">Acknowledged</Typography>
                  <Typography>
                    {selectedAlarm.acknowledged_by} @ {new Date(selectedAlarm.acknowledged_at).toLocaleString()}
                  </Typography>
                </Box>
              )}
              {selectedAlarm.closing_date && (
                <Box>
                  <Typography variant="subtitle2" color="text.secondary">Closed At</Typography>
                  <Typography>{new Date(selectedAlarm.closing_date).toLocaleString()}</Typography>
                </Box>
              )}
            </Stack>
          )}
        </DialogContent>
        <DialogActions>
          {selectedAlarm?.is_active && !selectedAlarm?.acknowledged_at && (
            <Button
              onClick={() => {
                acknowledgeMutation.mutate(selectedAlarm.id)
                setDetailDialogOpen(false)
              }}
              color="primary"
            >
              Acknowledge
            </Button>
          )}
          {selectedAlarm?.is_active && (
            <Button
              onClick={() => {
                closeMutation.mutate(selectedAlarm.id)
                setDetailDialogOpen(false)
              }}
              color="error"
            >
              Close Alarm
            </Button>
          )}
          <Button onClick={() => setDetailDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

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
    </Box>
  )
}
