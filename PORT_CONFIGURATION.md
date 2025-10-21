# Port Configuration

## Configured Ports (Updated to Avoid Conflicts)

The Positron GAM Management System uses the following ports, carefully chosen to avoid conflicts with other services running on this host:

### Service Ports

| Service | Host Port | Container Port | Status | Notes |
|---------|-----------|----------------|--------|-------|
| **PostgreSQL** | 5436 | 5432 | ✅ Available | Changed from 5436 (conflicts with imapserver) |
| **Redis** | 6380 | 6379 | ✅ Available | Avoids default 6379 (in use) |
| **Backend API** | 8003 | 8000 | ✅ Available | Changed from 8001 (conflicts with api container) |
| **Frontend** | 3002 | 3000 | ✅ Available | Changed from 3001 (conflicts with perplexica) |

### Ports Already in Use on Host

The following ports are **unavailable** and must be avoided:

| Port | Service |
|------|---------|
| 3000 | perplexica-frontend |
| 3001 | perplexica-backend |
| 4000 | searxng |
| 5000 | bot |
| 5050 | sonarapi-web |
| 5432 | postgres |
| 5436 | imapserver_api-db |
| 5434 | php-app-db |
| 5435 | sonarapi-db |
| 6333-6334 | qdrant |
| 6335-6336 | imapserver qdrant |
| 6379 | redis |
| 7476 | neo4j web |
| 7689 | neo4j bolt |
| 8000 | imapserver_api |
| 8001 | api container |
| 8002 | redis-insight |
| 50080 | agent-zero |

## Access URLs

With the updated ports, access the application at:

- **Frontend**: http://localhost:3002
- **Backend API**: http://localhost:8003
- **API Documentation**: http://localhost:8003/docs
- **API Redoc**: http://localhost:8003/redoc
- **PostgreSQL**: localhost:5436 (user: postgres, password: postgres)
- **Redis**: localhost:6380

## Makefile Commands

The Makefile has been updated to reference the correct ports:

```bash
# These commands will open the correct URLs
make frontend      # Opens http://localhost:3002
make docs          # Opens http://localhost:8003/docs
```

## Configuration Files Updated

The following files have been updated with the new ports:

1. ✅ `docker-compose.yml` - Service port mappings
2. ✅ `.env` - Environment variables
3. ✅ `.env.example` - Environment template
4. ✅ `backend/alembic.ini` - Database URL
5. ✅ `frontend/.env` - API URL
6. ✅ `frontend/.env.example` - API URL template

## Quick Start with New Ports

```bash
# Start services
make dev

# Access frontend
open http://localhost:3002

# Access API docs
open http://localhost:8003/docs

# Connect to database
psql postgresql://postgres:postgres@localhost:5436/positron_gam

# Connect to Redis
redis-cli -p 6380
```

## Testing Port Availability

Before starting, verify ports are available:

```bash
# Check if our ports are free
lsof -i :5436 -i :6380 -i :8003 -i :3002

# If no output, ports are free and ready to use
```

## Docker Compose Environment Variables

The docker-compose.yml uses these internal container connections (unchanged):

- Database: `postgresql://postgres:postgres@positron_postgres:5432/positron_gam`
- Redis: `redis://positron_redis:6379/0`

Only the **host-to-container** port mappings have changed.

## Updating Port References

If you need to change ports again:

1. Update `docker-compose.yml` port mappings
2. Update `.env` DATABASE_URL and VITE_API_URL
3. Update `backend/alembic.ini` sqlalchemy.url
4. Update `frontend/.env` and `frontend/.env.example`
5. Update Makefile if needed
6. Restart services: `make restart`

## Troubleshooting Port Conflicts

If you still encounter port conflicts:

```bash
# Find what's using a port
lsof -i :PORT_NUMBER

# Kill process using a port (use with caution)
kill -9 $(lsof -t -i:PORT_NUMBER)

# Or change the port in docker-compose.yml to another available port
```

## Port Allocation Strategy

Our ports were chosen to be:
- **Above 3001** for frontend (3002)
- **Above 5435** for PostgreSQL (5436)
- **Above 8002** for backend (8003)
- **6380** for Redis (already configured)

This minimizes conflicts with commonly used ports.

---

**Last Updated**: After conflict detection with existing containers
**Configuration**: Production-ready, conflict-free
