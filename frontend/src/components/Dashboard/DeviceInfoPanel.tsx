import { Card, CardHeader, CardContent, Box, Typography, Chip, Divider } from '@mui/material'
import { Router as RouterIcon } from '@mui/icons-material'

interface DeviceInfo {
  model: string
  totalPorts: number
  activePorts: number
  firmware: string
  uptime: string
  location?: string
}

interface DeviceInfoPanelProps {
  device: DeviceInfo
}

const DeviceInfoPanel = ({ device }: DeviceInfoPanelProps) => {
  return (
    <Card>
      <CardHeader
        title="Primary GAM Device"
        titleTypographyProps={{ variant: 'h6' }}
        action={
          <Chip
            label="Online"
            color="success"
            size="small"
            sx={{ fontWeight: 'bold' }}
          />
        }
      />
      <CardContent>
        {/* Device Image/Icon */}
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            bgcolor: '#f5f5f5',
            borderRadius: 2,
            p: 3,
            mb: 3,
          }}
        >
          <Box
            sx={{
              width: 200,
              height: 150,
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
              alignItems: 'center',
              bgcolor: 'white',
              borderRadius: 1,
              border: '2px solid #e0e0e0',
            }}
          >
            <RouterIcon sx={{ fontSize: 80, color: '#1976d2', mb: 1 }} />
            <Typography variant="h6" sx={{ fontWeight: 'bold', color: '#424242' }}>
              Positron GAM
            </Typography>
          </Box>
        </Box>

        {/* Device Specifications */}
        <Box>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            Device Specifications
          </Typography>
          <Divider sx={{ mb: 2 }} />

          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Typography variant="body2" color="text.secondary">
                Model:
              </Typography>
              <Typography variant="body2" sx={{ fontWeight: 500 }}>
                {device.model}
              </Typography>
            </Box>

            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Typography variant="body2" color="text.secondary">
                Total Ports:
              </Typography>
              <Typography variant="body2" sx={{ fontWeight: 500 }}>
                {device.totalPorts}
              </Typography>
            </Box>

            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Typography variant="body2" color="text.secondary">
                Active Ports:
              </Typography>
              <Typography variant="body2" sx={{ fontWeight: 500, color: 'success.main' }}>
                {device.activePorts} / {device.totalPorts}
              </Typography>
            </Box>

            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Typography variant="body2" color="text.secondary">
                Firmware:
              </Typography>
              <Typography variant="body2" sx={{ fontWeight: 500 }}>
                {device.firmware}
              </Typography>
            </Box>

            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Typography variant="body2" color="text.secondary">
                Uptime:
              </Typography>
              <Typography variant="body2" sx={{ fontWeight: 500 }}>
                {device.uptime}
              </Typography>
            </Box>

            {device.location && (
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="body2" color="text.secondary">
                  Location:
                </Typography>
                <Typography variant="body2" sx={{ fontWeight: 500 }}>
                  {device.location}
                </Typography>
              </Box>
            )}
          </Box>
        </Box>
      </CardContent>
    </Card>
  )
}

export default DeviceInfoPanel
