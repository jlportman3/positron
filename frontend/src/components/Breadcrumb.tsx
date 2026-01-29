import { Box, Typography } from '@mui/material'
import { Home as HomeIcon } from '@mui/icons-material'
import { useNavigate } from 'react-router-dom'

interface BreadcrumbProps {
  current: string
  items?: { label: string; path: string }[]
}

export default function Breadcrumb({ current, items }: BreadcrumbProps) {
  const navigate = useNavigate()

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
      <HomeIcon
        sx={{
          fontSize: 18,
          color: '#51bcda',
          cursor: 'pointer',
          '&:hover': { color: '#3a9fc0' },
        }}
        onClick={() => navigate('/')}
      />
      {items?.map((item) => (
        <Box key={item.path} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography sx={{ color: '#999', fontSize: '0.875rem' }}>/</Typography>
          <Typography
            sx={{
              color: '#51bcda',
              fontSize: '0.875rem',
              cursor: 'pointer',
              '&:hover': { color: '#3a9fc0' },
            }}
            onClick={() => navigate(item.path)}
          >
            {item.label}
          </Typography>
        </Box>
      ))}
      <Typography sx={{ color: '#999', fontSize: '0.875rem' }}>/</Typography>
      <Typography sx={{ color: '#2c2c2c', fontSize: '0.875rem', fontWeight: 500 }}>
        {current}
      </Typography>
    </Box>
  )
}
