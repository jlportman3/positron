import { useState } from 'react'
import {
  Box,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Typography,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  InputAdornment,
  Chip,
} from '@mui/material'
import { Add, Edit, Delete, ArrowDownward, ArrowUpward } from '@mui/icons-material'

interface SpeedProfile {
  id: string
  name: string
  downloadMbps: number
  uploadMbps: number
  subscriberCount: number
}

const SpeedProfilesSettings = () => {
  const [profiles, setProfiles] = useState<SpeedProfile[]>([
    { id: '1', name: 'Basic 100/10', downloadMbps: 100, uploadMbps: 10, subscriberCount: 45 },
    { id: '2', name: 'Standard 200/20', downloadMbps: 200, uploadMbps: 20, subscriberCount: 89 },
    { id: '3', name: 'Premium 500/50', downloadMbps: 500, uploadMbps: 50, subscriberCount: 34 },
    { id: '4', name: 'Ultra 1000/100', downloadMbps: 1000, uploadMbps: 100, subscriberCount: 12 },
  ])

  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingProfile, setEditingProfile] = useState<SpeedProfile | null>(null)
  const [formData, setFormData] = useState({ name: '', downloadMbps: 0, uploadMbps: 0 })

  const handleAdd = () => {
    setEditingProfile(null)
    setFormData({ name: '', downloadMbps: 100, uploadMbps: 10 })
    setDialogOpen(true)
  }

  const handleEdit = (profile: SpeedProfile) => {
    setEditingProfile(profile)
    setFormData({
      name: profile.name,
      downloadMbps: profile.downloadMbps,
      uploadMbps: profile.uploadMbps,
    })
    setDialogOpen(true)
  }

  const handleDelete = (id: string) => {
    const profile = profiles.find((p) => p.id === id)
    if (profile && profile.subscriberCount > 0) {
      alert(`Cannot delete profile "${profile.name}" - it has ${profile.subscriberCount} active subscribers`)
      return
    }
    if (confirm('Are you sure you want to delete this speed profile?')) {
      setProfiles(profiles.filter((p) => p.id !== id))
    }
  }

  const handleSave = () => {
    if (editingProfile) {
      setProfiles(
        profiles.map((p) =>
          p.id === editingProfile.id
            ? { ...p, ...formData }
            : p
        )
      )
    } else {
      const newProfile: SpeedProfile = {
        id: String(Date.now()),
        ...formData,
        subscriberCount: 0,
      }
      setProfiles([...profiles, newProfile])
    }
    setDialogOpen(false)
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h6">Speed Profiles (Bandwidth Plans)</Typography>
        <Button variant="contained" startIcon={<Add />} onClick={handleAdd}>
          Add Profile
        </Button>
      </Box>

      <TableContainer>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Profile Name</TableCell>
              <TableCell align="center">Download Speed</TableCell>
              <TableCell align="center">Upload Speed</TableCell>
              <TableCell align="center">Active Subscribers</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {profiles.map((profile) => (
              <TableRow key={profile.id}>
                <TableCell sx={{ fontWeight: 500 }}>{profile.name}</TableCell>
                <TableCell align="center">
                  <Chip
                    icon={<ArrowDownward sx={{ fontSize: 16 }} />}
                    label={`${profile.downloadMbps} Mbps`}
                    color="primary"
                    size="small"
                    variant="outlined"
                  />
                </TableCell>
                <TableCell align="center">
                  <Chip
                    icon={<ArrowUpward sx={{ fontSize: 16 }} />}
                    label={`${profile.uploadMbps} Mbps`}
                    color="secondary"
                    size="small"
                    variant="outlined"
                  />
                </TableCell>
                <TableCell align="center">{profile.subscriberCount}</TableCell>
                <TableCell align="right">
                  <IconButton size="small" onClick={() => handleEdit(profile)}>
                    <Edit />
                  </IconButton>
                  <IconButton
                    size="small"
                    color="error"
                    onClick={() => handleDelete(profile.id)}
                    disabled={profile.subscriberCount > 0}
                  >
                    <Delete />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Add/Edit Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{editingProfile ? 'Edit Speed Profile' : 'Add New Speed Profile'}</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Profile Name"
            fullWidth
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            placeholder="e.g., Premium 500/50"
            sx={{ mb: 2, mt: 1 }}
          />
          <TextField
            margin="dense"
            label="Download Speed"
            type="number"
            fullWidth
            value={formData.downloadMbps}
            onChange={(e) => setFormData({ ...formData, downloadMbps: Number(e.target.value) })}
            InputProps={{
              endAdornment: <InputAdornment position="end">Mbps</InputAdornment>,
            }}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Upload Speed"
            type="number"
            fullWidth
            value={formData.uploadMbps}
            onChange={(e) => setFormData({ ...formData, uploadMbps: Number(e.target.value) })}
            InputProps={{
              endAdornment: <InputAdornment position="end">Mbps</InputAdornment>,
            }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleSave} variant="contained" disabled={!formData.name}>
            Save
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default SpeedProfilesSettings
