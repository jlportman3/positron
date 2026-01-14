import { useQuery } from '@tanstack/react-query'
import { Grid, Box, CircularProgress, Typography } from '@mui/material'
import api from '../../services/api'
import type { GAMDevice, Subscriber } from '../../types'

// Import dashboard components
import StatisticsCards from './StatisticsCards'
import NetworkStatusChart from './NetworkStatusChart'
import DeviceInfoPanel from './DeviceInfoPanel'
import RecentActivity from './RecentActivity'

export default function Dashboard() {
  const { data: devices, isLoading: devicesLoading } = useQuery<GAMDevice[]>({
    queryKey: ['devices'],
    queryFn: async () => {
      const response = await api.get('/gam/devices')
      return response.data
    },
  })

  const { data: subscribers, isLoading: subscribersLoading } = useQuery<Subscriber[]>({
    queryKey: ['subscribers'],
    queryFn: async () => {
      const response = await api.get('/subscribers')
      return response.data
    },
  })

  if (devicesLoading || subscribersLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    )
  }

  // Calculate statistics
  const activeDevices = devices?.filter((d) => d.status === 'online').length || 0
  const totalDevices = devices?.length || 0
  const activeSubscribers = subscribers?.filter((s) => s.status === 'active').length || 0
  const totalSubscribers = subscribers?.length || 0
  const portFailures = devices?.reduce((acc, device) => {
    // Count ports with errors (this would come from real port data)
    return acc + 0 // Placeholder - update with real port failure logic
  }, 0) || 0
  const lowSignal = 0 // Placeholder - would come from SNMP/monitoring data

  // Statistics for cards
  const stats = {
    loginRequired: totalDevices - activeDevices, // Devices offline/requiring attention
    activeDevices: activeSubscribers,
    portFailures: portFailures,
    lowSignal: lowSignal,
  }

  // Generate network status chart data (last 24 hours, hourly)
  const networkData = Array.from({ length: 24 }, (_, i) => {
    const hour = i.toString().padStart(2, '0') + ':00'
    // In production, this would come from actual monitoring data
    const baseOnline = activeDevices
    const variation = Math.floor(Math.random() * 3) - 1
    const online = Math.max(0, baseOnline + variation)
    const offline = totalDevices - online

    return {
      time: hour,
      online: online,
      offline: offline,
      total: totalDevices,
    }
  })

  // Get primary device info (first device or create mock data)
  const primaryDevice = devices && devices.length > 0 ? devices[0] : null
  const deviceInfo = {
    model: primaryDevice?.model || 'GAM-24-M',
    totalPorts: primaryDevice?.port_count || 24,
    activePorts: primaryDevice?.active_subscribers || 0,
    firmware: 'v1.8.2', // Would come from device data
    uptime: '15 days, 7 hours', // Would come from device data
    location: 'Primary Headend', // Would come from device data
  }

  // Generate recent activity events
  const recentEvents = [
    {
      id: '1',
      type: 'success' as const,
      message: 'New subscriber activated',
      timestamp: '2 minutes ago',
      device: 'GAM-24-M #1',
    },
    {
      id: '2',
      type: 'info' as const,
      message: 'Firmware update available',
      timestamp: '15 minutes ago',
      device: 'GAM-12-C #3',
    },
    {
      id: '3',
      type: 'warning' as const,
      message: 'Signal quality below threshold',
      timestamp: '1 hour ago',
      device: 'GAM-24-M #2',
    },
    {
      id: '4',
      type: 'success' as const,
      message: 'Device came online',
      timestamp: '3 hours ago',
      device: 'GAM-12-M #5',
    },
    {
      id: '5',
      type: 'info' as const,
      message: 'Scheduled maintenance completed',
      timestamp: '5 hours ago',
    },
  ]

  return (
    <Box>
      {/* Page Title */}
      <Typography variant="h5" sx={{ mb: 3, fontWeight: 500 }}>
        Dashboard Overview
      </Typography>

      {/* Statistics Cards */}
      <Box sx={{ mb: 3 }}>
        <StatisticsCards stats={stats} />
      </Box>

      {/* Main Content Grid */}
      <Grid container spacing={3}>
        {/* Left Column - Network Status Chart */}
        <Grid item xs={12} md={8}>
          <NetworkStatusChart data={networkData} />
        </Grid>

        {/* Right Column - Device Info */}
        <Grid item xs={12} md={4}>
          <DeviceInfoPanel device={deviceInfo} />
        </Grid>

        {/* Bottom Row - Recent Activity */}
        <Grid item xs={12}>
          <RecentActivity events={recentEvents} />
        </Grid>
      </Grid>
    </Box>
  )
}
