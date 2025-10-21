# System Patterns: Positron GAM Management System

## System Architecture

### High-Level Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Sonar/Splynx  │    │   React Web UI  │    │  GAM Devices    │
│  Billing Systems│    │   (Frontend)    │    │  (Hardware)     │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          │ REST API/Webhooks    │ HTTP/WebSocket       │ SNMP/SSH
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────┴───────────┐
                    │   FastAPI Backend       │
                    │   (Python)              │
                    └─────────────┬───────────┘
                                  │
                    ┌─────────────┴───────────┐
                    │   PostgreSQL + Redis    │
                    │   (Data & Cache)        │
                    └─────────────────────────┘
```

### Component Architecture

#### Backend Services Layer
- **FastAPI Application**: Async REST API with automatic documentation
- **GAM Manager Service**: Device communication and configuration
- **Provisioning Engine**: Subscriber service automation
- **Integration Service**: Billing system synchronization
- **Monitoring Service**: Device health and performance tracking
- **Background Workers**: Celery tasks for async operations

#### Data Layer
- **PostgreSQL**: Primary data store with async operations
- **Redis**: Caching, session storage, and job queue
- **SQLAlchemy ORM**: Database abstraction with async support

#### Communication Layer
- **SNMP Client**: Device monitoring and status collection
- **SSH Client**: Device configuration and provisioning
- **HTTP Client**: Billing system API integration
- **WebSocket**: Real-time frontend updates

## Key Technical Decisions

### Technology Stack Rationale

#### Python FastAPI Backend
- **Async Support**: Essential for handling multiple GAM device connections
- **Network Libraries**: Excellent SNMP (pysnmp) and SSH (netmiko) support
- **API Documentation**: Automatic OpenAPI/Swagger generation
- **Performance**: Comparable to Node.js with better network automation ecosystem

#### PostgreSQL Database
- **Reliability**: ACID compliance for billing integration
- **JSON Support**: Flexible configuration storage (JSONB)
- **Async Support**: Native async drivers (asyncpg)
- **Scalability**: Handles 50+ devices with complex relationships

#### React TypeScript Frontend
- **Type Safety**: Reduces runtime errors in complex UI
- **Component Reusability**: Modular design for different device types
- **Real-time Updates**: WebSocket integration for live monitoring
- **Material-UI**: Professional ISP management interface

#### Docker Deployment
- **Isolation**: Avoid conflicts with existing server applications
- **Scalability**: Easy horizontal scaling as device count grows
- **Updates**: Zero-downtime deployments
- **Development**: Consistent environment across team

### Design Patterns

#### Repository Pattern
```python
class GAMDeviceRepository:
    async def get_by_ip(self, ip_address: str) -> GAMDevice
    async def get_available_ports(self, device_id: UUID) -> List[GAMPort]
    async def update_status(self, device_id: UUID, status: DeviceStatus)
```

#### Service Layer Pattern
```python
class ProvisioningService:
    def __init__(self, gam_repo, subscriber_repo, bandwidth_repo):
        self.gam_repo = gam_repo
        self.subscriber_repo = subscriber_repo
        self.bandwidth_repo = bandwidth_repo
    
    async def provision_subscriber(self, request: ProvisioningRequest):
        # Business logic isolated from API and data layers
```

#### Factory Pattern for Device Communication
```python
class GAMConnectionFactory:
    @staticmethod
    def create_connection(device: GAMDevice) -> GAMConnection:
        if device.model.endswith('C'):
            return CoaxGAMConnection(device)
        else:
            return CopperGAMConnection(device)
```

#### Observer Pattern for Monitoring
```python
class DeviceMonitor:
    def __init__(self):
        self.observers = []
    
    def attach(self, observer: DeviceObserver):
        self.observers.append(observer)
    
    async def notify_status_change(self, device_id: UUID, status: DeviceStatus):
        for observer in self.observers:
            await observer.on_device_status_change(device_id, status)
```

## Component Relationships

### Data Model Relationships
```
GAMDevice (1) ──── (N) GAMPort
    │                   │
    │                   │
    └─── (N) Subscriber ┘
              │
              └─── (1) BandwidthPlan

ExternalSystem (1) ──── (N) SyncJob
```

### Service Dependencies
```
API Layer
    ├── GAM Management API
    │   └── GAMService
    │       ├── GAMRepository
    │       └── SNMPClient, SSHClient
    │
    ├── Subscriber API  
    │   └── ProvisioningService
    │       ├── SubscriberRepository
    │       ├── GAMService
    │       └── BandwidthRepository
    │
    └── Integration API
        └── SyncService
            ├── SonarClient
            ├── SplynxClient
            └── WebhookHandler
```

### Communication Patterns

#### Synchronous Operations
- **API Requests**: Frontend ↔ Backend REST API
- **Device Configuration**: Backend → GAM devices (SSH)
- **Billing API Calls**: Backend → Sonar/Splynx APIs

#### Asynchronous Operations
- **Device Monitoring**: Background SNMP polling
- **Billing Sync**: Scheduled sync jobs via Celery
- **Webhook Processing**: Event-driven billing updates
- **Real-time Updates**: WebSocket notifications to frontend

#### Error Handling Patterns
```python
class GAMConnectionError(Exception):
    def __init__(self, device_id: UUID, message: str):
        self.device_id = device_id
        self.message = message

class RetryableOperation:
    @retry(stop=stop_after_attempt(3), wait=wait_exponential())
    async def execute(self):
        # Operation with automatic retry logic
```

## Scalability Considerations

### Horizontal Scaling
- **Stateless Backend**: Multiple FastAPI instances behind load balancer
- **Database Connection Pooling**: Async connection pool management
- **Redis Clustering**: Distributed caching and job queue
- **Container Orchestration**: Docker Swarm or Kubernetes ready

### Performance Optimization
- **Async Operations**: Non-blocking I/O for device communication
- **Connection Pooling**: Reuse SNMP/SSH connections to devices
- **Caching Strategy**: Redis for frequently accessed device data
- **Database Indexing**: Optimized queries for device and subscriber lookups

### Monitoring and Observability
- **Structured Logging**: JSON logs for centralized analysis
- **Metrics Collection**: Prometheus-compatible metrics
- **Health Checks**: Kubernetes/Docker health endpoints
- **Distributed Tracing**: Request tracing across services
