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
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Checkbox,
  Collapse,
} from '@mui/material'
import {
  Folder as FolderIcon,
  FolderOpen as FolderOpenIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  DeviceHub as DeviceIcon,
  ExpandMore as ExpandMoreIcon,
  ChevronRight as ChevronRightIcon,
} from '@mui/icons-material'
import { groupsApi, devicesApi, exportApi, downloadFile } from '../services/api'
import Breadcrumb from '../components/Breadcrumb'
import ListToolbar from '../components/ListToolbar'

interface GroupFormData {
  name: string
  description: string
  parent_id: string
}

const defaultFormData: GroupFormData = {
  name: '',
  description: '',
  parent_id: '',
}

// All available columns
const allColumns = [
  { id: 'name', label: 'Name', visible: true },
  { id: 'description', label: 'Description', visible: true },
  { id: 'devices', label: 'Devices', visible: true },
  { id: 'subgroups', label: 'Subgroups', visible: true },
]

interface GroupTreeNode {
  id: string
  name: string
  description: string
  parent_id: string | null
  device_count: number
  children: GroupTreeNode[]
}

function TreeNode({
  node,
  level = 0,
  onEdit,
  onDelete,
  onManageDevices,
  isColumnVisible,
}: {
  node: GroupTreeNode
  level?: number
  onEdit: (group: any) => void
  onDelete: (group: any) => void
  onManageDevices: (group: any) => void
  isColumnVisible: (id: string) => boolean
}) {
  const [expanded, setExpanded] = useState(true)
  const hasChildren = node.children && node.children.length > 0

  return (
    <>
      <TableRow hover>
        {isColumnVisible('name') && (
          <TableCell sx={{ pl: 2 + level * 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              {hasChildren ? (
                <IconButton size="small" onClick={() => setExpanded(!expanded)}>
                  {expanded ? <ExpandMoreIcon /> : <ChevronRightIcon />}
                </IconButton>
              ) : (
                <Box sx={{ width: 28 }} />
              )}
              {expanded && hasChildren ? (
                <FolderOpenIcon color="primary" />
              ) : (
                <FolderIcon color="action" />
              )}
              <Typography variant="body2" fontWeight="medium">
                {node.name}
              </Typography>
            </Box>
          </TableCell>
        )}
        {isColumnVisible('description') && (
          <TableCell>
            <Typography variant="body2" color="text.secondary">
              {node.description || '-'}
            </Typography>
          </TableCell>
        )}
        {isColumnVisible('devices') && (
          <TableCell align="center">
            <Typography variant="body2">{node.device_count}</Typography>
          </TableCell>
        )}
        {isColumnVisible('subgroups') && (
          <TableCell align="center">
            <Typography variant="body2">{node.children?.length || 0}</Typography>
          </TableCell>
        )}
        <TableCell>
          <Tooltip title="Manage Devices">
            <IconButton size="small" onClick={() => onManageDevices(node)}>
              <DeviceIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title="Edit">
            <IconButton size="small" onClick={() => onEdit(node)}>
              <EditIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title="Delete">
            <IconButton
              size="small"
              color="error"
              onClick={() => onDelete(node)}
              disabled={node.device_count > 0 || hasChildren}
            >
              <DeleteIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </TableCell>
      </TableRow>
      {hasChildren && (
        <TableRow>
          <TableCell colSpan={5} sx={{ p: 0 }}>
            <Collapse in={expanded}>
              <Table size="small">
                <TableBody>
                  {node.children.map((child) => (
                    <TreeNode
                      key={child.id}
                      node={child}
                      level={level + 1}
                      onEdit={onEdit}
                      onDelete={onDelete}
                      onManageDevices={onManageDevices}
                      isColumnVisible={isColumnVisible}
                    />
                  ))}
                </TableBody>
              </Table>
            </Collapse>
          </TableCell>
        </TableRow>
      )}
    </>
  )
}

export default function Groups() {
  const queryClient = useQueryClient()
  const [columns, setColumns] = useState(allColumns)

  // Dialog state
  const [dialogOpen, setDialogOpen] = useState(false)
  const [dialogMode, setDialogMode] = useState<'create' | 'edit'>('create')
  const [editingGroup, setEditingGroup] = useState<any>(null)
  const [formData, setFormData] = useState<GroupFormData>(defaultFormData)
  const [formError, setFormError] = useState('')

  // Delete confirmation state
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [deletingGroup, setDeletingGroup] = useState<any>(null)

  // Device management dialog
  const [deviceDialogOpen, setDeviceDialogOpen] = useState(false)
  const [managingGroup, setManagingGroup] = useState<any>(null)
  const [selectedDevices, setSelectedDevices] = useState<string[]>([])

  // Fetch group tree
  const { data: treeData, isLoading: treeLoading } = useQuery({
    queryKey: ['groups-tree'],
    queryFn: () => groupsApi.getTree().then((res) => res.data),
  })

  // Fetch flat list for parent selection
  const { data: groupsData } = useQuery({
    queryKey: ['groups-list'],
    queryFn: () => groupsApi.list({ page_size: 100 }).then((res) => res.data),
  })

  // Fetch all devices for assignment
  const { data: devicesData } = useQuery({
    queryKey: ['devices-all'],
    queryFn: () => devicesApi.list({ page_size: 200 }).then((res) => res.data),
  })

  // Fetch devices in managing group
  const { data: groupDevicesData, refetch: refetchGroupDevices } = useQuery({
    queryKey: ['group-devices', managingGroup?.id],
    queryFn: () =>
      managingGroup
        ? groupsApi.getDevices(managingGroup.id).then((res) => res.data)
        : Promise.resolve([]),
    enabled: !!managingGroup,
  })

  // Mutations
  const createMutation = useMutation({
    mutationFn: (data: any) => groupsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['groups-tree'] })
      queryClient.invalidateQueries({ queryKey: ['groups-list'] })
      setDialogOpen(false)
      resetForm()
    },
    onError: (error: any) => {
      setFormError(error.response?.data?.detail || 'Failed to create group')
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) =>
      groupsApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['groups-tree'] })
      queryClient.invalidateQueries({ queryKey: ['groups-list'] })
      setDialogOpen(false)
      resetForm()
    },
    onError: (error: any) => {
      setFormError(error.response?.data?.detail || 'Failed to update group')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => groupsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['groups-tree'] })
      queryClient.invalidateQueries({ queryKey: ['groups-list'] })
      setDeleteDialogOpen(false)
      setDeletingGroup(null)
    },
  })

  const assignDevicesMutation = useMutation({
    mutationFn: ({ groupId, deviceIds }: { groupId: string; deviceIds: string[] }) =>
      groupsApi.assignDevices(groupId, deviceIds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['groups-tree'] })
      queryClient.invalidateQueries({ queryKey: ['group-devices'] })
      queryClient.invalidateQueries({ queryKey: ['devices-all'] })
    },
  })

  const removeDeviceMutation = useMutation({
    mutationFn: ({ groupId, deviceId }: { groupId: string; deviceId: string }) =>
      groupsApi.removeDevice(groupId, deviceId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['groups-tree'] })
      queryClient.invalidateQueries({ queryKey: ['group-devices'] })
      queryClient.invalidateQueries({ queryKey: ['devices-all'] })
      refetchGroupDevices()
    },
  })

  const resetForm = () => {
    setFormData(defaultFormData)
    setFormError('')
    setEditingGroup(null)
  }

  const openCreateDialog = () => {
    resetForm()
    setDialogMode('create')
    setDialogOpen(true)
  }

  const openEditDialog = (group: any) => {
    setEditingGroup(group)
    setFormData({
      name: group.name || '',
      description: group.description || '',
      parent_id: group.parent_id || '',
    })
    setDialogMode('edit')
    setDialogOpen(true)
  }

  const openDeleteDialog = (group: any) => {
    setDeletingGroup(group)
    setDeleteDialogOpen(true)
  }

  const openDeviceDialog = (group: any) => {
    setManagingGroup(group)
    setSelectedDevices([])
    setDeviceDialogOpen(true)
  }

  const handleSubmit = () => {
    if (!formData.name) {
      setFormError('Name is required')
      return
    }

    setFormError('')

    const submitData = {
      name: formData.name,
      description: formData.description,
      parent_id: formData.parent_id || null,
    }

    if (dialogMode === 'create') {
      createMutation.mutate(submitData)
    } else if (editingGroup) {
      updateMutation.mutate({
        id: editingGroup.id,
        data: submitData,
      })
    }
  }

  const handleDelete = () => {
    if (deletingGroup) {
      deleteMutation.mutate(deletingGroup.id)
    }
  }

  const handleAssignDevices = () => {
    if (managingGroup && selectedDevices.length > 0) {
      assignDevicesMutation.mutate({
        groupId: managingGroup.id,
        deviceIds: selectedDevices,
      })
      setSelectedDevices([])
    }
  }

  const handleRemoveDevice = (deviceId: string) => {
    if (managingGroup) {
      removeDeviceMutation.mutate({
        groupId: managingGroup.id,
        deviceId,
      })
    }
  }

  // Get devices not already in this group
  const unassignedDevices =
    devicesData?.items?.filter(
      (d: any) =>
        !d.group_id &&
        (!groupDevicesData || !groupDevicesData.some((gd: any) => gd.id === d.id))
    ) || []

  const isColumnVisible = (columnId: string) =>
    columns.find((c) => c.id === columnId)?.visible ?? false

  const handleExport = async () => {
    try {
      const response = await exportApi.groups()
      const filename = `groups_${new Date().toISOString().slice(0, 10)}.csv`
      downloadFile(response.data, filename)
    } catch (error) {
      console.error('Export failed:', error)
    }
  }

  return (
    <Box>
      <Breadcrumb current="Groups" />

      <ListToolbar
        page={0}
        pageSize={100}
        total={groupsData?.total || 0}
        onPageChange={() => {}}
        onPageSizeChange={() => {}}
        actions={[
          {
            label: 'Export All Data (CSV)',
            onClick: handleExport,
          },
          {
            label: 'Add Group',
            onClick: openCreateDialog,
          },
        ]}
        columns={columns}
        onColumnsChange={setColumns}
      />

      {groupsData && (
        <Box sx={{ mb: 2 }}>
          <Chip label={`Total: ${groupsData.total}`} size="small" />
        </Box>
      )}

      <TableContainer component={Paper}>
        {treeLoading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          <Table size="small">
            <TableHead>
              <TableRow>
                {isColumnVisible('name') && <TableCell>Name</TableCell>}
                {isColumnVisible('description') && <TableCell>Description</TableCell>}
                {isColumnVisible('devices') && <TableCell align="center">Devices</TableCell>}
                {isColumnVisible('subgroups') && <TableCell align="center">Subgroups</TableCell>}
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {treeData?.map((node: GroupTreeNode) => (
                <TreeNode
                  key={node.id}
                  node={node}
                  onEdit={openEditDialog}
                  onDelete={openDeleteDialog}
                  onManageDevices={openDeviceDialog}
                  isColumnVisible={isColumnVisible}
                />
              ))}
              {(!treeData || treeData.length === 0) && (
                <TableRow>
                  <TableCell colSpan={columns.filter((c) => c.visible).length + 1} align="center">
                    No groups found
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
          {dialogMode === 'create' ? 'Add Group' : 'Edit Group'}
        </DialogTitle>
        <DialogContent>
          {formError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {formError}
            </Alert>
          )}
          <Grid container spacing={2} sx={{ pt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                size="small"
                label="Group Name *"
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
                multiline
                rows={2}
              />
            </Grid>
            <Grid item xs={12}>
              <FormControl fullWidth size="small">
                <InputLabel>Parent Group</InputLabel>
                <Select
                  value={formData.parent_id}
                  label="Parent Group"
                  onChange={(e) => setFormData({ ...formData, parent_id: e.target.value })}
                >
                  <MenuItem value="">None (Root Level)</MenuItem>
                  {groupsData?.items
                    ?.filter((g: any) => g.id !== editingGroup?.id)
                    .map((group: any) => (
                      <MenuItem key={group.id} value={group.id}>
                        {group.name}
                      </MenuItem>
                    ))}
                </Select>
              </FormControl>
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
        <DialogTitle>Delete Group</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete group "{deletingGroup?.name}"?
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            This action cannot be undone.
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

      {/* Device Management Dialog */}
      <Dialog
        open={deviceDialogOpen}
        onClose={() => setDeviceDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Manage Devices - {managingGroup?.name}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2}>
            {/* Current devices in group */}
            <Grid item xs={6}>
              <Typography variant="subtitle2" gutterBottom>
                Devices in Group ({groupDevicesData?.length || 0})
              </Typography>
              <Paper variant="outlined" sx={{ maxHeight: 300, overflow: 'auto' }}>
                <List dense>
                  {groupDevicesData?.map((device: any) => (
                    <ListItem key={device.id}>
                      <ListItemText
                        primary={device.name || device.serial_number}
                        secondary={device.serial_number}
                      />
                      <ListItemSecondaryAction>
                        <IconButton
                          edge="end"
                          size="small"
                          color="error"
                          onClick={() => handleRemoveDevice(device.id)}
                          disabled={removeDeviceMutation.isPending}
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </ListItemSecondaryAction>
                    </ListItem>
                  ))}
                  {(!groupDevicesData || groupDevicesData.length === 0) && (
                    <ListItem>
                      <ListItemText
                        secondary="No devices in this group"
                        sx={{ textAlign: 'center' }}
                      />
                    </ListItem>
                  )}
                </List>
              </Paper>
            </Grid>

            {/* Available devices to add */}
            <Grid item xs={6}>
              <Typography variant="subtitle2" gutterBottom>
                Available Devices ({unassignedDevices.length})
              </Typography>
              <Paper variant="outlined" sx={{ maxHeight: 300, overflow: 'auto' }}>
                <List dense>
                  {unassignedDevices.map((device: any) => (
                    <ListItem
                      key={device.id}
                      button
                      onClick={() => {
                        if (selectedDevices.includes(device.id)) {
                          setSelectedDevices(selectedDevices.filter((id) => id !== device.id))
                        } else {
                          setSelectedDevices([...selectedDevices, device.id])
                        }
                      }}
                    >
                      <Checkbox
                        edge="start"
                        checked={selectedDevices.includes(device.id)}
                        size="small"
                      />
                      <ListItemText
                        primary={device.name || device.serial_number}
                        secondary={device.serial_number}
                      />
                    </ListItem>
                  ))}
                  {unassignedDevices.length === 0 && (
                    <ListItem>
                      <ListItemText
                        secondary="No unassigned devices available"
                        sx={{ textAlign: 'center' }}
                      />
                    </ListItem>
                  )}
                </List>
              </Paper>
              {selectedDevices.length > 0 && (
                <Button
                  variant="contained"
                  size="small"
                  sx={{ mt: 1 }}
                  onClick={handleAssignDevices}
                  disabled={assignDevicesMutation.isPending}
                >
                  Add {selectedDevices.length} Device(s) to Group
                </Button>
              )}
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeviceDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
