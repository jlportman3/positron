import { useState } from 'react'
import {
  Box,
  Paper,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Switch,
  FormControlLabel,
  Chip,
  Stack,
  Card,
  CardContent,
  Grid,
  Tabs,
  Tab,
  FormGroup,
  Checkbox,
  Alert,
  Tooltip,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  CircularProgress,
} from '@mui/material'
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Send as SendIcon,
  Email as EmailIcon,
  Webhook as WebhookIcon,
  Notifications as NotificationsIcon,
  History as HistoryIcon,
} from '@mui/icons-material'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { notificationsApi } from '../services/api'
import Breadcrumb from '../components/Breadcrumb'

interface NotificationSubscription {
  id: string
  user_id: string
  name: string
  enabled: boolean
  severities: string
  device_ids: string | null
  group_ids: string | null
  notify_email: boolean
  notify_webhook: boolean
  webhook_url: string | null
  min_interval_minutes: number
  last_notification_at: string | null
  created_at: string
  updated_at: string
}

interface NotificationLog {
  id: string
  subscription_id: string
  alarm_id: string | null
  channel: string
  recipient: string
  subject: string | null
  status: string
  error_message: string | null
  sent_at: string | null
  created_at: string
}

interface NotificationStats {
  total_subscriptions: number
  enabled_subscriptions: number
  total_sent_today: number
  total_sent_week: number
  failed_today: number
}

const SEVERITY_OPTIONS = [
  { value: 'CR', label: 'Critical', color: 'error' as const },
  { value: 'MJ', label: 'Major', color: 'warning' as const },
  { value: 'MN', label: 'Minor', color: 'info' as const },
  { value: 'NA', label: 'Normal', color: 'success' as const },
]

export default function Notifications() {
  const [tabIndex, setTabIndex] = useState(0)
  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [testDialogOpen, setTestDialogOpen] = useState(false)
  const [selectedSubscription, setSelectedSubscription] = useState<NotificationSubscription | null>(null)
  const [formData, setFormData] = useState({
    name: '',
    enabled: true,
    severities: ['CR', 'MJ'],
    notify_email: true,
    notify_webhook: false,
    webhook_url: '',
    min_interval_minutes: 5,
  })
  const [testChannel, setTestChannel] = useState('email')
  const [testRecipient, setTestRecipient] = useState('')

  const queryClient = useQueryClient()

  // Queries
  const { data: subscriptions = [], isLoading: subscriptionsLoading } = useQuery<NotificationSubscription[]>({
    queryKey: ['notifications'],
    queryFn: async () => {
      const response = await notificationsApi.list()
      return response.data
    },
  })

  const { data: stats } = useQuery<NotificationStats>({
    queryKey: ['notification-stats'],
    queryFn: async () => {
      const response = await notificationsApi.getStats()
      return response.data
    },
  })

  const { data: logs = [] } = useQuery<NotificationLog[]>({
    queryKey: ['notification-logs'],
    queryFn: async () => {
      const response = await notificationsApi.getLogs({ page_size: 100 })
      return response.data
    },
  })

  // Mutations
  const createMutation = useMutation({
    mutationFn: (data: any) => notificationsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
      queryClient.invalidateQueries({ queryKey: ['notification-stats'] })
      setEditDialogOpen(false)
      resetForm()
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) =>
      notificationsApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
      queryClient.invalidateQueries({ queryKey: ['notification-stats'] })
      setEditDialogOpen(false)
      resetForm()
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => notificationsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
      queryClient.invalidateQueries({ queryKey: ['notification-stats'] })
    },
  })

  const testMutation = useMutation({
    mutationFn: ({ id, channel, recipient }: { id: string; channel: string; recipient?: string }) =>
      notificationsApi.test(id, { channel, recipient }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notification-logs'] })
      setTestDialogOpen(false)
    },
  })

  const resetForm = () => {
    setFormData({
      name: '',
      enabled: true,
      severities: ['CR', 'MJ'],
      notify_email: true,
      notify_webhook: false,
      webhook_url: '',
      min_interval_minutes: 5,
    })
    setSelectedSubscription(null)
  }

  const handleEdit = (subscription: NotificationSubscription) => {
    setSelectedSubscription(subscription)
    setFormData({
      name: subscription.name,
      enabled: subscription.enabled,
      severities: subscription.severities.split(',').filter(Boolean),
      notify_email: subscription.notify_email,
      notify_webhook: subscription.notify_webhook,
      webhook_url: subscription.webhook_url || '',
      min_interval_minutes: subscription.min_interval_minutes,
    })
    setEditDialogOpen(true)
  }

  const handleCreate = () => {
    resetForm()
    setEditDialogOpen(true)
  }

  const handleSave = () => {
    const data = {
      ...formData,
      severities: formData.severities.join(','),
    }
    if (selectedSubscription) {
      updateMutation.mutate({ id: selectedSubscription.id, data })
    } else {
      createMutation.mutate(data)
    }
  }

  const handleDelete = (id: string) => {
    if (confirm('Are you sure you want to delete this subscription?')) {
      deleteMutation.mutate(id)
    }
  }

  const handleTest = (subscription: NotificationSubscription) => {
    setSelectedSubscription(subscription)
    setTestChannel(subscription.notify_email ? 'email' : 'webhook')
    setTestRecipient('')
    setTestDialogOpen(true)
  }

  const handleSendTest = () => {
    if (selectedSubscription) {
      testMutation.mutate({
        id: selectedSubscription.id,
        channel: testChannel,
        recipient: testRecipient || undefined,
      })
    }
  }

  const handleSeverityChange = (severity: string) => {
    const newSeverities = formData.severities.includes(severity)
      ? formData.severities.filter((s) => s !== severity)
      : [...formData.severities, severity]
    setFormData({ ...formData, severities: newSeverities })
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString()
  }

  if (subscriptionsLoading) {
    return (
      <Box>
        <Breadcrumb current="Notifications" />
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      </Box>
    )
  }

  return (
    <Box>
      <Breadcrumb current="Notifications" />

      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleCreate}
        >
          Add Subscription
        </Button>
      </Box>

      {/* Stats Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={2.4}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Subscriptions
              </Typography>
              <Typography variant="h4">
                {stats?.enabled_subscriptions || 0}/{stats?.total_subscriptions || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Enabled
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Sent Today
              </Typography>
              <Typography variant="h4" color="primary">
                {stats?.total_sent_today || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Sent This Week
              </Typography>
              <Typography variant="h4" color="info.main">
                {stats?.total_sent_week || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Failed Today
              </Typography>
              <Typography variant="h4" color={stats?.failed_today ? 'error' : 'text.primary'}>
                {stats?.failed_today || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabs */}
      <Paper sx={{ mb: 2 }}>
        <Tabs value={tabIndex} onChange={(_, v) => setTabIndex(v)}>
          <Tab icon={<NotificationsIcon />} label="Subscriptions" iconPosition="start" />
          <Tab icon={<HistoryIcon />} label="History" iconPosition="start" />
        </Tabs>
      </Paper>

      {/* Subscriptions Tab */}
      {tabIndex === 0 && (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>Enabled</TableCell>
                <TableCell>Severities</TableCell>
                <TableCell>Channels</TableCell>
                <TableCell>Rate Limit</TableCell>
                <TableCell>Last Sent</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {subscriptions.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    <Typography color="text.secondary" sx={{ py: 4 }}>
                      No notification subscriptions configured
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                subscriptions.map((sub) => (
                  <TableRow key={sub.id}>
                    <TableCell>{sub.name}</TableCell>
                    <TableCell>
                      <Chip
                        label={sub.enabled ? 'Enabled' : 'Disabled'}
                        color={sub.enabled ? 'success' : 'default'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <Stack direction="row" spacing={0.5}>
                        {sub.severities.split(',').map((sev) => {
                          const option = SEVERITY_OPTIONS.find((o) => o.value === sev)
                          return option ? (
                            <Chip
                              key={sev}
                              label={option.label}
                              color={option.color}
                              size="small"
                            />
                          ) : null
                        })}
                      </Stack>
                    </TableCell>
                    <TableCell>
                      <Stack direction="row" spacing={1}>
                        {sub.notify_email && (
                          <Tooltip title="Email">
                            <EmailIcon color="action" fontSize="small" />
                          </Tooltip>
                        )}
                        {sub.notify_webhook && (
                          <Tooltip title="Webhook">
                            <WebhookIcon color="action" fontSize="small" />
                          </Tooltip>
                        )}
                      </Stack>
                    </TableCell>
                    <TableCell>{sub.min_interval_minutes} min</TableCell>
                    <TableCell>
                      {sub.last_notification_at
                        ? formatDate(sub.last_notification_at)
                        : 'Never'}
                    </TableCell>
                    <TableCell align="right">
                      <Tooltip title="Test">
                        <IconButton size="small" onClick={() => handleTest(sub)}>
                          <SendIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Edit">
                        <IconButton size="small" onClick={() => handleEdit(sub)}>
                          <EditIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Delete">
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => handleDelete(sub.id)}
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* History Tab */}
      {tabIndex === 1 && (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Time</TableCell>
                <TableCell>Channel</TableCell>
                <TableCell>Recipient</TableCell>
                <TableCell>Subject</TableCell>
                <TableCell>Status</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {logs.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} align="center">
                    <Typography color="text.secondary" sx={{ py: 4 }}>
                      No notification history
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                logs.map((log) => (
                  <TableRow key={log.id}>
                    <TableCell>{formatDate(log.created_at)}</TableCell>
                    <TableCell>
                      <Stack direction="row" spacing={1} alignItems="center">
                        {log.channel === 'email' ? (
                          <EmailIcon fontSize="small" />
                        ) : (
                          <WebhookIcon fontSize="small" />
                        )}
                        {log.channel}
                      </Stack>
                    </TableCell>
                    <TableCell sx={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {log.recipient}
                    </TableCell>
                    <TableCell>{log.subject || '-'}</TableCell>
                    <TableCell>
                      <Tooltip title={log.error_message || ''}>
                        <Chip
                          label={log.status}
                          color={log.status === 'sent' ? 'success' : log.status === 'failed' ? 'error' : 'default'}
                          size="small"
                        />
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Edit Dialog */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {selectedSubscription ? 'Edit Subscription' : 'Add Subscription'}
        </DialogTitle>
        <DialogContent>
          <Stack spacing={3} sx={{ mt: 1 }}>
            <TextField
              label="Name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              fullWidth
              required
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

            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Alarm Severities
              </Typography>
              <FormGroup row>
                {SEVERITY_OPTIONS.map((option) => (
                  <FormControlLabel
                    key={option.value}
                    control={
                      <Checkbox
                        checked={formData.severities.includes(option.value)}
                        onChange={() => handleSeverityChange(option.value)}
                      />
                    }
                    label={option.label}
                  />
                ))}
              </FormGroup>
            </Box>

            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Notification Channels
              </Typography>
              <FormGroup>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={formData.notify_email}
                      onChange={(e) =>
                        setFormData({ ...formData, notify_email: e.target.checked })
                      }
                    />
                  }
                  label="Email (sent to your user email)"
                />
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={formData.notify_webhook}
                      onChange={(e) =>
                        setFormData({ ...formData, notify_webhook: e.target.checked })
                      }
                    />
                  }
                  label="Webhook"
                />
              </FormGroup>
            </Box>

            {formData.notify_webhook && (
              <TextField
                label="Webhook URL"
                value={formData.webhook_url}
                onChange={(e) => setFormData({ ...formData, webhook_url: e.target.value })}
                fullWidth
                placeholder="https://example.com/webhook"
              />
            )}

            <TextField
              label="Rate Limit (minutes)"
              type="number"
              value={formData.min_interval_minutes}
              onChange={(e) =>
                setFormData({ ...formData, min_interval_minutes: parseInt(e.target.value) || 5 })
              }
              fullWidth
              helperText="Minimum time between notifications for the same alarm type"
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleSave}
            disabled={!formData.name || formData.severities.length === 0}
          >
            Save
          </Button>
        </DialogActions>
      </Dialog>

      {/* Test Dialog */}
      <Dialog open={testDialogOpen} onClose={() => setTestDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Send Test Notification</DialogTitle>
        <DialogContent>
          <Stack spacing={3} sx={{ mt: 1 }}>
            <Alert severity="info">
              This will send a test notification using your subscription settings.
            </Alert>

            <FormControl fullWidth>
              <InputLabel>Channel</InputLabel>
              <Select
                value={testChannel}
                label="Channel"
                onChange={(e) => setTestChannel(e.target.value)}
              >
                {selectedSubscription?.notify_email && (
                  <MenuItem value="email">Email</MenuItem>
                )}
                {selectedSubscription?.notify_webhook && (
                  <MenuItem value="webhook">Webhook</MenuItem>
                )}
              </Select>
            </FormControl>

            <TextField
              label={testChannel === 'email' ? 'Override Email Address' : 'Override Webhook URL'}
              value={testRecipient}
              onChange={(e) => setTestRecipient(e.target.value)}
              fullWidth
              placeholder={testChannel === 'email' ? 'Leave empty to use your email' : 'Leave empty to use configured URL'}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTestDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            startIcon={<SendIcon />}
            onClick={handleSendTest}
            disabled={testMutation.isPending}
          >
            {testMutation.isPending ? 'Sending...' : 'Send Test'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
