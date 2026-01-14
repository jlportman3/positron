import { Box, Typography, Alert } from '@mui/material'

const ODBSettings = () => {
  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        ODB (Optical Distribution Box / Splitters)
      </Typography>
      <Alert severity="info" sx={{ mt: 2 }}>
        ODB management allows you to define splitter configurations and optical distribution points.
        This feature will help track physical network topology.
      </Alert>
      <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
        Coming soon: Manage splitters, fiber distribution, and physical network topology.
      </Typography>
    </Box>
  )
}

export default ODBSettings
