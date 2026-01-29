import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  CircularProgress,
  Grid,
  Card,
  CardContent,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
} from '@mui/material'
import {
  History as HistoryIcon,
  Today as TodayIcon,
  DateRange as WeekIcon,
} from '@mui/icons-material'
import { auditLogsApi, exportApi, downloadFile } from '../services/api'
import Breadcrumb from '../components/Breadcrumb'
import ListToolbar from '../components/ListToolbar'

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleString()
}

// Available columns
const allColumns = [
  { id: 'user', label: 'User', visible: true },
  { id: 'ip', label: 'IP Address', visible: true },
  { id: 'type', label: 'Type', visible: true },
  { id: 'description', label: 'Description', visible: true },
  { id: 'status', label: 'Status', visible: true },
  { id: 'date', label: 'Date', visible: true },
]

export default function AuditLogs() {
  const [page, setPage] = useState(0)
  const [rowsPerPage, setRowsPerPage] = useState(50)
  const [actionFilter, setActionFilter] = useState('')
  const [entityTypeFilter, setEntityTypeFilter] = useState('')
  const [usernameFilter] = useState('')
  const [searchFilter, setSearchFilter] = useState('')
  const [columns, setColumns] = useState(allColumns)

  // Detail dialog
  const [detailDialogOpen, setDetailDialogOpen] = useState(false)
  const [selectedLog, setSelectedLog] = useState<any>(null)

  // Fetch audit logs
  const { data, isLoading } = useQuery({
    queryKey: ['audit-logs', page, rowsPerPage, actionFilter, entityTypeFilter, usernameFilter, searchFilter],
    queryFn: () =>
      auditLogsApi
        .list({
          page: page + 1,
          page_size: rowsPerPage,
          action: actionFilter || undefined,
          entity_type: entityTypeFilter || undefined,
          username: usernameFilter || undefined,
          search: searchFilter || undefined,
        })
        .then((res) => res.data),
  })

  // Fetch stats
  const { data: statsData } = useQuery({
    queryKey: ['audit-logs-stats'],
    queryFn: () => auditLogsApi.getStats().then((res) => res.data),
  })

  // Fetch action types for filter
  const { data: actionTypes } = useQuery({
    queryKey: ['audit-log-actions'],
    queryFn: () => auditLogsApi.getActionTypes().then((res) => res.data),
  })

  // Fetch entity types for filter
  const { data: entityTypes } = useQuery({
    queryKey: ['audit-log-entity-types'],
    queryFn: () => auditLogsApi.getEntityTypes().then((res) => res.data),
  })

  const openDetailDialog = (log: any) => {
    setSelectedLog(log)
    setDetailDialogOpen(true)
  }

  const isColumnVisible = (columnId: string) =>
    columns.find((c) => c.id === columnId)?.visible ?? false

  const handleExport = async () => {
    try {
      const response = await exportApi.auditLogs()
      const filename = `audit_logs_${new Date().toISOString().slice(0, 10)}.csv`
      downloadFile(response.data, filename)
    } catch (error) {
      console.error('Export failed:', error)
    }
  }

  const actionFilterOptions = [
    { value: '', label: 'All Actions' },
    ...(actionTypes?.actions?.map((a: string) => ({ value: a, label: a })) || []),
  ]

  const entityTypeOptions = [
    { value: '', label: 'All Types' },
    ...(entityTypes?.entity_types?.map((t: string) => ({ value: t, label: t })) || []),
  ]

  return (
    <Box>
      <Breadcrumb current="Audit Logs" />

      {/* Stats Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={4}>
          <Card>
            <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <HistoryIcon color="primary" sx={{ fontSize: 40 }} />
              <Box>
                <Typography variant="h4">{statsData?.total_entries || 0}</Typography>
                <Typography variant="body2" color="text.secondary">
                  Total Entries
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Card>
            <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <TodayIcon color="success" sx={{ fontSize: 40 }} />
              <Box>
                <Typography variant="h4">{statsData?.entries_today || 0}</Typography>
                <Typography variant="body2" color="text.secondary">
                  Today
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Card>
            <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <WeekIcon color="info" sx={{ fontSize: 40 }} />
              <Box>
                <Typography variant="h4">{statsData?.entries_this_week || 0}</Typography>
                <Typography variant="body2" color="text.secondary">
                  This Week
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <ListToolbar
        search={searchFilter}
        onSearchChange={(value) => {
          setSearchFilter(value)
          setPage(0)
        }}
        searchPlaceholder="Search description..."
        filters={[
          {
            value: actionFilter,
            onChange: (value) => {
              setActionFilter(value)
              setPage(0)
            },
            options: actionFilterOptions,
          },
          {
            value: entityTypeFilter,
            onChange: (value) => {
              setEntityTypeFilter(value)
              setPage(0)
            },
            options: entityTypeOptions,
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
        pageSizeOptions={[20, 50, 100]}
        actions={[
          {
            label: 'Export All Data (CSV)',
            onClick: handleExport,
          },
        ]}
        columns={columns}
        onColumnsChange={setColumns}
      />

      {data && (
        <Box sx={{ mb: 2 }}>
          <Chip label={`Total: ${data.total}`} size="small" />
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
                {isColumnVisible('user') && <TableCell>User</TableCell>}
                {isColumnVisible('ip') && <TableCell>IP Address</TableCell>}
                {isColumnVisible('type') && <TableCell>Type</TableCell>}
                {isColumnVisible('description') && <TableCell>Description</TableCell>}
                {isColumnVisible('status') && <TableCell>Status</TableCell>}
                {isColumnVisible('date') && <TableCell>Date</TableCell>}
              </TableRow>
            </TableHead>
            <TableBody>
              {data?.items.map((log: any) => (
                <TableRow key={log.id} hover onClick={() => openDetailDialog(log)} sx={{ cursor: 'pointer' }}>
                  {isColumnVisible('user') && (
                    <TableCell>{log.username}</TableCell>
                  )}
                  {isColumnVisible('ip') && (
                    <TableCell>{log.ip_address || '-'}</TableCell>
                  )}
                  {isColumnVisible('type') && (
                    <TableCell>{log.action || log.entity_type || '-'}</TableCell>
                  )}
                  {isColumnVisible('description') && (
                    <TableCell>
                      <Typography variant="body2" noWrap sx={{ maxWidth: 400 }}>
                        {log.description || `${log.entity_type}: ${log.entity_name || log.entity_id || ''}`}
                      </Typography>
                    </TableCell>
                  )}
                  {isColumnVisible('status') && (
                    <TableCell>
                      <Chip
                        label={log.status || 'OK'}
                        size="small"
                        color={log.status === 'ERROR' ? 'error' : 'success'}
                        variant="outlined"
                      />
                    </TableCell>
                  )}
                  {isColumnVisible('date') && (
                    <TableCell>
                      <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                        {formatDate(log.created_at)}
                      </Typography>
                    </TableCell>
                  )}
                </TableRow>
              ))}
              {data?.items.length === 0 && (
                <TableRow>
                  <TableCell colSpan={columns.filter((c) => c.visible).length + 1} align="center">
                    No audit log entries found
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        )}
      </TableContainer>

      {/* Detail Dialog */}
      <Dialog
        open={detailDialogOpen}
        onClose={() => setDetailDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Audit Log Details - {selectedLog?.action} {selectedLog?.entity_type}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={6}>
              <Typography variant="subtitle2" color="text.secondary">
                User
              </Typography>
              <Typography variant="body1">{selectedLog?.username}</Typography>
            </Grid>
            <Grid item xs={6}>
              <Typography variant="subtitle2" color="text.secondary">
                Timestamp
              </Typography>
              <Typography variant="body1">
                {selectedLog?.created_at && formatDate(selectedLog.created_at)}
              </Typography>
            </Grid>
            <Grid item xs={6}>
              <Typography variant="subtitle2" color="text.secondary">
                Entity
              </Typography>
              <Typography variant="body1">
                {selectedLog?.entity_name || selectedLog?.entity_id || '-'}
              </Typography>
            </Grid>
            <Grid item xs={6}>
              <Typography variant="subtitle2" color="text.secondary">
                IP Address
              </Typography>
              <Typography variant="body1">{selectedLog?.ip_address || '-'}</Typography>
            </Grid>
            <Grid item xs={12}>
              <Typography variant="subtitle2" color="text.secondary">
                Description
              </Typography>
              <Typography variant="body1">{selectedLog?.description || '-'}</Typography>
            </Grid>
            {selectedLog?.old_values && (
              <Grid item xs={12}>
                <Typography variant="subtitle2" color="text.secondary">
                  Old Values
                </Typography>
                <Paper
                  variant="outlined"
                  sx={{
                    p: 1,
                    bgcolor: 'error.dark',
                    fontFamily: 'monospace',
                    fontSize: 12,
                    whiteSpace: 'pre-wrap',
                    overflow: 'auto',
                    maxHeight: 200,
                  }}
                >
                  {JSON.stringify(JSON.parse(selectedLog.old_values), null, 2)}
                </Paper>
              </Grid>
            )}
            {selectedLog?.new_values && (
              <Grid item xs={12}>
                <Typography variant="subtitle2" color="text.secondary">
                  New Values
                </Typography>
                <Paper
                  variant="outlined"
                  sx={{
                    p: 1,
                    bgcolor: 'success.dark',
                    fontFamily: 'monospace',
                    fontSize: 12,
                    whiteSpace: 'pre-wrap',
                    overflow: 'auto',
                    maxHeight: 200,
                  }}
                >
                  {JSON.stringify(JSON.parse(selectedLog.new_values), null, 2)}
                </Paper>
              </Grid>
            )}
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
