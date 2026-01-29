import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
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
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  FormControlLabel,
  Switch,
  Grid,
  TextField,
  Menu,
  ListItemIcon,
  ListItemText,
} from '@mui/material'
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  MoreVert as MoreIcon,
  Visibility as ViewIcon,
  Router as DeviceIcon,
  OpenInNew as PortalIcon,
} from '@mui/icons-material'
import { subscribersApi, devicesApi, bandwidthsApi, endpointsApi, exportApi, downloadFile } from '../services/api'
import Breadcrumb from '../components/Breadcrumb'
import ListToolbar from '../components/ListToolbar'

interface SubscriberFormData {
  device_id: string
  endpoint_mac_address: string
  name: string
  description: string
  bw_profile_id: string
  vlan_id: number
  vlan_is_tagged: boolean
  remapped_vlan_id: number
  port2_vlan_id: number
  port2_vlan_is_tagged: boolean
  trunk_mode: boolean
  port_if_index: number
  double_tags: boolean
  nni_if_index: number
  outer_tag_vlan_id: number
  poe_mode_ctrl: string
}

const defaultFormData: SubscriberFormData = {
  device_id: '',
  endpoint_mac_address: '',
  name: '',
  description: '',
  bw_profile_id: '',
  vlan_id: 0,
  vlan_is_tagged: false,
  remapped_vlan_id: 0,
  port2_vlan_id: 0,
  port2_vlan_is_tagged: false,
  trunk_mode: false,
  port_if_index: 0,
  double_tags: false,
  nni_if_index: 0,
  outer_tag_vlan_id: 0,
  poe_mode_ctrl: '',
}

// All available columns
const allColumns = [
  { id: 'name', label: 'Name', visible: true },
  { id: 'description', label: 'Description', visible: true },
  { id: 'endpoint', label: 'Endpoint', visible: true },
  { id: 'bandwidth', label: 'Bandwidth', visible: true },
  { id: 'vlanPort1', label: 'VLAN Id Port #1', visible: true },
  { id: 'vlanPort2', label: 'VLAN Id Port #2', visible: true },
  { id: 'systemName', label: 'System Name', visible: true },
  { id: 'gamIp', label: 'GAM IP Address', visible: false },
  { id: 'groups', label: 'Groups', visible: false },
]

export default function Subscribers() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [page, setPage] = useState(0)
  const [rowsPerPage, setRowsPerPage] = useState(20)
  const [search, setSearch] = useState('')
  const [deviceFilter, setDeviceFilter] = useState<string>('')
  const [columns, setColumns] = useState(allColumns)

  // Dialog state
  const [dialogOpen, setDialogOpen] = useState(false)
  const [dialogMode, setDialogMode] = useState<'create' | 'edit'>('create')
  const [editingSubscriber, setEditingSubscriber] = useState<any>(null)
  const [formData, setFormData] = useState<SubscriberFormData>(defaultFormData)
  const [formError, setFormError] = useState('')

  // Delete confirmation state
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [deletingSubscriber, setDeletingSubscriber] = useState<any>(null)

  // Row action menu state
  const [actionAnchor, setActionAnchor] = useState<null | HTMLElement>(null)
  const [selectedSubscriber, setSelectedSubscriber] = useState<any>(null)

  const handleOpenActionMenu = (event: React.MouseEvent<HTMLElement>, subscriber: any) => {
    event.stopPropagation()
    setActionAnchor(event.currentTarget)
    setSelectedSubscriber(subscriber)
  }

  const handleCloseActionMenu = () => {
    setActionAnchor(null)
    setSelectedSubscriber(null)
  }

  const handleViewSubscriberDetails = () => {
    if (selectedSubscriber) {
      navigate(`/subscribers/${selectedSubscriber.id}`)
    }
    handleCloseActionMenu()
  }

  const handleViewGamDetails = () => {
    if (selectedSubscriber) {
      navigate(`/devices/${selectedSubscriber.device_id}`)
    }
    handleCloseActionMenu()
  }

  const handleOpenGamPortal = () => {
    if (selectedSubscriber?.device_id) {
      const device = devicesData?.items?.find((d: any) => d.id === selectedSubscriber.device_id)
      if (device?.ip_address) {
        window.open(`https://${device.ip_address}`, '_blank')
      }
    }
    handleCloseActionMenu()
  }

  const handleMenuEdit = () => {
    if (selectedSubscriber) {
      openEditDialog(selectedSubscriber)
    }
    handleCloseActionMenu()
  }

  const handleMenuDelete = () => {
    if (selectedSubscriber) {
      openDeleteDialog(selectedSubscriber)
    }
    handleCloseActionMenu()
  }

  // Fetch devices for filter dropdown
  const { data: devicesData } = useQuery({
    queryKey: ['devices-list'],
    queryFn: () => devicesApi.list({ page_size: 100 }).then((res) => res.data),
  })

  // Fetch bandwidths for form dropdown
  const { data: bandwidthsData } = useQuery({
    queryKey: ['bandwidths-list', formData.device_id],
    queryFn: () =>
      bandwidthsApi
        .list({ device_id: formData.device_id || undefined, page_size: 100 })
        .then((res) => res.data),
    enabled: !!formData.device_id,
  })

  // Fetch endpoints for form dropdown (unprovisioned endpoints only)
  const { data: endpointsData } = useQuery({
    queryKey: ['endpoints-unprovisioned', formData.device_id],
    queryFn: () =>
      endpointsApi
        .list({ device_id: formData.device_id || undefined, page_size: 100 })
        .then((res) => res.data),
    enabled: !!formData.device_id,
  })

  // Create device lookup map
  const deviceMap = new Map<string, string>()
  devicesData?.items?.forEach((d: any) => {
    deviceMap.set(d.id, d.name || d.serial_number)
  })

  const { data, isLoading } = useQuery({
    queryKey: ['subscribers', page, rowsPerPage, search, deviceFilter],
    queryFn: () =>
      subscribersApi
        .list({
          page: page + 1,
          page_size: rowsPerPage,
          search: search || undefined,
          device_id: deviceFilter || undefined,
        })
        .then((res) => res.data),
  })

  // Mutations
  const createMutation = useMutation({
    mutationFn: (data: any) => subscribersApi.createOnDevice(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subscribers'] })
      setDialogOpen(false)
      resetForm()
    },
    onError: (error: any) => {
      setFormError(error.response?.data?.detail || 'Failed to create subscriber')
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) =>
      subscribersApi.updateOnDevice(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subscribers'] })
      setDialogOpen(false)
      resetForm()
    },
    onError: (error: any) => {
      setFormError(error.response?.data?.detail || 'Failed to update subscriber')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => subscribersApi.deleteFromDevice(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subscribers'] })
      setDeleteDialogOpen(false)
      setDeletingSubscriber(null)
    },
  })

  const resetForm = () => {
    setFormData(defaultFormData)
    setFormError('')
    setEditingSubscriber(null)
  }

  const openCreateDialog = () => {
    resetForm()
    setDialogMode('create')
    setDialogOpen(true)
  }

  const openEditDialog = (subscriber: any) => {
    setEditingSubscriber(subscriber)
    setFormData({
      device_id: subscriber.device_id,
      endpoint_mac_address: subscriber.endpoint_mac_address || '',
      name: subscriber.name || '',
      description: subscriber.description || '',
      bw_profile_id: subscriber.bw_profile_id || '',
      vlan_id: subscriber.port1_vlan_id || 0,
      vlan_is_tagged: subscriber.vlan_is_tagged || false,
      remapped_vlan_id: subscriber.remapped_vlan_id || 0,
      port2_vlan_id: subscriber.port2_vlan_id || 0,
      port2_vlan_is_tagged: subscriber.vlan_is_tagged2 || false,
      trunk_mode: subscriber.trunk_mode || false,
      port_if_index: subscriber.port_if_index || 0,
      double_tags: subscriber.double_tags || false,
      nni_if_index: subscriber.nni_if_index || 0,
      outer_tag_vlan_id: 0,
      poe_mode_ctrl: subscriber.poe_mode_ctrl || '',
    })
    setDialogMode('edit')
    setDialogOpen(true)
  }

  const openDeleteDialog = (subscriber: any) => {
    setDeletingSubscriber(subscriber)
    setDeleteDialogOpen(true)
  }

  const handleSubmit = () => {
    if (!formData.name) {
      setFormError('Name is required')
      return
    }
    if (dialogMode === 'create' && !formData.device_id) {
      setFormError('Device is required')
      return
    }
    if (dialogMode === 'create' && !formData.endpoint_mac_address) {
      setFormError('Endpoint is required')
      return
    }

    setFormError('')

    if (dialogMode === 'create') {
      createMutation.mutate(formData)
    } else if (editingSubscriber) {
      updateMutation.mutate({
        id: editingSubscriber.id,
        data: formData,
      })
    }
  }

  const handleDelete = () => {
    if (deletingSubscriber) {
      deleteMutation.mutate(deletingSubscriber.id)
    }
  }

  const handleExport = async () => {
    try {
      const response = await exportApi.subscribers(deviceFilter || undefined)
      const filename = `subscribers_${new Date().toISOString().slice(0, 10)}.csv`
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
      <Breadcrumb current="Subscribers" />

      <ListToolbar
        search={search}
        onSearchChange={(value) => {
          setSearch(value)
          setPage(0)
        }}
        searchPlaceholder="Search subscribers..."
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
        pageSizeOptions={[20, 50, 100, 500]}
        actions={[
          {
            label: 'Export to CSV',
            onClick: handleExport,
          },
          {
            label: 'Add Subscriber',
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
                    <Tooltip title="Subscriber account identifier"><span>Name</span></Tooltip>
                  </TableCell>
                )}
                {isColumnVisible('description') && (
                  <TableCell>
                    <Tooltip title="Human-readable subscriber name"><span>Description</span></Tooltip>
                  </TableCell>
                )}
                {isColumnVisible('endpoint') && (
                  <TableCell>
                    <Tooltip title="MAC address of assigned CPE endpoint"><span>Endpoint</span></Tooltip>
                  </TableCell>
                )}
                {isColumnVisible('bandwidth') && (
                  <TableCell>
                    <Tooltip title="Assigned bandwidth profile"><span>Bandwidth</span></Tooltip>
                  </TableCell>
                )}
                {isColumnVisible('vlanPort1') && (
                  <TableCell>
                    <Tooltip title="VLAN ID for Ethernet port 1"><span>VLAN Id Port #1</span></Tooltip>
                  </TableCell>
                )}
                {isColumnVisible('vlanPort2') && (
                  <TableCell>
                    <Tooltip title="VLAN ID for Ethernet port 2"><span>VLAN Id Port #2</span></Tooltip>
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
                {isColumnVisible('groups') && (
                  <TableCell>
                    <Tooltip title="Device group assignment"><span>Groups</span></Tooltip>
                  </TableCell>
                )}
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {data?.items.map((sub: any) => {
                const device = devicesData?.items?.find((d: any) => d.id === sub.device_id)
                return (
                  <TableRow
                    key={sub.id}
                    hover
                    sx={{ cursor: 'pointer' }}
                    onClick={() => navigate(`/subscribers/${sub.id}`)}
                  >
                    {isColumnVisible('name') && (
                      <TableCell>
                        <Typography variant="body2" fontWeight="medium">
                          {sub.name}
                        </Typography>
                      </TableCell>
                    )}
                    {isColumnVisible('description') && (
                      <TableCell>
                        <Typography variant="body2" color="text.secondary">
                          {sub.description || '-'}
                        </Typography>
                      </TableCell>
                    )}
                    {isColumnVisible('endpoint') && (
                      <TableCell>
                        <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                          {sub.endpoint_mac_address || '-'}
                        </Typography>
                      </TableCell>
                    )}
                    {isColumnVisible('bandwidth') && (
                      <TableCell>
                        {sub.bw_profile_name || (sub.bw_profile_id === 0 ? 'Default BW Profile' : '-')}
                      </TableCell>
                    )}
                    {isColumnVisible('vlanPort1') && (
                      <TableCell>
                        {sub.port1_vlan_id || '-'}
                        {sub.vlan_is_tagged && ' (T)'}
                      </TableCell>
                    )}
                    {isColumnVisible('vlanPort2') && (
                      <TableCell>
                        {sub.port2_vlan_id || '-'}
                        {sub.vlan_is_tagged2 && ' (T)'}
                      </TableCell>
                    )}
                    {isColumnVisible('systemName') && (
                      <TableCell>
                        {device?.name || device?.serial_number || '-'}
                      </TableCell>
                    )}
                    {isColumnVisible('gamIp') && (
                      <TableCell>
                        <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                          {device?.ip_address || '-'}
                        </Typography>
                      </TableCell>
                    )}
                    {isColumnVisible('groups') && (
                      <TableCell>
                        <Typography variant="body2" color="text.secondary">
                          {sub.group_name || device?.group_name || '-'}
                        </Typography>
                      </TableCell>
                    )}
                    <TableCell onClick={(e) => e.stopPropagation()}>
                      <Tooltip title="Actions">
                        <IconButton size="small" onClick={(e) => handleOpenActionMenu(e, sub)}>
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
                    No subscribers found
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        )}
      </TableContainer>

      {/* Create/Edit Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          {dialogMode === 'create' ? 'Add Subscriber' : 'Edit Subscriber'}
        </DialogTitle>
        <DialogContent>
          {formError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {formError}
            </Alert>
          )}
          <Grid container spacing={2} sx={{ pt: 1 }}>
            {dialogMode === 'create' && (
              <>
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Device *</InputLabel>
                    <Select
                      value={formData.device_id}
                      label="Device *"
                      onChange={(e) =>
                        setFormData({ ...formData, device_id: e.target.value, endpoint_mac_address: '' })
                      }
                    >
                      {devicesData?.items?.map((device: any) => (
                        <MenuItem key={device.id} value={device.id}>
                          {device.name || device.serial_number}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth size="small" disabled={!formData.device_id}>
                    <InputLabel>Endpoint *</InputLabel>
                    <Select
                      value={formData.endpoint_mac_address}
                      label="Endpoint *"
                      onChange={(e) =>
                        setFormData({ ...formData, endpoint_mac_address: e.target.value })
                      }
                    >
                      {endpointsData?.items
                        ?.filter((ep: any) => ep.alive)
                        .map((endpoint: any) => (
                          <MenuItem key={endpoint.mac_address} value={endpoint.mac_address}>
                            {endpoint.mac_address} - {endpoint.conf_endpoint_name || 'Unprovisioned'}
                          </MenuItem>
                        ))}
                    </Select>
                  </FormControl>
                </Grid>
              </>
            )}
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                size="small"
                label="Subscriber Name *"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                size="small"
                label="Description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth size="small">
                <InputLabel>Bandwidth Profile</InputLabel>
                <Select
                  value={formData.bw_profile_id}
                  label="Bandwidth Profile"
                  onChange={(e) => setFormData({ ...formData, bw_profile_id: e.target.value })}
                >
                  <MenuItem value="">None</MenuItem>
                  {bandwidthsData?.items?.map((bw: any) => (
                    <MenuItem key={bw.id} value={bw.id}>
                      {bw.name} ({bw.ds_bw}/{bw.us_bw} Mbps)
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth size="small">
                <InputLabel>PoE Mode</InputLabel>
                <Select
                  value={formData.poe_mode_ctrl}
                  label="PoE Mode"
                  onChange={(e) => setFormData({ ...formData, poe_mode_ctrl: e.target.value })}
                >
                  <MenuItem value="">Auto</MenuItem>
                  <MenuItem value="on">On</MenuItem>
                  <MenuItem value="off">Off</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <Typography variant="subtitle2" gutterBottom sx={{ mt: 1 }}>
                VLAN Configuration
              </Typography>
            </Grid>
            <Grid item xs={6} md={3}>
              <TextField
                fullWidth
                size="small"
                type="number"
                label="Port 1 VLAN"
                value={formData.vlan_id}
                onChange={(e) =>
                  setFormData({ ...formData, vlan_id: parseInt(e.target.value) || 0 })
                }
              />
            </Grid>
            <Grid item xs={6} md={3}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.vlan_is_tagged}
                    onChange={(e) =>
                      setFormData({ ...formData, vlan_is_tagged: e.target.checked })
                    }
                  />
                }
                label="Tagged"
              />
            </Grid>
            <Grid item xs={6} md={3}>
              <TextField
                fullWidth
                size="small"
                type="number"
                label="Port 2 VLAN"
                value={formData.port2_vlan_id}
                onChange={(e) =>
                  setFormData({ ...formData, port2_vlan_id: parseInt(e.target.value) || 0 })
                }
              />
            </Grid>
            <Grid item xs={6} md={3}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.port2_vlan_is_tagged}
                    onChange={(e) =>
                      setFormData({ ...formData, port2_vlan_is_tagged: e.target.checked })
                    }
                  />
                }
                label="Tagged"
              />
            </Grid>
            <Grid item xs={6} md={3}>
              <TextField
                fullWidth
                size="small"
                type="number"
                label="Remapped VLAN"
                value={formData.remapped_vlan_id}
                onChange={(e) =>
                  setFormData({ ...formData, remapped_vlan_id: parseInt(e.target.value) || 0 })
                }
              />
            </Grid>
            <Grid item xs={6} md={3}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.trunk_mode}
                    onChange={(e) => setFormData({ ...formData, trunk_mode: e.target.checked })}
                  />
                }
                label="Trunk Mode"
              />
            </Grid>
            <Grid item xs={6} md={3}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.double_tags}
                    onChange={(e) => setFormData({ ...formData, double_tags: e.target.checked })}
                  />
                }
                label="Double Tags"
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
        <DialogTitle>Delete Subscriber</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete subscriber "{deletingSubscriber?.name}"?
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            This will remove the subscriber from the device and save the configuration.
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

      {/* Row Action Menu */}
      <Menu
        anchorEl={actionAnchor}
        open={Boolean(actionAnchor)}
        onClose={handleCloseActionMenu}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        transformOrigin={{ vertical: 'top', horizontal: 'right' }}
      >
        <MenuItem onClick={handleViewSubscriberDetails}>
          <ListItemIcon>
            <ViewIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>View Subscriber Details</ListItemText>
        </MenuItem>
        <MenuItem onClick={handleMenuEdit} disabled={!selectedSubscriber?.json_id}>
          <ListItemIcon>
            <EditIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Edit Subscriber</ListItemText>
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
        <MenuItem onClick={handleMenuDelete} disabled={!selectedSubscriber?.json_id}>
          <ListItemIcon>
            <DeleteIcon fontSize="small" color="error" />
          </ListItemIcon>
          <ListItemText>Delete Subscriber</ListItemText>
        </MenuItem>
      </Menu>
    </Box>
  )
}
