# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Positron GAM Management System - An open-source, self-hosted management system for Positron GAM (G.hn Access Multiplexer) equipment. Replaces VIRTUOSO's paid management features and integrates with Sonar and Splynx billing systems for managing 11-50 GAM units.

**Tech Stack:**
- Backend: Python FastAPI with async/await
- Database: PostgreSQL with SQLAlchemy ORM (asyncpg driver)
- Cache/Queue: Redis with Celery for background jobs
- Frontend: React with TypeScript and Material-UI (planned)
- Deployment: Docker containers via docker-compose

## Development Commands

### Docker Development Environment

```bash
# Start all services (backend, postgres, redis, celery)
docker-compose -f docker-compose.dev.yml up -d

# View logs (all services or specific service)
docker-compose -f docker-compose.dev.yml logs -f
docker-compose -f docker-compose.dev.yml logs -f positron_backend

# Stop all services
docker-compose -f docker-compose.dev.yml down

# Rebuild containers after dependency changes
docker-compose -f docker-compose.dev.yml up -d --build
```

### Database Management

```bash
# Run migrations
docker-compose -f docker-compose.dev.yml exec positron_backend alembic upgrade head

# Create new migration
docker-compose -f docker-compose.dev.yml exec positron_backend alembic revision --autogenerate -m "migration message"

# Rollback migration
docker-compose -f docker-compose.dev.yml exec positron_backend alembic downgrade -1
```

### Testing

```bash
# Run tests inside container
docker-compose -f docker-compose.dev.yml exec positron_backend pytest

# Run specific test file
docker-compose -f docker-compose.dev.yml exec positron_backend pytest tests/unit/test_gam_manager.py

# Run with coverage
docker-compose -f docker-compose.dev.yml exec positron_backend pytest --cov=app tests/
```

## Architecture

### Backend Structure

The backend follows a layered architecture:

1. **API Layer** (`app/api/v1/`): FastAPI endpoints, request/response handling
2. **Service Layer** (`app/services/`): Business logic for device management, provisioning, and billing integration
3. **Model Layer** (`app/models/`): SQLAlchemy ORM models
4. **Utils Layer** (`app/utils/`): SNMP/SSH clients, validators, helpers
5. **Workers** (`app/workers/`): Celery background tasks for sync and monitoring

### Database Models

Key models and their relationships:

- **GAMDevice**: Physical GAM hardware units
  - Fields: ip_address, model (GAM-12-M/24-M/12-C/24-C), status, SNMP/SSH credentials
  - Has many GAMPort and Subscriber
  - Properties: `port_count`, `active_subscribers`, `is_coax_model`, `is_copper_model`

- **GAMPort**: Individual ports on GAM devices
  - Fields: port_number, port_type (MIMO/SISO/COAX), status, link speeds, SNR values
  - Belongs to GAMDevice, has many Subscriber
  - Property: `is_available` (accounts for coax multi-subscriber support - up to 16 per port)

- **Subscriber**: Customer service configurations
  - Belongs to GAMDevice and GAMPort
  - Links to BandwidthPlan and ExternalSystem
  - Fields: vlan_id, endpoint_mac, external_id (Sonar/Splynx customer ID)

- **BandwidthPlan**: Service speed tiers
  - Fields: downstream_mbps, upstream_mbps

- **ExternalSystem**: Billing system integrations (Sonar/Splynx)
  - Manages API credentials and sync configuration

- **SyncJob**: Background job tracking for billing system synchronization

### Port Configuration

**Important port mappings** (avoid conflicts with existing services):
- PostgreSQL: 5436 (host) → 5432 (container)
- Redis: 6380 (host) → 6379 (container)
- Backend API: 8001 (host) → 8000 (container)
- Frontend: 3001 (host) → 3000 (container)

### Device Communication

GAM devices are managed via:
- **SNMP**: Monitoring, status collection, device discovery (pysnmp library)
- **SSH**: Configuration changes, provisioning commands (netmiko/paramiko)

### Configuration Management

Environment variables are managed via:
1. `.env` file (copy from `.env.example`)
2. `app/config.py` using pydantic-settings
3. Docker environment overrides in docker-compose files

**Important defaults:**
- Default management VLAN: 4093
- Subscriber VLAN range: 100-4000
- SNMP community: "public" (change in production)

### Async Patterns

The codebase uses async/await throughout:
- Database operations: `AsyncSession` from SQLAlchemy
- API endpoints: `async def` functions
- External API calls: `httpx` for async HTTP
- Database dependency injection: `get_db()` async generator

## GAM Device Models

Supported models with port-specific behavior:
- **GAM-12-M**: 12-port copper (MIMO/SISO)
- **GAM-24-M**: 24-port copper (MIMO/SISO)
- **GAM-12-C**: 12-port coax (up to 16 subscribers per port)
- **GAM-24-C**: 24-port coax (up to 16 subscribers per port)

Coax ports support multiple subscribers (up to 16), while copper ports support one subscriber per port.

## Billing Integration

Two-way sync with:
- **Sonar**: API-based customer/service sync with webhooks
- **Splynx**: API-based customer/service sync with webhooks

Celery workers handle scheduled synchronization jobs. Webhook handlers process real-time updates from billing systems.

## Current Development Phase

Phase 1 (Foundation) is mostly complete:
- ✅ Docker environment configured
- ✅ Database models defined
- ✅ Basic backend structure created
- ⏳ FastAPI application skeleton (main.py not yet implemented)

Next steps: Phase 2 - Device Management (API routes, SNMP/SSH clients, device discovery)
