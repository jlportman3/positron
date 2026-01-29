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
  CircularProgress,
  IconButton,
  Tooltip,
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
  FormControlLabel,
  Switch,
  Alert,
} from '@mui/material'
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  VpnKey as PasswordIcon,
  MoreVert as MoreIcon,
} from '@mui/icons-material'
import Menu from '@mui/material/Menu'
import ListItemIcon from '@mui/material/ListItemIcon'
import ListItemText from '@mui/material/ListItemText'
import { usersApi, exportApi, downloadFile } from '../services/api'
import Breadcrumb from '../components/Breadcrumb'
import ListToolbar from '../components/ListToolbar'

// Privilege levels (0-15)
const privilegeLevels = [
  { level: 0, name: 'Read Only' },
  { level: 1, name: 'Guest' },
  { level: 2, name: 'Level 2' },
  { level: 3, name: 'Level 3' },
  { level: 4, name: 'Level 4' },
  { level: 5, name: 'User' },
  { level: 6, name: 'Level 6' },
  { level: 7, name: 'Level 7' },
  { level: 8, name: 'Level 8' },
  { level: 9, name: 'Level 9' },
  { level: 10, name: 'Operator' },
  { level: 11, name: 'Level 11' },
  { level: 12, name: 'Supervisor' },
  { level: 13, name: 'Level 13' },
  { level: 14, name: 'Admin' },
  { level: 15, name: 'Master' },
]

// All available columns
const allColumns = [
  { id: 'username', label: 'User Name', visible: true },
  { id: 'timeout', label: 'User Inactivity Session Timeout', visible: true },
  { id: 'privilege', label: 'Privilege level', visible: true },
  { id: 'timezone', label: 'Time Zone', visible: true },
  { id: 'enabled', label: 'Enabled', visible: true },
  { id: 'device', label: 'Device', visible: false },
  { id: 'radius', label: 'Radius', visible: false },
]

interface UserFormData {
  username: string
  email: string
  password: string
  privilege_level: number
  enabled: boolean
  session_timeout: number
}

const defaultFormData: UserFormData = {
  username: '',
  email: '',
  password: '',
  privilege_level: 5,
  enabled: true,
  session_timeout: 15,
}

export default function Users() {
  const queryClient = useQueryClient()
  const [page, setPage] = useState(0)
  const [rowsPerPage, setRowsPerPage] = useState(20)
  const [search, setSearch] = useState('')
  const [columns, setColumns] = useState(allColumns)

  // Dialog state
  const [dialogOpen, setDialogOpen] = useState(false)
  const [dialogMode, setDialogMode] = useState<'create' | 'edit'>('create')
  const [editingUser, setEditingUser] = useState<any>(null)
  const [formData, setFormData] = useState<UserFormData>(defaultFormData)
  const [formError, setFormError] = useState('')

  // Delete dialog
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [deletingUser, setDeletingUser] = useState<any>(null)

  // Password change dialog
  const [passwordDialogOpen, setPasswordDialogOpen] = useState(false)
  const [passwordUser, setPasswordUser] = useState<any>(null)
  const [newPassword, setNewPassword] = useState('')
  const [passwordError, setPasswordError] = useState('')

  // Row action menu state
  const [actionAnchor, setActionAnchor] = useState<null | HTMLElement>(null)
  const [selectedUser, setSelectedUser] = useState<any>(null)

  const handleOpenActionMenu = (event: React.MouseEvent<HTMLElement>, user: any) => {
    event.stopPropagation()
    setActionAnchor(event.currentTarget)
    setSelectedUser(user)
  }

  const handleCloseActionMenu = () => {
    setActionAnchor(null)
    setSelectedUser(null)
  }

  const handleMenuEdit = () => {
    if (selectedUser) {
      handleOpenDialog('edit', selectedUser)
    }
    handleCloseActionMenu()
  }

  const handleMenuChangePassword = () => {
    if (selectedUser) {
      setPasswordUser(selectedUser)
      setNewPassword('')
      setPasswordError('')
      setPasswordDialogOpen(true)
    }
    handleCloseActionMenu()
  }

  const handleMenuDelete = () => {
    if (selectedUser) {
      handleDelete(selectedUser)
    }
    handleCloseActionMenu()
  }

  const { data, isLoading } = useQuery({
    queryKey: ['users', page, rowsPerPage, search],
    queryFn: () =>
      usersApi
        .list({
          page: page + 1,
          page_size: rowsPerPage,
          search: search || undefined,
        })
        .then((res) => res.data),
  })

  const createMutation = useMutation({
    mutationFn: (data: UserFormData) => usersApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
      handleCloseDialog()
    },
    onError: (error: any) => {
      const detail = error.response?.data?.detail
      setFormError(typeof detail === 'string' ? detail : Array.isArray(detail) ? detail.map((d: any) => d.msg || JSON.stringify(d)).join(', ') : 'Failed to create user')
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<UserFormData> }) =>
      usersApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
      handleCloseDialog()
    },
    onError: (error: any) => {
      const detail = error.response?.data?.detail
      setFormError(typeof detail === 'string' ? detail : Array.isArray(detail) ? detail.map((d: any) => d.msg || JSON.stringify(d)).join(', ') : 'Failed to update user')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => usersApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
      setDeleteDialogOpen(false)
      setDeletingUser(null)
    },
    onError: (error: any) => {
      const detail = error.response?.data?.detail
      setFormError(typeof detail === 'string' ? detail : Array.isArray(detail) ? detail.map((d: any) => d.msg || JSON.stringify(d)).join(', ') : 'Failed to delete user')
    },
  })

  const changePasswordMutation = useMutation({
    mutationFn: ({ id, password }: { id: string; password: string }) =>
      usersApi.update(id, { password }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
      setPasswordDialogOpen(false)
      setPasswordUser(null)
      setNewPassword('')
    },
    onError: (error: any) => {
      const detail = error.response?.data?.detail
      setPasswordError(typeof detail === 'string' ? detail : Array.isArray(detail) ? detail.map((d: any) => d.msg || JSON.stringify(d)).join(', ') : 'Failed to change password')
    },
  })

  const handleChangePassword = () => {
    if (!newPassword) {
      setPasswordError('Password is required')
      return
    }
    if (newPassword.length < 6) {
      setPasswordError('Password must be at least 6 characters')
      return
    }
    if (passwordUser) {
      changePasswordMutation.mutate({ id: passwordUser.id, password: newPassword })
    }
  }

  const handleOpenDialog = (mode: 'create' | 'edit', user?: any) => {
    setDialogMode(mode)
    setFormError('')
    if (mode === 'edit' && user) {
      setEditingUser(user)
      setFormData({
        username: user.username,
        email: user.email || '',
        password: '',
        privilege_level: user.privilege_level,
        enabled: user.enabled,
        session_timeout: user.session_timeout || 15,
      })
    } else {
      setEditingUser(null)
      setFormData(defaultFormData)
    }
    setDialogOpen(true)
  }

  const handleCloseDialog = () => {
    setDialogOpen(false)
    setEditingUser(null)
    setFormError('')
  }

  const handleSubmit = () => {
    if (!formData.username) {
      setFormError('Username is required')
      return
    }
    if (dialogMode === 'create' && !formData.password) {
      setFormError('Password is required for new users')
      return
    }

    if (dialogMode === 'create') {
      createMutation.mutate({ ...formData, email: formData.email || undefined } as any)
    } else if (editingUser) {
      const updateData: Partial<UserFormData> = {
        username: formData.username,
        email: formData.email || undefined,
        privilege_level: formData.privilege_level,
        enabled: formData.enabled,
        session_timeout: formData.session_timeout,
      }
      if (formData.password) {
        updateData.password = formData.password
      }
      updateMutation.mutate({ id: editingUser.id, data: updateData })
    }
  }

  const handleDelete = (user: any) => {
    setDeletingUser(user)
    setDeleteDialogOpen(true)
  }

  const handleExport = async () => {
    try {
      const response = await exportApi.users()
      const filename = `users_${new Date().toISOString().slice(0, 10)}.csv`
      downloadFile(response.data, filename)
    } catch (error) {
      console.error('Export failed:', error)
    }
  }

  const isColumnVisible = (columnId: string) =>
    columns.find((c) => c.id === columnId)?.visible ?? false

  return (
    <Box>
      <Breadcrumb current="Users" />

      <ListToolbar
        search={search}
        onSearchChange={(value) => {
          setSearch(value)
          setPage(0)
        }}
        searchPlaceholder="Search users..."
        page={page}
        pageSize={rowsPerPage}
        total={data?.total || 0}
        onPageChange={setPage}
        onPageSizeChange={(size) => {
          setRowsPerPage(size)
          setPage(0)
        }}
        pageSizeOptions={[10, 20, 50, 100]}
        actions={[
          {
            label: 'Create New User',
            onClick: () => handleOpenDialog('create'),
          },
          {
            label: 'Export All Data (CSV)',
            onClick: handleExport,
          },
        ]}
        columns={columns}
        onColumnsChange={setColumns}
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
                  {isColumnVisible('username') && (
                    <TableCell>
                      <Tooltip title="Login username"><span>User Name</span></Tooltip>
                    </TableCell>
                  )}
                  {isColumnVisible('timeout') && (
                    <TableCell>
                      <Tooltip title="Minutes before auto-logout (0 = no timeout)"><span>User Inactivity Session Timeout</span></Tooltip>
                    </TableCell>
                  )}
                  {isColumnVisible('privilege') && (
                    <TableCell>
                      <Tooltip title="Access privilege level (1-15, 15 = admin)"><span>Privilege level</span></Tooltip>
                    </TableCell>
                  )}
                  {isColumnVisible('timezone') && (
                    <TableCell>
                      <Tooltip title="User's timezone"><span>Time Zone</span></Tooltip>
                    </TableCell>
                  )}
                  {isColumnVisible('enabled') && (
                    <TableCell>
                      <Tooltip title="Account enabled status"><span>Enabled</span></Tooltip>
                    </TableCell>
                  )}
                  {isColumnVisible('device') && (
                    <TableCell>
                      <Tooltip title="Device access flag"><span>Device</span></Tooltip>
                    </TableCell>
                  )}
                  {isColumnVisible('radius') && (
                    <TableCell>
                      <Tooltip title="RADIUS authentication"><span>Radius</span></Tooltip>
                    </TableCell>
                  )}
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {data?.items?.map((user: any) => (
                  <TableRow key={user.id} hover>
                    {isColumnVisible('username') && (
                      <TableCell sx={{ fontWeight: 500 }}>{user.username}</TableCell>
                    )}
                    {isColumnVisible('timeout') && (
                      <TableCell>{user.session_timeout || 30}</TableCell>
                    )}
                    {isColumnVisible('privilege') && (
                      <TableCell>{user.privilege_level}</TableCell>
                    )}
                    {isColumnVisible('timezone') && (
                      <TableCell>{user.timezone || 'America/Chicago'}</TableCell>
                    )}
                    {isColumnVisible('enabled') && (
                      <TableCell>{user.enabled ? 'Yes' : 'No'}</TableCell>
                    )}
                    {isColumnVisible('device') && (
                      <TableCell>{user.is_device ? 'Yes' : '-'}</TableCell>
                    )}
                    {isColumnVisible('radius') && (
                      <TableCell>{user.is_radius ? 'Yes' : '-'}</TableCell>
                    )}
                    <TableCell>
                      <Tooltip title="Actions">
                        <IconButton size="small" onClick={(e) => handleOpenActionMenu(e, user)}>
                          <MoreIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                ))}
                {data?.items?.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={columns.filter((c) => c.visible).length} align="center">
                      No users found
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>

      {/* Create/Edit Dialog */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>{dialogMode === 'create' ? 'Add User' : 'Edit User'}</DialogTitle>
        <DialogContent>
          {formError && (
            <Alert severity="error" sx={{ mb: 2, mt: 1 }}>
              {formError}
            </Alert>
          )}
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
            <TextField
              label="Username"
              value={formData.username}
              onChange={(e) => setFormData({ ...formData, username: e.target.value })}
              required
              fullWidth
              disabled={dialogMode === 'edit'}
            />
            <TextField
              label="Email"
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              fullWidth
            />
            <TextField
              label={dialogMode === 'create' ? 'Password' : 'New Password (leave blank to keep current)'}
              type="password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              required={dialogMode === 'create'}
              fullWidth
            />
            <FormControl fullWidth>
              <InputLabel>Privilege Level</InputLabel>
              <Select
                value={formData.privilege_level}
                label="Privilege Level"
                onChange={(e) => setFormData({ ...formData, privilege_level: Number(e.target.value) })}
              >
                {privilegeLevels.map((p) => (
                  <MenuItem key={p.level} value={p.level}>
                    {p.level} - {p.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <TextField
              label="Session Timeout (minutes)"
              type="number"
              value={formData.session_timeout}
              onChange={(e) => setFormData({ ...formData, session_timeout: parseInt(e.target.value) || 15 })}
              fullWidth
              inputProps={{ min: 1, max: 1440 }}
            />
            <FormControlLabel
              control={
                <Switch
                  checked={formData.enabled}
                  onChange={(e) => setFormData({ ...formData, enabled: e.target.checked })}
                />
              }
              label="Enabled"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleSubmit}
            disabled={createMutation.isPending || updateMutation.isPending}
          >
            {dialogMode === 'create' ? 'Create' : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Delete User</DialogTitle>
        <DialogContent>
          Are you sure you want to delete user "{deletingUser?.username}"?
          This action cannot be undone.
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button
            color="error"
            variant="contained"
            onClick={() => deletingUser && deleteMutation.mutate(deletingUser.id)}
            disabled={deleteMutation.isPending}
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>

      {/* Change Password Dialog */}
      <Dialog open={passwordDialogOpen} onClose={() => setPasswordDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Change Password</DialogTitle>
        <DialogContent>
          {passwordError && (
            <Alert severity="error" sx={{ mb: 2, mt: 1 }}>
              {passwordError}
            </Alert>
          )}
          <Box sx={{ pt: 1 }}>
            <TextField
              label="New Password"
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              fullWidth
              required
              helperText="Minimum 6 characters"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPasswordDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleChangePassword}
            disabled={changePasswordMutation.isPending}
          >
            Change Password
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
        <MenuItem onClick={handleMenuEdit}>
          <ListItemIcon>
            <EditIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Edit User</ListItemText>
        </MenuItem>
        <MenuItem onClick={handleMenuChangePassword}>
          <ListItemIcon>
            <PasswordIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Change Password</ListItemText>
        </MenuItem>
        <MenuItem onClick={handleMenuDelete} disabled={selectedUser?.username === 'admin'}>
          <ListItemIcon>
            <DeleteIcon fontSize="small" color="error" />
          </ListItemIcon>
          <ListItemText>Delete User</ListItemText>
        </MenuItem>
      </Menu>
    </Box>
  )
}
