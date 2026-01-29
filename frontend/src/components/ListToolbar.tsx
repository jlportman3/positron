import { useState } from 'react'
import {
  Box,
  TextField,
  InputAdornment,
  FormControl,
  Select,
  MenuItem,
  IconButton,
  Button,
  Menu,
  Typography,
  Checkbox,
  ListItemText,
} from '@mui/material'
import {
  Search as SearchIcon,
  ChevronLeft as PrevIcon,
  ChevronRight as NextIcon,
  KeyboardArrowDown as ArrowDownIcon,
} from '@mui/icons-material'

interface FilterOption {
  value: string
  label: string
}

interface ColumnOption {
  id: string
  label: string
  visible: boolean
}

interface ListToolbarProps {
  search?: string
  onSearchChange?: (value: string) => void
  searchPlaceholder?: string
  filters?: {
    value: string
    onChange: (value: string) => void
    options: FilterOption[]
    label?: string
  }[]
  page: number
  pageSize: number
  total: number
  onPageChange: (page: number) => void
  onPageSizeChange: (size: number) => void
  pageSizeOptions?: number[]
  actions?: {
    label: string
    onClick: () => void
    disabled?: boolean
  }[]
  columns?: ColumnOption[]
  onColumnsChange?: (columns: ColumnOption[]) => void
}

export default function ListToolbar({
  search,
  onSearchChange,
  searchPlaceholder = 'Search...',
  filters = [],
  page,
  pageSize,
  total,
  onPageChange,
  onPageSizeChange,
  pageSizeOptions = [20, 50, 100, 500],
  actions = [],
  columns,
  onColumnsChange,
}: ListToolbarProps) {
  const [actionsAnchor, setActionsAnchor] = useState<null | HTMLElement>(null)
  const [columnsAnchor, setColumnsAnchor] = useState<null | HTMLElement>(null)

  const totalPages = Math.ceil(total / pageSize)
  const startRow = page * pageSize + 1
  const endRow = Math.min((page + 1) * pageSize, total)

  const handleColumnToggle = (columnId: string) => {
    if (columns && onColumnsChange) {
      const updated = columns.map((col) =>
        col.id === columnId ? { ...col, visible: !col.visible } : col
      )
      onColumnsChange(updated)
    }
  }

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 1.5,
        mb: 2,
        flexWrap: 'wrap',
      }}
    >
      {/* Search */}
      {onSearchChange && (
        <TextField
          size="small"
          placeholder={searchPlaceholder}
          value={search || ''}
          onChange={(e) => onSearchChange(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon sx={{ color: '#999', fontSize: 20 }} />
              </InputAdornment>
            ),
          }}
          sx={{
            width: 200,
            '& .MuiOutlinedInput-root': {
              backgroundColor: '#fff',
              fontSize: '0.875rem',
            },
          }}
        />
      )}

      {/* Filters */}
      {filters.map((filter, index) => (
        <FormControl key={index} size="small" sx={{ minWidth: 140 }}>
          <Select
            value={filter.value}
            onChange={(e) => filter.onChange(e.target.value)}
            displayEmpty
            sx={{
              backgroundColor: '#fff',
              fontSize: '0.875rem',
            }}
          >
            {filter.options.map((opt) => (
              <MenuItem key={opt.value} value={opt.value}>
                {opt.label}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      ))}

      {/* Spacer */}
      <Box sx={{ flexGrow: 1 }} />

      {/* Pagination */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
        <IconButton
          size="small"
          onClick={() => onPageChange(page - 1)}
          disabled={page === 0}
          sx={{
            border: '1px solid #ddd',
            borderRadius: 1,
            width: 28,
            height: 28,
          }}
        >
          <PrevIcon sx={{ fontSize: 18 }} />
        </IconButton>
        <IconButton
          size="small"
          onClick={() => onPageChange(page + 1)}
          disabled={page >= totalPages - 1}
          sx={{
            border: '1px solid #ddd',
            borderRadius: 1,
            width: 28,
            height: 28,
          }}
        >
          <NextIcon sx={{ fontSize: 18 }} />
        </IconButton>
        <FormControl size="small" sx={{ minWidth: 100 }}>
          <Select
            value={pageSize}
            onChange={(e) => onPageSizeChange(Number(e.target.value))}
            sx={{
              backgroundColor: '#fff',
              fontSize: '0.8125rem',
              '& .MuiSelect-select': {
                py: 0.5,
              },
            }}
          >
            {pageSizeOptions.map((size) => (
              <MenuItem key={size} value={size}>
                {size} rows
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <Typography
          variant="body2"
          sx={{ color: '#666', fontSize: '0.8125rem', ml: 1 }}
        >
          {startRow}-{endRow} of {total}
        </Typography>
      </Box>

      {/* Actions Button */}
      {actions.length > 0 && (
        <>
          <Button
            variant="outlined"
            size="small"
            endIcon={<ArrowDownIcon />}
            onClick={(e) => setActionsAnchor(e.currentTarget)}
            sx={{
              textTransform: 'uppercase',
              fontSize: '0.75rem',
              fontWeight: 600,
              borderColor: '#51bcda',
              color: '#51bcda',
              '&:hover': {
                borderColor: '#3a9fc0',
                backgroundColor: 'rgba(81, 188, 218, 0.08)',
              },
            }}
          >
            Actions
          </Button>
          <Menu
            anchorEl={actionsAnchor}
            open={Boolean(actionsAnchor)}
            onClose={() => setActionsAnchor(null)}
          >
            {actions.map((action, index) => (
              <MenuItem
                key={index}
                onClick={() => {
                  action.onClick()
                  setActionsAnchor(null)
                }}
                disabled={action.disabled}
              >
                {action.label}
              </MenuItem>
            ))}
          </Menu>
        </>
      )}

      {/* Columns Button */}
      {columns && onColumnsChange && (
        <>
          <Button
            variant="outlined"
            size="small"
            endIcon={<ArrowDownIcon />}
            onClick={(e) => setColumnsAnchor(e.currentTarget)}
            sx={{
              textTransform: 'uppercase',
              fontSize: '0.75rem',
              fontWeight: 600,
              borderColor: '#51bcda',
              color: '#51bcda',
              '&:hover': {
                borderColor: '#3a9fc0',
                backgroundColor: 'rgba(81, 188, 218, 0.08)',
              },
            }}
          >
            Columns
          </Button>
          <Menu
            anchorEl={columnsAnchor}
            open={Boolean(columnsAnchor)}
            onClose={() => setColumnsAnchor(null)}
          >
            {columns.map((column) => (
              <MenuItem
                key={column.id}
                onClick={() => handleColumnToggle(column.id)}
                dense
              >
                <Checkbox
                  checked={column.visible}
                  size="small"
                  sx={{ p: 0, mr: 1 }}
                />
                <ListItemText primary={column.label} />
              </MenuItem>
            ))}
          </Menu>
        </>
      )}
    </Box>
  )
}
