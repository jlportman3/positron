import { Grid, Card, CardContent, Typography, Box } from '@mui/material'
import {
  ErrorOutline,
  CheckCircleOutline,
  Cancel,
  Warning,
} from '@mui/icons-material'

interface StatisticCardProps {
  title: string
  value: number
  color: string
  icon: React.ReactNode
  footer?: string
}

const StatisticCard = ({ title, value, color, icon, footer }: StatisticCardProps) => {
  return (
    <Card
      sx={{
        background: color,
        color: 'white',
        height: '100%',
        minHeight: 140,
      }}
    >
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Box>
            <Typography variant="h6" sx={{ fontWeight: 500, mb: 2 }}>
              {title}
            </Typography>
            <Typography variant="h2" sx={{ fontWeight: 'bold', mb: 1 }}>
              {value}
            </Typography>
            {footer && (
              <Typography variant="caption" sx={{ opacity: 0.9 }}>
                {footer}
              </Typography>
            )}
          </Box>
          <Box
            sx={{
              opacity: 0.3,
              fontSize: '3rem',
            }}
          >
            {icon}
          </Box>
        </Box>
      </CardContent>
    </Card>
  )
}

interface DashboardStats {
  loginRequired: number
  activeDevices: number
  portFailures: number
  lowSignal: number
}

interface StatisticsCardsProps {
  stats: DashboardStats
}

const StatisticsCards = ({ stats }: StatisticsCardsProps) => {
  return (
    <Grid container spacing={3}>
      <Grid item xs={12} sm={6} md={3}>
        <StatisticCard
          title="Login Necessary"
          value={stats.loginRequired}
          color="linear-gradient(135deg, #1976d2 0%, #2196f3 100%)"
          icon={<ErrorOutline sx={{ fontSize: 'inherit' }} />}
          footer="Devices requiring attention"
        />
      </Grid>

      <Grid item xs={12} sm={6} md={3}>
        <StatisticCard
          title="Total Activated"
          value={stats.activeDevices}
          color="linear-gradient(135deg, #2e7d32 0%, #4caf50 100%)"
          icon={<CheckCircleOutline sx={{ fontSize: 'inherit' }} />}
          footer="Active subscribers"
        />
      </Grid>

      <Grid item xs={12} sm={6} md={3}>
        <StatisticCard
          title="Port Failures"
          value={stats.portFailures}
          color="linear-gradient(135deg, #424242 0%, #616161 100%)"
          icon={<Cancel sx={{ fontSize: 'inherit' }} />}
          footer="Ports with issues"
        />
      </Grid>

      <Grid item xs={12} sm={6} md={3}>
        <StatisticCard
          title="Low Signal"
          value={stats.lowSignal}
          color="linear-gradient(135deg, #f57c00 0%, #ff9800 100%)"
          icon={<Warning sx={{ fontSize: 'inherit' }} />}
          footer="Signal warnings"
        />
      </Grid>
    </Grid>
  )
}

export default StatisticsCards
