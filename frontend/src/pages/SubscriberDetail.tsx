import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Box,
  Typography,
  Grid,
  Chip,
  Button,
  CircularProgress,
  Card,
  CardContent,
  Alert,
  Snackbar,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
} from '@mui/material'
import {
  ArrowBack as BackIcon,
  ContentCopy as CopyIcon,
  Router as DeviceIcon,
  Delete as DeleteIcon,
  CloudUpload as PushIcon,
  Person as PersonIcon,
  Lan as EndpointIcon,
} from '@mui/icons-material'
import { subscribersApi, devicesApi, getErrorMessage } from '../services/api'
import Breadcrumb from '../components/Breadcrumb'

function InfoRow({ label, value, mono }: { label: string; value: any; mono?: boolean }) {
  return (
    <Box sx={{ display: 'flex', py: 0.5 }}>
      <Typography variant="body2" color="text.secondary" sx={{ width: 200, flexShrink: 0 }}>
        {label}
      </Typography>
      <Typography variant="body2" sx={mono ? { fontFamily: 'monospace' } : undefined}>
        {value ?? '-'}
      </Typography>
    </Box>
  )
}

export default function SubscriberDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success',
  })
  const [confirmDialog, setConfirmDialog] = useState<{
    open: boolean; title: string; message: string; action: (() => void) | null
  }>({ open: false, title: '', message: '', action: null })

  const { data: subscriber, isLoading } = useQuery({
    queryKey: ['subscriber', id],
    queryFn: () => subscribersApi.get(id!).then((res) => res.data),
    enabled: !!id,
  })

  const { data: device } = useQuery({
    queryKey: ['device', subscriber?.device_id],
    queryFn: () => devicesApi.get(subscriber!.device_id).then((res) => res.data),
    enabled: !!subscriber?.device_id,
  })

  const pushToDeviceMutation = useMutation({
    mutationFn: () => subscribersApi.updateOnDevice(id!, subscriber),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subscriber', id] })
      setSnackbar({ open: true, message: 'Subscriber pushed to device', severity: 'success' })
    },
    onError: (error: any) => {
      setSnackbar({ open: true, message: getErrorMessage(error, 'Push to device failed'), severity: 'error' })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: () => subscribersApi.delete(id!),
    onSuccess: () => {
      setSnackbar({ open: true, message: 'Subscriber deleted', severity: 'success' })
      navigate('/subscribers')
    },
    onError: (error: any) => {
      setSnackbar({ open: true, message: getErrorMessage(error, 'Delete failed'), severity: 'error' })
    },
  })

  const copyMac = () => {
    if (subscriber?.endpoint_mac_address) {
      navigator.clipboard.writeText(subscriber.endpoint_mac_address)
      setSnackbar({ open: true, message: 'MAC address copied', severity: 'success' })
    }
  }

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    )
  }

  if (!subscriber) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">Subscriber not found</Alert>
        <Button startIcon={<BackIcon />} onClick={() => navigate('/subscribers')} sx={{ mt: 2 }}>
          Back to Subscribers
        </Button>
      </Box>
    )
  }

  return (
    <Box>
      <Breadcrumb
        items={[{ label: 'Subscribers', path: '/subscribers' }]}
        current={subscriber.name}
      />

      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
        <IconButton onClick={() => navigate('/subscribers')}>
          <BackIcon />
        </IconButton>
        <Box sx={{ flex: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <PersonIcon color="primary" />
            <Typography variant="h5">{subscriber.name}</Typography>
            {subscriber.json_id && (
              <Chip label={`GAM ID: ${subscriber.json_id}`} size="small" variant="outlined" />
            )}
          </Box>
          {subscriber.endpoint_mac_address && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: 0.5 }}>
              <Typography variant="body2" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
                {subscriber.endpoint_mac_address}
              </Typography>
              <IconButton size="small" onClick={copyMac} sx={{ p: 0.25 }}>
                <CopyIcon sx={{ fontSize: 14 }} />
              </IconButton>
            </Box>
          )}
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            size="small"
            startIcon={<DeviceIcon />}
            onClick={() => navigate(`/devices/${subscriber.device_id}`)}
          >
            View GAM
          </Button>
          {subscriber.endpoint_id && (
            <Button
              variant="outlined"
              size="small"
              startIcon={<EndpointIcon />}
              onClick={() => navigate(`/endpoints/${subscriber.endpoint_id}`)}
            >
              View Endpoint
            </Button>
          )}
          <Button
            variant="outlined"
            size="small"
            startIcon={<PushIcon />}
            disabled={pushToDeviceMutation.isPending}
            onClick={() => setConfirmDialog({
              open: true,
              title: 'Push to Device',
              message: `Push subscriber "${subscriber.name}" configuration to the GAM device?`,
              action: () => pushToDeviceMutation.mutate(),
            })}
          >
            Push to Device
          </Button>
          <Button
            variant="outlined"
            size="small"
            color="error"
            startIcon={<DeleteIcon />}
            onClick={() => setConfirmDialog({
              open: true,
              title: 'Delete Subscriber',
              message: `Delete subscriber "${subscriber.name}"? This cannot be undone.`,
              action: () => deleteMutation.mutate(),
            })}
          >
            Delete
          </Button>
        </Box>
      </Box>

      <Grid container spacing={2}>
        {/* Identity */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="subtitle2" gutterBottom>Identification</Typography>
              <InfoRow label="Name" value={subscriber.name} />
              <InfoRow label="Description" value={subscriber.description} />
              <InfoRow label="GAM ID" value={subscriber.json_id} />
              <InfoRow label="UID" value={subscriber.uid} />
              <InfoRow label="Created" value={subscriber.created_at ? new Date(subscriber.created_at).toLocaleString() : null} />
              <InfoRow label="Updated" value={subscriber.updated_at ? new Date(subscriber.updated_at).toLocaleString() : null} />
            </CardContent>
          </Card>
        </Grid>

        {/* Endpoint */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="subtitle2" gutterBottom>Endpoint Association</Typography>
              <InfoRow label="Endpoint Name" value={subscriber.endpoint_name} />
              <InfoRow label="MAC Address" value={subscriber.endpoint_mac_address} mono />
              <InfoRow label="Endpoint GAM ID" value={subscriber.endpoint_json_id} />
              <InfoRow label="Bandwidth Profile" value={subscriber.bw_profile_name} />
              <InfoRow label="BW Profile ID" value={subscriber.bw_profile_id} />
              <InfoRow label="PoE Mode" value={subscriber.poe_mode_ctrl} />
            </CardContent>
          </Card>
        </Grid>

        {/* VLAN Port 1 */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="subtitle2" gutterBottom>VLAN Configuration - Port 1</Typography>
              <InfoRow label="VLAN ID" value={subscriber.port1_vlan_id} />
              <InfoRow label="Tagged" value={subscriber.vlan_is_tagged ? 'Yes' : 'No'} />
              <InfoRow label="Allowed Tagged VLANs" value={subscriber.allowed_tagged_vlan} />
              <InfoRow label="Remapped VLAN" value={subscriber.remapped_vlan_id} />
              <InfoRow label="Double Tags" value={subscriber.double_tags ? 'Yes' : 'No'} />
              <InfoRow label="Trunk Mode" value={subscriber.trunk_mode ? 'Yes' : 'No'} />
            </CardContent>
          </Card>
        </Grid>

        {/* VLAN Port 2 */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="subtitle2" gutterBottom>VLAN Configuration - Port 2</Typography>
              <InfoRow label="VLAN ID" value={subscriber.port2_vlan_id} />
              <InfoRow label="Tagged" value={subscriber.vlan_is_tagged2 ? 'Yes' : 'No'} />
              <InfoRow label="Allowed Tagged VLANs" value={subscriber.allowed_tagged_vlan2} />
            </CardContent>
          </Card>
        </Grid>

        {/* Port Configuration */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="subtitle2" gutterBottom>Port Configuration</Typography>
              <InfoRow label="Port Interface" value={subscriber.port_if_index} />
              <InfoRow label="NNI Interface" value={subscriber.nni_if_index} />
            </CardContent>
          </Card>
        </Grid>

        {/* GAM Device */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="subtitle2" gutterBottom>GAM Device</Typography>
              <InfoRow label="Device" value={device?.name || device?.serial_number} />
              <InfoRow label="IP Address" value={device?.ip_address} mono />
              <InfoRow label="Model" value={device?.product_class} />
            </CardContent>
          </Card>
        </Grid>

        {/* Splynx Integration */}
        {(subscriber.splynx_customer_id || subscriber.splynx_service_id) && (
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="subtitle2" gutterBottom>Splynx Integration</Typography>
                <InfoRow label="Customer ID" value={subscriber.splynx_customer_id} />
                <InfoRow label="Service ID" value={subscriber.splynx_service_id} />
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>

      {/* Confirm Dialog */}
      <Dialog open={confirmDialog.open} onClose={() => setConfirmDialog({ ...confirmDialog, open: false })}>
        <DialogTitle>{confirmDialog.title}</DialogTitle>
        <DialogContent>
          <DialogContentText>{confirmDialog.message}</DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmDialog({ ...confirmDialog, open: false })}>Cancel</Button>
          <Button variant="contained" onClick={() => { confirmDialog.action?.(); setConfirmDialog({ ...confirmDialog, open: false }) }}>
            Confirm
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={3000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert onClose={() => setSnackbar({ ...snackbar, open: false })} severity={snackbar.severity} variant="filled">
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  )
}
