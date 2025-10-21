# Implementation Plan

## Overview

Build an open-source, self-hosted management system for Positron GAM equipment that replaces VIRTUOSO's paid management features, integrates with Sonar and Splynx billing systems, and manages 11-50 GAM units in a medium-scale ISP deployment. The system will provide subscriber management, automated provisioning, and comprehensive device monitoring through a modern web interface deployed via Docker containers.

## Types

Define comprehensive data models and API interfaces for GAM device management, subscriber provisioning, and billing system integration.

### Core Data Models

```python
# Device Models
class GAMDevice:
    id: UUID
    name: str
    ip_address: str
    mac_address: str
    model: str  # GAM-12-M, GAM-24-M, GAM-12-C, GAM-24-C
    firmware_version: str
    location: str
    status: DeviceStatus
    last_seen: datetime
    snmp_community: str
    ssh_credentials: dict
    management_vlan: int
    created_at: datetime
    updated_at: datetime

class GAMPort:
    id: UUID
    gam_device_id: UUID
    port_number: int
    port_type: PortType  # MIMO, SISO, COAX
    status: PortStatus
    name: str
    enabled: bool
    subscriber_id: Optional[UUID]
    
class Subscriber:
    id: UUID
    name: str
    email: str
    phone: str
    service_address: str
    gam_device_id: UUID
    gam_port_id: UUID
    endpoint_mac: str
    vlan_id: int
    bandwidth_plan_id: UUID
    status: SubscriberStatus
    external_id: str  # Sonar/Splynx customer ID
    created_at: datetime
    updated_at: datetime

class BandwidthPlan:
    id: UUID
    name: str
    description: str
    downstream_mbps: int
    upstream_mbps: int
    created_at: datetime

# Integration Models
class ExternalSystem:
    id: UUID
    name: str  # "sonar", "splynx"
    type: SystemType
    api_url: str
    api_key: str
    enabled: bool
    sync_interval: int
    last_sync: datetime

class SyncJob:
    id: UUID
    system_id: UUID
    job_type: JobType
    status: JobStatus
    started_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]
    records_processed: int
```

### API Response Types

```python
class DeviceStatusResponse:
    device_id: UUID
    status: str
    uptime: int
    cpu_usage: float
    memory_usage: float
    temperature: float
    port_count: int
    active_subscribers: int

class ProvisioningRequest:
    subscriber_id: UUID
    gam_device_id: UUID
    port_number: int
    bandwidth_plan_id: UUID
    vlan_id: int
    endpoint_mac: str

class BillingSystemCustomer:
    external_id: str
    name: str
    email: str
    service_address: str
    plan_name: str
    bandwidth_down: int
    bandwidth_up: int
    status: str
```

## Files

Create a modern Python FastAPI backend with React frontend, deployed via Docker containers.

### New Files to Create

**Backend Structure:**
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application entry point
│   ├── config.py                  # Configuration management
│   ├── database.py                # Database connection and models
│   ├── models/
│   │   ├── __init__.py
│   │   ├── gam.py                 # GAM device models
│   │   ├── subscriber.py          # Subscriber models
│   │   ├── bandwidth.py           # Bandwidth plan models
│   │   └── integration.py         # External system models
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── gam.py             # GAM device endpoints
│   │   │   ├── subscribers.py     # Subscriber management
│   │   │   ├── provisioning.py    # Provisioning endpoints
│   │   │   ├── monitoring.py      # Device monitoring
│   │   │   └── integration.py     # Sonar/Splynx integration
│   ├── services/
│   │   ├── __init__.py
│   │   ├── gam_manager.py         # GAM device communication
│   │   ├── provisioning.py        # Provisioning logic
│   │   ├── monitoring.py          # Device monitoring service
│   │   ├── sonar_client.py        # Sonar API integration
│   │   └── splynx_client.py       # Splynx API integration
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── snmp_client.py         # SNMP communication
│   │   ├── ssh_client.py          # SSH communication
│   │   └── validators.py          # Input validation
│   └── workers/
│       ├── __init__.py
│       ├── sync_worker.py         # Background sync jobs
│       └── monitoring_worker.py   # Device monitoring worker
├── requirements.txt               # Python dependencies
├── Dockerfile                     # Backend container
└── alembic/                      # Database migrations
    ├── versions/
    └── alembic.ini
```

**Frontend Structure:**
```
frontend/
├── public/
│   ├── index.html
│   └── favicon.ico
├── src/
│   ├── components/
│   │   ├── Dashboard/
│   │   │   ├── Dashboard.tsx      # Main dashboard
│   │   │   └── DeviceOverview.tsx # Device status overview
│   │   ├── GAM/
│   │   │   ├── GAMList.tsx        # GAM device list
│   │   │   ├── GAMDetail.tsx      # GAM device details
│   │   │   └── PortManagement.tsx # Port configuration
│   │   ├── Subscribers/
│   │   │   ├── SubscriberList.tsx # Subscriber management
│   │   │   ├── SubscriberForm.tsx # Add/edit subscriber
│   │   │   └── Provisioning.tsx   # Provisioning interface
│   │   ├── Integration/
│   │   │   ├── SonarSync.tsx      # Sonar integration
│   │   │   └── SplynxSync.tsx     # Splynx integration
│   │   └── Common/
│   │       ├── Layout.tsx         # App layout
│   │       ├── Navigation.tsx     # Navigation menu
│   │       └── LoadingSpinner.tsx # Loading component
│   ├── services/
│   │   ├── api.ts                 # API client
│   │   ├── gamService.ts          # GAM API calls
│   │   ├── subscriberService.ts   # Subscriber API calls
│   │   └── integrationService.ts  # Integration API calls
│   ├── types/
│   │   ├── gam.ts                 # GAM type definitions
│   │   ├── subscriber.ts          # Subscriber types
│   │   └── api.ts                 # API response types
│   ├── utils/
│   │   ├── constants.ts           # App constants
│   │   └── helpers.ts             # Utility functions
│   ├── App.tsx                    # Main app component
│   └── index.tsx                  # React entry point
├── package.json                   # Node dependencies
├── tsconfig.json                  # TypeScript config
└── Dockerfile                     # Frontend container
```

**Infrastructure Files:**
```
docker-compose.yml                 # Multi-container orchestration
docker-compose.dev.yml             # Development environment
.env.example                       # Environment variables template
nginx.conf                         # Reverse proxy configuration
README.md                          # Project documentation
docs/
├── API.md                         # API documentation
├── DEPLOYMENT.md                  # Deployment guide
└── INTEGRATION.md                 # Sonar/Splynx integration guide
```

### Configuration Files to Create

**docker-compose.yml** - Production deployment
**docker-compose.dev.yml** - Development environment with hot reload
**.env.example** - Environment variables template
**nginx.conf** - Reverse proxy and SSL termination
**requirements.txt** - Python dependencies
**package.json** - Node.js dependencies

## Functions

Implement core device management, provisioning automation, and billing system integration functions.

### New Functions

**GAM Device Management (backend/app/services/gam_manager.py):**
```python
async def discover_gam_devices(network_range: str) -> List[GAMDevice]
async def connect_to_gam(device: GAMDevice) -> GAMConnection
async def get_device_status(device_id: UUID) -> DeviceStatus
async def get_port_status(device_id: UUID, port_number: int) -> PortStatus
async def configure_port(device_id: UUID, port_number: int, config: PortConfig) -> bool
async def create_subscriber_service(device_id: UUID, subscriber_config: SubscriberConfig) -> bool
async def update_bandwidth_plan(device_id: UUID, subscriber_id: UUID, plan: BandwidthPlan) -> bool
async def get_device_diagnostics(device_id: UUID) -> DeviceDiagnostics
```

**Provisioning Service (backend/app/services/provisioning.py):**
```python
async def provision_subscriber(request: ProvisioningRequest) -> ProvisioningResult
async def deprovision_subscriber(subscriber_id: UUID) -> bool
async def update_subscriber_service(subscriber_id: UUID, updates: SubscriberUpdate) -> bool
async def validate_provisioning_request(request: ProvisioningRequest) -> ValidationResult
async def check_port_availability(device_id: UUID, port_number: int) -> bool
async def assign_vlan(subscriber_id: UUID) -> int
```

**Sonar Integration (backend/app/services/sonar_client.py):**
```python
async def authenticate_sonar(api_url: str, api_key: str) -> bool
async def get_sonar_customers() -> List[SonarCustomer]
async def get_customer_services(customer_id: str) -> List[SonarService]
async def sync_customer_to_subscriber(customer: SonarCustomer) -> Subscriber
async def update_service_status(service_id: str, status: str) -> bool
async def create_sonar_webhook(webhook_url: str) -> bool
```

**Splynx Integration (backend/app/services/splynx_client.py):**
```python
async def authenticate_splynx(api_url: str, api_key: str) -> bool
async def get_splynx_customers() -> List[SplynxCustomer]
async def get_customer_services(customer_id: str) -> List[SplynxService]
async def sync_customer_to_subscriber(customer: SplynxCustomer) -> Subscriber
async def update_service_status(service_id: str, status: str) -> bool
async def handle_splynx_webhook(payload: dict) -> bool
```

**Monitoring Service (backend/app/services/monitoring.py):**
```python
async def monitor_all_devices() -> List[DeviceStatus]
async def check_device_health(device_id: UUID) -> HealthStatus
async def collect_device_metrics(device_id: UUID) -> DeviceMetrics
async def detect_device_issues(device_id: UUID) -> List[Issue]
async def send_alert(alert: Alert) -> bool
async def generate_monitoring_report() -> MonitoringReport
```

### Modified Functions

No existing functions to modify - this is a new project.

## Classes

Implement comprehensive device management, subscriber handling, and integration classes.

### New Classes

**GAM Device Management (backend/app/services/gam_manager.py):**
```python
class GAMConnection:
    """Manages connection to a single GAM device via SNMP/SSH"""
    
class GAMManager:
    """Central manager for all GAM devices"""
    
class PortManager:
    """Manages individual GAM ports and their configuration"""
    
class DeviceDiscovery:
    """Discovers GAM devices on the network"""
```

**Provisioning System (backend/app/services/provisioning.py):**
```python
class ProvisioningEngine:
    """Core provisioning logic and workflow management"""
    
class SubscriberProvisioner:
    """Handles subscriber-specific provisioning tasks"""
    
class VLANManager:
    """Manages VLAN assignment and configuration"""
    
class BandwidthManager:
    """Manages bandwidth plan assignment and enforcement"""
```

**Integration Framework (backend/app/services/):**
```python
class BillingSystemClient:
    """Base class for billing system integrations"""
    
class SonarClient(BillingSystemClient):
    """Sonar-specific API client and sync logic"""
    
class SplynxClient(BillingSystemClient):
    """Splynx-specific API client and sync logic"""
    
class WebhookHandler:
    """Handles incoming webhooks from billing systems"""
```

**Monitoring System (backend/app/services/monitoring.py):**
```python
class DeviceMonitor:
    """Monitors individual device health and performance"""
    
class AlertManager:
    """Manages alerts and notifications"""
    
class MetricsCollector:
    """Collects and stores device metrics"""
    
class HealthChecker:
    """Performs health checks on devices and services"""
```

### Frontend Classes (TypeScript)

**React Components (frontend/src/components/):**
```typescript
class GAMDeviceManager {
    // GAM device state management
}

class SubscriberManager {
    // Subscriber state management
}

class ProvisioningWorkflow {
    // Provisioning workflow management
}

class IntegrationManager {
    // Billing system integration management
}
```

## Dependencies

Add modern Python and Node.js dependencies for network automation, API development, and web interface.

### Backend Dependencies (requirements.txt)
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
alembic==1.12.1
psycopg2-binary==2.9.9
redis==5.0.1
celery==5.3.4
pydantic==2.5.0
pydantic-settings==2.1.0
netmiko==4.3.0
pysnmp==4.4.12
paramiko==3.3.1
httpx==0.25.2
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
pytest==7.4.3
pytest-asyncio==0.21.1
```

### Frontend Dependencies (package.json)
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.8.0",
    "typescript": "^4.9.5",
    "@types/react": "^18.0.28",
    "@types/react-dom": "^18.0.11",
    "axios": "^1.6.0",
    "react-query": "^3.39.3",
    "@mui/material": "^5.14.0",
    "@mui/icons-material": "^5.14.0",
    "@emotion/react": "^11.11.0",
    "@emotion/styled": "^11.11.0",
    "recharts": "^2.8.0",
    "react-hook-form": "^7.47.0",
    "date-fns": "^2.30.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.0.3",
    "vite": "^4.4.5",
    "eslint": "^8.45.0",
    "@typescript-eslint/eslint-plugin": "^6.0.0",
    "@typescript-eslint/parser": "^6.0.0"
  }
}
```

### Infrastructure Dependencies
- **PostgreSQL 15** - Primary database
- **Redis 7** - Caching and job queue
- **Nginx** - Reverse proxy and SSL termination
- **Docker & Docker Compose** - Containerization

## Testing

Implement comprehensive testing strategy for device communication, provisioning workflows, and integration reliability.

### Backend Testing Structure
```
tests/
├── unit/
│   ├── test_gam_manager.py        # GAM device management tests
│   ├── test_provisioning.py       # Provisioning logic tests
│   ├── test_sonar_client.py       # Sonar integration tests
│   └── test_splynx_client.py      # Splynx integration tests
├── integration/
│   ├── test_gam_communication.py  # Real GAM device tests
│   ├── test_billing_sync.py       # End-to-end sync tests
│   └── test_provisioning_flow.py  # Complete provisioning tests
└── fixtures/
    ├── gam_responses.py           # Mock GAM responses
    ├── sonar_data.py              # Mock Sonar data
    └── splynx_data.py             # Mock Splynx data
```

### Frontend Testing
```
frontend/src/__tests__/
├── components/
│   ├── GAMList.test.tsx
│   ├── SubscriberForm.test.tsx
│   └── Provisioning.test.tsx
├── services/
│   ├── api.test.ts
│   └── gamService.test.ts
└── utils/
    └── helpers.test.ts
```

### Test Configuration Files
- **pytest.ini** - Python test configuration
- **jest.config.js** - JavaScript test configuration
- **docker-compose.test.yml** - Test environment setup

## Implementation Order

Execute development in logical phases to minimize integration conflicts and ensure working system at each milestone.

### Phase 1: Foundation (Weeks 1-2)
1. **Project Setup**
   - Initialize Git repository with proper .gitignore
   - Create Docker development environment
   - Set up PostgreSQL database with initial schema
   - Configure Redis for job queue

2. **Core Backend Structure**
   - Implement FastAPI application with basic routing
   - Create database models for GAM devices and subscribers
   - Set up Alembic for database migrations
   - Implement basic authentication and authorization

3. **GAM Device Communication**
   - Develop SNMP client for device discovery and monitoring
   - Implement SSH client for device configuration
   - Create GAM device manager with basic CRUD operations
   - Test communication with actual GAM hardware

### Phase 2: Device Management (Weeks 3-4)
4. **Device Discovery and Registration**
   - Implement network scanning for GAM device discovery
   - Create device registration and configuration interface
   - Develop port management and status monitoring
   - Add device health checking and alerting

5. **Basic Frontend**
   - Set up React application with TypeScript
   - Create main dashboard with device overview
   - Implement GAM device list and detail views
   - Add basic navigation and layout components

### Phase 3: Subscriber Management (Weeks 5-6)
6. **Subscriber Data Model**
   - Implement subscriber database schema
   - Create subscriber CRUD operations
   - Add bandwidth plan management
   - Develop VLAN assignment logic

7. **Provisioning Engine**
   - Build core provisioning workflow
   - Implement subscriber service creation
   - Add bandwidth plan enforcement
   - Create provisioning status tracking

### Phase 4: Billing Integration (Weeks 7-9)
8. **Sonar Integration**
   - Develop Sonar API client
   - Implement customer data synchronization
   - Create webhook handling for real-time updates
   - Add bidirectional sync capabilities

9. **Splynx Integration**
   - Develop Splynx API client
   - Implement customer data synchronization
   - Create webhook handling for real-time updates
   - Add bidirectional sync capabilities

10. **Integration Management UI**
    - Create integration configuration interface
    - Add sync status monitoring and controls
    - Implement conflict resolution workflows
    - Add integration health monitoring

### Phase 5: Advanced Features (Weeks 10-12)
11. **Monitoring and Diagnostics**
    - Implement comprehensive device monitoring
    - Add performance metrics collection
    - Create alerting and notification system
    - Build monitoring dashboard

12. **Automation and Workflows**
    - Add automated provisioning workflows
    - Implement bulk operations
    - Create scheduled sync jobs
    - Add audit logging and reporting

### Phase 6: Production Readiness (Weeks 13-14)
13. **Testing and Quality Assurance**
    - Complete unit test coverage
    - Perform integration testing with real devices
    - Load testing with multiple GAM devices
    - Security testing and vulnerability assessment

14. **Documentation and Deployment**
    - Complete API documentation
    - Create deployment guides
    - Set up production Docker configuration
    - Implement backup and recovery procedures

### Phase 7: Future Enhancements (Post-MVP)
15. **Multi-tenant Architecture**
    - Design tenant isolation
    - Implement organization management
    - Add role-based access control
    - Create tenant-specific configurations

16. **Advanced Analytics**
    - Add usage analytics and reporting
    - Implement predictive maintenance
    - Create capacity planning tools
    - Add business intelligence dashboards
