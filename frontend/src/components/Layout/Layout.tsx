import { ReactNode } from 'react'
import { Box } from '@mui/material'
import TopNavigation from '../Dashboard/TopNavigation'

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      {/* Top Navigation */}
      <TopNavigation />

      {/* Main Content */}
      <Box sx={{ flexGrow: 1, p: 3, bgcolor: '#f5f5f5' }}>
        {children}
      </Box>
    </Box>
  )
}
