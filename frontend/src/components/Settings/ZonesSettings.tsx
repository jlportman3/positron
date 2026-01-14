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
} from '@mui/material'
import { Add, Edit, Delete } from '@mui/icons-material'

interface Zone {
  id: string
  name: string
  description: string
  gamCount: number
}

const ZonesSettings = () => {
  const [zones, setZones] = useState<Zone[]>([
    { id: '1', name: 'Headquarters', description: 'Main building distribution', gamCount: 5 },
    { id: '2', name: 'North Campus', description: 'Northern distribution point', gamCount: 3 },
    { id: '3', name: 'South Campus', description: 'Southern distribution point', gamCount: 2 },
  ])

  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingZone, setEditingZone] = useState<Zone | null>(null)
  const [formData, setFormData] = useState({ name: '', description: '' })

  const handleAdd = () => {
    setEditingZone(null)
    setFormData({ name: '', description: '' })
    setDialogOpen(true)
  }

  const handleEdit = (zone: Zone) => {
    setEditingZone(zone)
    setFormData({ name: zone.name, description: zone.description })
    setDialogOpen(true)
  }

  const handleDelete = (id: string) => {
    if (confirm('Are you sure you want to delete this zone?')) {
      setZones(zones.filter((z) => z.id !== id))
    }
  }

  const handleSave = () => {
    if (editingZone) {
      // Update existing
      setZones(
        zones.map((z) =>
          z.id === editingZone.id
            ? { ...z, name: formData.name, description: formData.description }
            : z
        )
      )
    } else {
      // Add new
      const newZone: Zone = {
        id: String(Date.now()),
        name: formData.name,
        description: formData.description,
        gamCount: 0,
      }
      setZones([...zones, newZone])
    }
    setDialogOpen(false)
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h6">Manage Zones</Typography>
        <Button variant="contained" startIcon={<Add />} onClick={handleAdd}>
          Add Zone
        </Button>
      </Box>

      <TableContainer>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Zone Name</TableCell>
              <TableCell>Description</TableCell>
              <TableCell align="center">GAM Devices</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {zones.map((zone) => (
              <TableRow key={zone.id}>
                <TableCell>{zone.name}</TableCell>
                <TableCell>{zone.description}</TableCell>
                <TableCell align="center">{zone.gamCount}</TableCell>
                <TableCell align="right">
                  <IconButton size="small" onClick={() => handleEdit(zone)}>
                    <Edit />
                  </IconButton>
                  <IconButton size="small" color="error" onClick={() => handleDelete(zone.id)}>
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
        <DialogTitle>{editingZone ? 'Edit Zone' : 'Add New Zone'}</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Zone Name"
            fullWidth
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Description"
            fullWidth
            multiline
            rows={3}
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleSave} variant="contained">
            Save
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default ZonesSettings
