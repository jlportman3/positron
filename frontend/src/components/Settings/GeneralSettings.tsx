import { Box, Typography, TextField, Button, Divider, Switch, FormControlLabel } from '@mui/material'

const GeneralSettings = () => {
  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        General Settings
      </Typography>

      <Box sx={{ mt: 3 }}>
        <Typography variant="subtitle2" gutterBottom>
          System Configuration
        </Typography>
        <TextField
          label="Company Name"
          fullWidth
          defaultValue="Positron GAM Management"
          sx={{ mb: 2, mt: 1 }}
        />
        <TextField
          label="System Email"
          type="email"
          fullWidth
          defaultValue="admin@example.com"
          sx={{ mb: 2 }}
        />
        <FormControlLabel
          control={<Switch defaultChecked />}
          label="Enable email notifications"
        />
      </Box>

      <Divider sx={{ my: 3 }} />

      <Box>
        <Typography variant="subtitle2" gutterBottom>
          Default VLAN Configuration
        </Typography>
        <TextField
          label="Management VLAN"
          type="number"
          defaultValue={4093}
          sx={{ mb: 2, mt: 1, mr: 2, width: 200 }}
        />
        <TextField
          label="Subscriber VLAN Start"
          type="number"
          defaultValue={100}
          sx={{ mb: 2, width: 200 }}
        />
      </Box>

      <Box sx={{ mt: 3 }}>
        <Button variant="contained">Save Settings</Button>
      </Box>
    </Box>
  )
}

export default GeneralSettings
