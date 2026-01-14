import { useState, useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import {
  Box,
  Paper,
  Typography,
} from '@mui/material'
import {
  LocationOn,
  AccountTree,
  Router,
  Speed,
  Devices,
  Settings as SettingsIcon,
  Payment,
} from '@mui/icons-material'

// Import setting sections
import ZonesSettings from './ZonesSettings'
import ODBSettings from './ODBSettings'
import GAMTypesSettings from './GAMTypesSettings'
import SpeedProfilesSettings from './SpeedProfilesSettings'
import GAMDevicesSettings from './GAMDevicesSettings'
import GeneralSettings from './GeneralSettings'
import BillingSettings from './BillingSettings'

const SettingsPage = () => {
  const location = useLocation()
  const [currentTab, setCurrentTab] = useState(0)

  // Read tab from URL query parameter
  useEffect(() => {
    const params = new URLSearchParams(location.search)
    const tabParam = params.get('tab')
    if (tabParam !== null) {
      const tabIndex = parseInt(tabParam, 10)
      if (!isNaN(tabIndex) && tabIndex >= 0 && tabIndex < 6) {
        setCurrentTab(tabIndex)
      }
    }
  }, [location.search])

  const settingsSections = [
    { label: 'Zones', icon: <LocationOn />, component: <ZonesSettings /> },
    { label: 'ODB (Splitters)', icon: <AccountTree />, component: <ODBSettings /> },
    { label: 'GAM Types', icon: <Router />, component: <GAMTypesSettings /> },
    { label: 'Speed Profiles', icon: <Speed />, component: <SpeedProfilesSettings /> },
    { label: 'General', icon: <SettingsIcon />, component: <GeneralSettings /> },
    { label: 'Billing', icon: <Payment />, component: <BillingSettings /> },
  ]

  const currentSection = settingsSections[currentTab]

  return (
    <Box sx={{ width: '100%' }}>
      <Typography variant="h5" sx={{ mb: 3, fontWeight: 500 }}>
        Settings - {currentSection.label}
      </Typography>

      <Paper sx={{ width: '100%', p: 3 }}>
        {currentSection.component}
      </Paper>
    </Box>
  )
}

export default SettingsPage
