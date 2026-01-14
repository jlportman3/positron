import { Box, Typography, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Chip } from '@mui/material'

const GAMTypesSettings = () => {
  const gamModels = [
    { model: 'GAM-4-M', ports: 4, technology: 'Copper', maxSubscribersPerPort: 1 },
    { model: 'GAM-8-M', ports: 8, technology: 'Copper', maxSubscribersPerPort: 1 },
    { model: 'GAM-12-M', ports: 12, technology: 'Copper', maxSubscribersPerPort: 1 },
    { model: 'GAM-24-M', ports: 24, technology: 'Copper', maxSubscribersPerPort: 1 },
    { model: 'GAM-4-C', ports: 4, technology: 'Coax', maxSubscribersPerPort: 16 },
    { model: 'GAM-12-C', ports: 12, technology: 'Coax', maxSubscribersPerPort: 16 },
    { model: 'GAM-24-C', ports: 24, technology: 'Coax', maxSubscribersPerPort: 16 },
  ]

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        GAM Device Types
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Supported Positron GAM models and their specifications.
      </Typography>

      <TableContainer>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Model</TableCell>
              <TableCell align="center">Ports</TableCell>
              <TableCell align="center">Technology</TableCell>
              <TableCell align="center">Max Subscribers/Port</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {gamModels.map((model) => (
              <TableRow key={model.model}>
                <TableCell sx={{ fontWeight: 500 }}>{model.model}</TableCell>
                <TableCell align="center">{model.ports}</TableCell>
                <TableCell align="center">
                  <Chip
                    label={model.technology}
                    color={model.technology === 'Copper' ? 'primary' : 'secondary'}
                    size="small"
                  />
                </TableCell>
                <TableCell align="center">{model.maxSubscribersPerPort}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  )
}

export default GAMTypesSettings
