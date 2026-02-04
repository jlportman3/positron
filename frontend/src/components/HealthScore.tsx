import { Box, Chip, LinearProgress, Tooltip, Typography } from '@mui/material';

interface HealthScoreProps {
  score: number;
  status: string;
  showBar?: boolean;
  size?: 'small' | 'medium';
}

const statusColors: Record<string, 'success' | 'warning' | 'error' | 'default'> = {
  healthy: 'success',
  degraded: 'warning',
  critical: 'error',
  offline: 'default',
};

const statusLabels: Record<string, string> = {
  healthy: 'Healthy',
  degraded: 'Degraded',
  critical: 'Critical',
  offline: 'Offline',
};

export default function HealthScore({ score, status, showBar = false, size = 'small' }: HealthScoreProps) {
  const color = statusColors[status] || 'default';
  const label = statusLabels[status] || status;

  if (showBar) {
    return (
      <Box sx={{ width: '100%' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
          <Typography variant="body2" color="text.secondary">
            Health Score
          </Typography>
          <Typography variant="body2" fontWeight="bold">
            {score} - {label}
          </Typography>
        </Box>
        <LinearProgress
          variant="determinate"
          value={score}
          color={color === 'default' ? 'inherit' : color}
          sx={{ height: 8, borderRadius: 1 }}
        />
      </Box>
    );
  }

  return (
    <Tooltip title={`Health Score: ${score}`}>
      <Chip
        label={`${score} ${label}`}
        color={color}
        size={size}
        variant={status === 'offline' ? 'outlined' : 'filled'}
      />
    </Tooltip>
  );
}
