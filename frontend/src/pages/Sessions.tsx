import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  IconButton,
  Tooltip,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Button,
} from '@mui/material'
import { Delete as DeleteIcon } from '@mui/icons-material'
import { format } from 'date-fns'
import Breadcrumb from '../components/Breadcrumb'
import ListToolbar from '../components/ListToolbar'
import { sessionsApi } from '../services/api'

interface Session {
  id: string
  session_id: string
  user_id: string
  username: string
  ip_address: string
  user_agent: string
  privilege_level: number
  created_at: string
  last_activity: string
  expires_at: string
  is_current?: boolean
}

export default function Sessions() {
  const queryClient = useQueryClient()
  const [searchQuery, setSearchQuery] = useState('')
  const [confirmDialog, setConfirmDialog] = useState<{ open: boolean; sessionId: string | null }>({
    open: false,
    sessionId: null,
  })

  const { data: sessions, isLoading } = useQuery({
    queryKey: ['sessions'],
    queryFn: () => sessionsApi.list().then((res) => res.data),
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  const terminateMutation = useMutation({
    mutationFn: (sessionId: string) => sessionsApi.terminate(sessionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sessions'] })
      setConfirmDialog({ open: false, sessionId: null })
    },
  })

  const handleTerminate = (sessionId: string) => {
    setConfirmDialog({ open: true, sessionId })
  }

  const confirmTerminate = () => {
    if (confirmDialog.sessionId) {
      terminateMutation.mutate(confirmDialog.sessionId)
    }
  }

  const filteredSessions = (sessions || []).filter((session: Session) =>
    session.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
    session.ip_address.includes(searchQuery)
  )

  // Available columns
  const columns = [
    { id: 'ip_address', label: 'IP Address', sortable: true },
    { id: 'username', label: 'Username', sortable: true },
    { id: 'accessed', label: 'Accessed Time', sortable: true },
    { id: 'privileges', label: 'Privileges', sortable: true },
    { id: 'actions', label: 'Actions', sortable: false },
  ]

  return (
    <Box>
      <Breadcrumb current="Active Sessions" />

      <ListToolbar
        search={searchQuery}
        onSearchChange={setSearchQuery}
        searchPlaceholder="Search..."
        page={0}
        pageSize={100}
        total={filteredSessions?.length || 0}
        onPageChange={() => {}}
        onPageSizeChange={() => {}}
      />

      <Paper>

        {isLoading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  {columns.map((col) => (
                    <TableCell key={col.id}>{col.label}</TableCell>
                  ))}
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredSessions.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={columns.length} align="center">
                      No active sessions
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredSessions.map((session: Session) => (
                    <TableRow key={session.id || session.session_id}>
                      <TableCell>{session.ip_address}</TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          {session.username}
                          {session.is_current && (
                            <Chip
                              label="Current"
                              size="small"
                              color="primary"
                              sx={{ ml: 1 }}
                            />
                          )}
                        </Box>
                      </TableCell>
                      <TableCell>
                        {session.last_activity
                          ? format(new Date(session.last_activity), 'yyyy-MM-dd hh:mm a')
                          : '-'}
                      </TableCell>
                      <TableCell>{session.privilege_level}</TableCell>
                      <TableCell>
                        {!session.is_current && (
                          <Tooltip title="Terminate Session">
                            <IconButton
                              size="small"
                              color="error"
                              onClick={() => handleTerminate(session.session_id || session.id)}
                            >
                              <DeleteIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        )}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>

      {/* Confirm Terminate Dialog */}
      <Dialog open={confirmDialog.open} onClose={() => setConfirmDialog({ open: false, sessionId: null })}>
        <DialogTitle>Terminate Session</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to terminate this session? The user will be logged out immediately.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmDialog({ open: false, sessionId: null })}>Cancel</Button>
          <Button onClick={confirmTerminate} color="error" variant="contained">
            Terminate
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
