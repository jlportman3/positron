import { useState } from 'react'
import {
  Box,
  Tabs,
  Tab,
  IconButton,
  Avatar,
  Menu,
  MenuItem,
  Typography,
  ListItemIcon,
  ListItemText,
} from '@mui/material'
import {
  Dashboard as DashboardIcon,
  Settings as SettingsIcon,
  Router as RouterIcon,
  Assessment as AssessmentIcon,
  Build as BuildIcon,
  Assignment as AssignmentIcon,
  AccountCircle,
  LocationOn,
  AccountTree,
  Speed,
  Business,
  Payment,
  DeviceUnknown,
} from '@mui/icons-material'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'

const TopNavigation = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout } = useAuthStore()
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)
  const [settingsAnchorEl, setSettingsAnchorEl] = useState<null | HTMLElement>(null)

  const menuItems = [
    { label: 'Dashboard', path: '/', icon: <DashboardIcon /> },
    { label: 'Unconfigured', path: '/unconfigured', icon: <DeviceUnknown /> },
    { label: 'Configured', path: '/configured', icon: <SettingsIcon /> },
    { label: 'Subscribers', path: '/subscribers', icon: <AssignmentIcon /> },
    { label: 'Reports', path: '/reports', icon: <AssessmentIcon /> },
    { label: 'Provisioning', path: '/provisioning', icon: <BuildIcon /> },
  ]

  const settingsMenuItems = [
    { label: 'GAM Devices', path: '/devices', icon: <RouterIcon /> },
    { label: 'Zones', path: '/settings?tab=0', icon: <LocationOn /> },
    { label: 'ODB (Splitters)', path: '/settings?tab=1', icon: <AccountTree /> },
    { label: 'GAM Types', path: '/settings?tab=2', icon: <RouterIcon /> },
    { label: 'Speed Profiles', path: '/settings?tab=3', icon: <Speed /> },
    { label: 'General', path: '/settings?tab=4', icon: <Business /> },
    { label: 'Billing', path: '/settings?tab=5', icon: <Payment /> },
  ]

  const getCurrentTab = () => {
    const currentPath = location.pathname
    const index = menuItems.findIndex((item) => item.path === currentPath)
    return index >= 0 ? index : false
  }

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    navigate(menuItems[newValue].path)
  }

  const handleSettingsMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setSettingsAnchorEl(event.currentTarget)
  }

  const handleSettingsMenuClose = () => {
    setSettingsAnchorEl(null)
  }

  const handleSettingsNavigate = (path: string) => {
    navigate(path)
    handleSettingsMenuClose()
  }

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget)
  }

  const handleMenuClose = () => {
    setAnchorEl(null)
  }

  const handleLogout = () => {
    logout()
    handleMenuClose()
    navigate('/login')
  }

  return (
    <Box
      sx={{
        bgcolor: 'background.paper',
        borderBottom: 1,
        borderColor: 'divider',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        px: 2,
      }}
    >
      <Tabs
        value={getCurrentTab()}
        onChange={handleTabChange}
        variant="scrollable"
        scrollButtons="auto"
        sx={{ flexGrow: 1 }}
      >
        {menuItems.map((item) => (
          <Tab
            key={item.path}
            label={item.label}
            icon={item.icon}
            iconPosition="start"
            sx={{
              minHeight: 64,
              textTransform: 'none',
              fontSize: '0.95rem',
            }}
          />
        ))}
      </Tabs>

      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, ml: 2 }}>
        {/* Settings Menu Button */}
        <Box
          onClick={handleSettingsMenuOpen}
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 0.5,
            cursor: 'pointer',
            px: 1.5,
            py: 0.5,
            borderRadius: 1,
            '&:hover': {
              bgcolor: 'action.hover',
            },
          }}
        >
          <SettingsIcon fontSize="small" />
          <Typography variant="body2">Settings</Typography>
        </Box>

        <Menu
          anchorEl={settingsAnchorEl}
          open={Boolean(settingsAnchorEl)}
          onClose={handleSettingsMenuClose}
          transformOrigin={{ horizontal: 'right', vertical: 'top' }}
          anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
          PaperProps={{
            sx: { minWidth: 200 }
          }}
        >
          {settingsMenuItems.map((item) => (
            <MenuItem key={item.path} onClick={() => handleSettingsNavigate(item.path)}>
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText>{item.label}</ListItemText>
            </MenuItem>
          ))}
        </Menu>

        {/* User Menu */}
        <Typography variant="body2" sx={{ display: { xs: 'none', md: 'block' } }}>
          {user?.username}
        </Typography>
        <IconButton onClick={handleMenuOpen} size="small">
          <Avatar sx={{ width: 32, height: 32 }}>
            <AccountCircle />
          </Avatar>
        </IconButton>

        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={handleMenuClose}
          transformOrigin={{ horizontal: 'right', vertical: 'top' }}
          anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
        >
          <MenuItem disabled>
            <Typography variant="body2">{user?.email}</Typography>
          </MenuItem>
          <MenuItem onClick={handleLogout}>Logout</MenuItem>
        </Menu>
      </Box>
    </Box>
  )
}

export default TopNavigation
