# Alamo GAM

Management system for Positron G.hn Access Multiplexer (GAM) equipment. Built for Alamo Broadband Inc.

## Features

- **Device Management** - GAM device registration via announcement protocol, online/offline tracking
- **Endpoint Monitoring** - G.hn CPE endpoints with PHY rates, wire length, signal quality
- **Subscriber Provisioning** - VLAN assignment, bandwidth profiles, PoE control, trunk mode
- **Splynx Integration** - Automatic CPE lookup, auto-provisioning, QC ticket creation, daily reconciliation
- **Alarm System** - Real-time monitoring with severity levels (CR/MJ/MN/NA)
- **User Management** - 16 privilege levels, session management, audit logging
- **JSON-RPC** - Direct device communication for subscriber CRUD, config save, firmware management
- **SSH Tunnels** - Built-in SSH server for NAT'd device reverse tunnels
- **White-Label** - Configurable branding (name, logo, colors)
- **REST API** - Full CRUD API with interactive Swagger docs

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3.11 / FastAPI |
| Frontend | React 18 / TypeScript / Vite / MUI |
| Database | PostgreSQL 15 |
| Cache | Redis 7 |
| Task Queue | FastAPI BackgroundTasks |
| HTTP Client | httpx (async) |
| Containers | Docker Compose |

## Running

### Prerequisites

- Docker and Docker Compose

### Start

```bash
docker compose up -d
```

### Access

- **Frontend**: http://localhost:3005
- **Backend API**: http://localhost:8005
- **API Docs**: http://localhost:8005/docs

### Default Credentials

- **Admin**: `admin` / `admin`
- **Device Auth**: `device` / `device` (announcement endpoint)

## Architecture

```
positron/
├── backend/
│   ├── app/
│   │   ├── api/              # REST endpoints
│   │   ├── core/             # Config, security, database
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Business logic
│   │   ├── rpc/              # JSON-RPC client
│   │   ├── integrations/     # Splynx client
│   │   └── scheduler/        # Polling & background tasks
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/       # Reusable UI components
│   │   ├── pages/            # Page components
│   │   ├── services/         # API client
│   │   └── store/            # Zustand state
│   ├── Dockerfile
│   └── package.json
├── docs/                     # Protocol reference documentation
└── docker-compose.yml
```

## Device Configuration

Point GAM devices to this server:

1. Access the GAM CLI or web interface
2. Set announcement URL: `http://<server-ip>:8005/device/announcement/request`
3. Set announcement credentials: `device` / `device`
4. Set announcement period (e.g., 60 seconds)

## API Endpoints

### Authentication
- `POST /auth/login` - Login
- `POST /auth/logout` - Logout
- `GET /auth/session` - Current session info

### Device Announcement
- `PUT /device/announcement/request` - Device registration (Basic Auth)

### Devices
- `GET /devices` - List devices
- `GET /devices/{id}` - Device details
- `POST /devices` - Create device
- `PATCH /devices/{id}` - Update device
- `DELETE /devices/{id}` - Delete device

### Endpoints
- `GET /endpoints` - List endpoints
- `GET /endpoints/{id}` - Endpoint details

### Subscribers
- `GET /subscribers` - List subscribers
- `POST /subscribers` - Create subscriber
- `PATCH /subscribers/{id}` - Update subscriber
- `DELETE /subscribers/{id}` - Delete subscriber

### Bandwidths
- `GET /bandwidths` - List bandwidth profiles
- `POST /bandwidths` - Create profile
- `PATCH /bandwidths/{id}` - Update profile

### Alarms
- `GET /alarms` - List alarms
- `GET /alarms/counts` - Alarm counts by severity
- `POST /alarms/{id}/acknowledge` - Acknowledge alarm

### Splynx Integration
- `POST /splynx/lookup/{endpoint_id}` - Lookup endpoint MAC in Splynx
- `GET /splynx/lookup-tasks` - List pending lookup tasks
- `POST /splynx/reconciliation/run` - Trigger reconciliation
- `GET /splynx/admins` - Fetch Splynx administrators

### Users
- `GET /users` - List users
- `POST /users` - Create user
- `PATCH /users/{id}` - Update user
- `DELETE /users/{id}` - Delete user

### Settings
- `GET /settings` - Get all settings
- `PATCH /settings` - Update settings

## Environment Variables

### Backend

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | postgresql+asyncpg://... | PostgreSQL connection |
| `REDIS_URL` | redis://localhost:6379/0 | Redis connection |
| `SECRET_KEY` | change-me | Session encryption key |
| `DEVICE_USERNAME` | device | Device auth username |
| `DEVICE_PASSWORD` | device | Device auth password |
| `BRAND_NAME` | Alamo GAM | White-label product name |
| `BRAND_PRIMARY_COLOR` | #1976d2 | Theme primary color |

### Frontend

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_URL` | http://localhost:8005 | Backend API URL |

## Privilege Levels

| Level | Name | Capabilities |
|-------|------|--------------|
| 0 | Device | Device announcements only |
| 1 | Viewer | Read-only access |
| 3 | Operator | Basic operations |
| 5 | Manager | Subscriber management |
| 7 | Admin | User management |
| 9 | SuperAdmin | Delete users |
| 15 | Master | Full access |

## Supported Hardware

| Model | Type | Ports |
|-------|------|-------|
| GAM-4-C | Coax | 4 |
| GAM-12-C | Coax | 12 |
| GAM-12-M | Copper | 12 |
| GAM-24-M | Copper | 24 |

## License

Proprietary - Alamo Broadband Inc.
