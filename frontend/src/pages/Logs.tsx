import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Box,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Button,
  CircularProgress,
  Chip,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
  InputAdornment,
} from '@mui/material'
import {
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  Search as SearchIcon,
} from '@mui/icons-material'
import { auditLogsApi } from '../services/api'
import Breadcrumb from '../components/Breadcrumb'
import ListToolbar from '../components/ListToolbar'

interface AuditLogEntry {
  id: string
  user_id: string | null
  username: string
  ip_address: string | null
  action: string
  entity_type: string
  entity_id: string | null
  entity_name: string | null
  description: string | null
  old_values: string | null
  new_values: string | null
  created_at: string
}

const actionColors: Record<string, 'error' | 'warning' | 'info' | 'success' | 'default'> = {
  CREATE: 'success',
  UPDATE: 'info',
  DELETE: 'error',
  LOGIN: 'default',
  LOGOUT: 'default',
  SYNC: 'info',
  PROVISION: 'success',
  RPC: 'warning',
}

const allColumns = [
  { id: 'timestamp', label: 'Timestamp', visible: true },
  { id: 'action', label: 'Action', visible: true },
  { id: 'entityType', label: 'Entity Type', visible: true },
  { id: 'entityName', label: 'Entity', visible: true },
  { id: 'username', label: 'User', visible: true },
  { id: 'ipAddress', label: 'IP Address', visible: true },
  { id: 'description', label: 'Description', visible: true },
]

export default function Logs() {
  const [page, setPage] = useState(0)
  const [rowsPerPage, setRowsPerPage] = useState(50)
  const [search, setSearch] = useState('')
  const [actionFilter, setActionFilter] = useState<string>('')
  const [entityFilter, setEntityFilter] = useState<string>('')
  const [columns, setColumns] = useState(allColumns)

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['audit-logs', page, rowsPerPage, search, actionFilter, entityFilter],
    queryFn: () =>
      auditLogsApi
        .list({
          page: page + 1,
          page_size: rowsPerPage,
          search: search || undefined,
          action: actionFilter || undefined,
          entity_type: entityFilter || undefined,
        })
        .then((res) => res.data),
  })

  const { data: actionTypes } = useQuery({
    queryKey: ['audit-log-actions'],
    queryFn: () => auditLogsApi.getActionTypes().then((res) => res.data.actions as string[]),
  })

  const { data: entityTypes } = useQuery({
    queryKey: ['audit-log-entity-types'],
    queryFn: () => auditLogsApi.getEntityTypes().then((res) => res.data.entity_types as string[]),
  })

  const logs: AuditLogEntry[] = data?.items || []

  const handleExportCSV = () => {
    if (!logs.length) return
    const headers = ['Timestamp', 'Action', 'Entity Type', 'Entity', 'User', 'IP Address', 'Description']
    const csvContent = [
      headers.join(','),
      ...logs.map((log) =>
        [
          log.created_at,
          log.action,
          log.entity_type,
          log.entity_name || '',
          log.username,
          log.ip_address || '',
          `"${(log.description || '').replace(/"/g, '""')}"`,
        ].join(',')
      ),
    ].join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `audit-logs-${new Date().toISOString().split('T')[0]}.csv`
    a.click()
    window.URL.revokeObjectURL(url)
  }

  const isColumnVisible = (columnId: string) =>
    columns.find((c) => c.id === columnId)?.visible ?? false

  return (
    <Box>
      <Breadcrumb current="Logs" />

      <ListToolbar
        page={page}
        pageSize={rowsPerPage}
        total={data?.total || 0}
        onPageChange={setPage}
        onPageSizeChange={(size) => {
          setRowsPerPage(size)
          setPage(0)
        }}
        pageSizeOptions={[20, 50, 100, 200]}
        columns={columns}
        onColumnsChange={setColumns}
        actions={[
          {
            label: 'Refresh',
            icon: <RefreshIcon />,
            onClick: () => refetch(),
          },
          {
            label: 'Export CSV',
            icon: <DownloadIcon />,
            onClick: handleExportCSV,
          },
        ]}
      />

      {/* Filters */}
      <Paper sx={{ mb: 2, p: 2, display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
        <TextField
          size="small"
          placeholder="Search logs..."
          value={search}
          onChange={(e) => {
            setSearch(e.target.value)
            setPage(0)
          }}
          sx={{ minWidth: 220 }}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon fontSize="small" />
              </InputAdornment>
            ),
          }}
        />
        <FormControl size="small" sx={{ minWidth: 140 }}>
          <InputLabel>Action</InputLabel>
          <Select
            value={actionFilter}
            label="Action"
            onChange={(e) => {
              setActionFilter(e.target.value)
              setPage(0)
            }}
          >
            <MenuItem value="">All</MenuItem>
            {actionTypes?.map((a) => (
              <MenuItem key={a} value={a}>
                {a}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <FormControl size="small" sx={{ minWidth: 140 }}>
          <InputLabel>Entity Type</InputLabel>
          <Select
            value={entityFilter}
            label="Entity Type"
            onChange={(e) => {
              setEntityFilter(e.target.value)
              setPage(0)
            }}
          >
            <MenuItem value="">All</MenuItem>
            {entityTypes?.map((t) => (
              <MenuItem key={t} value={t}>
                {t}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        {(search || actionFilter || entityFilter) && (
          <Button
            size="small"
            onClick={() => {
              setSearch('')
              setActionFilter('')
              setEntityFilter('')
              setPage(0)
            }}
          >
            Clear Filters
          </Button>
        )}
      </Paper>

      <Paper>
        {isLoading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow sx={{ backgroundColor: '#f5f5f5' }}>
                  {isColumnVisible('timestamp') && (
                    <TableCell sx={{ fontWeight: 600, width: 180 }}>Timestamp</TableCell>
                  )}
                  {isColumnVisible('action') && (
                    <TableCell sx={{ fontWeight: 600, width: 100 }}>Action</TableCell>
                  )}
                  {isColumnVisible('entityType') && (
                    <TableCell sx={{ fontWeight: 600, width: 120 }}>Entity Type</TableCell>
                  )}
                  {isColumnVisible('entityName') && (
                    <TableCell sx={{ fontWeight: 600, width: 200 }}>Entity</TableCell>
                  )}
                  {isColumnVisible('username') && (
                    <TableCell sx={{ fontWeight: 600, width: 120 }}>User</TableCell>
                  )}
                  {isColumnVisible('ipAddress') && (
                    <TableCell sx={{ fontWeight: 600, width: 130 }}>IP Address</TableCell>
                  )}
                  {isColumnVisible('description') && (
                    <TableCell sx={{ fontWeight: 600 }}>Description</TableCell>
                  )}
                </TableRow>
              </TableHead>
              <TableBody>
                {logs.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={columns.filter((c) => c.visible).length} align="center" sx={{ py: 4 }}>
                      <Typography color="text.secondary">
                        No log entries found
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  logs.map((log) => (
                    <TableRow key={log.id} hover>
                      {isColumnVisible('timestamp') && (
                        <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>
                          {new Date(log.created_at).toLocaleString()}
                        </TableCell>
                      )}
                      {isColumnVisible('action') && (
                        <TableCell>
                          <Chip
                            label={log.action}
                            size="small"
                            color={actionColors[log.action] || 'default'}
                            sx={{ minWidth: 70 }}
                          />
                        </TableCell>
                      )}
                      {isColumnVisible('entityType') && (
                        <TableCell>{log.entity_type}</TableCell>
                      )}
                      {isColumnVisible('entityName') && (
                        <TableCell>{log.entity_name || '-'}</TableCell>
                      )}
                      {isColumnVisible('username') && (
                        <TableCell>{log.username}</TableCell>
                      )}
                      {isColumnVisible('ipAddress') && (
                        <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>
                          {log.ip_address || '-'}
                        </TableCell>
                      )}
                      {isColumnVisible('description') && (
                        <TableCell sx={{ fontSize: '0.85rem' }}>
                          {log.description || '-'}
                        </TableCell>
                      )}
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>
    </Box>
  )
}
