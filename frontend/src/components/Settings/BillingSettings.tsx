import { Box, Typography, TextField, Button, Divider, MenuItem, FormControlLabel, Switch } from '@mui/material'

const BillingSettings = () => {
  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Billing Integration
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Configure integration with Sonar or Splynx billing systems.
      </Typography>

      <TextField
        select
        label="Billing System"
        fullWidth
        defaultValue="none"
        sx={{ mb: 3 }}
      >
        <MenuItem value="none">None</MenuItem>
        <MenuItem value="sonar">Sonar</MenuItem>
        <MenuItem value="splynx">Splynx</MenuItem>
      </TextField>

      <Divider sx={{ my: 3 }} />

      <Typography variant="subtitle2" gutterBottom>
        Sonar Configuration
      </Typography>
      <TextField
        label="Sonar API URL"
        fullWidth
        placeholder="https://your-instance.sonar.software"
        sx={{ mb: 2, mt: 1 }}
      />
      <TextField
        label="API Key"
        fullWidth
        type="password"
        sx={{ mb: 2 }}
      />
      <FormControlLabel
        control={<Switch />}
        label="Enable automatic synchronization"
        sx={{ mb: 2 }}
      />

      <Divider sx={{ my: 3 }} />

      <Typography variant="subtitle2" gutterBottom>
        Splynx Configuration
      </Typography>
      <TextField
        label="Splynx API URL"
        fullWidth
        placeholder="https://your-instance.splynx.com"
        sx={{ mb: 2, mt: 1 }}
      />
      <TextField
        label="API Key"
        fullWidth
        type="password"
        sx={{ mb: 2 }}
      />
      <TextField
        label="API Secret"
        fullWidth
        type="password"
        sx={{ mb: 2 }}
      />
      <FormControlLabel
        control={<Switch />}
        label="Enable automatic synchronization"
        sx={{ mb: 2 }}
      />

      <Box sx={{ mt: 3 }}>
        <Button variant="contained" sx={{ mr: 2 }}>Save Configuration</Button>
        <Button variant="outlined">Test Connection</Button>
      </Box>
    </Box>
  )
}

export default BillingSettings
