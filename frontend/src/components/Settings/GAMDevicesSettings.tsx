import { Box, Typography, Alert } from '@mui/material'
import { Link } from 'react-router-dom'

const GAMDevicesSettings = () => {
  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        GAM Devices Management
      </Typography>
      <Alert severity="info" sx={{ mt: 2 }}>
        To manage GAM devices, please use the <Link to="/devices" style={{ color: 'inherit', fontWeight: 'bold' }}>GAM Devices</Link> page.
      </Alert>
      <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
        You can add, configure, and monitor GAM devices from the dedicated Devices section.
      </Typography>
    </Box>
  )
}

export default GAMDevicesSettings
