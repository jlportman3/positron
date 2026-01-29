import { useState } from 'react'
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
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Stack,
  FormControlLabel,
  Switch,
  Tooltip,
} from '@mui/material'
import {
  Settings as SettingsIcon,
  Link as LinkIcon,
  LinkOff as LinkOffIcon,
  FiberManualRecord as FiberIcon,
  Cable as CableIcon,
} from '@mui/icons-material'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { portsApi } from '../services/api'
import { useNavigate } from 'react-router-dom'
import Breadcrumb from '../components/Breadcrumb'
import ListToolbar from '../components/ListToolbar'

interface Port {
  id: string
  device_id: string
  key: string
  position: number | null
  link: boolean
  fdx: boolean
  speed: string | null
  fiber: boolean
  sfp_type: string | null
  sfp_vendor_name: string | null
  sfp_vendor_pn: string | null
  sfp_vendor_sn: string | null
  present: boolean
  loss_of_signal: boolean
  tx_fault: boolean
  shutdown: boolean
  mtu: number
  device_name: string | null
  device_serial: string | null
  created_at: string
  updated_at: string
}

const allColumns = [
  { id: 'device', label: 'Device', visible: true },
  { id: 'port', label: 'Port', visible: true },
  { id: 'type', label: 'Type', visible: true },
  { id: 'link', label: 'Link', visible: true },
  { id: 'speed', label: 'Speed', visible: true },
  { id: 'sfp', label: 'SFP', visible: true },
  { id: 'mtu', label: 'MTU', visible: true },
  { id: 'status', label: 'Status', visible: true },
]

export default function Ports() {
  const [page, setPage] = useState(0)
  const [rowsPerPage, setRowsPerPage] = useState(25)
  const [search, setSearch] = useState('')
  const [linkFilter, setLinkFilter] = useState<string>('')
  const [columns, setColumns] = useState(allColumns)
  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [selectedPort, setSelectedPort] = useState<Port | null>(null)
  const [formData, setFormData] = useState({
    shutdown: false,
    mtu: 1500,
  })

  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data: ports = [], isLoading } = useQuery<Port[]>({
    queryKey: ['ports-all', page, rowsPerPage, search, linkFilter],
    queryFn: async () => {
      const response = await portsApi.listAll({
        page: page + 1,
        page_size: rowsPerPage,
        search: search || undefined,
        link: linkFilter === '' ? undefined : linkFilter === 'up',
      })
      return response.data
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) =>
      portsApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ports-all'] })
      setEditDialogOpen(false)
    },
  })

  const handleEdit = (port: Port) => {
    setSelectedPort(port)
    setFormData({
      shutdown: port.shutdown,
      mtu: port.mtu,
    })
    setEditDialogOpen(true)
  }

  const handleSave = () => {
    if (selectedPort) {
      updateMutation.mutate({ id: selectedPort.id, data: formData })
    }
  }

  const isColumnVisible = (columnId: string) =>
    columns.find((c) => c.id === columnId)?.visible ?? false

  const linkFilterOptions = [
    { value: '', label: 'All' },
    { value: 'up', label: 'Link Up' },
    { value: 'down', label: 'Link Down' },
  ]

  return (
    <Box>
      <Breadcrumb current="Ports" />

      <ListToolbar
        search={search}
        onSearchChange={(value) => {
          setSearch(value)
          setPage(0)
        }}
        searchPlaceholder="Search ports or devices..."
        filters={[
          {
            value: linkFilter,
            onChange: (value) => {
              setLinkFilter(value)
              setPage(0)
            },
            options: linkFilterOptions,
          },
        ]}
        page={page}
        pageSize={rowsPerPage}
        total={ports.length}
        onPageChange={setPage}
        onPageSizeChange={(size) => {
          setRowsPerPage(size)
          setPage(0)
        }}
        pageSizeOptions={[10, 25, 50, 100]}
        columns={columns}
        onColumnsChange={setColumns}
      />

      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              {isColumnVisible('device') && <TableCell>Device</TableCell>}
              {isColumnVisible('port') && <TableCell>Port</TableCell>}
              {isColumnVisible('type') && <TableCell>Type</TableCell>}
              {isColumnVisible('link') && <TableCell>Link</TableCell>}
              {isColumnVisible('speed') && <TableCell>Speed</TableCell>}
              {isColumnVisible('sfp') && <TableCell>SFP</TableCell>}
              {isColumnVisible('mtu') && <TableCell>MTU</TableCell>}
              {isColumnVisible('status') && <TableCell>Status</TableCell>}
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={columns.filter((c) => c.visible).length + 1} align="center">
                  Loading...
                </TableCell>
              </TableRow>
            ) : ports.length === 0 ? (
              <TableRow>
                <TableCell colSpan={columns.filter((c) => c.visible).length + 1} align="center">
                  <Typography color="text.secondary" sx={{ py: 4 }}>
                    No ports found
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              ports.map((port) => (
                <TableRow key={port.id} hover>
                  {isColumnVisible('device') && (
                    <TableCell>
                      <Typography
                        variant="body2"
                        sx={{
                          cursor: 'pointer',
                          '&:hover': { textDecoration: 'underline' },
                        }}
                        onClick={() => navigate(`/devices/${port.device_id}`)}
                      >
                        {port.device_name || port.device_serial}
                      </Typography>
                    </TableCell>
                  )}
                  {isColumnVisible('port') && (
                    <TableCell>
                      <Stack direction="row" spacing={1} alignItems="center">
                        {port.fiber ? (
                          <FiberIcon sx={{ fontSize: 16, color: 'info.main' }} />
                        ) : (
                          <CableIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
                        )}
                        <Typography variant="body2">{port.key}</Typography>
                      </Stack>
                    </TableCell>
                  )}
                  {isColumnVisible('type') && (
                    <TableCell>
                      <Chip
                        label={port.fiber ? 'Fiber' : 'Copper'}
                        size="small"
                        color={port.fiber ? 'info' : 'default'}
                        variant="outlined"
                      />
                    </TableCell>
                  )}
                  {isColumnVisible('link') && (
                    <TableCell>
                      <Stack direction="row" spacing={1} alignItems="center">
                        {port.link ? (
                          <LinkIcon sx={{ fontSize: 18, color: 'success.main' }} />
                        ) : (
                          <LinkOffIcon sx={{ fontSize: 18, color: 'text.disabled' }} />
                        )}
                        <Chip
                          label={port.link ? 'Up' : 'Down'}
                          size="small"
                          color={port.link ? 'success' : 'default'}
                        />
                      </Stack>
                    </TableCell>
                  )}
                  {isColumnVisible('speed') && (
                    <TableCell>
                      {port.speed || '-'}
                      {port.fdx && ' FDX'}
                    </TableCell>
                  )}
                  {isColumnVisible('sfp') && (
                    <TableCell>
                      {port.fiber ? (
                        port.present ? (
                          <Tooltip title={`${port.sfp_vendor_name || ''} ${port.sfp_vendor_pn || ''}`}>
                            <Chip
                              label={port.sfp_type || 'Present'}
                              size="small"
                              color={port.loss_of_signal || port.tx_fault ? 'warning' : 'success'}
                              variant="outlined"
                            />
                          </Tooltip>
                        ) : (
                          <Chip label="Not Present" size="small" variant="outlined" />
                        )
                      ) : (
                        '-'
                      )}
                    </TableCell>
                  )}
                  {isColumnVisible('mtu') && <TableCell>{port.mtu}</TableCell>}
                  {isColumnVisible('status') && (
                    <TableCell>
                      {port.shutdown ? (
                        <Chip label="Shutdown" size="small" color="error" />
                      ) : (
                        <Chip label="Enabled" size="small" color="success" variant="outlined" />
                      )}
                    </TableCell>
                  )}
                  <TableCell align="right">
                    <Tooltip title="Configure">
                      <IconButton size="small" onClick={() => handleEdit(port)}>
                        <SettingsIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Edit Dialog */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Configure Port: {selectedPort?.key}</DialogTitle>
        <DialogContent>
          <Stack spacing={3} sx={{ mt: 1 }}>
            <Box>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Device: {selectedPort?.device_name || selectedPort?.device_serial}
              </Typography>
            </Box>

            <FormControlLabel
              control={
                <Switch
                  checked={formData.shutdown}
                  onChange={(e) => setFormData({ ...formData, shutdown: e.target.checked })}
                  color="error"
                />
              }
              label="Admin Shutdown"
            />

            <TextField
              label="MTU"
              type="number"
              value={formData.mtu}
              onChange={(e) => setFormData({ ...formData, mtu: parseInt(e.target.value) || 1500 })}
              fullWidth
              helperText="Maximum Transmission Unit (default: 1500)"
              inputProps={{ min: 64, max: 9216 }}
            />

            {selectedPort?.fiber && selectedPort.present && (
              <Paper variant="outlined" sx={{ p: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  SFP Information
                </Typography>
                <Stack spacing={1}>
                  <Typography variant="body2">
                    Type: {selectedPort.sfp_type || 'Unknown'}
                  </Typography>
                  <Typography variant="body2">
                    Vendor: {selectedPort.sfp_vendor_name || 'Unknown'}
                  </Typography>
                  <Typography variant="body2">
                    Part Number: {selectedPort.sfp_vendor_pn || 'Unknown'}
                  </Typography>
                  <Typography variant="body2">
                    Serial: {selectedPort.sfp_vendor_sn || 'Unknown'}
                  </Typography>
                  {selectedPort.loss_of_signal && (
                    <Chip label="Loss of Signal" color="warning" size="small" />
                  )}
                  {selectedPort.tx_fault && (
                    <Chip label="TX Fault" color="error" size="small" />
                  )}
                </Stack>
              </Paper>
            )}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleSave}
            disabled={updateMutation.isPending}
          >
            {updateMutation.isPending ? 'Saving...' : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
