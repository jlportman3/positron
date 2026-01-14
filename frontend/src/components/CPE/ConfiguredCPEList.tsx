import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Chip,
  IconButton,
  TextField,
  InputAdornment,
  CircularProgress,
  Alert,
  TablePagination,
  Tooltip,
} from '@mui/material'
import {
  Visibility as ViewIcon,
  Search as SearchIcon,
  Refresh as RefreshIcon,
  CheckCircle,
  Cancel,
  Warning,
} from '@mui/icons-material'
import { useNavigate } from 'react-router-dom'
import api from '../../services/api'

interface ConfiguredCPE {
  id: string
  status: string
  subscriber_name: string
  serial_number: string
  mac_address: string
  onu_type: string
  zone: string
  odb: string
  signal: number
  bandwidth_ratio: string
  vlan: number
  voip: string
  tv: string
  type: string
  auth_date: string
  gam_device_name?: string
  gam_port?: number
}

const ConfiguredCPEList = () => {
  const navigate = useNavigate()
  const [searchTerm, setSearchTerm] = useState('')
  const [page, setPage] = useState(0)
  const [rowsPerPage, setRowsPerPage] = useState(100)

  const { data: response, isLoading, error, refetch } = useQuery({
    queryKey: ['configured-cpe', page, rowsPerPage],
    queryFn: async () => {
      const res = await api.get('/subscribers', {
        params: {
          status: 'active',
          limit: rowsPerPage,
          offset: page * rowsPerPage,
        },
      })
      return {
        data: res.data,
        total: res.headers['x-total-count'] ? parseInt(res.headers['x-total-count']) : res.data.length,
      }
    },
  })

  const configuredDevices = response?.data || []
  const totalCount = response?.total || 0

  const filteredDevices = configuredDevices.filter(
    (device: ConfiguredCPE) =>
      device.subscriber_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      device.serial_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      device.mac_address?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'active':
      case 'online':
        return <CheckCircle sx={{ color: 'success.main', fontSize: 20 }} />
      case 'offline':
      case 'inactive':
        return <Cancel sx={{ color: 'error.main', fontSize: 20 }} />
      case 'warning':
        return <Warning sx={{ color: 'warning.main', fontSize: 20 }} />
      default:
        return <Cancel sx={{ color: 'grey.500', fontSize: 20 }} />
    }
  }

  const getSignalBars = (signal?: number) => {
    if (!signal) return null

    let color = 'success.main'
    if (signal < 25) color = 'error.main'
    else if (signal < 35) color = 'warning.main'

    return (
      <Box sx={{ display: 'flex', gap: 0.3, alignItems: 'flex-end' }}>
        {[1, 2, 3, 4].map((bar) => (
          <Box
            key={bar}
            sx={{
              width: 4,
              height: bar * 3,
              bgcolor: signal >= bar * 10 ? color : 'grey.300',
              borderRadius: 0.5,
            }}
          />
        ))}
      </Box>
    )
  }

  const handleChangePage = (_event: unknown, newPage: number) => {
    setPage(newPage)
  }

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10))
    setPage(0)
  }

  const handleViewDetails = (deviceId: string) => {
    navigate(`/subscribers/${deviceId}`)
  }

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    )
  }

  if (error) {
    return (
      <Box>
        <Typography variant="h5" sx={{ mb: 3, fontWeight: 500 }}>
          Configured CPE Devices
        </Typography>
        <Alert severity="error">
          Failed to load configured CPE devices. Please try again later.
        </Alert>
      </Box>
    )
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h5" sx={{ fontWeight: 500 }}>
            Configured CPE Devices
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
            {totalCount} configured endpoint{totalCount !== 1 ? 's' : ''} displayed
          </Typography>
        </Box>
        <IconButton onClick={() => refetch()} color="primary">
          <RefreshIcon />
        </IconButton>
      </Box>

      <Paper>
        <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
          <TextField
            fullWidth
            size="small"
            placeholder="Search by name, serial number, or MAC address..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
          />
        </Box>

        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Status</TableCell>
                <TableCell>View</TableCell>
                <TableCell>Name</TableCell>
                <TableCell>SN / MAC</TableCell>
                <TableCell>ONU</TableCell>
                <TableCell>Zone</TableCell>
                <TableCell>ODB</TableCell>
                <TableCell>Signal</TableCell>
                <TableCell>B/R</TableCell>
                <TableCell>VLAN</TableCell>
                <TableCell>VoIP</TableCell>
                <TableCell>TV</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Auth date</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredDevices.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={14} align="center" sx={{ py: 8 }}>
                    <Typography variant="body2" color="text.secondary">
                      {searchTerm
                        ? 'No configured devices match your search'
                        : 'No configured CPE devices found'}
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                filteredDevices.map((device: ConfiguredCPE) => (
                  <TableRow key={device.id} hover>
                    <TableCell>
                      <Tooltip title={device.status || 'Unknown'}>
                        {getStatusIcon(device.status)}
                      </Tooltip>
                    </TableCell>
                    <TableCell>
                      <IconButton
                        size="small"
                        onClick={() => handleViewDetails(device.id)}
                        sx={{ bgcolor: 'primary.main', color: 'white', '&:hover': { bgcolor: 'primary.dark' } }}
                      >
                        <ViewIcon fontSize="small" />
                      </IconButton>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">{device.subscriber_name || '-'}</Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                        {device.serial_number || device.mac_address || '-'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
                        {device.onu_type || device.gam_device_name || '-'}
                      </Typography>
                      {device.gam_port && (
                        <Typography variant="caption" color="text.secondary">
                          Port {device.gam_port}
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
                        {device.zone || '-'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
                        {device.odb || 'None'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      {device.signal ? (
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          {getSignalBars(device.signal)}
                        </Box>
                      ) : (
                        <Typography variant="body2">-</Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={device.bandwidth_ratio || '-'}
                        size="small"
                        sx={{ fontSize: '0.7rem', height: 20 }}
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">{device.vlan || '-'}</Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
                        {device.voip || '-'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
                        {device.tv || '-'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={device.type || '-'}
                        size="small"
                        sx={{ fontSize: '0.7rem', height: 20 }}
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
                        {device.auth_date || '-'}
                      </Typography>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>

        <TablePagination
          rowsPerPageOptions={[25, 50, 100, 200]}
          component="div"
          count={totalCount}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
        />
      </Paper>
    </Box>
  )
}

export default ConfiguredCPEList
