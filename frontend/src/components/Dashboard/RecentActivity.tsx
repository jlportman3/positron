import {
  Card,
  CardHeader,
  CardContent,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
  Box,
  Typography,
} from '@mui/material'
import {
  CheckCircle,
  Error,
  Warning,
  Info,
  PowerSettingsNew,
  Settings,
} from '@mui/icons-material'

interface ActivityEvent {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  message: string
  timestamp: string
  device?: string
}

interface RecentActivityProps {
  events: ActivityEvent[]
}

const getEventIcon = (type: string) => {
  switch (type) {
    case 'success':
      return <CheckCircle sx={{ color: 'success.main' }} />
    case 'error':
      return <Error sx={{ color: 'error.main' }} />
    case 'warning':
      return <Warning sx={{ color: 'warning.main' }} />
    case 'info':
    default:
      return <Info sx={{ color: 'info.main' }} />
  }
}

const getEventColor = (type: string): 'success' | 'error' | 'warning' | 'info' => {
  switch (type) {
    case 'success':
      return 'success'
    case 'error':
      return 'error'
    case 'warning':
      return 'warning'
    case 'info':
    default:
      return 'info'
  }
}

const RecentActivity = ({ events }: RecentActivityProps) => {
  return (
    <Card>
      <CardHeader
        title="Recent Activity"
        titleTypographyProps={{ variant: 'h6' }}
        action={
          <Typography variant="caption" color="text.secondary">
            Last 24 hours
          </Typography>
        }
      />
      <CardContent sx={{ pt: 0 }}>
        {events.length === 0 ? (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <Typography variant="body2" color="text.secondary">
              No recent activity
            </Typography>
          </Box>
        ) : (
          <List sx={{ py: 0 }}>
            {events.map((event, index) => (
              <ListItem
                key={event.id}
                sx={{
                  borderBottom: index < events.length - 1 ? '1px solid' : 'none',
                  borderColor: 'divider',
                  px: 0,
                  py: 1.5,
                }}
              >
                <ListItemIcon sx={{ minWidth: 40 }}>
                  {getEventIcon(event.type)}
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                      <Typography variant="body2">{event.message}</Typography>
                      {event.device && (
                        <Chip label={event.device} size="small" variant="outlined" />
                      )}
                    </Box>
                  }
                  secondary={
                    <Typography variant="caption" color="text.secondary">
                      {event.timestamp}
                    </Typography>
                  }
                />
              </ListItem>
            ))}
          </List>
        )}
      </CardContent>
    </Card>
  )
}

export default RecentActivity
