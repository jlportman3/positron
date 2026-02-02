import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  Box,
  Drawer,
  AppBar,
  Toolbar,
  List,
  Typography,
  Divider,
  IconButton,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Collapse,
} from '@mui/material'
import {
  Menu as MenuIcon,
  ShowChart as MonitoringIcon,
  Groups as ServicesIcon,
  Devices as DevicesIcon,
  BookmarkBorder as VersionsIcon,
  Business as AdminIcon,
  Logout as LogoutIcon,
  Settings as SettingsIcon,
  ExpandLess,
  ExpandMore,
  SupervisorAccount as UsersHeaderIcon,
} from '@mui/icons-material'
import { useAuthStore } from '../store/authStore'
import { authApi, alarmsApi } from '../services/api'
import { alarmColors } from '../theme'

const drawerWidth = 200

// Sidebar sections
const sidebarSections = [
  {
    title: 'MONITORING',
    icon: <MonitoringIcon fontSize="small" />,
    items: [
      { prefix: 'D', text: 'Dashboard', path: '/' },
      { prefix: 'A', text: 'Alarms', path: '/alarms' },
    ],
  },
  {
    title: 'SERVICES',
    icon: <ServicesIcon fontSize="small" />,
    items: [
      { prefix: 'S', text: 'Subscribers', path: '/subscribers' },
      { prefix: 'B', text: 'Bandwidths', path: '/bandwidths' },
    ],
  },
  {
    title: 'DEVICES',
    icon: <DevicesIcon fontSize="small" />,
    items: [
      { prefix: 'G', text: 'GAM', path: '/devices' },
      { prefix: 'E', text: 'Endpoints', path: '/endpoints' },
      { prefix: 'G', text: 'Groups', path: '/groups' },
      { prefix: 'T', text: 'Timezones', path: '/timezones' },
      { prefix: 'F', text: 'Firmware Versions', path: '/firmware' },
      { prefix: 'U', text: 'Add Version', path: '/firmware/add' },
    ],
  },
  {
    title: 'ALAMOGAM VERSIONS',
    icon: <VersionsIcon fontSize="small" />,
    items: [
      { prefix: 'L', text: 'List', path: '/system-info' },
      { prefix: 'U', text: 'Upload', path: '/system-info?tab=upload' },
      { prefix: 'LI', text: 'Licenses', path: '/system-info?tab=license' },
      { prefix: 'C', text: 'Certificates', path: '/system-info?tab=certificates' },
    ],
  },
  {
    title: 'ADMIN',
    icon: <AdminIcon fontSize="small" />,
    items: [
      { prefix: 'AS', text: 'Active Sessions', path: '/sessions' },
      { prefix: 'L', text: 'Logs', path: '/logs' },
      { prefix: 'U', text: 'Users', path: '/users' },
      { prefix: 'S', text: 'Settings', path: '/settings' },
      { prefix: 'A', text: 'Auditing', path: '/audit-logs' },
      { prefix: 'N', text: 'Notifications', path: '/notifications' },
    ],
  },
]

// Alarm severity badge
function AlarmBadge({ label, count, color }: { label: string; count: number; color: string }) {
  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 0.75,
        px: 1,
      }}
    >
      <Typography
        variant="caption"
        sx={{
          fontWeight: 500,
          color: '#666',
          fontSize: '0.75rem',
        }}
      >
        {label}
      </Typography>
      <Box
        sx={{
          width: 24,
          height: 24,
          borderRadius: '50%',
          backgroundColor: count > 0 ? color : '#e0e0e0',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <Typography
          variant="caption"
          sx={{
            fontWeight: 600,
            color: count > 0 ? '#fff' : '#999',
            fontSize: '0.7rem',
          }}
        >
          {count}
        </Typography>
      </Box>
    </Box>
  )
}

interface LayoutProps {
  children: React.ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const navigate = useNavigate()
  const location = useLocation()
  const [mobileOpen, setMobileOpen] = useState(false)
  const [openSections, setOpenSections] = useState<Record<string, boolean>>({
    MONITORING: true,
    SERVICES: true,
    DEVICES: true,
    'ALAMOGAM VERSIONS': false,
    ADMIN: true,
  })
  const { user, logout } = useAuthStore()

  const handleSectionToggle = (section: string) => {
    setOpenSections((prev) => ({ ...prev, [section]: !prev[section] }))
  }

  // Fetch alarm counts
  const { data: alarmCounts } = useQuery({
    queryKey: ['alarm-counts'],
    queryFn: () => alarmsApi.getCounts().then((res) => res.data),
    refetchInterval: 30000,
  })

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen)
  }

  const handleMenuClick = (path: string) => {
    navigate(path)
    setMobileOpen(false)
  }

  const handleLogout = async () => {
    try {
      await authApi.logout()
    } catch (e) {
      // Ignore errors
    }
    logout()
    navigate('/login')
  }

  const isPathActive = (path: string) => {
    if (path === '/') return location.pathname === '/'
    return location.pathname.startsWith(path)
  }

  const drawer = (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', backgroundColor: '#2c3e50' }}>
      {/* Logo Header */}
      <Box sx={{ p: 2, display: 'flex', alignItems: 'center', gap: 1.5 }}>
        <Box
          sx={{
            width: 32,
            height: 32,
            borderRadius: '50%',
            background: 'linear-gradient(135deg, #eb5757 0%, #f5a623 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Typography sx={{ color: 'white', fontWeight: 700, fontSize: 14 }}>A</Typography>
        </Box>
        <Typography variant="h6" sx={{ fontWeight: 600, color: 'white', fontSize: '1.1rem' }}>
          ALAMO GAM
        </Typography>
      </Box>

      <Divider sx={{ borderColor: 'rgba(255,255,255,0.1)' }} />

      {/* Navigation Sections */}
      <Box sx={{ flexGrow: 1, overflow: 'auto', py: 1 }}>
        {sidebarSections.map((section) => (
          <Box key={section.title}>
            <ListItemButton
              onClick={() => handleSectionToggle(section.title)}
              sx={{
                py: 1,
                px: 2,
                '&:hover': { backgroundColor: 'rgba(255,255,255,0.05)' },
              }}
            >
              <ListItemIcon sx={{ minWidth: 28, color: section.title === 'DEVICES' && openSections[section.title] ? '#51bcda' : 'rgba(255,255,255,0.7)' }}>
                {section.icon}
              </ListItemIcon>
              <ListItemText
                primary={section.title}
                primaryTypographyProps={{
                  fontSize: '0.75rem',
                  fontWeight: 500,
                  color: 'rgba(255,255,255,0.9)',
                  letterSpacing: '0.3px',
                }}
              />
              {section.items.length > 0 && (
                openSections[section.title] ? (
                  <ExpandMore sx={{ fontSize: 18, color: 'rgba(255,255,255,0.5)' }} />
                ) : (
                  <ExpandLess sx={{ fontSize: 18, color: 'rgba(255,255,255,0.5)', transform: 'rotate(180deg)' }} />
                )
              )}
            </ListItemButton>
            <Collapse in={openSections[section.title]} timeout="auto" unmountOnExit>
              <List disablePadding>
                {section.items.map((item) => (
                  <ListItem key={item.path + item.text} disablePadding>
                    <ListItemButton
                      selected={isPathActive(item.path)}
                      onClick={() => handleMenuClick(item.path)}
                      sx={{
                        py: 0.75,
                        pl: 3,
                        borderLeft: isPathActive(item.path) ? '3px solid #51bcda' : '3px solid transparent',
                      }}
                    >
                      <Typography
                        sx={{
                          color: 'rgba(255,255,255,0.5)',
                          fontSize: '0.7rem',
                          fontWeight: 500,
                          width: 24,
                          mr: 1,
                        }}
                      >
                        {item.prefix}
                      </Typography>
                      <ListItemText
                        primary={item.text}
                        primaryTypographyProps={{
                          fontSize: '0.8rem',
                          color: isPathActive(item.path) ? '#51bcda' : 'rgba(255,255,255,0.85)',
                        }}
                      />
                    </ListItemButton>
                  </ListItem>
                ))}
              </List>
            </Collapse>
          </Box>
        ))}
      </Box>

      {/* User info + settings + logout */}
      <Divider sx={{ borderColor: 'rgba(255,255,255,0.1)' }} />
      <Box sx={{ px: 2, py: 1.5 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box
            onClick={() => navigate('/my-settings')}
            sx={{ display: 'flex', alignItems: 'center', gap: 1, cursor: 'pointer', '&:hover .gear-icon': { color: '#51bcda' } }}
          >
            <SettingsIcon className="gear-icon" sx={{ fontSize: 18, color: 'rgba(255,255,255,0.5)', transition: 'color 0.2s' }} />
            <Box>
              <Typography sx={{ color: '#51bcda', fontSize: '0.8rem', fontWeight: 600, lineHeight: 1.2 }}>
                {user?.username || 'admin'}
              </Typography>
              <Typography sx={{ color: 'rgba(255,255,255,0.5)', fontSize: '0.65rem', lineHeight: 1.2 }}>
                {user?.privilege_name || 'Master'}
              </Typography>
            </Box>
          </Box>
          <IconButton onClick={handleLogout} size="small" sx={{ color: 'rgba(255,255,255,0.6)', '&:hover': { color: '#eb5757' } }}>
            <LogoutIcon fontSize="small" />
          </IconButton>
        </Box>
      </Box>
    </Box>
  )

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar
        position="fixed"
        sx={{
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          ml: { sm: `${drawerWidth}px` },
        }}
      >
        <Toolbar sx={{ justifyContent: 'space-between' }}>
          <IconButton
            color="inherit"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { sm: 'none' } }}
          >
            <MenuIcon />
          </IconButton>

          {/* Left side - User icons */}
          <Box sx={{ display: 'flex', gap: 1 }}>
            <IconButton
              size="small"
              sx={{
                backgroundColor: '#f5a623',
                color: 'white',
                width: 32,
                height: 32,
                '&:hover': { backgroundColor: '#e09000' },
              }}
            >
              <UsersHeaderIcon sx={{ fontSize: 18 }} />
            </IconButton>
            <IconButton
              size="small"
              sx={{
                backgroundColor: '#51bcda',
                color: 'white',
                width: 32,
                height: 32,
                '&:hover': { backgroundColor: '#3a9fc0' },
              }}
            >
              <UsersHeaderIcon sx={{ fontSize: 18 }} />
            </IconButton>
          </Box>

          {/* Right side - Alarm badges */}
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            <AlarmBadge label="CR" count={alarmCounts?.critical || 0} color={alarmColors.CR} />
            <AlarmBadge label="MJ" count={alarmCounts?.major || 0} color={alarmColors.MJ} />
            <AlarmBadge label="MN" count={alarmCounts?.minor || 0} color={alarmColors.MN} />
            <AlarmBadge label="NA" count={alarmCounts?.normal || 0} color={alarmColors.NA} />
          </Box>
        </Toolbar>
      </AppBar>

      <Box
        component="nav"
        sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
      >
        {/* Mobile drawer */}
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{ keepMounted: true }}
          sx={{
            display: { xs: 'block', sm: 'none' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: drawerWidth,
            },
          }}
        >
          {drawer}
        </Drawer>
        {/* Desktop drawer */}
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: drawerWidth,
            },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          mt: 8,
          backgroundColor: '#f4f3ef',
          minHeight: '100vh',
        }}
      >
        {children}
      </Box>
    </Box>
  )
}
