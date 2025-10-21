# Technical Context: Positron GAM Management System

## Technologies Used

### Backend Stack
- **Python 3.11**: Modern Python with async/await support
- **FastAPI 0.104.1**: High-performance async web framework
- **SQLAlchemy 2.0.23**: Modern ORM with async support
- **PostgreSQL 15**: Primary database with JSONB support
- **Redis 7**: Caching, sessions, and job queue
- **Celery 5.3.4**: Background task processing
- **Alembic 1.12.1**: Database migrations

### Network Automation Libraries
- **netmiko 4.3.0**: SSH connections to GAM devices
- **pysnmp 4.4.12**: SNMP monitoring and configuration
- **paramiko 3.3.1**: Low-level SSH operations
- **httpx 0.25.2**: Async HTTP client for billing APIs

### Frontend Stack (Planned)
- **React 18.2.0**: Modern UI framework
- **TypeScript 4.9.5**: Type safety for complex interfaces
- **Material-UI 5.14.0**: Professional component library
- **React Query 3.39.3**: Server state management
- **Recharts 2.8.0**: Data visualization for monitoring

### Infrastructure
- **Docker & Docker Compose**: Containerized deployment
- **Nginx**: Reverse proxy and SSL termination
- **PostgreSQL**: Persistent data storage
- **Redis**: Caching and job queue

## Development Setup

### Environment Configuration
```bash
# Database (conflict-free ports)
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/positron_gam
REDIS_URL=redis://localhost:6380/0

# Application
SECRET_KEY=dev-secret-key-change-in-production
DEBUG=true
API_HOST=0.0.0.0
API_PORT=8000

# GAM Device Communication
DEFAULT_SNMP_COMMUNITY=public
SNMP_TIMEOUT=10
SSH_TIMEOUT=30

# Billing Integration
SONAR_API_URL=https://your-sonar-instance.com/api
SPLYNX_API_URL=https://your-splynx-instance.com/api/2.0
```

### Docker Configuration
```yaml
# Conflict-free port mapping
services:
  positron_postgres: 5433:5432  # Avoid default 5432
  positron_redis: 6380:6379     # Avoid default 6379  
  positron_backend: 8001:8000   # Avoid default 8000
  positron_frontend: 3001:3000  # Avoid default 3000
```

### Project Structure
```
positron/
├── backend/                    # Python FastAPI backend
│   ├── app/
│   │   ├── models/            # SQLAlchemy database models
│   │   ├── api/v1/            # REST API endpoints
│   │   ├── services/          # Business logic layer
│   │   ├── utils/             # Utility functions
│   │   └── workers/           # Celery background tasks
│   ├── requirements.txt       # Python dependencies
│   └── Dockerfile.dev         # Development container
├── frontend/                  # React TypeScript frontend
├── memory-bank/               # Project documentation
├── docs/                      # Technical documentation
├── tests/                     # Test suites
└── docker-compose.dev.yml     # Development environment
```

## Technical Constraints

### GAM Device Limitations
- **SNMP Access**: Requires community string configuration
- **SSH Access**: Username/password or key-based authentication
- **Concurrent Connections**: Limited simultaneous SSH sessions
- **Configuration Persistence**: Changes must be saved to device flash
- **Firmware Compatibility**: Different firmware versions may have different capabilities

### Network Requirements
- **Management VLAN**: GAM devices typically on VLAN 4093
- **SNMP Ports**: UDP 161 (queries) and 162 (traps)
- **SSH Port**: TCP 22 (configurable)
- **Network Reachability**: Backend must reach all GAM device management IPs

### Billing System Integration
- **API Rate Limits**: Sonar/Splynx have request rate limitations
- **Authentication**: API keys with potential expiration
- **Data Consistency**: Handle eventual consistency between systems
- **Webhook Reliability**: Must handle webhook delivery failures

### Scalability Constraints
- **Database Connections**: PostgreSQL connection pool limits
- **Memory Usage**: SNMP/SSH connection state in memory
- **Background Jobs**: Celery worker capacity for sync operations
- **Real-time Updates**: WebSocket connection limits

## Dependencies

### Critical Dependencies
```python
# Core Framework
fastapi==0.104.1              # Web framework
uvicorn[standard]==0.24.0     # ASGI server

# Database
sqlalchemy==2.0.23           # ORM
alembic==1.12.1              # Migrations
psycopg2-binary==2.9.9       # PostgreSQL driver
asyncpg==0.29.0              # Async PostgreSQL

# Caching & Jobs
redis==5.0.1                 # Cache/sessions
celery==5.3.4                # Background tasks
aioredis==2.0.1              # Async Redis

# Network Automation
netmiko==4.3.0               # SSH to devices
pysnmp==4.4.12               # SNMP operations
paramiko==3.3.1              # SSH library
httpx==0.25.2                # HTTP client

# Security & Validation
pydantic==2.5.0              # Data validation
python-jose[cryptography]==3.3.0  # JWT tokens
passlib[bcrypt]==1.7.4       # Password hashing
```

### Development Dependencies
```python
# Testing
pytest==7.4.3               # Test framework
pytest-asyncio==0.21.1      # Async testing
pytest-mock==3.12.0         # Mocking

# Configuration
python-dotenv==1.0.0        # Environment variables
pydantic-settings==2.1.0    # Settings management
```

## Integration Specifications

### GAM Device Communication

#### SNMP Operations
```python
# Device discovery and monitoring
community = "public"
port = 161
timeout = 10
retries = 3

# Key OIDs for GAM devices
system_description = "1.3.6.1.2.1.1.1.0"
system_uptime = "1.3.6.1.2.1.1.3.0"
interface_table = "1.3.6.1.2.1.2.2.1"
```

#### SSH Configuration
```python
# Connection parameters
port = 22
timeout = 30
connection_timeout = 10
auth_timeout = 10

# Command patterns
show_version = "show version"
show_interfaces = "show interfaces"
configure_subscriber = "configure subscriber {id} vlan {vlan} bandwidth {bw}"
```

### Billing System APIs

#### Sonar Integration
```python
# API Configuration
base_url = "https://instance.sonar.software/api/graphql"
headers = {
    "Authorization": f"Bearer {api_token}",
    "Content-Type": "application/json"
}

# Key GraphQL queries
customers_query = """
query GetCustomers($limit: Int) {
  accounts(limit: $limit) {
    entities {
      id name email_address
      services { id type status }
    }
  }
}
"""
```

#### Splynx Integration
```python
# API Configuration  
base_url = "https://instance.splynx.com/api/2.0"
auth = {
    "auth_type": "api_key",
    "key": api_key,
    "secret": api_secret
}

# Key REST endpoints
customers_endpoint = "/admin/customers/customer"
services_endpoint = "/admin/customers/customer/{id}/internet-services"
```

## Deployment Architecture

### Container Strategy
- **Multi-stage builds**: Optimize image sizes
- **Non-root users**: Security best practices
- **Health checks**: Container orchestration support
- **Volume mounts**: Development hot-reload

### Network Configuration
- **Internal networks**: Container-to-container communication
- **Port mapping**: External access with conflict avoidance
- **Environment variables**: Configuration injection
- **Secrets management**: Secure credential handling

### Data Persistence
- **Named volumes**: Database and Redis data
- **Backup strategies**: Database dump automation
- **Migration handling**: Alembic integration
- **Configuration persistence**: Environment-based config
