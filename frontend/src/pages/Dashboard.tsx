import { useQuery } from '@tanstack/react-query'
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  CircularProgress,
  Link,
} from '@mui/material'
import {
  Flag as FlagIcon,
  Description as DocIcon,
  Email as EmailIcon,
} from '@mui/icons-material'
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { dashboardApi, settingsApi } from '../services/api'
import { alarmColors } from '../theme'
import FleetHealth from '../components/FleetHealth'

// Status card - horizontal layout with icon on left
function StatusCard({
  title,
  value,
  subtitle,
  icon,
  valueColor,
}: {
  title: string
  value: string | number
  subtitle: string
  icon: React.ReactNode
  valueColor?: string
}) {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
          {/* Icon on left */}
          <Box sx={{ pt: 0.5 }}>
            {icon}
          </Box>
          {/* Text content on right */}
          <Box sx={{ flex: 1, textAlign: 'right' }}>
            <Typography
              variant="body2"
              sx={{
                color: '#666',
                fontWeight: 500,
                mb: 0.5,
              }}
            >
              {title}
            </Typography>
            <Typography
              variant="h4"
              sx={{
                fontWeight: 600,
                color: valueColor || '#2c2c2c',
                lineHeight: 1,
              }}
            >
              {value}
            </Typography>
          </Box>
        </Box>
        {/* Footer */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            mt: 2,
            pt: 1,
            borderTop: '1px solid #f0f0f0',
          }}
        >
          <Typography variant="caption" sx={{ color: '#999' }}>
            {subtitle}
          </Typography>
        </Box>
      </CardContent>
    </Card>
  )
}

// Legend item for horizontal legend bar
function LegendItem({ color, label }: { color: string; label: string }) {
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
      <Box
        sx={{
          width: 24,
          height: 8,
          backgroundColor: color,
          borderRadius: 0.5,
        }}
      />
      <Typography variant="caption" sx={{ color: '#666', fontSize: '0.7rem' }}>
        {label}
      </Typography>
    </Box>
  )
}

// Chart card with legend bar
function ChartCard({
  title,
  legendItems,
  footerText,
  children,
}: {
  title: string
  legendItems?: { color: string; label: string }[]
  footerText?: string
  children: React.ReactNode
}) {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent sx={{ p: 2 }}>
        <Typography
          variant="subtitle2"
          sx={{
            fontWeight: 600,
            color: '#2c2c2c',
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
            mb: 1,
            textAlign: 'center',
          }}
        >
          {title}
        </Typography>
        {/* Legend bar */}
        {legendItems && legendItems.length > 0 && (
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'center',
              flexWrap: 'wrap',
              gap: 1.5,
              mb: 1,
            }}
          >
            {legendItems.map((item, index) => (
              <LegendItem key={index} color={item.color} label={item.label} />
            ))}
          </Box>
        )}
        {children}
        {/* Footer text */}
        {footerText && (
          <Typography
            variant="caption"
            sx={{
              display: 'block',
              textAlign: 'center',
              color: '#999',
              mt: 1,
              fontSize: '0.7rem',
            }}
          >
            {footerText}
          </Typography>
        )}
      </CardContent>
    </Card>
  )
}

// VM Status display with dots
function VMStatusDisplay({ status }: { status: string }) {
  const isOK = status === 'OK'
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 0.5 }}>
      <Box
        sx={{
          width: 10,
          height: 10,
          borderRadius: '50%',
          backgroundColor: isOK ? '#6bd098' : '#eb5757',
        }}
      />
      <Box
        sx={{
          width: 10,
          height: 10,
          borderRadius: '50%',
          backgroundColor: isOK ? '#6bd098' : '#aaa',
        }}
      />
      <Box
        sx={{
          width: 10,
          height: 10,
          borderRadius: '50%',
          backgroundColor: isOK ? '#6bd098' : '#aaa',
        }}
      />
    </Box>
  )
}

const CHART_COLORS = {
  online: '#6bd098',
  offline: '#eb5757',
  baseline: '#6bd098',
  nonBaseline: '#aaaaaa',
}

export default function Dashboard() {
  const { data: dashboardData, isLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: () => dashboardApi.getData().then((res) => res.data),
    refetchInterval: 30000,
  })

  const { data: apiSetting } = useQuery({
    queryKey: ['setting-api-enabled'],
    queryFn: () => settingsApi.get('api_enabled').then((res) => res.data),
  })

  const apiEnabled = apiSetting?.value !== 'false'

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    )
  }

  const stats = dashboardData?.stats

  // Pie chart data for GAM Status
  const gamStatusData = [
    { name: 'Online', value: stats?.online_devices || 0, color: CHART_COLORS.online },
    { name: 'Offline', value: stats?.offline_devices || 0, color: CHART_COLORS.offline },
  ]

  // Pie chart data for Active Alarms
  const alarmData = [
    { name: 'CR', value: stats?.alarm_critical || 0, color: alarmColors.CR },
    { name: 'MJ', value: stats?.alarm_major || 0, color: alarmColors.MJ },
    { name: 'MN', value: stats?.alarm_minor || 0, color: alarmColors.MN },
    { name: 'NA', value: stats?.alarm_normal || 0, color: alarmColors.NA },
  ].filter(d => d.value > 0)

  // Pie chart data for Endpoint Statuses
  const endpointStatusData = [
    { name: 'Offline', value: stats?.endpoints_offline || 0, color: '#eb5757' },
    { name: 'MJ TCA', value: stats?.endpoints_mj_tca || 0, color: '#f5a623' },
    { name: 'MN TCA', value: stats?.endpoints_mn_tca || 0, color: '#f8e71c' },
    { name: 'Not Configured', value: stats?.endpoints_not_configured || 0, color: '#aaaaaa' },
    { name: 'OK', value: stats?.endpoints_ok || 0, color: '#6bd098' },
  ].filter(d => d.value > 0)

  // Pie chart data for GAM Baseline
  const baselineData = [
    { name: 'Baseline', value: stats?.baseline_devices || stats?.online_devices || 0, color: CHART_COLORS.baseline },
    { name: 'Non-Baseline', value: stats?.non_baseline_devices || 0, color: CHART_COLORS.nonBaseline },
  ]

  // Bar chart data for Subscribers per Bandwidth (from real API data)
  const bandwidthData = dashboardData?.bandwidth_distribution || []

  // Bar chart data for Software Versions (from real API data)
  const versionData = dashboardData?.version_distribution || []

  return (
    <Box>
      {/* Row 1: Status Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={6} sm={3}>
          <StatusCard
            title="Active Critical Alarms"
            value={stats?.alarm_critical || 0}
            subtitle="Current Status"
            icon={<FlagIcon sx={{ color: '#eb5757', fontSize: 40 }} />}
          />
        </Grid>
        <Grid item xs={6} sm={3}>
          <StatusCard
            title="Recent Critical Alarms"
            value={stats?.recent_critical || 0}
            subtitle="Last 24H"
            icon={<DocIcon sx={{ color: '#f5a623', fontSize: 40 }} />}
          />
        </Grid>
        <Grid item xs={6} sm={3}>
          <StatusCard
            title="VM"
            value="OK"
            subtitle="Current Status"
            icon={<VMStatusDisplay status="OK" />}
            valueColor="#6bd098"
          />
        </Grid>
        <Grid item xs={6} sm={3}>
          <StatusCard
            title="Notification"
            value="N/A"
            subtitle="Last 24H"
            icon={<EmailIcon sx={{ color: '#aaa', fontSize: 40 }} />}
          />
        </Grid>
      </Grid>

      {/* Row 2: Pie Charts (2x2 grid) */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <ChartCard
            title="GAM Status"
            legendItems={[
              { color: CHART_COLORS.online, label: 'Online' },
              { color: CHART_COLORS.offline, label: 'Offline' },
            ]}
            footerText={`Online: ${stats?.online_devices || 0} - Offline: ${stats?.offline_devices || 0}`}
          >
            <Box sx={{ height: 150 }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={gamStatusData}
                    cx="50%"
                    cy="50%"
                    innerRadius={35}
                    outerRadius={55}
                    dataKey="value"
                  >
                    {gamStatusData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </Box>
          </ChartCard>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <ChartCard
            title="Active Alarms"
            legendItems={[
              { color: alarmColors.CR, label: 'CR' },
              { color: alarmColors.MJ, label: 'MJ' },
              { color: alarmColors.MN, label: 'MN' },
              { color: alarmColors.NA, label: 'NA' },
            ]}
            footerText={`CR: ${stats?.alarm_critical || 0} - MJ: ${stats?.alarm_major || 0} - MN: ${stats?.alarm_minor || 0} - NA: ${stats?.alarm_normal || 0}`}
          >
            <Box sx={{ height: 150 }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={alarmData.length > 0 ? alarmData : [{ name: 'None', value: 1, color: '#e0e0e0' }]}
                    cx="50%"
                    cy="50%"
                    innerRadius={35}
                    outerRadius={55}
                    dataKey="value"
                  >
                    {(alarmData.length > 0 ? alarmData : [{ name: 'None', value: 1, color: '#e0e0e0' }]).map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </Box>
          </ChartCard>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <ChartCard
            title="Endpoints Statuses"
            legendItems={[
              { color: '#eb5757', label: 'Offline' },
              { color: '#f5a623', label: 'MJ TCA' },
              { color: '#f8e71c', label: 'MN TCA' },
              { color: '#aaaaaa', label: 'Not Configured' },
              { color: '#6bd098', label: 'OK' },
            ]}
            footerText={`Offline: ${stats?.endpoints_offline || 0} - MJ TCA: ${stats?.endpoints_mj_tca || 0} - MN TCA: ${stats?.endpoints_mn_tca || 0} - Not Configured: ${stats?.endpoints_not_configured || 0} - OK: ${stats?.endpoints_ok || 0}`}
          >
            <Box sx={{ height: 150 }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={endpointStatusData}
                    cx="50%"
                    cy="50%"
                    innerRadius={35}
                    outerRadius={55}
                    dataKey="value"
                  >
                    {endpointStatusData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </Box>
          </ChartCard>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <ChartCard
            title="GAM Baseline"
            legendItems={[
              { color: CHART_COLORS.baseline, label: 'Baseline' },
              { color: CHART_COLORS.nonBaseline, label: 'Non-Baseline' },
            ]}
            footerText={`Baseline: ${stats?.baseline_devices || stats?.online_devices || 0} - Non-Baseline: ${stats?.non_baseline_devices || 0}`}
          >
            <Box sx={{ height: 150 }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={baselineData}
                    cx="50%"
                    cy="50%"
                    innerRadius={35}
                    outerRadius={55}
                    dataKey="value"
                  >
                    {baselineData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </Box>
          </ChartCard>
        </Grid>
      </Grid>

      {/* Row 3: Bar Charts */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} md={6}>
          <ChartCard title="Subscribers per Bandwidth Profiles">
            <Box sx={{ height: 220 }}>
              {bandwidthData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={bandwidthData} layout="vertical">
                    <XAxis type="number" tick={{ fontSize: 11 }} />
                    <YAxis dataKey="name" type="category" width={100} tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Bar dataKey="count" fill="#51bcda" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                  <Typography color="text.secondary">No bandwidth profiles configured</Typography>
                </Box>
              )}
            </Box>
          </ChartCard>
        </Grid>
        <Grid item xs={12} md={6}>
          <ChartCard title="Software Versions">
            <Box sx={{ height: 220 }}>
              {versionData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={versionData} layout="vertical">
                    <XAxis type="number" tick={{ fontSize: 11 }} />
                    <YAxis dataKey="name" type="category" width={100} tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Bar dataKey="count" fill="#6bd098" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                  <Typography color="text.secondary">No devices registered</Typography>
                </Box>
              )}
            </Box>
          </ChartCard>
        </Grid>
      </Grid>

      {/* Row 4: Fleet Health */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} md={4}>
          <FleetHealth />
        </Grid>
      </Grid>

      {/* Footer */}
      <Box
        sx={{
          textAlign: 'center',
          py: 2,
          borderTop: '1px solid #e0e0e0',
          color: '#999',
          fontSize: '0.75rem',
        }}
      >
        Alamo GAM 1.0.0 - © 2026 Alamo Broadband Inc. All rights reserved
        {apiEnabled && (
          <>
            <Box component="span" sx={{ mx: 1 }}>•</Box>
            <Link href="/api/docs" target="_blank" sx={{ color: '#51bcda', textDecoration: 'none' }}>
              API Docs
            </Link>
          </>
        )}
      </Box>
    </Box>
  )
}
