import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
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
  Button,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  Grid,
} from '@mui/material'
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Sync as SyncIcon,
} from '@mui/icons-material'
import { bandwidthsApi, devicesApi, exportApi, downloadFile } from '../services/api'
import Breadcrumb from '../components/Breadcrumb'
import ListToolbar from '../components/ListToolbar'


interface BandwidthFormData {
  device_id: string
  name: string
  description: string
  ds_bw: number
  us_bw: number
}

const defaultFormData: BandwidthFormData = {
  device_id: '',
  name: '',
  description: '',
  ds_bw: 100,
  us_bw: 100,
}

// All available columns
const allColumns = [
  { id: 'name', label: 'Name', visible: true },
  { id: 'downstream', label: 'Downstream (Mbps)', visible: true },
  { id: 'upstream', label: 'Upstream (Mbps)', visible: true },
  { id: 'description', label: 'Description', visible: true },
  { id: 'systems', label: 'Systems', visible: true },
  { id: 'synchronized', label: 'Synchronized', visible: false },
]

export default function Bandwidths() {
  const queryClient = useQueryClient()
  const [page, setPage] = useState(0)
  const [rowsPerPage, setRowsPerPage] = useState(50)
  const [deviceFilter, setDeviceFilter] = useState<string>('')
  const [columns, setColumns] = useState(allColumns)

  // Dialog state
  const [dialogOpen, setDialogOpen] = useState(false)
  const [dialogMode, setDialogMode] = useState<'create' | 'edit'>('create')
  const [editingBandwidth, setEditingBandwidth] = useState<any>(null)
  const [formData, setFormData] = useState<BandwidthFormData>(defaultFormData)
  const [formError, setFormError] = useState('')

  // Delete confirmation state
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [deletingBandwidth, setDeletingBandwidth] = useState<any>(null)

  // Fetch devices for filter dropdown
  const { data: devicesData } = useQuery({
    queryKey: ['devices-list'],
    queryFn: () => devicesApi.list({ page_size: 100 }).then((res) => res.data),
  })

  // Create device lookup map
  const deviceMap = new Map<string, string>()
  devicesData?.items?.forEach((d: any) => {
    deviceMap.set(d.id, d.name || d.serial_number)
  })

  const { data, isLoading } = useQuery({
    queryKey: ['bandwidths', page, rowsPerPage, deviceFilter],
    queryFn: () =>
      bandwidthsApi
        .list({
          page: page + 1,
          page_size: rowsPerPage,
          device_id: deviceFilter || undefined,
        })
        .then((res) => res.data),
  })

  // Mutations
  const createMutation = useMutation({
    mutationFn: (data: any) => bandwidthsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bandwidths'] })
      setDialogOpen(false)
      resetForm()
    },
    onError: (error: any) => {
      setFormError(error.response?.data?.detail || 'Failed to create bandwidth profile')
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) =>
      bandwidthsApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bandwidths'] })
      setDialogOpen(false)
      resetForm()
    },
    onError: (error: any) => {
      setFormError(error.response?.data?.detail || 'Failed to update bandwidth profile')
    },
  })

  const pushMutation = useMutation({
    mutationFn: (id: string) => bandwidthsApi.pushToDevice(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bandwidths'] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => bandwidthsApi.deleteFromDevice(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bandwidths'] })
      setDeleteDialogOpen(false)
      setDeletingBandwidth(null)
    },
  })

  const resetForm = () => {
    setFormData(defaultFormData)
    setFormError('')
    setEditingBandwidth(null)
  }

  const openCreateDialog = () => {
    resetForm()
    setDialogMode('create')
    setDialogOpen(true)
  }

  const openEditDialog = (bandwidth: any) => {
    setEditingBandwidth(bandwidth)
    setFormData({
      device_id: bandwidth.device_id,
      name: bandwidth.name || '',
      description: bandwidth.description || '',
      ds_bw: bandwidth.ds_bw || 100,
      us_bw: bandwidth.us_bw || 100,
    })
    setDialogMode('edit')
    setDialogOpen(true)
  }

  const openDeleteDialog = (bandwidth: any) => {
    setDeletingBandwidth(bandwidth)
    setDeleteDialogOpen(true)
  }

  const handleSubmit = () => {
    if (!formData.name) {
      setFormError('Name is required')
      return
    }
    setFormError('')

    if (dialogMode === 'create') {
      const deviceId = formData.device_id || devicesData?.items?.[0]?.id
      if (!deviceId) {
        setFormError('No devices available')
        return
      }
      createMutation.mutate({ ...formData, device_id: deviceId })
    } else if (editingBandwidth) {
      updateMutation.mutate({
        id: editingBandwidth.id,
        data: {
          name: formData.name,
          description: formData.description,
          ds_bw: formData.ds_bw,
          us_bw: formData.us_bw,
        },
      })
    }
  }

  const handleDelete = () => {
    if (deletingBandwidth) {
      deleteMutation.mutate(deletingBandwidth.id)
    }
  }

  const handleExport = async () => {
    try {
      const response = await exportApi.bandwidths(deviceFilter || undefined)
      const filename = `bandwidths_${new Date().toISOString().slice(0, 10)}.csv`
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

  return (
    <Box>
      <Breadcrumb current="Bandwidths" />

      <ListToolbar
        filters={[
          {
            value: deviceFilter,
            onChange: (value) => {
              setDeviceFilter(value)
              setPage(0)
            },
            options: deviceFilterOptions,
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
          {
            label: 'Add Profile',
            onClick: openCreateDialog,
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
                {isColumnVisible('name') && (
                  <TableCell>
                    <Tooltip title="Bandwidth profile name"><span>Name</span></Tooltip>
                  </TableCell>
                )}
                {isColumnVisible('downstream') && (
                  <TableCell align="right">
                    <Tooltip title="Download speed in Mbps"><span>Downstream (Mbps)</span></Tooltip>
                  </TableCell>
                )}
                {isColumnVisible('upstream') && (
                  <TableCell align="right">
                    <Tooltip title="Upload speed in Mbps"><span>Upstream (Mbps)</span></Tooltip>
                  </TableCell>
                )}
                {isColumnVisible('description') && (
                  <TableCell>
                    <Tooltip title="Profile description"><span>Description</span></Tooltip>
                  </TableCell>
                )}
                {isColumnVisible('systems') && (
                  <TableCell align="right">
                    <Tooltip title="Number of GAM devices using this profile"><span>Systems</span></Tooltip>
                  </TableCell>
                )}
                {isColumnVisible('synchronized') && (
                  <TableCell align="center">
                    <Tooltip title="Profile sync status with devices"><span>Synchronized</span></Tooltip>
                  </TableCell>
                )}
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {data?.items.map((bw: any) => (
                <TableRow
                  key={bw.id}
                  hover
                  sx={{
                    opacity: bw.deleted ? 0.5 : 1,
                    textDecoration: bw.deleted ? 'line-through' : 'none',
                  }}
                >
                  {isColumnVisible('name') && (
                    <TableCell>
                      <Typography variant="body2" fontWeight="medium">
                        {bw.name}
                      </Typography>
                    </TableCell>
                  )}
                  {isColumnVisible('downstream') && (
                    <TableCell align="right">
                      <Typography variant="body2">
                        {bw.ds_bw || '-'}
                      </Typography>
                    </TableCell>
                  )}
                  {isColumnVisible('upstream') && (
                    <TableCell align="right">
                      <Typography variant="body2">
                        {bw.us_bw || '-'}
                      </Typography>
                    </TableCell>
                  )}
                  {isColumnVisible('description') && (
                    <TableCell>
                      <Typography variant="body2" color="text.secondary">
                        {bw.description || '-'}
                      </Typography>
                    </TableCell>
                  )}
                  {isColumnVisible('systems') && (
                    <TableCell align="right">
                      <Typography variant="body2">
                        {bw.system_count || 1}
                      </Typography>
                    </TableCell>
                  )}
                  {isColumnVisible('synchronized') && (
                    <TableCell align="center">
                      {bw.deleted ? (
                        <Typography variant="body2" color="error">No</Typography>
                      ) : bw.sync ? (
                        <Typography variant="body2" color="success.main">Yes</Typography>
                      ) : bw.sync_error ? (
                        <Tooltip title={bw.sync_error}>
                          <Typography variant="body2" color="error">No</Typography>
                        </Tooltip>
                      ) : (
                        <Typography variant="body2" color="warning.main">Pending</Typography>
                      )}
                    </TableCell>
                  )}
                  <TableCell>
                    {!bw.deleted && (
                      <>
                        <Tooltip title="Push to Device">
                          <IconButton
                            size="small"
                            color="primary"
                            onClick={() => pushMutation.mutate(bw.id)}
                            disabled={pushMutation.isPending}
                          >
                            <SyncIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Edit">
                          <IconButton size="small" onClick={() => openEditDialog(bw)}>
                            <EditIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Delete">
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => openDeleteDialog(bw)}
                            disabled={bw.name === 'Default' || bw.is_default}
                          >
                            <DeleteIcon fontSize="small" />
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
                    No bandwidth profiles found
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        )}
      </TableContainer>

      {/* Create/Edit Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {dialogMode === 'create' ? 'Add Bandwidth Profile' : 'Edit Bandwidth Profile'}
        </DialogTitle>
        <DialogContent>
          {formError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {formError}
            </Alert>
          )}
          <Grid container spacing={2} sx={{ pt: 1 }}>
            {dialogMode === 'create' && (
              <Grid item xs={12}>
                <Alert severity="info" sx={{ py: 0 }}>
                  New bandwidth profiles are automatically pushed to all GAM devices.
                </Alert>
              </Grid>
            )}
            <Grid item xs={12}>
              <TextField
                fullWidth
                size="small"
                label="Profile Name *"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                size="small"
                label="Description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              />
            </Grid>
            <Grid item xs={6}>
              <TextField
                fullWidth
                size="small"
                type="number"
                label="Downstream (Mbps)"
                value={formData.ds_bw}
                onChange={(e) =>
                  setFormData({ ...formData, ds_bw: parseInt(e.target.value) || 0 })
                }
                InputProps={{
                  endAdornment: <Typography variant="caption">Mbps</Typography>,
                }}
              />
            </Grid>
            <Grid item xs={6}>
              <TextField
                fullWidth
                size="small"
                type="number"
                label="Upstream (Mbps)"
                value={formData.us_bw}
                onChange={(e) =>
                  setFormData({ ...formData, us_bw: parseInt(e.target.value) || 0 })
                }
                InputProps={{
                  endAdornment: <Typography variant="caption">Mbps</Typography>,
                }}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleSubmit}
            disabled={createMutation.isPending || updateMutation.isPending}
          >
            {createMutation.isPending || updateMutation.isPending
              ? 'Saving...'
              : dialogMode === 'create'
              ? 'Create'
              : 'Update'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Delete Bandwidth Profile</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete bandwidth profile "{deletingBandwidth?.name}"?
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            This will remove the profile from the device and save the configuration.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            color="error"
            onClick={handleDelete}
            disabled={deleteMutation.isPending}
          >
            {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
