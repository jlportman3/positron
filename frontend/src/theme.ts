import { createTheme } from '@mui/material/styles'

// Color palette
const colors = {
  primary: '#51bcda',        // Cyan/teal - main action color
  primaryDark: '#3a9fc0',    // Darker teal for hover
  secondary: '#6bd098',      // Green for success states
  background: '#f4f3ef',     // Light gray page background
  paper: '#ffffff',          // White cards
  sidebar: '#2c3e50',        // Dark sidebar
  sidebarText: '#ffffff',
  sidebarTextMuted: 'rgba(255,255,255,0.6)',
  text: '#2c2c2c',           // Dark gray text
  textSecondary: '#6c757d',
  border: '#e0e0e0',
  // Alarm severity colors
  alarmCritical: '#eb5757',  // Red - CR
  alarmMajor: '#f5a623',     // Orange - MJ
  alarmMinor: '#f8e71c',     // Yellow - MN
  alarmNA: '#7ed3f7',        // Light blue - NA
  // Status colors
  online: '#6bd098',         // Green
  offline: '#aaaaaa',        // Gray
  warning: '#ffa534',        // Orange
  error: '#eb5757',          // Red
}

export const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: colors.primary,
      dark: colors.primaryDark,
      contrastText: '#ffffff',
    },
    secondary: {
      main: colors.secondary,
    },
    background: {
      default: colors.background,
      paper: colors.paper,
    },
    text: {
      primary: colors.text,
      secondary: colors.textSecondary,
    },
    success: {
      main: colors.online,
    },
    warning: {
      main: colors.warning,
    },
    error: {
      main: colors.error,
    },
    divider: colors.border,
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 500,
      fontSize: '1.5rem',
      color: colors.text,
    },
    h5: {
      fontWeight: 500,
      color: colors.text,
    },
    h6: {
      fontWeight: 500,
      color: colors.text,
    },
  },
  shape: {
    borderRadius: 4,
  },
  components: {
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundColor: colors.sidebar,
          color: colors.sidebarText,
          width: 200,
          borderRight: 'none',
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: '#ffffff',
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
          color: colors.text,
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 4,
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
          border: `1px solid ${colors.border}`,
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 4,
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'uppercase',
          borderRadius: 4,
          fontWeight: 500,
          fontSize: '0.8125rem',
        },
        contained: {
          boxShadow: 'none',
          '&:hover': {
            boxShadow: '0 2px 4px rgba(0,0,0,0.15)',
          },
        },
        outlined: {
          borderColor: colors.primary,
          '&:hover': {
            backgroundColor: 'rgba(81, 188, 218, 0.08)',
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 4,
          fontWeight: 500,
        },
        sizeSmall: {
          height: 22,
          fontSize: '0.75rem',
        },
      },
    },
    MuiTableHead: {
      styleOverrides: {
        root: {
          backgroundColor: '#f5f5f5',
          '& .MuiTableCell-head': {
            fontWeight: 600,
            color: colors.text,
            borderBottom: `1px solid ${colors.border}`,
            fontSize: '0.8125rem',
            padding: '12px 16px',
          },
        },
      },
    },
    MuiTableRow: {
      styleOverrides: {
        root: {
          '&:hover': {
            backgroundColor: 'rgba(81, 188, 218, 0.04)',
          },
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          borderBottom: `1px solid ${colors.border}`,
          padding: '10px 16px',
          fontSize: '0.875rem',
        },
      },
    },
    MuiListItemButton: {
      styleOverrides: {
        root: {
          borderRadius: 0,
          paddingLeft: 24,
          paddingRight: 16,
          '&.Mui-selected': {
            backgroundColor: 'rgba(81, 188, 218, 0.2)',
            borderLeft: `3px solid ${colors.primary}`,
            paddingLeft: 21,
            '&:hover': {
              backgroundColor: 'rgba(81, 188, 218, 0.3)',
            },
          },
          '&:hover': {
            backgroundColor: 'rgba(255, 255, 255, 0.08)',
          },
        },
      },
    },
    MuiListItemIcon: {
      styleOverrides: {
        root: {
          color: 'inherit',
          minWidth: 32,
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 4,
          },
        },
      },
    },
    MuiSelect: {
      styleOverrides: {
        root: {
          borderRadius: 4,
        },
      },
    },
    MuiTab: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 500,
          fontSize: '0.875rem',
          minWidth: 80,
        },
      },
    },
    MuiTabs: {
      styleOverrides: {
        indicator: {
          backgroundColor: colors.primary,
        },
      },
    },
  },
})

// Export alarm colors for use in components
export const alarmColors = {
  CR: colors.alarmCritical,
  MJ: colors.alarmMajor,
  MN: colors.alarmMinor,
  NA: colors.alarmNA,
}

export const statusColors = {
  online: colors.online,
  offline: colors.offline,
  warning: colors.warning,
  error: colors.error,
}
