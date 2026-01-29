import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || ''

export const api = axios.create({
  baseURL: API_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add session token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('session_id')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor for auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('session_id')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authApi = {
  login: (username: string, password: string) =>
    api.post('/auth/login', { username, password }),
  logout: () => api.post('/auth/logout'),
  getSession: () => api.get('/auth/session'),
}

// Devices API
export const devicesApi = {
  list: (params?: {
    page?: number
    page_size?: number
    search?: string
    is_online?: boolean
  }) => api.get('/devices', { params }),
  get: (id: string) => api.get(`/devices/${id}`),
  create: (data: any) => api.post('/devices', data),
  update: (id: string, data: any) => api.patch(`/devices/${id}`, data),
  delete: (id: string) => api.delete(`/devices/${id}`),
  sync: (id: string) => api.post(`/devices/${id}/sync`),
  syncAll: () => api.post('/devices/sync-all'),
  bulkDelete: (deviceIds: string[]) =>
    api.post('/devices/bulk-delete', { device_ids: deviceIds }),
  saveConfig: (id: string) => api.post(`/devices/${id}/save-config`),
  downloadConfig: (id: string) => api.post(`/devices/${id}/download-config`),
  firmwareSwap: (id: string) => api.post(`/devices/${id}/firmware-swap`),
  getTimezone: (id: string) => api.get(`/devices/${id}/timezone`),
  updateTimezone: (id: string, data: any) => api.patch(`/devices/${id}/timezone`, data),
}

// Endpoints API
export const endpointsApi = {
  list: (params?: {
    page?: number
    page_size?: number
    device_id?: string
    alive?: boolean
    search?: string
  }) => api.get('/endpoints', { params }),
  get: (id: string) => api.get(`/endpoints/${id}`),
  poeReset: (id: string) => api.post(`/endpoints/${id}/poe-reset`),
  reboot: (id: string) => api.post(`/endpoints/${id}/reboot`),
  refreshDetails: (id: string) => api.post(`/endpoints/${id}/refresh-details`),
  quarantine: (id: string, reason?: string) =>
    api.post(`/endpoints/${id}/quarantine`, reason ? { reason } : undefined),
  unquarantine: (id: string) => api.post(`/endpoints/${id}/unquarantine`),
  configure: (id: string, data: { port_if_index: string; name?: string; description?: string }) =>
    api.post(`/endpoints/${id}/configure`, data),
  autoConfigure: (id: string) => api.post(`/endpoints/${id}/auto-configure`),
  unprovision: (id: string) => api.post(`/endpoints/${id}/unprovision`),
}

// Subscribers API
export const subscribersApi = {
  list: (params?: {
    page?: number
    page_size?: number
    device_id?: string
    search?: string
  }) => api.get('/subscribers', { params }),
  get: (id: string) => api.get(`/subscribers/${id}`),
  create: (data: any) => api.post('/subscribers', data),
  update: (id: string, data: any) => api.patch(`/subscribers/${id}`, data),
  delete: (id: string) => api.delete(`/subscribers/${id}`),
  // Device push operations
  createOnDevice: (data: any) => api.post('/subscribers/device/create', data),
  updateOnDevice: (id: string, data: any) => api.put(`/subscribers/${id}/device`, data),
  deleteFromDevice: (id: string) => api.delete(`/subscribers/${id}/device`),
}

// Alarms API
export const alarmsApi = {
  list: (params?: {
    page?: number
    page_size?: number
    device_id?: string
    severity?: string
    active_only?: boolean
  }) => api.get('/alarms', { params }),
  getCounts: () => api.get('/alarms/counts'),
  get: (id: string) => api.get(`/alarms/${id}`),
  acknowledge: (id: string) => api.post(`/alarms/${id}/acknowledge`),
  close: (id: string) => api.post(`/alarms/${id}/close`),
}

// Users API
export const usersApi = {
  list: (params?: {
    page?: number
    page_size?: number
    search?: string
  }) => api.get('/users', { params }),
  getMe: () => api.get('/users/me'),
  get: (id: string) => api.get(`/users/${id}`),
  create: (data: any) => api.post('/users', data),
  update: (id: string, data: any) => api.patch(`/users/${id}`, data),
  delete: (id: string) => api.delete(`/users/${id}`),
}

// Ports API
export const portsApi = {
  list: (params?: { device_id?: string }) => api.get('/ports', { params }),
  listAll: (params?: {
    page?: number
    page_size?: number
    link?: boolean
    search?: string
  }) => api.get('/ports/all', { params }),
  get: (id: string) => api.get(`/ports/${id}`),
  update: (id: string, data: { shutdown?: boolean; mtu?: number }) =>
    api.patch(`/ports/${id}`, data),
}

// Bandwidth Profiles API
export const bandwidthsApi = {
  list: (params?: {
    page?: number
    page_size?: number
    device_id?: string
  }) => api.get('/bandwidths', { params }),
  get: (id: string) => api.get(`/bandwidths/${id}`),
  create: (data: any) => api.post('/bandwidths', data),
  update: (id: string, data: any) => api.patch(`/bandwidths/${id}`, data),
  delete: (id: string) => api.delete(`/bandwidths/${id}`),
  // Device push operations
  pushToDevice: (id: string) => api.post(`/bandwidths/${id}/push`),
  deleteFromDevice: (id: string) => api.delete(`/bandwidths/${id}/device`),
}

// Groups API
export const groupsApi = {
  list: (params?: {
    page?: number
    page_size?: number
    parent_id?: string
  }) => api.get('/groups', { params }),
  getTree: () => api.get('/groups/tree'),
  get: (id: string) => api.get(`/groups/${id}`),
  create: (data: any) => api.post('/groups', data),
  update: (id: string, data: any) => api.patch(`/groups/${id}`, data),
  delete: (id: string) => api.delete(`/groups/${id}`),
  // Device assignment
  getDevices: (id: string) => api.get(`/groups/${id}/devices`),
  assignDevices: (id: string, deviceIds: string[]) =>
    api.post(`/groups/${id}/devices`, { device_ids: deviceIds }),
  removeDevice: (groupId: string, deviceId: string) =>
    api.delete(`/groups/${groupId}/devices/${deviceId}`),
}

// Dashboard API
export const dashboardApi = {
  getData: () => api.get('/dashboard'),
}

// Audit Logs API
export const auditLogsApi = {
  list: (params?: {
    page?: number
    page_size?: number
    action?: string
    entity_type?: string
    username?: string
    search?: string
    start_date?: string
    end_date?: string
  }) => api.get('/audit-logs', { params }),
  get: (id: string) => api.get(`/audit-logs/${id}`),
  getStats: () => api.get('/audit-logs/stats'),
  getActionTypes: () => api.get('/audit-logs/actions'),
  getEntityTypes: () => api.get('/audit-logs/entity-types'),
}

// Settings API
export const settingsApi = {
  list: (params?: { type?: string }) => api.get('/settings', { params }),
  getByType: () => api.get('/settings/by-type'),
  get: (key: string) => api.get(`/settings/${key}`),
  update: (key: string, value: string) =>
    api.put(`/settings/${key}`, { value }),
  bulkUpdate: (settings: Record<string, string>) =>
    api.post('/settings/bulk', { settings }),
  resetDefaults: () => api.post('/settings/reset-defaults'),
  testEmail: (to: string) => api.post('/settings/test-email', { to }),
}

// Notifications API
export const notificationsApi = {
  list: () => api.get('/notifications'),
  get: (id: string) => api.get(`/notifications/${id}`),
  create: (data: any) => api.post('/notifications', data),
  update: (id: string, data: any) => api.patch(`/notifications/${id}`, data),
  delete: (id: string) => api.delete(`/notifications/${id}`),
  getStats: () => api.get('/notifications/stats'),
  getLogs: (params?: {
    page?: number
    page_size?: number
    subscription_id?: string
    status?: string
  }) => api.get('/notifications/logs', { params }),
  test: (id: string, data: { channel: string; recipient?: string }) =>
    api.post(`/notifications/${id}/test`, data),
}

// Export API - CSV downloads
export const exportApi = {
  devices: () => api.get('/export/devices', { responseType: 'blob' }),
  endpoints: (deviceId?: string) =>
    api.get('/export/endpoints', {
      params: deviceId ? { device_id: deviceId } : undefined,
      responseType: 'blob',
    }),
  subscribers: (deviceId?: string) =>
    api.get('/export/subscribers', {
      params: deviceId ? { device_id: deviceId } : undefined,
      responseType: 'blob',
    }),
  alarms: (params?: { device_id?: string; active_only?: boolean }) =>
    api.get('/export/alarms', { params, responseType: 'blob' }),
  bandwidths: (deviceId?: string) =>
    api.get('/export/bandwidths', {
      params: deviceId ? { device_id: deviceId } : undefined,
      responseType: 'blob',
    }),
  groups: () => api.get('/export/groups', { responseType: 'blob' }),
  users: () => api.get('/export/users', { responseType: 'blob' }),
  auditLogs: (params?: { start_date?: string; end_date?: string }) =>
    api.get('/export/audit-logs', { params, responseType: 'blob' }),
}

// Helper to extract error message from API errors (handles Pydantic validation error arrays)
export const getErrorMessage = (error: any, fallback: string = 'An error occurred'): string => {
  const detail = error?.response?.data?.detail
  if (!detail) return fallback
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return detail.map((d: any) => d.msg || JSON.stringify(d)).join(', ')
  return fallback
}

// Helper function to download blob as file
export const downloadFile = (blob: Blob, filename: string) => {
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', filename)
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}

// Firmware API
export const firmwareApi = {
  list: (params?: {
    page?: number
    page_size?: number
    model_type?: string
  }) => api.get('/firmware', { params }),
  get: (id: string) => api.get(`/firmware/${id}`),
  upload: (formData: FormData) => api.post('/firmware', formData),
  delete: (id: string) => api.delete(`/firmware/${id}`),
  setDefault: (id: string) => api.post(`/firmware/${id}/set-default`),
  deploy: (deviceId: string, firmwareId: string, autoSwap?: boolean) =>
    api.post(`/firmware/deploy/${deviceId}`, null, {
      params: { firmware_id: firmwareId, auto_swap: autoSwap },
    }),
  bulkDownload: (deviceIds: string[]) =>
    api.post('/firmware/bulk-download', { device_ids: deviceIds }),
  bulkDownloadActivate: (deviceIds: string[]) =>
    api.post('/firmware/bulk-download-activate', { device_ids: deviceIds }),
  bulkActivateAlternate: (deviceIds: string[]) =>
    api.post('/firmware/bulk-activate-alternate', { device_ids: deviceIds }),
}

// Timezones API
export const timezonesApi = {
  list: () => api.get('/timezones'),
  get: (id: string) => api.get(`/timezones/${id}`),
  create: (data: any) => api.post('/timezones', data),
  update: (id: string, data: any) => api.patch(`/timezones/${id}`, data),
  delete: (id: string) => api.delete(`/timezones/${id}`),
}

// Sessions API
export const sessionsApi = {
  list: () => api.get('/sessions'),
  get: (id: string) => api.get(`/sessions/${id}`),
  terminate: (sessionId: string) => api.delete(`/sessions/${sessionId}`),
}

// Config Backup API
export const configBackupApi = {
  create: (deviceId: string, configType?: string) =>
    api.post(`/config-backups/devices/${deviceId}/config-backup`, null, {
      params: configType ? { config_type: configType } : undefined,
    }),
  list: (deviceId: string) =>
    api.get(`/config-backups/devices/${deviceId}/config-backups`),
  getContent: (backupId: string) =>
    api.get(`/config-backups/config-backups/${backupId}/content`),
  restore: (backupId: string) =>
    api.post(`/config-backups/config-backups/${backupId}/restore`),
  delete: (backupId: string) =>
    api.delete(`/config-backups/config-backups/${backupId}`),
}

// Subscriber Import API
export const subscriberImportApi = {
  upload: (formData: FormData) =>
    api.post('/subscriber-import/import', formData),
}

// Splynx Integration API
export const splynxApi = {
  getStatus: () => api.get('/splynx/status'),
  testConnection: () => api.post('/splynx/test-connection'),
  getAdmins: () => api.get('/splynx/admins'),
  lookupEndpoint: (endpointId: string) =>
    api.post(`/splynx/lookup/${endpointId}`),
}
