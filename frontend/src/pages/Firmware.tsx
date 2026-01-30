import { useState, useRef, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  IconButton,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
  Tooltip,
  Alert,
  Snackbar,
  Checkbox,
  ButtonGroup,
  TextField,
  FormControlLabel,
  Switch,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
} from '@mui/material'
import {
  CloudUpload as UploadIcon,
  Delete as DeleteIcon,
  Star as DefaultIcon,
  StarBorder as SetDefaultIcon,
  Download as DownloadIcon,
  Refresh as RefreshIcon,
  SwapHoriz as SwapIcon,
  Add as AddIcon,
  InsertDriveFile as FileIcon,
} from '@mui/icons-material'
import { firmwareApi, devicesApi, getErrorMessage } from '../services/api'
import { format } from 'date-fns'
import Breadcrumb from '../components/Breadcrumb'

export default function Firmware() {
  const queryClient = useQueryClient()
  const [searchParams, setSearchParams] = useSearchParams()
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Dialog state
  const [uploadOpen, setUploadOpen] = useState(false)
  const [uploadFiles, setUploadFiles] = useState<File[]>([])
  const [uploadError, setUploadError] = useState('')
  const [uploadVersion, setUploadVersion] = useState('')
  const [uploadRevision, setUploadRevision] = useState('')
  const [uploadTechnology, setUploadTechnology] = useState('')
  const [uploadIsDefault, setUploadIsDefault] = useState(false)
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({ open: false, message: '', severity: 'success' })

  // Device selection for bulk actions
  const [selectedDevices, setSelectedDevices] = useState<string[]>([])

  // Auto-open upload dialog if redirected from "Add Version"
  useEffect(() => {
    if (searchParams.get('upload') === 'true') {
      setUploadOpen(true)
      setSearchParams({})
    }
  }, [searchParams, setSearchParams])

  // Fetch firmware lists
  const { data: mimoFirmwares } = useQuery({
    queryKey: ['firmware-mimo'],
    queryFn: () =>
      firmwareApi.list({ model_type: 'mimo' }).then((res) => res.data),
  })

  const { data: coaxFirmwares } = useQuery({
    queryKey: ['firmware-coax'],
    queryFn: () =>
      firmwareApi.list({ model_type: 'coax' }).then((res) => res.data),
  })

  // Fetch devices for upgrade status
  const { data: devicesData, isLoading: devicesLoading } = useQuery({
    queryKey: ['devices-firmware'],
    queryFn: () => devicesApi.list({ page_size: 200 }).then((res) => res.data),
  })

  // Mutations
  const uploadMutation = useMutation({
    mutationFn: (formData: FormData) => firmwareApi.upload(formData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['firmware-mimo'] })
      queryClient.invalidateQueries({ queryKey: ['firmware-coax'] })
      handleCloseUpload()
      setSnackbar({ open: true, message: 'Firmware uploaded successfully', severity: 'success' })
    },
    onError: (error: any) => {
      setUploadError(getErrorMessage(error, 'Upload failed'))
      setSnackbar({ open: true, message: getErrorMessage(error, 'Upload failed'), severity: 'error' })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => firmwareApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['firmware-mimo'] })
      queryClient.invalidateQueries({ queryKey: ['firmware-coax'] })
    },
  })

  const setDefaultMutation = useMutation({
    mutationFn: (id: string) => firmwareApi.setDefault(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['firmware-mimo'] })
      queryClient.invalidateQueries({ queryKey: ['firmware-coax'] })
    },
  })

  const downloadOnlyMutation = useMutation({
    mutationFn: (deviceIds: string[]) => firmwareApi.bulkDownload(deviceIds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['devices-firmware'] })
      setSelectedDevices([])
    },
  })

  const downloadActivateMutation = useMutation({
    mutationFn: (deviceIds: string[]) => firmwareApi.bulkDownloadActivate(deviceIds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['devices-firmware'] })
      setSelectedDevices([])
    },
  })

  const activateAlternateMutation = useMutation({
    mutationFn: (deviceIds: string[]) => firmwareApi.bulkActivateAlternate(deviceIds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['devices-firmware'] })
      setSelectedDevices([])
    },
  })

  const handleCloseUpload = () => {
    setUploadOpen(false)
    setUploadFiles([])
    setUploadError('')
    setUploadVersion('')
    setUploadRevision('')
    setUploadTechnology('')
    setUploadIsDefault(false)
  }

  const handleUpload = () => {
    if (uploadFiles.length === 0) return
    const formData = new FormData()
    uploadFiles.forEach((file) => formData.append('files', file))
    if (uploadVersion) formData.append('version', uploadVersion)
    if (uploadRevision) formData.append('revision', uploadRevision)
    if (uploadTechnology) formData.append('technology', uploadTechnology)
    formData.append('is_default', String(uploadIsDefault))
    uploadMutation.mutate(formData)
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    setUploadFiles(files)
  }

  const handleSelectDevice = (deviceId: string) => {
    if (selectedDevices.includes(deviceId)) {
      setSelectedDevices(selectedDevices.filter((id) => id !== deviceId))
    } else {
      setSelectedDevices([...selectedDevices, deviceId])
    }
  }

  const handleSelectAll = () => {
    if (selectedDevices.length === devicesData?.items?.length) {
      setSelectedDevices([])
    } else {
      setSelectedDevices(devicesData?.items?.map((d: any) => d.id) || [])
    }
  }

  const renderFirmwareTable = (title: string, firmwares: any, emptyText: string) => (
    <Paper sx={{ mb: 3 }}>
      <Box
        sx={{
          p: 2,
          borderBottom: 1,
          borderColor: 'divider',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <Typography variant="h6">{title}</Typography>
        <Button
          variant="outlined"
          size="small"
          startIcon={<AddIcon />}
          onClick={() => setUploadOpen(true)}
        >
          Add Version
        </Button>
      </Box>
      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Compatibility</TableCell>
              <TableCell>Version</TableCell>
              <TableCell>Revision</TableCell>
              <TableCell>Baseline</TableCell>
              <TableCell>Date</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {firmwares?.items?.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  {emptyText}
                </TableCell>
              </TableRow>
            ) : (
              firmwares?.items?.map((fw: any) => (
                <TableRow key={fw.id}>
                  <TableCell>
                    {fw.port_qty
                      ? `${fw.technology || fw.model_type} ${fw.port_qty}`
                      : fw.model_type || 'All'}
                  </TableCell>
                  <TableCell>
                    <Chip label={fw.version} size="small" color="primary" variant="outlined" />
                  </TableCell>
                  <TableCell>{fw.revision || '-'}</TableCell>
                  <TableCell>
                    {fw.is_default ? (
                      <Tooltip title="Baseline firmware">
                        <DefaultIcon color="primary" fontSize="small" />
                      </Tooltip>
                    ) : (
                      <Tooltip title="Set as baseline">
                        <IconButton
                          size="small"
                          onClick={() => setDefaultMutation.mutate(fw.id)}
                        >
                          <SetDefaultIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    )}
                  </TableCell>
                  <TableCell>
                    {fw.uploaded_at
                      ? format(new Date(fw.uploaded_at), 'yyyy-MM-dd')
                      : '-'}
                  </TableCell>
                  <TableCell>
                    <Tooltip title="Delete">
                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => deleteMutation.mutate(fw.id)}
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Paper>
  )

  return (
    <Box>
      <Breadcrumb current="Firmware Versions" />

      {renderFirmwareTable('Mimo Firmwares', mimoFirmwares, 'No Mimo firmwares available')}
      {renderFirmwareTable('Coax Firmwares', coaxFirmwares, 'No Coax firmwares available')}

      {/* Device Upgrade Status Section */}
      <Paper>
        <Box
          sx={{
            p: 2,
            borderBottom: 1,
            borderColor: 'divider',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <Typography variant="h6">Device Upgrade Status</Typography>
          <ButtonGroup variant="outlined" size="small">
            <Button
              onClick={() => downloadOnlyMutation.mutate(selectedDevices)}
              disabled={selectedDevices.length === 0 || downloadOnlyMutation.isPending}
              startIcon={<DownloadIcon />}
            >
              DOWNLOAD ONLY
            </Button>
            <Button
              onClick={() => downloadActivateMutation.mutate(selectedDevices)}
              disabled={selectedDevices.length === 0 || downloadActivateMutation.isPending}
              startIcon={<RefreshIcon />}
            >
              TRIGGER DOWNLOAD AND ACTIVATION
            </Button>
            <Button
              onClick={() => activateAlternateMutation.mutate(selectedDevices)}
              disabled={selectedDevices.length === 0 || activateAlternateMutation.isPending}
              startIcon={<SwapIcon />}
            >
              TRIGGER ALTERNATE ACTIVATION
            </Button>
          </ButtonGroup>
        </Box>
        <TableContainer>
          {devicesLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
              <CircularProgress />
            </Box>
          ) : (
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell padding="checkbox">
                    <Checkbox
                      checked={
                        selectedDevices.length > 0 &&
                        selectedDevices.length === devicesData?.items?.length
                      }
                      indeterminate={
                        selectedDevices.length > 0 &&
                        selectedDevices.length < (devicesData?.items?.length || 0)
                      }
                      onChange={handleSelectAll}
                    />
                  </TableCell>
                  <TableCell>System Name</TableCell>
                  <TableCell>IP Address</TableCell>
                  <TableCell>Model</TableCell>
                  <TableCell>Current Version</TableCell>
                  <TableCell>Alternate Version</TableCell>
                  <TableCell>Serial</TableCell>
                  <TableCell>Upgrade Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {devicesData?.items?.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={8} align="center">
                      No devices found
                    </TableCell>
                  </TableRow>
                ) : (
                  devicesData?.items?.map((device: any) => (
                    <TableRow key={device.id} hover>
                      <TableCell padding="checkbox">
                        <Checkbox
                          checked={selectedDevices.includes(device.id)}
                          onChange={() => handleSelectDevice(device.id)}
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" fontWeight="medium">
                          {device.name || device.serial_number}
                        </Typography>
                      </TableCell>
                      <TableCell>{device.ip_address}</TableCell>
                      <TableCell>{device.product_class || '-'}</TableCell>
                      <TableCell>
                        <Chip
                          label={device.software_version || '-'}
                          size="small"
                          color="primary"
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>
                        {device.swap_software_version || '-'}
                      </TableCell>
                      <TableCell>{device.serial_number}</TableCell>
                      <TableCell>
                        <Chip
                          label={device.upgrade_status || 'idle'}
                          size="small"
                          color={
                            device.upgrade_status === 'downloading'
                              ? 'warning'
                              : device.upgrade_status === 'complete'
                              ? 'success'
                              : device.upgrade_status === 'error'
                              ? 'error'
                              : 'default'
                          }
                        />
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          )}
        </TableContainer>
      </Paper>

      {/* Upload Dialog */}
      <Dialog open={uploadOpen} onClose={handleCloseUpload} maxWidth="sm" fullWidth>
        <DialogTitle>Upload Firmware</DialogTitle>
        <DialogContent>
          {uploadError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {uploadError}
            </Alert>
          )}
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Upload firmware files (.mfip, .xml, .sha256, .sign). If a firmware.xml
            manifest is included, version metadata will be auto-extracted.
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
            <input
              type="file"
              ref={fileInputRef}
              style={{ display: 'none' }}
              onChange={handleFileSelect}
              multiple
              accept=".mfip,.xml,.sha256,.sign"
            />
            <Button
              variant="outlined"
              onClick={() => fileInputRef.current?.click()}
              startIcon={<UploadIcon />}
              fullWidth
            >
              {uploadFiles.length > 0
                ? `${uploadFiles.length} file(s) selected`
                : 'Select File(s)'}
            </Button>
            {uploadFiles.length > 0 && (
              <List dense>
                {uploadFiles.map((file, idx) => (
                  <ListItem key={idx}>
                    <ListItemIcon sx={{ minWidth: 32 }}>
                      <FileIcon fontSize="small" />
                    </ListItemIcon>
                    <ListItemText
                      primary={file.name}
                      secondary={`${(file.size / 1024 / 1024).toFixed(1)} MB`}
                    />
                  </ListItem>
                ))}
              </List>
            )}
            <TextField
              label="Version (auto-detected from manifest)"
              size="small"
              value={uploadVersion}
              onChange={(e) => setUploadVersion(e.target.value)}
              placeholder="e.g., 1.8.1"
            />
            <TextField
              label="Revision (auto-detected from manifest)"
              size="small"
              value={uploadRevision}
              onChange={(e) => setUploadRevision(e.target.value)}
              placeholder="e.g., r5"
            />
            <TextField
              label="Technology (auto-detected from manifest)"
              size="small"
              value={uploadTechnology}
              onChange={(e) => setUploadTechnology(e.target.value)}
              placeholder="e.g., mimo or coax"
            />
            <FormControlLabel
              control={
                <Switch
                  checked={uploadIsDefault}
                  onChange={(e) => setUploadIsDefault(e.target.checked)}
                />
              }
              label="Set as baseline (default for this technology)"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseUpload}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleUpload}
            disabled={uploadFiles.length === 0 || uploadMutation.isPending}
          >
            {uploadMutation.isPending ? 'Uploading...' : 'Upload'}
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={() => setSnackbar({ ...snackbar, open: false })} severity={snackbar.severity} variant="filled">
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  )
}
