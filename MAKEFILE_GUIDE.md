# Makefile Command Reference

The Positron GAM Management System includes a comprehensive Makefile for easy development, deployment, and maintenance.

## Quick Reference

```bash
make help          # Show all available commands
make setup         # Complete initial setup
make dev           # Start development environment
make logs          # View logs
make migrate       # Run database migrations
make test          # Run tests
```

## Installation & Setup

### Initial Setup
```bash
make setup         # Build, start, and initialize everything
make verify        # Verify installation
make check         # Health check all services
```

### Manual Setup Steps
```bash
make dev-build     # Build and start services
make migrate       # Run database migrations
make seed          # Load sample data (optional)
```

## Development Commands

### Starting/Stopping Services
```bash
make dev           # Start development environment
make dev-build     # Build and start (rebuilds containers)
make stop          # Stop services (keeps containers)
make down          # Stop and remove containers
make restart       # Restart all services
```

### Viewing Logs
```bash
make logs              # All services
make logs-backend      # Backend only
make logs-frontend     # Frontend only
make logs-db           # Database only
make tail              # Tail last 100 lines
make tail SVC=backend  # Tail specific service
```

### Service Status
```bash
make status        # Show container status
make ps            # Show running containers
make stats         # Show resource usage
make check         # Health check services
make ports         # Show port usage
```

## Database Operations

### Migrations
```bash
make migrate                              # Apply all pending migrations
make migrate-create MSG="add user table" # Create new migration
make migrate-rollback                     # Rollback last migration
make migrate-history                      # View migration history
```

### Database Management
```bash
make db-shell      # Access PostgreSQL shell
make backup        # Backup database
make restore FILE=backups/backup.sql  # Restore from backup
make seed          # Load sample data
make db-reset      # Reset database (WARNING: deletes all data)
```

### Example Migration Workflow
```bash
# 1. Create a new migration
make migrate-create MSG="add bandwidth limits"

# 2. Apply the migration
make migrate

# 3. If something goes wrong, rollback
make migrate-rollback
```

## Testing & Quality

### Running Tests
```bash
make test              # Run backend tests
make test-cov          # Run with coverage report
make test-frontend     # Run frontend tests
```

### Code Quality
```bash
make lint              # Lint backend code
make lint-frontend     # Lint frontend code
```

## Shell Access

```bash
make shell-backend     # Access backend container
make shell-frontend    # Access frontend container
make shell-db          # Access database container
```

### Example: Installing a Package
```bash
# Backend
make shell-backend
pip install new-package
# Update requirements.txt manually

# Frontend
make shell-frontend
npm install new-package
```

## Production Deployment

### Deploy to Production
```bash
make prod-build        # Build production images
make prod-deploy       # Full deployment (build, up, migrate)
make prod              # Start production services
make prod-down         # Stop production services
make prod-logs         # View production logs
```

### Production Deployment Workflow
```bash
# 1. Build production images
make prod-build

# 2. Deploy (automatically runs migrations)
make prod-deploy

# 3. Check health
make check

# 4. Monitor logs
make prod-logs
```

## Maintenance

### Cleanup
```bash
make clean         # Clean containers and volumes
make clean-all     # Clean everything including images
make prune         # Remove unused Docker resources
```

### Updates
```bash
make update        # Pull latest code and restart
make rebuild       # Rebuild all containers from scratch
```

### Quick Commands
```bash
make quick-start   # Fast setup (alias for setup)
make quick-stop    # Fast stop (alias for down)
make quick-restart # Down, up, and migrate
```

## Utility Commands

### Information
```bash
make env           # Show environment variables
make version       # Show version information
make info          # Show system information
make images        # Show Docker images
make volumes       # Show Docker volumes
```

### Open in Browser
```bash
make docs          # Open API documentation
make frontend      # Open frontend application
```

### Advanced Operations
```bash
make exec CMD="python manage.py shell"  # Execute command in backend
make scale NUM=4                        # Scale backend to 4 instances
```

## Common Workflows

### Daily Development
```bash
# Start working
make dev
make logs

# Make changes to code (auto-reloads)

# Run tests
make test

# View logs if needed
make logs-backend

# Stop when done
make stop
```

### Adding a Database Model
```bash
# 1. Edit model file
vim backend/app/models/new_model.py

# 2. Create migration
make migrate-create MSG="add new model"

# 3. Apply migration
make migrate

# 4. Verify
make db-shell
\dt  # List tables
```

### Debugging Issues
```bash
# Check service health
make check

# View logs
make logs

# Check specific service
make logs-backend

# Access container shell
make shell-backend

# Check database
make db-shell
```

### Backup and Restore
```bash
# Create backup before major changes
make backup

# If something goes wrong, restore
make restore FILE=backups/backup_20251003_120000.sql

# Or reset everything
make db-reset
```

### Testing a Pull Request
```bash
# 1. Pull latest changes
git pull

# 2. Rebuild and restart
make rebuild

# 3. Run migrations
make migrate

# 4. Run tests
make test

# 5. Check health
make check
```

### Production Hotfix
```bash
# 1. Pull hotfix
git pull

# 2. Backup production database
make backup

# 3. Deploy update
make prod-deploy

# 4. Verify
make check
make prod-logs
```

## Troubleshooting

### Services Won't Start
```bash
# Check what's running
make status

# Check port conflicts
make ports

# View logs for errors
make logs

# Try rebuilding
make rebuild
```

### Database Issues
```bash
# Check database container
make status

# Access database
make db-shell

# Check logs
make logs-db

# If corrupted, reset (WARNING: deletes data)
make db-reset
```

### Frontend Not Loading
```bash
# Check logs
make logs-frontend

# Rebuild frontend
make down
make dev-build

# Verify health
make check
```

### Migration Errors
```bash
# Check migration status
make migrate-history

# Rollback problematic migration
make migrate-rollback

# Fix migration file, then reapply
make migrate
```

## Environment Variables

The Makefile uses these environment variables:

- `MSG` - Message for creating migrations
- `FILE` - File path for database restore
- `SVC` - Service name for targeted operations
- `CMD` - Command to execute in container
- `NUM` - Number of instances for scaling

### Examples
```bash
make migrate-create MSG="add user permissions"
make restore FILE=backups/backup_20251003.sql
make tail SVC=backend
make exec CMD="pytest tests/test_api.py"
make scale NUM=3
```

## Tips & Best Practices

1. **Always backup before major changes**
   ```bash
   make backup
   ```

2. **Use `make check` regularly**
   ```bash
   make check  # Quick health check
   ```

3. **Monitor logs during development**
   ```bash
   make logs  # Keep this running in a separate terminal
   ```

4. **Clean up regularly**
   ```bash
   make prune  # Remove unused Docker resources
   ```

5. **Create migrations with descriptive names**
   ```bash
   make migrate-create MSG="add subscriber status field"
   ```

6. **Use quick commands for speed**
   ```bash
   make quick-restart  # Faster than down + dev + migrate
   ```

## Keyboard Shortcuts Workflow

For even faster development:

```bash
# Terminal 1: Logs
make logs

# Terminal 2: Commands
make dev          # Start
make test         # Test
make migrate      # Update DB
make shell-backend # Debug
```

## Getting Help

```bash
make help     # Show all commands with descriptions
```

For detailed information about specific features, see:
- [README.md](README.md) - Project overview
- [QUICKSTART.md](QUICKSTART.md) - Getting started guide
- [DEPLOYMENT.md](DEPLOYMENT.md) - Production deployment
- [PROJECT_STATUS.md](PROJECT_STATUS.md) - Current status
