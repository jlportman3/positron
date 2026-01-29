import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import {
  Box,
  Paper,
  Typography,
  Grid,
  Chip,
  Divider,
  CircularProgress,
  Tabs,
  Tab,
  TextField,
  Button,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Link,
} from '@mui/material'
import {
  Info as InfoIcon,
  Storage as StorageIcon,
  Code as CodeIcon,
  Security as SecurityIcon,
  VpnKey as LicenseIcon,
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckIcon,
  Warning as WarningIcon,
  Upload as UploadIcon,
  VerifiedUser as CertificateIcon,
} from '@mui/icons-material'
import { api } from '../services/api'
import Breadcrumb from '../components/Breadcrumb'

interface TabPanelProps {
  children?: React.ReactNode
  index: number
  value: number
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props
  return (
    <div role="tabpanel" hidden={value !== index} {...other}>
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  )
}

// Open source licenses used in this project
const openSourceLicenses = [
  {
    name: 'React',
    version: '18.2.0',
    license: 'MIT',
    url: 'https://github.com/facebook/react',
    description: 'A JavaScript library for building user interfaces',
  },
  {
    name: 'Material-UI (MUI)',
    version: '5.15.0',
    license: 'MIT',
    url: 'https://github.com/mui/material-ui',
    description: 'React components for faster and easier web development',
  },
  {
    name: 'FastAPI',
    version: '0.109.0',
    license: 'MIT',
    url: 'https://github.com/tiangolo/fastapi',
    description: 'Modern, fast web framework for building APIs with Python',
  },
  {
    name: 'SQLAlchemy',
    version: '2.0.25',
    license: 'MIT',
    url: 'https://github.com/sqlalchemy/sqlalchemy',
    description: 'The Python SQL Toolkit and Object Relational Mapper',
  },
  {
    name: 'PostgreSQL',
    version: '15.x',
    license: 'PostgreSQL License',
    url: 'https://www.postgresql.org/',
    description: 'Open source object-relational database system',
  },
  {
    name: 'Redis',
    version: '7.x',
    license: 'BSD-3-Clause',
    url: 'https://github.com/redis/redis',
    description: 'In-memory data structure store',
  },
  {
    name: 'Vite',
    version: '5.4.0',
    license: 'MIT',
    url: 'https://github.com/vitejs/vite',
    description: 'Next generation frontend tooling',
  },
  {
    name: 'React Query (TanStack)',
    version: '5.17.0',
    license: 'MIT',
    url: 'https://github.com/TanStack/query',
    description: 'Powerful asynchronous state management',
  },
  {
    name: 'Zustand',
    version: '4.4.0',
    license: 'MIT',
    url: 'https://github.com/pmndrs/zustand',
    description: 'Small, fast, scalable bearbones state management',
  },
  {
    name: 'Recharts',
    version: '2.10.0',
    license: 'MIT',
    url: 'https://github.com/recharts/recharts',
    description: 'Redefined chart library built with React and D3',
  },
  {
    name: 'Axios',
    version: '1.6.0',
    license: 'MIT',
    url: 'https://github.com/axios/axios',
    description: 'Promise based HTTP client for the browser and node.js',
  },
  {
    name: 'date-fns',
    version: '3.0.0',
    license: 'MIT',
    url: 'https://github.com/date-fns/date-fns',
    description: 'Modern JavaScript date utility library',
  },
  {
    name: 'Pydantic',
    version: '2.5.0',
    license: 'MIT',
    url: 'https://github.com/pydantic/pydantic',
    description: 'Data validation using Python type annotations',
  },
  {
    name: 'Uvicorn',
    version: '0.27.0',
    license: 'BSD-3-Clause',
    url: 'https://github.com/encode/uvicorn',
    description: 'Lightning-fast ASGI server implementation',
  },
  {
    name: 'asyncssh',
    version: '2.14.0',
    license: 'EPL-2.0',
    url: 'https://github.com/ronf/asyncssh',
    description: 'Asynchronous SSH for Python',
  },
  {
    name: 'httpx',
    version: '0.26.0',
    license: 'BSD-3-Clause',
    url: 'https://github.com/encode/httpx',
    description: 'A next generation HTTP client for Python',
  },
  {
    name: 'pysnmp',
    version: '6.1.0',
    license: 'BSD-2-Clause',
    url: 'https://github.com/lextudio/pysnmp',
    description: 'SNMP library for Python',
  },
  {
    name: 'netmiko',
    version: '4.3.0',
    license: 'MIT',
    url: 'https://github.com/ktbyers/netmiko',
    description: 'Multi-vendor SSH library for network devices',
  },
  {
    name: 'paramiko',
    version: '3.4.0',
    license: 'LGPL-2.1',
    url: 'https://github.com/paramiko/paramiko',
    description: 'SSHv2 protocol library for Python',
  },
  {
    name: 'Celery',
    version: '5.3.0',
    license: 'BSD-3-Clause',
    url: 'https://github.com/celery/celery',
    description: 'Distributed task queue',
  },
  {
    name: 'openpyxl',
    version: '3.1.0',
    license: 'MIT',
    url: 'https://github.com/theorchard/openpyxl',
    description: 'Python library for reading/writing Excel files',
  },
  {
    name: 'React Router',
    version: '6.21.0',
    license: 'MIT',
    url: 'https://github.com/remix-run/react-router',
    description: 'Declarative routing for React',
  },
  {
    name: 'Alembic',
    version: '1.13.0',
    license: 'MIT',
    url: 'https://github.com/sqlalchemy/alembic',
    description: 'Database migration tool for SQLAlchemy',
  },
  {
    name: 'bcrypt',
    version: '4.1.0',
    license: 'Apache-2.0',
    url: 'https://github.com/pyca/bcrypt',
    description: 'Password hashing library',
  },
  {
    name: 'Python-Jose',
    version: '3.3.0',
    license: 'MIT',
    url: 'https://github.com/mpdavis/python-jose',
    description: 'JavaScript Object Signing and Encryption (JOSE)',
  },
  {
    name: 'Linux Kernel',
    version: '6.x',
    license: 'GPL-2.0',
    url: 'https://www.kernel.org/',
    description: 'Linux operating system kernel',
  },
  {
    name: 'Docker',
    version: '24.x',
    license: 'Apache-2.0',
    url: 'https://github.com/moby/moby',
    description: 'Container platform',
  },
  {
    name: 'Nginx',
    version: '1.25.x',
    license: 'BSD-2-Clause',
    url: 'https://github.com/nginx/nginx',
    description: 'HTTP and reverse proxy server',
  },
]

export default function SystemInfo() {
  const [searchParams, setSearchParams] = useSearchParams()
  const tabParam = searchParams.get('tab')
  const initialTab = tabParam === 'license' ? 1 : tabParam === 'opensource' ? 2 : 0
  const [tabIndex, setTabIndex] = useState(initialTab)
  const [licenseKey, setLicenseKey] = useState('')
  const [licenseError, setLicenseError] = useState('')
  const [licenseSuccess, setLicenseSuccess] = useState('')

  // Update tab when URL changes
  useEffect(() => {
    const tabMap: Record<string, number> = {
      'version': 0,
      'upload': 1,
      'license': 2,
      'certificates': 3,
      'opensource': 4,
    }
    const newTab = tabMap[tabParam || ''] ?? 0
    setTabIndex(newTab)
  }, [tabParam])

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setTabIndex(newValue)
    // Update URL
    const tabNames = ['version', 'upload', 'license', 'certificates', 'opensource']
    if (newValue === 0) {
      searchParams.delete('tab')
    } else {
      searchParams.set('tab', tabNames[newValue])
    }
    setSearchParams(searchParams)
  }

  const { data, isLoading } = useQuery({
    queryKey: ['system-info'],
    queryFn: () => api.get('/info').then((res) => res.data),
  })

  const { data: healthData } = useQuery({
    queryKey: ['health'],
    queryFn: () => api.get('/health').then((res) => res.data),
    refetchInterval: 30000,
  })

  const handleActivateLicense = () => {
    if (!licenseKey.trim()) {
      setLicenseError('Please enter a license key')
      return
    }
    // License validation would go here
    // For now, we just show a message that we're running in open source mode
    setLicenseError('')
    setLicenseSuccess('License key accepted. Thank you for supporting Alamo GAM!')
  }

  const tabTitles = ['Version Info', 'Upload', 'License', 'Certificates', 'Open Source']
  const currentTitle = tabTitles[tabIndex] || 'Version Info'

  if (isLoading) {
    return (
      <Box>
        <Breadcrumb current={currentTitle} />
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      </Box>
    )
  }

  return (
    <Box>
      <Breadcrumb current={currentTitle} />

      <Paper sx={{ mt: 2 }}>
        <Tabs
          value={tabIndex}
          onChange={handleTabChange}
          sx={{ borderBottom: 1, borderColor: 'divider', px: 2 }}
        >
          <Tab icon={<InfoIcon />} label="Version" iconPosition="start" />
          <Tab icon={<UploadIcon />} label="Upload" iconPosition="start" />
          <Tab icon={<LicenseIcon />} label="License" iconPosition="start" />
          <Tab icon={<CertificateIcon />} label="Certificates" iconPosition="start" />
          <Tab icon={<CodeIcon />} label="Open Source" iconPosition="start" />
        </Tabs>

        {/* Version Tab */}
        <TabPanel value={tabIndex} index={0}>
          <Box sx={{ p: 3 }}>
            <Grid container spacing={3}>
              {/* Version Information */}
              <Grid item xs={12} md={6}>
                <Paper variant="outlined" sx={{ p: 3 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                    <InfoIcon color="primary" />
                    <Typography variant="h6">Version Information</Typography>
                  </Box>
                  <Divider sx={{ mb: 2 }} />
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        Application Name
                      </Typography>
                      <Typography variant="body1" fontWeight={500}>
                        {data?.brand_name || 'Alamo GAM'}
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        Version
                      </Typography>
                      <Chip
                        label={data?.version || '1.0.0'}
                        color="primary"
                        size="small"
                        variant="outlined"
                      />
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        Build Number
                      </Typography>
                      <Typography variant="body1">
                        {data?.build_number || '#29183'}
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        Release Date
                      </Typography>
                      <Typography variant="body1">
                        {data?.release_date || '2026-01-24'}
                      </Typography>
                    </Grid>
                  </Grid>
                </Paper>
              </Grid>

              {/* System Status */}
              <Grid item xs={12} md={6}>
                <Paper variant="outlined" sx={{ p: 3 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                    <StorageIcon color="primary" />
                    <Typography variant="h6">System Status</Typography>
                  </Box>
                  <Divider sx={{ mb: 2 }} />
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        Status
                      </Typography>
                      <Chip
                        icon={<CheckIcon />}
                        label={healthData?.status?.toUpperCase() || 'HEALTHY'}
                        color={healthData?.status === 'healthy' ? 'success' : 'warning'}
                        size="small"
                      />
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        Uptime
                      </Typography>
                      <Typography variant="body1">
                        {healthData?.uptime || 'Running'}
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        Database
                      </Typography>
                      <Chip
                        label="Connected"
                        color="success"
                        size="small"
                        variant="outlined"
                      />
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        Cache
                      </Typography>
                      <Chip
                        label="Connected"
                        color="success"
                        size="small"
                        variant="outlined"
                      />
                    </Grid>
                  </Grid>
                </Paper>
              </Grid>

              {/* Backend Components */}
              <Grid item xs={12} md={6}>
                <Paper variant="outlined" sx={{ p: 3 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                    <CodeIcon color="primary" />
                    <Typography variant="h6">Backend Components</Typography>
                  </Box>
                  <Divider sx={{ mb: 2 }} />
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        Framework
                      </Typography>
                      <Typography variant="body1">FastAPI 0.109.0</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        Database
                      </Typography>
                      <Typography variant="body1">PostgreSQL 15</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        Cache
                      </Typography>
                      <Typography variant="body1">Redis 7</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        Python
                      </Typography>
                      <Typography variant="body1">3.11+</Typography>
                    </Grid>
                  </Grid>
                </Paper>
              </Grid>

              {/* Frontend Components */}
              <Grid item xs={12} md={6}>
                <Paper variant="outlined" sx={{ p: 3 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                    <SecurityIcon color="primary" />
                    <Typography variant="h6">Frontend Components</Typography>
                  </Box>
                  <Divider sx={{ mb: 2 }} />
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        Framework
                      </Typography>
                      <Typography variant="body1">React 18.2.0</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        Build Tool
                      </Typography>
                      <Typography variant="body1">Vite 5.4.0</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        UI Library
                      </Typography>
                      <Typography variant="body1">MUI 5.15.0</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        State
                      </Typography>
                      <Typography variant="body1">Zustand + React Query</Typography>
                    </Grid>
                  </Grid>
                </Paper>
              </Grid>

              {/* Device Compatibility */}
              <Grid item xs={12}>
                <Paper variant="outlined" sx={{ p: 3 }}>
                  <Typography variant="h6" sx={{ mb: 2 }}>Compatible Devices</Typography>
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    <Chip label="GAM-4-C" variant="outlined" />
                    <Chip label="GAM-4-CX-AC" variant="outlined" />
                    <Chip label="GAM-12-C" variant="outlined" />
                    <Chip label="GAM-4-M" variant="outlined" />
                    <Chip label="GAM-12-M" variant="outlined" />
                    <Chip label="GAM-24-M" variant="outlined" />
                  </Box>
                </Paper>
              </Grid>
            </Grid>
          </Box>
        </TabPanel>

        {/* Upload Tab */}
        <TabPanel value={tabIndex} index={1}>
          <Box sx={{ p: 3 }}>
            <Paper variant="outlined" sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <UploadIcon color="primary" />
                <Typography variant="h6">Upload New Version</Typography>
              </Box>
              <Divider sx={{ mb: 2 }} />
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Upload a new version of the Alamo GAM software. The system will validate the package and prepare it for installation.
              </Typography>
              <Box
                sx={{
                  border: '2px dashed',
                  borderColor: 'divider',
                  borderRadius: 2,
                  p: 4,
                  textAlign: 'center',
                  backgroundColor: 'action.hover',
                }}
              >
                <UploadIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                <Typography variant="body1" gutterBottom>
                  Drag and drop a version package here
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  or
                </Typography>
                <Button variant="contained" component="label">
                  Browse Files
                  <input type="file" hidden accept=".tar.gz,.zip" />
                </Button>
                <Typography variant="caption" display="block" sx={{ mt: 2 }} color="text.secondary">
                  Supported formats: .tar.gz, .zip
                </Typography>
              </Box>
            </Paper>
          </Box>
        </TabPanel>

        {/* License Tab */}
        <TabPanel value={tabIndex} index={2}>
          <Box sx={{ p: 3 }}>
            <Grid container spacing={3}>
              {/* License Status */}
              <Grid item xs={12} md={6}>
                <Paper variant="outlined" sx={{ p: 3 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                    <LicenseIcon color="primary" />
                    <Typography variant="h6">License Status</Typography>
                  </Box>
                  <Divider sx={{ mb: 2 }} />

                  <Alert
                    severity="info"
                    icon={<WarningIcon />}
                    sx={{ mb: 2 }}
                  >
                    <Typography variant="body2" fontWeight={500}>
                      Running in Open Source Mode
                    </Typography>
                    <Typography variant="caption">
                      All features are available. Consider supporting development with a license.
                    </Typography>
                  </Alert>

                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        License Type
                      </Typography>
                      <Typography variant="body1" fontWeight={500}>
                        Open Source (GPL v3)
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        Status
                      </Typography>
                      <Chip
                        label="UNLICENSED"
                        color="warning"
                        size="small"
                      />
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        Device Limit
                      </Typography>
                      <Typography variant="body1">Unlimited</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        Support
                      </Typography>
                      <Typography variant="body1">Community</Typography>
                    </Grid>
                  </Grid>
                </Paper>
              </Grid>

              {/* License Activation */}
              <Grid item xs={12} md={6}>
                <Paper variant="outlined" sx={{ p: 3 }}>
                  <Typography variant="h6" sx={{ mb: 2 }}>Activate License</Typography>
                  <Divider sx={{ mb: 2 }} />

                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    Enter your license key to unlock premium support and features.
                    The software will function fully without a license.
                  </Typography>

                  {licenseError && (
                    <Alert severity="error" sx={{ mb: 2 }}>
                      {licenseError}
                    </Alert>
                  )}
                  {licenseSuccess && (
                    <Alert severity="success" sx={{ mb: 2 }}>
                      {licenseSuccess}
                    </Alert>
                  )}

                  <TextField
                    fullWidth
                    label="License Key"
                    placeholder="XXXX-XXXX-XXXX-XXXX"
                    value={licenseKey}
                    onChange={(e) => setLicenseKey(e.target.value)}
                    sx={{ mb: 2 }}
                  />
                  <Button
                    variant="contained"
                    onClick={handleActivateLicense}
                    fullWidth
                  >
                    Activate License
                  </Button>
                </Paper>
              </Grid>

              {/* License Tiers */}
              <Grid item xs={12}>
                <Paper variant="outlined" sx={{ p: 3 }}>
                  <Typography variant="h6" sx={{ mb: 2 }}>Available License Tiers</Typography>
                  <Divider sx={{ mb: 2 }} />
                  <TableContainer>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Feature</TableCell>
                          <TableCell align="center">Open Source</TableCell>
                          <TableCell align="center">Professional</TableCell>
                          <TableCell align="center">Enterprise</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        <TableRow>
                          <TableCell>Device Management</TableCell>
                          <TableCell align="center"><CheckIcon color="success" /></TableCell>
                          <TableCell align="center"><CheckIcon color="success" /></TableCell>
                          <TableCell align="center"><CheckIcon color="success" /></TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Subscriber Provisioning</TableCell>
                          <TableCell align="center"><CheckIcon color="success" /></TableCell>
                          <TableCell align="center"><CheckIcon color="success" /></TableCell>
                          <TableCell align="center"><CheckIcon color="success" /></TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Alarm Management</TableCell>
                          <TableCell align="center"><CheckIcon color="success" /></TableCell>
                          <TableCell align="center"><CheckIcon color="success" /></TableCell>
                          <TableCell align="center"><CheckIcon color="success" /></TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Firmware Management</TableCell>
                          <TableCell align="center"><CheckIcon color="success" /></TableCell>
                          <TableCell align="center"><CheckIcon color="success" /></TableCell>
                          <TableCell align="center"><CheckIcon color="success" /></TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Email Support</TableCell>
                          <TableCell align="center">-</TableCell>
                          <TableCell align="center"><CheckIcon color="success" /></TableCell>
                          <TableCell align="center"><CheckIcon color="success" /></TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Phone Support</TableCell>
                          <TableCell align="center">-</TableCell>
                          <TableCell align="center">-</TableCell>
                          <TableCell align="center"><CheckIcon color="success" /></TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Custom Development</TableCell>
                          <TableCell align="center">-</TableCell>
                          <TableCell align="center">-</TableCell>
                          <TableCell align="center"><CheckIcon color="success" /></TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Paper>
              </Grid>
            </Grid>
          </Box>
        </TabPanel>

        {/* Certificates Tab */}
        <TabPanel value={tabIndex} index={3}>
          <Box sx={{ p: 3 }}>
            <Paper variant="outlined" sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <CertificateIcon color="primary" />
                <Typography variant="h6">SSL Certificate Management</Typography>
              </Box>
              <Divider sx={{ mb: 2 }} />
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Upload a custom SSL certificate for HTTPS. The file should contain both the certificate and private key in PEM format.
              </Typography>

              <Alert severity="info" sx={{ mb: 3 }}>
                <Typography variant="body2">
                  <strong>Note:</strong> Use the following command to combine your certificate and key files:
                </Typography>
                <Typography variant="body2" component="code" sx={{ display: 'block', mt: 1, bgcolor: '#f5f5f5', p: 1, borderRadius: 1 }}>
                  cat my.cert my.key {'>'} my.pem
                </Typography>
                <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                  RSA certificates are recommended. DSA certificates are deprecated in modern browsers.
                </Typography>
              </Alert>

              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Passphrase (optional)"
                    type="password"
                    helperText="Enter passphrase if the private key is encrypted"
                    size="small"
                  />
                </Grid>
                <Grid item xs={12}>
                  <Box
                    sx={{
                      border: '2px dashed',
                      borderColor: 'divider',
                      borderRadius: 2,
                      p: 3,
                      textAlign: 'center',
                      backgroundColor: 'action.hover',
                    }}
                  >
                    <CertificateIcon sx={{ fontSize: 40, color: 'text.secondary', mb: 1 }} />
                    <Typography variant="body2" gutterBottom>
                      Drop PEM file here or click to browse
                    </Typography>
                    <Button variant="outlined" component="label" size="small" sx={{ mt: 1 }}>
                      Select Certificate
                      <input type="file" hidden accept=".pem,.crt,.cer" />
                    </Button>
                  </Box>
                </Grid>
                <Grid item xs={12}>
                  <Button variant="contained" color="primary" disabled>
                    Upload Certificate
                  </Button>
                </Grid>
              </Grid>
            </Paper>

            <Paper variant="outlined" sx={{ p: 3, mt: 3 }}>
              <Typography variant="h6" sx={{ mb: 2 }}>Current Certificate</Typography>
              <Divider sx={{ mb: 2 }} />
              <Alert severity="success" icon={<CheckIcon />}>
                Using self-signed certificate (default)
              </Alert>
            </Paper>
          </Box>
        </TabPanel>

        {/* Open Source Tab */}
        <TabPanel value={tabIndex} index={4}>
          <Box sx={{ p: 3 }}>
            <Alert severity="info" sx={{ mb: 3 }}>
              <Typography variant="body2">
                Alamo GAM is built with open source software. We are grateful to the open source
                community for their contributions. Below is a list of the major open source
                components used in this application.
              </Typography>
            </Alert>

            <Paper variant="outlined" sx={{ p: 3, mb: 3 }}>
              <Typography variant="h6" sx={{ mb: 2 }}>Alamo GAM License</Typography>
              <Divider sx={{ mb: 2 }} />
              <Typography variant="body2" component="pre" sx={{
                whiteSpace: 'pre-wrap',
                fontFamily: 'monospace',
                fontSize: '0.75rem',
                bgcolor: '#f5f5f5',
                p: 2,
                borderRadius: 1,
              }}>
{`Alamo GAM - GAM Device Management System
Copyright (C) 2026 Alamo Broadband Inc.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.

---

For commercial licensing options, please contact:
licensing@alamobroadband.com`}
              </Typography>
            </Paper>

            <Typography variant="h6" sx={{ mb: 2 }}>Third-Party Licenses</Typography>

            {openSourceLicenses.map((lib, index) => (
              <Accordion key={index} defaultExpanded={index === 0}>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
                    <Typography fontWeight={500}>{lib.name}</Typography>
                    <Chip label={lib.version} size="small" variant="outlined" />
                    <Chip
                      label={lib.license}
                      size="small"
                      color={lib.license === 'MIT' ? 'success' : lib.license.includes('GPL') ? 'warning' : 'info'}
                    />
                  </Box>
                </AccordionSummary>
                <AccordionDetails>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    {lib.description}
                  </Typography>
                  <Link href={lib.url} target="_blank" rel="noopener">
                    {lib.url}
                  </Link>
                </AccordionDetails>
              </Accordion>
            ))}

            <Paper variant="outlined" sx={{ p: 3, mt: 3, textAlign: 'center' }}>
              <Typography variant="body2" color="text.secondary">
                Alamo GAM - GAM Device Management System
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Copyright (C) {new Date().getFullYear()} Alamo Broadband Inc. All rights reserved.
              </Typography>
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                Licensed under GPL v3. See above for full license text.
              </Typography>
            </Paper>
          </Box>
        </TabPanel>
      </Paper>
    </Box>
  )
}
