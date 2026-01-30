import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Box,
  Paper,
  Tabs,
  Tab,
  CircularProgress,
  Button,
  TextField,
  Switch,
  FormControlLabel,
  Grid,
  Alert,
  Snackbar,
  Card,
  CardContent,
  CardHeader,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  InputAdornment,
  IconButton,
} from '@mui/material'
import {
  Save as SaveIcon,
  Refresh as RefreshIcon,
  Visibility,
  VisibilityOff,
  Casino as GenerateIcon,
} from '@mui/icons-material'
import { settingsApi, splynxApi, bandwidthsApi } from '../services/api'
import Breadcrumb from '../components/Breadcrumb'

interface TabPanelProps {
  children?: React.ReactNode
  index: number
  value: number
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props
  return (
    <div hidden={value !== index} {...other}>
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  )
}

interface SettingFieldProps {
  label: string
  settingKey: string
  value: string
  type: 'text' | 'number' | 'boolean' | 'password' | 'textarea'
  helperText?: string
  onChange: (key: string, value: string) => void
}

function SettingField({
  label,
  settingKey,
  value,
  type,
  helperText,
  onChange,
}: SettingFieldProps) {
  if (type === 'boolean') {
    return (
      <FormControlLabel
        control={
          <Switch
            checked={value === 'true'}
            onChange={(e) => onChange(settingKey, e.target.checked ? 'true' : 'false')}
          />
        }
        label={label}
      />
    )
  }

  return (
    <TextField
      fullWidth
      size="small"
      label={label}
      value={value}
      type={type === 'password' ? 'password' : type === 'number' ? 'number' : 'text'}
      multiline={type === 'textarea'}
      rows={type === 'textarea' ? 4 : 1}
      onChange={(e) => onChange(settingKey, e.target.value)}
      helperText={helperText}
    />
  )
}

// Password field with show/hide toggle
interface PasswordFieldProps {
  label: string
  settingKey: string
  value: string
  helperText?: string
  onChange: (key: string, value: string) => void
  endButton?: React.ReactNode
}

function PasswordField({
  label,
  settingKey,
  value,
  helperText,
  onChange,
  endButton,
}: PasswordFieldProps) {
  const [showPassword, setShowPassword] = useState(false)

  return (
    <Box sx={{ display: 'flex', gap: 1 }}>
      <TextField
        fullWidth
        size="small"
        label={label}
        value={value}
        type={showPassword ? 'text' : 'password'}
        onChange={(e) => onChange(settingKey, e.target.value)}
        helperText={helperText}
        InputProps={{
          endAdornment: (
            <InputAdornment position="end">
              <IconButton
                size="small"
                onClick={() => setShowPassword(!showPassword)}
                edge="end"
              >
                {showPassword ? <VisibilityOff /> : <Visibility />}
              </IconButton>
            </InputAdornment>
          ),
        }}
      />
      {endButton}
    </Box>
  )
}

// Generate random secret
function generateSecret(length: number = 32): string {
  const chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
  let result = ''
  for (let i = 0; i < length; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length))
  }
  return result
}

// Privilege sub-tabs with their fields
const PRIVILEGE_TABS = [
  {
    name: 'Monitoring',
    fields: [
      { key: 'alarms_display', label: 'Alarms Display' },
      { key: 'alarms_radius_test', label: 'Alarms Radius Test' },
    ],
  },
  {
    name: 'Services',
    fields: [
      { key: 'subscribers_display', label: 'Subscribers Display' },
      { key: 'subscribers_edit', label: 'Subscribers Edit' },
      { key: 'bandwidths_display', label: 'Bandwidths Display' },
      { key: 'bandwidths_edit', label: 'Bandwidths Edit' },
    ],
  },
  {
    name: 'Automation',
    fields: [
      { key: 'automation_display', label: 'Automation Display' },
      { key: 'automation_edit', label: 'Automation Edit' },
    ],
  },
  {
    name: 'Devices',
    fields: [
      { key: 'gam_display', label: 'GAM Display' },
      { key: 'gam_edit', label: 'GAM Edit' },
      { key: 'endpoints_display', label: 'Endpoints Display' },
      { key: 'endpoints_edit', label: 'Endpoints Edit' },
      { key: 'groups_display', label: 'Groups Display' },
      { key: 'groups_edit', label: 'Groups Edit' },
      { key: 'timezones_display', label: 'Timezones Display' },
      { key: 'timezones_edit', label: 'Timezones Edit' },
      { key: 'firmware_display', label: 'Firmware Display' },
      { key: 'firmware_edit', label: 'Firmware Edit' },
    ],
  },
  {
    name: 'Versions',
    fields: [
      { key: 'versions_display', label: 'Versions Display' },
      { key: 'versions_edit', label: 'Versions Edit' },
    ],
  },
  {
    name: 'Admin',
    fields: [
      { key: 'sessions_display', label: 'Active Sessions Display' },
      { key: 'sessions_edit', label: 'Active Sessions Edit' },
      { key: 'logs_display', label: 'Logs Display' },
      { key: 'users_display', label: 'Users Display' },
      { key: 'users_edit', label: 'Users Edit' },
      { key: 'settings_display', label: 'Settings Display' },
      { key: 'settings_edit', label: 'Settings Edit' },
      { key: 'auditing_display', label: 'Auditing Display' },
      { key: 'notifications_display', label: 'Notifications Display' },
      { key: 'notifications_edit', label: 'Notifications Edit' },
    ],
  },
]

const TIMEZONE_OPTIONS = [
  // US timezones first
  'America/New_York', 'America/Chicago', 'America/Denver', 'America/Los_Angeles',
  'America/Anchorage', 'America/Phoenix', 'Pacific/Honolulu',
  // Americas
  'America/Toronto', 'America/Vancouver', 'America/Edmonton', 'America/Winnipeg',
  'America/Halifax', 'America/Mexico_City', 'America/Bogota', 'America/Lima',
  'America/Santiago', 'America/Buenos_Aires', 'America/Sao_Paulo',
  // Europe
  'Europe/London', 'Europe/Paris', 'Europe/Berlin', 'Europe/Madrid', 'Europe/Rome',
  'Europe/Amsterdam', 'Europe/Brussels', 'Europe/Zurich', 'Europe/Stockholm',
  'Europe/Oslo', 'Europe/Helsinki', 'Europe/Warsaw', 'Europe/Prague',
  'Europe/Vienna', 'Europe/Athens', 'Europe/Istanbul', 'Europe/Moscow',
  // Asia
  'Asia/Dubai', 'Asia/Karachi', 'Asia/Kolkata', 'Asia/Dhaka', 'Asia/Bangkok',
  'Asia/Singapore', 'Asia/Hong_Kong', 'Asia/Shanghai', 'Asia/Tokyo', 'Asia/Seoul',
  // Oceania
  'Australia/Sydney', 'Australia/Melbourne', 'Australia/Brisbane', 'Australia/Perth',
  'Pacific/Auckland', 'Pacific/Fiji',
  // Africa
  'Africa/Cairo', 'Africa/Lagos', 'Africa/Johannesburg', 'Africa/Nairobi',
  // UTC
  'UTC',
]

const DEFAULT_TERMS_TEMPLATE = `TERMS AND CONDITIONS OF USE

By accessing this network management system, you agree to the following terms:

1. AUTHORIZED USE ONLY
Access to this system is restricted to authorized personnel only. Unauthorized access is prohibited and may be subject to criminal prosecution.

2. ACCEPTABLE USE
Users shall use this system solely for legitimate network management purposes. Any misuse, including but not limited to unauthorized configuration changes, data exfiltration, or disruption of services, is strictly prohibited.

3. SESSION MONITORING
All sessions may be monitored and recorded for security and auditing purposes. By logging in, you consent to such monitoring.

4. DATA PRIVACY
User credentials and session data are stored securely. Personal information is used solely for authentication and audit purposes and will not be shared with third parties.

5. PASSWORD POLICY
Users are responsible for maintaining the confidentiality of their credentials. Sharing of login credentials is prohibited. Report any suspected compromise immediately.

6. SERVICE AVAILABILITY
The system is provided on an "as-is" basis. While reasonable efforts are made to ensure availability, no guarantee of uninterrupted service is made.

7. LIMITATION OF LIABILITY
The system operator shall not be liable for any damages arising from authorized or unauthorized use of this system, including but not limited to data loss, service interruption, or configuration errors.

8. COMPLIANCE
Users must comply with all applicable laws, regulations, and organizational policies when using this system.

9. MODIFICATIONS
These terms may be updated at any time. Continued use of the system constitutes acceptance of any modifications.`

export default function Settings() {
  const queryClient = useQueryClient()
  const [tabValue, setTabValue] = useState(0)
  const [radiusTab, setRadiusTab] = useState(0)
  const [privilegeTab, setPrivilegeTab] = useState(0)
  const [formData, setFormData] = useState<Record<string, string>>({})
  const [hasChanges, setHasChanges] = useState(false)
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success',
  })

  const { data: settingsData, isLoading } = useQuery({
    queryKey: ['settings-by-type'],
    queryFn: () => settingsApi.getByType().then((res) => res.data),
  })

  const { data: bandwidthPlans } = useQuery({
    queryKey: ['bandwidths-all'],
    queryFn: () => bandwidthsApi.list({ page_size: 200 }).then((res) => res.data.items || res.data),
  })

  // Initialize form data when settings are loaded
  useEffect(() => {
    if (settingsData) {
      const initialData: Record<string, string> = {}
      Object.values(settingsData).forEach((settings: any) => {
        settings.forEach((s: any) => {
          initialData[s.key] = s.value || ''
        })
      })
      setFormData(initialData)
      setHasChanges(false)
    }
  }, [settingsData])

  const bulkUpdateMutation = useMutation({
    mutationFn: (settings: Record<string, string>) => settingsApi.bulkUpdate(settings),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings-by-type'] })
      setHasChanges(false)
      setSnackbar({ open: true, message: 'Settings saved successfully', severity: 'success' })
    },
    onError: (error: any) => {
      setSnackbar({
        open: true,
        message: error.response?.data?.detail || 'Failed to save settings',
        severity: 'error',
      })
    },
  })

  const resetMutation = useMutation({
    mutationFn: () => settingsApi.resetDefaults(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings-by-type'] })
      setSnackbar({ open: true, message: 'Settings reset to defaults', severity: 'success' })
    },
    onError: (error: any) => {
      setSnackbar({
        open: true,
        message: error.response?.data?.detail || 'Failed to reset settings',
        severity: 'error',
      })
    },
  })

  const handleChange = (key: string, value: string) => {
    setFormData((prev) => ({ ...prev, [key]: value }))
    setHasChanges(true)
  }

  const handleSave = () => {
    bulkUpdateMutation.mutate(formData)
  }

  const handleReset = () => {
    if (window.confirm('Reset all settings to their default values?')) {
      resetMutation.mutate()
    }
  }

  // Test email state
  const [testEmailStatus, setTestEmailStatus] = useState<{ loading: boolean; result: string | null; error: boolean }>({
    loading: false,
    result: null,
    error: false,
  })

  const handleTestEmail = async () => {
    setTestEmailStatus({ loading: true, result: null, error: false })
    try {
      await settingsApi.testEmail(formData._test_email_to || '')
      setTestEmailStatus({ loading: false, result: 'Test email sent successfully!', error: false })
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to send test email'
      setTestEmailStatus({ loading: false, result: errorMsg, error: true })
    }
  }

  // Splynx connection test state
  const [splynxTestStatus, setSplynxTestStatus] = useState<{ loading: boolean; result: string | null; error: boolean }>({
    loading: false,
    result: null,
    error: false,
  })

  // Fetch Splynx admins for assignee dropdown
  const { data: splynxAdmins } = useQuery({
    queryKey: ['splynx-admins'],
    queryFn: () => splynxApi.getAdmins().then((res) => res.data),
    enabled: tabValue === 7 && !!formData.splynx_api_url && !!formData.splynx_api_key,
  })

  const handleSplynxTest = async () => {
    setSplynxTestStatus({ loading: true, result: null, error: false })
    try {
      const response = await splynxApi.testConnection()
      if (response.data.status === 'success') {
        setSplynxTestStatus({ loading: false, result: 'Connection successful!', error: false })
      } else {
        setSplynxTestStatus({ loading: false, result: response.data.error || 'Connection failed', error: true })
      }
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.response?.data?.error || err.message || 'Connection failed'
      setSplynxTestStatus({ loading: false, result: errorMsg, error: true })
    }
  }

  // Main settings tabs
  const tabs = ['General', 'Terms', 'Radius', 'Users', 'TCA', 'Privileges', 'SMTP Server', 'Splynx']

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box>
      <Breadcrumb current="Settings" />
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box />
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={handleReset}
            disabled={resetMutation.isPending}
          >
            Reset Defaults
          </Button>
          <Button
            variant="contained"
            startIcon={<SaveIcon />}
            onClick={handleSave}
            disabled={!hasChanges || bulkUpdateMutation.isPending}
          >
            {bulkUpdateMutation.isPending ? 'Saving...' : 'Save'}
          </Button>
        </Box>
      </Box>

      {hasChanges && (
        <Alert severity="info" sx={{ mb: 2 }}>
          You have unsaved changes. Click "Save" to apply them.
        </Alert>
      )}

      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={tabValue}
          onChange={(_, newValue) => setTabValue(newValue)}
          variant="scrollable"
          scrollButtons="auto"
        >
          {tabs.map((tab, index) => (
            <Tab key={index} label={tab} />
          ))}
        </Tabs>
      </Paper>

      {/* General Tab */}
      <TabPanel value={tabValue} index={0}>
        <Card sx={{ mb: 3 }}>
          <CardHeader title="GAM" />
          <CardContent>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <SettingField
                  label="Configuration Backup Quantity"
                  settingKey="device_config_backup_quantity"
                  value={formData.device_config_backup_quantity || '10'}
                  type="number"
                  onChange={handleChange}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <SettingField
                  label="Warning Announcement Delay (Minutes)"
                  settingKey="device_minutes_warning_active"
                  value={formData.device_minutes_warning_active || '2'}
                  type="number"
                  onChange={handleChange}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <SettingField
                  label="Error Announcement Delay (Minutes)"
                  settingKey="device_minutes_considered_active"
                  value={formData.device_minutes_considered_active || '5'}
                  type="number"
                  onChange={handleChange}
                />
              </Grid>
            </Grid>
          </CardContent>
        </Card>

        <Card sx={{ mb: 3 }}>
          <CardHeader title="API" />
          <CardContent>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <SettingField
                  label="Enable API Documentation"
                  settingKey="api_enabled"
                  value={formData.api_enabled || 'true'}
                  type="boolean"
                  onChange={handleChange}
                />
              </Grid>
            </Grid>
          </CardContent>
        </Card>

        <Card>
          <CardHeader title="Purge" />
          <CardContent>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <SettingField
                  label="Purge Audits Delay (Days)"
                  settingKey="auditing_purge_delay"
                  value={formData.auditing_purge_delay || '30'}
                  type="number"
                  onChange={handleChange}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <SettingField
                  label="Purge Alarms Delay (Days)"
                  settingKey="alarm_purge_delay"
                  value={formData.alarm_purge_delay || '30'}
                  type="number"
                  onChange={handleChange}
                />
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </TabPanel>

      {/* Terms Tab */}
      <TabPanel value={tabValue} index={1}>
        <Card>
          <CardHeader title="Terms and Conditions" />
          <CardContent>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                {!formData.login_terms && (
                  <Button
                    variant="outlined"
                    size="small"
                    sx={{ mb: 2 }}
                    onClick={() => handleChange('login_terms', DEFAULT_TERMS_TEMPLATE)}
                  >
                    Load Default Template
                  </Button>
                )}
                <SettingField
                  label="Login Terms"
                  settingKey="login_terms"
                  value={formData.login_terms || ''}
                  type="textarea"
                  helperText="Terms and conditions shown on login page"
                  onChange={handleChange}
                />
              </Grid>
              <Grid item xs={12}>
                <SettingField
                  label="Require Terms Acceptance"
                  settingKey="require_terms_acceptance"
                  value={formData.require_terms_acceptance || 'false'}
                  type="boolean"
                  onChange={handleChange}
                />
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </TabPanel>

      {/* Radius Tab */}
      <TabPanel value={tabValue} index={2}>
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Grid container spacing={3} alignItems="center">
              <Grid item xs={12} md={6}>
                <SettingField
                  label="Activate Radius"
                  settingKey="radius_activate"
                  value={formData.radius_activate || 'false'}
                  type="boolean"
                  onChange={handleChange}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <SettingField
                  label="Default User Inactivity Session Timeout"
                  settingKey="default_session_timeout"
                  value={formData.default_session_timeout || '30'}
                  type="number"
                  onChange={handleChange}
                />
              </Grid>
            </Grid>
          </CardContent>
        </Card>

        <Paper sx={{ mb: 2 }}>
          <Tabs
            value={radiusTab}
            onChange={(_, newValue) => setRadiusTab(newValue)}
          >
            <Tab label="#1" />
            <Tab label="#2" />
            <Tab label="#3" />
            <Tab label="#4" />
            <Tab label="#5" />
          </Tabs>
        </Paper>

        {[0, 1, 2, 3, 4].map((idx) => (
          <Box key={idx} hidden={radiusTab !== idx}>
            <Card>
              <CardContent>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <SettingField
                      label={`Radius #${idx + 1} IP address`}
                      settingKey={`radius_${idx + 1}_ip`}
                      value={formData[`radius_${idx + 1}_ip`] || ''}
                      type="text"
                      onChange={handleChange}
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <SettingField
                      label={`Radius #${idx + 1} secret`}
                      settingKey={`radius_${idx + 1}_secret`}
                      value={formData[`radius_${idx + 1}_secret`] || ''}
                      type="password"
                      onChange={handleChange}
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <SettingField
                      label={`Radius #${idx + 1} Authenticator`}
                      settingKey={`radius_${idx + 1}_authenticator`}
                      value={formData[`radius_${idx + 1}_authenticator`] || 'CHAP'}
                      type="text"
                      onChange={handleChange}
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <SettingField
                      label={`Radius #${idx + 1} Port`}
                      settingKey={`radius_${idx + 1}_port`}
                      value={formData[`radius_${idx + 1}_port`] || '1812'}
                      type="number"
                      onChange={handleChange}
                    />
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Box>
        ))}
      </TabPanel>

      {/* Users Tab */}
      <TabPanel value={tabValue} index={3}>
        <Card>
          <CardHeader title="User Settings" />
          <CardContent>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <SettingField
                  label="Default Session Timeout (minutes)"
                  settingKey="default_session_timeout"
                  value={formData.default_session_timeout || '30'}
                  type="number"
                  helperText="Default inactivity timeout for new users"
                  onChange={handleChange}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <SettingField
                  label="Max Session Duration (hours)"
                  settingKey="max_session_duration"
                  value={formData.max_session_duration || '24'}
                  type="number"
                  helperText="Maximum session duration before forced logout"
                  onChange={handleChange}
                />
              </Grid>
              <Grid item xs={12}>
                <SettingField
                  label="Enforce Strong Passwords"
                  settingKey="enforce_strong_passwords"
                  value={formData.enforce_strong_passwords || 'true'}
                  type="boolean"
                  onChange={handleChange}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth size="small">
                  <InputLabel>Default Timezone</InputLabel>
                  <Select
                    value={formData.default_user_timezone || 'America/Chicago'}
                    label="Default Timezone"
                    onChange={(e) => handleChange('default_user_timezone', e.target.value)}
                  >
                    {TIMEZONE_OPTIONS.map((tz) => (
                      <MenuItem key={tz} value={tz}>{tz}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </TabPanel>

      {/* TCA Tab (Threshold Crossing Alerts) */}
      <TabPanel value={tabValue} index={4}>
        <Card>
          <CardContent>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <SettingField
                  label="Max Usable Bandwidth (Mbps) - Warning Level"
                  settingKey="endpoint_tca_bandwidth_warning_level"
                  value={formData.endpoint_tca_bandwidth_warning_level || '800'}
                  type="number"
                  onChange={handleChange}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <SettingField
                  label="Max Usable Bandwidth (Mbps) - Error Level"
                  settingKey="endpoint_tca_bandwidth_error_level"
                  value={formData.endpoint_tca_bandwidth_error_level || '300'}
                  type="number"
                  onChange={handleChange}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <SettingField
                  label="PHY rate (Mbps) - Warning Level"
                  settingKey="endpoint_tca_phy_warning_level"
                  value={formData.endpoint_tca_phy_warning_level || '0'}
                  type="number"
                  onChange={handleChange}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <SettingField
                  label="PHY rate (Mbps) - Error Level"
                  settingKey="endpoint_tca_phy_error_level"
                  value={formData.endpoint_tca_phy_error_level || '0'}
                  type="number"
                  onChange={handleChange}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <SettingField
                  label="Maximum number of coax endpoints per G.hn port - Warning Level"
                  settingKey="max_coax_endpoints_warning_level"
                  value={formData.max_coax_endpoints_warning_level || '11'}
                  type="number"
                  onChange={handleChange}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <SettingField
                  label="Maximum number of coax endpoints per G.hn port - Error Level"
                  settingKey="max_coax_endpoints_error_level"
                  value={formData.max_coax_endpoints_error_level || '14'}
                  type="number"
                  onChange={handleChange}
                />
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </TabPanel>

      {/* Privileges Tab */}
      <TabPanel value={tabValue} index={5}>
        <Paper sx={{ mb: 2 }}>
          <Tabs
            value={privilegeTab}
            onChange={(_, newValue) => setPrivilegeTab(newValue)}
          >
            {PRIVILEGE_TABS.map((tab, index) => (
              <Tab key={index} label={tab.name} />
            ))}
          </Tabs>
        </Paper>

        {PRIVILEGE_TABS.map((tab, tabIndex) => (
          <Box key={tabIndex} hidden={privilegeTab !== tabIndex}>
            <Card>
              <CardContent>
                <Grid container spacing={3}>
                  {tab.fields.map((field) => (
                    <Grid item xs={12} md={6} key={field.key}>
                      <FormControl fullWidth size="small">
                        <InputLabel>{field.label}</InputLabel>
                        <Select
                          value={formData[`privilege_${field.key}`] || '5'}
                          label={field.label}
                          onChange={(e) => handleChange(`privilege_${field.key}`, e.target.value)}
                        >
                          {Array.from({ length: 15 }, (_, i) => i + 1).map((level) => (
                            <MenuItem key={level} value={String(level)}>
                              {level}{level === 1 ? ' (Viewer)' : level === 3 ? ' (Operator)' : level === 5 ? ' (Manager)' : level === 7 ? ' (Admin)' : level === 9 ? ' (SuperAdmin)' : level === 15 ? ' (Master)' : ''}
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </Grid>
                  ))}
                </Grid>
              </CardContent>
            </Card>
          </Box>
        ))}
      </TabPanel>

      {/* SMTP Server Tab */}
      <TabPanel value={tabValue} index={6}>
        <Card sx={{ mb: 3 }}>
          <CardHeader title="SMTP Server Configuration" />
          <CardContent>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <SettingField
                  label="Enable Email Notifications"
                  settingKey="email_enable"
                  value={formData.email_enable || 'false'}
                  type="boolean"
                  onChange={handleChange}
                />
              </Grid>
              <Grid item xs={12} md={8}>
                <SettingField
                  label="SMTP Host"
                  settingKey="email_host_name"
                  value={formData.email_host_name || ''}
                  type="text"
                  onChange={handleChange}
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <SettingField
                  label="SMTP Port"
                  settingKey="email_host_port"
                  value={formData.email_host_port || '587'}
                  type="number"
                  onChange={handleChange}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <SettingField
                  label="From Address"
                  settingKey="email_host_from"
                  value={formData.email_host_from || ''}
                  type="text"
                  onChange={handleChange}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <SettingField
                  label="Use SSL/TLS"
                  settingKey="email_host_ssl"
                  value={formData.email_host_ssl || 'true'}
                  type="boolean"
                  onChange={handleChange}
                />
              </Grid>
              <Grid item xs={12}>
                <SettingField
                  label="Requires Authentication"
                  settingKey="email_require_auth"
                  value={formData.email_require_auth || 'true'}
                  type="boolean"
                  onChange={handleChange}
                />
              </Grid>
              {formData.email_require_auth !== 'false' && (
                <>
                  <Grid item xs={12} md={6}>
                    <SettingField
                      label="Username"
                      settingKey="email_host_username"
                      value={formData.email_host_username || ''}
                      type="text"
                      onChange={handleChange}
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <SettingField
                      label="Password"
                      settingKey="email_host_password"
                      value={formData.email_host_password || ''}
                      type="password"
                      onChange={handleChange}
                    />
                  </Grid>
                </>
              )}
            </Grid>
          </CardContent>
        </Card>
        <Card>
          <CardHeader title="Test Email" />
          <CardContent>
            <Grid container spacing={2} alignItems="center">
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  size="small"
                  label="Recipient Email"
                  value={formData._test_email_to || ''}
                  onChange={(e) => setFormData({ ...formData, _test_email_to: e.target.value })}
                  placeholder="test@example.com"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <Button
                  variant="outlined"
                  onClick={handleTestEmail}
                  disabled={testEmailStatus.loading || !formData._test_email_to || !formData.email_host_name}
                >
                  {testEmailStatus.loading ? 'Sending...' : 'Send Test Email'}
                </Button>
                {testEmailStatus.result && (
                  <Alert severity={testEmailStatus.error ? 'error' : 'success'} sx={{ mt: 1 }}>
                    {testEmailStatus.result}
                  </Alert>
                )}
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </TabPanel>

      {/* Splynx Integration Tab */}
      <TabPanel value={tabValue} index={7}>
        <Card sx={{ mb: 3 }}>
          <CardHeader title="API Connection" />
          <CardContent>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <SettingField
                  label="Splynx API URL"
                  settingKey="splynx_api_url"
                  value={formData.splynx_api_url || ''}
                  type="text"
                  helperText="Full URL to your Splynx API (e.g., https://splynx.alamobb.net/api/2.0)"
                  onChange={handleChange}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <PasswordField
                  label="API Key"
                  settingKey="splynx_api_key"
                  value={formData.splynx_api_key || ''}
                  helperText="Splynx API key for authentication"
                  onChange={handleChange}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <PasswordField
                  label="API Secret"
                  settingKey="splynx_api_secret"
                  value={formData.splynx_api_secret || ''}
                  helperText="Splynx API secret for Basic auth"
                  onChange={handleChange}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <PasswordField
                  label="Webhook Secret"
                  settingKey="splynx_webhook_secret"
                  value={formData.splynx_webhook_secret || ''}
                  helperText="Secret for verifying incoming webhooks from Splynx"
                  onChange={handleChange}
                  endButton={
                    <Button
                      variant="outlined"
                      size="small"
                      startIcon={<GenerateIcon />}
                      onClick={() => handleChange('splynx_webhook_secret', generateSecret(32))}
                      sx={{ minWidth: 'auto', whiteSpace: 'nowrap' }}
                    >
                      Generate
                    </Button>
                  }
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, height: '100%' }}>
                  <Button
                    variant="outlined"
                    onClick={handleSplynxTest}
                    disabled={splynxTestStatus.loading || !formData.splynx_api_url || !formData.splynx_api_key || !formData.splynx_api_secret}
                  >
                    {splynxTestStatus.loading ? 'Testing...' : 'Test Connection'}
                  </Button>
                  {splynxTestStatus.result && (
                    <Alert severity={splynxTestStatus.error ? 'error' : 'success'} sx={{ py: 0 }}>
                      {splynxTestStatus.result}
                    </Alert>
                  )}
                </Box>
              </Grid>
            </Grid>
          </CardContent>
        </Card>

        <Card sx={{ mb: 3 }}>
          <CardHeader title="Auto-Provisioning" />
          <CardContent>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <SettingField
                  label="Enable Auto-Provisioning"
                  settingKey="splynx_auto_provision"
                  value={formData.splynx_auto_provision || 'false'}
                  type="boolean"
                  onChange={handleChange}
                />
              </Grid>
              <Grid item xs={12}>
                <Alert severity="info" sx={{ mb: 2 }}>
                  When enabled, new CPE devices detected on GAM will automatically be provisioned
                  by looking up the MAC address in Splynx inventory and creating the subscriber.
                </Alert>
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth size="small">
                  <InputLabel>Default Bandwidth Profile</InputLabel>
                  <Select
                    label="Default Bandwidth Profile"
                    value={formData.splynx_default_bandwidth_profile || ''}
                    onChange={(e) => handleChange('splynx_default_bandwidth_profile', e.target.value)}
                  >
                    <MenuItem value="">Unthrottled</MenuItem>
                    {bandwidthPlans?.filter((bw: any) => !bw.deleted).map((bw: any) => (
                      <MenuItem key={bw.id} value={bw.id}>{bw.name}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                <SettingField
                  label="Default VLAN"
                  settingKey="splynx_default_vlan"
                  value={formData.splynx_default_vlan || '100'}
                  type="text"
                  helperText="VLAN ID to assign when auto-provisioning"
                  onChange={handleChange}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <SettingField
                  label="Lookup Retry Duration (hours)"
                  settingKey="splynx_retry_duration_hours"
                  value={formData.splynx_retry_duration_hours || '24'}
                  type="number"
                  helperText="How long to retry looking up new endpoints in Splynx"
                  onChange={handleChange}
                />
              </Grid>
            </Grid>
          </CardContent>
        </Card>

        <Card sx={{ mb: 3 }}>
          <CardHeader title="QC Ticket Settings" />
          <CardContent>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth size="small">
                  <InputLabel>QC Ticket Assignee</InputLabel>
                  <Select
                    value={formData.splynx_qc_ticket_assignee_id || ''}
                    label="QC Ticket Assignee"
                    onChange={(e) => handleChange('splynx_qc_ticket_assignee_id', e.target.value)}
                  >
                    <MenuItem value="">
                      <em>None (unassigned)</em>
                    </MenuItem>
                    {splynxAdmins?.items?.map((admin: { id: number; name: string; email: string }) => (
                      <MenuItem key={admin.id} value={String(admin.id)}>
                        {admin.name} ({admin.email})
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                {!splynxAdmins?.items && formData.splynx_api_url && formData.splynx_api_key && formData.splynx_api_secret && (
                  <Alert severity="warning" sx={{ py: 0 }}>
                    Save settings and test connection to load administrators
                  </Alert>
                )}
              </Grid>
            </Grid>
          </CardContent>
        </Card>

        <Card>
          <CardHeader title="Reconciliation" />
          <CardContent>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <SettingField
                  label="Reconciliation Time (HH:MM)"
                  settingKey="splynx_reconciliation_time"
                  value={formData.splynx_reconciliation_time || '02:00'}
                  type="text"
                  helperText="Daily time to run GAM/Splynx reconciliation (24-hour format)"
                  onChange={handleChange}
                />
              </Grid>
              <Grid item xs={12}>
                <Alert severity="info">
                  Reconciliation compares GAM subscribers with Splynx inventory daily and creates
                  tickets in Splynx for any mismatches (name changes, orphaned subscribers, etc.)
                </Alert>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </TabPanel>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert severity={snackbar.severity} onClose={() => setSnackbar({ ...snackbar, open: false })}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  )
}
