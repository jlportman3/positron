# Positron GAM Management System

An open-source, self-hosted management system for Positron GAM (G.hn Access Multiplexer) equipment that replaces VIRTUOSO's paid management features and integrates with Sonar and Splynx billing systems.

## Features

- **GAM Device Management**: Centralized management for 11-50 GAM units
- **Subscriber Provisioning**: Automated subscriber service provisioning
- **Billing Integration**: Two-way sync with Sonar and Splynx systems
- **Monitoring & Diagnostics**: Real-time device health and performance monitoring
- **Modern Web Interface**: React-based dashboard for easy management
- **Docker Deployment**: Easy deployment and scaling with Docker containers

## Architecture

- **Backend**: Python FastAPI with async support
- **Frontend**: React with TypeScript and Material-UI
- **Database**: PostgreSQL for data persistence
- **Cache/Queue**: Redis for job processing and caching
- **Deployment**: Docker containers with docker-compose

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Git
- Make (optional, but recommended)

### Installation

#### Option 1: Using Makefile (Recommended)

```bash
# 1. Navigate to project
cd positron

# 2. Complete setup
make setup

# 3. Access the application
make frontend  # Opens http://localhost:3002
make docs      # Opens http://localhost:8003/docs
```

#### Option 2: Manual Setup

1. **Clone and configure**
   ```bash
   cd positron
   cp .env.example .env
   ```

2. **Start services**
   ```bash
   docker-compose -f docker-compose.dev.yml up -d
   ```

3. **Run migrations**
   ```bash
   docker-compose -f docker-compose.dev.yml exec positron_backend alembic upgrade head
   ```

4. **Access the application**
   - Frontend: http://localhost:3002
   - Backend API: http://localhost:8003
   - API Documentation: http://localhost:8003/docs

### Makefile Commands

```bash
make help      # Show all available commands
make dev       # Start development environment
make logs      # View logs
make test      # Run tests
make migrate   # Run database migrations
make backup    # Backup database
```

See [MAKEFILE_GUIDE.md](MAKEFILE_GUIDE.md) for complete command reference.

### Port Configuration

The system uses the following ports to avoid conflicts with existing applications:

- **PostgreSQL**: 5436 (instead of default 5432)
- **Redis**: 6380 (instead of default 6379)
- **Backend API**: 8001 (instead of default 8000)
- **Frontend**: 3001 (instead of default 3000)

## Supported GAM Models

- **GAM-12-M**: 12-port copper (MIMO/SISO)
- **GAM-24-M**: 24-port copper (MIMO/SISO)
- **GAM-12-C**: 12-port coax
- **GAM-24-C**: 24-port coax

## Integration Support

### Sonar
- Customer synchronization
- Service provisioning
- Billing status updates
- Webhook support

### Splynx
- Customer synchronization
- Service provisioning
- Billing status updates
- Webhook support

## Development

### Project Structure

```
positron/
├── backend/                 # Python FastAPI backend
│   ├── app/
│   │   ├── models/         # Database models
│   │   ├── api/            # API endpoints
│   │   ├── services/       # Business logic
│   │   ├── utils/          # Utilities
│   │   └── workers/        # Background workers
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile.dev      # Development container
├── frontend/               # React frontend (to be created)
├── docs/                   # Documentation
├── tests/                  # Test suites
├── docker-compose.dev.yml  # Development environment
└── .env.example           # Environment template
```

### Database Models

- **GAMDevice**: GAM hardware units with connection settings
- **GAMPort**: Individual ports on GAM devices
- **Subscriber**: Customer service configurations
- **BandwidthPlan**: Service speed and pricing plans
- **ExternalSystem**: Billing system integrations
- **SyncJob**: Background synchronization tasks

### Development Commands

#### Using Makefile
```bash
make dev       # Start development environment
make logs      # View logs
make stop      # Stop environment
make rebuild   # Rebuild containers
make test      # Run tests
make migrate   # Run database migrations
```

#### Using Docker Compose
```bash
docker-compose -f docker-compose.dev.yml up -d      # Start
docker-compose -f docker-compose.dev.yml logs -f    # Logs
docker-compose -f docker-compose.dev.yml down       # Stop
docker-compose -f docker-compose.dev.yml up -d --build  # Rebuild
```

## Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5436/positron_gam

# Redis
REDIS_URL=redis://localhost:6380/0

# Sonar Integration
SONAR_API_URL=https://your-sonar-instance.com/api
SONAR_API_KEY=your-sonar-api-key

# Splynx Integration
SPLYNX_API_URL=https://your-splynx-instance.com/api/2.0
SPLYNX_API_KEY=your-splynx-api-key
SPLYNX_API_SECRET=your-splynx-api-secret

# GAM Device Defaults
DEFAULT_SNMP_COMMUNITY=public
DEFAULT_MANAGEMENT_VLAN=4093
```

### GAM Device Connection

The system connects to GAM devices using:
- **SNMP**: For monitoring and status collection
- **SSH**: For configuration changes and provisioning

## Roadmap

### Phase 1: Foundation ✅
- [x] Project setup and Docker environment
- [x] Database models and configuration
- [x] Basic backend structure

### Phase 2: Device Management (In Progress)
- [ ] FastAPI application and API routes
- [ ] SNMP/SSH communication clients
- [ ] GAM device discovery and registration
- [ ] Basic web interface

### Phase 3: Subscriber Management
- [ ] Subscriber provisioning engine
- [ ] VLAN and bandwidth management
- [ ] Service lifecycle management

### Phase 4: Billing Integration
- [ ] Sonar API client and sync
- [ ] Splynx API client and sync
- [ ] Webhook handling
- [ ] Conflict resolution

### Phase 5: Advanced Features
- [ ] Monitoring and alerting
- [ ] Bulk operations
- [ ] Reporting and analytics

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is open source. See LICENSE file for details.

## Support

For questions and support:
- Create an issue in the repository
- Check the documentation in the `docs/` directory
- Review the implementation plan in `implementation_plan.md`
