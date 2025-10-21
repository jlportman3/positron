# Positron GAM Management - Quick Start Guide

This guide will help you get the Positron GAM Management System up and running quickly.

## Prerequisites

- Docker and Docker Compose installed
- Git (for cloning the repository)
- At least 4GB of available RAM
- Ports 5436, 6380, 8001, and 3001 available

## Quick Start

### 1. Clone and Configure

```bash
# Navigate to the project directory
cd positron

# Create environment file from example
cp .env.example .env

# Edit .env with your specific configuration (optional for development)
# For production, update database passwords, API keys, etc.
nano .env
```

### 2. Start the Application

```bash
# Start all services in development mode
docker-compose -f docker-compose.dev.yml up -d

# Wait for services to initialize (about 30-60 seconds)
# Check logs to monitor startup
docker-compose -f docker-compose.dev.yml logs -f
```

### 3. Initialize the Database

```bash
# Run database migrations
docker-compose -f docker-compose.dev.yml exec backend alembic upgrade head

# (Optional) Load sample data
docker-compose -f docker-compose.dev.yml exec backend python -m app.scripts.seed_data
```

### 4. Access the Application

- **Frontend Dashboard**: http://localhost:3002
- **Backend API**: http://localhost:8003
- **API Documentation**: http://localhost:8003/docs
- **PostgreSQL**: localhost:5436 (user: postgres, password: postgres)
- **Redis**: localhost:6380

## Initial Configuration

### Add Your First GAM Device

1. Open the web interface at http://localhost:3002
2. Navigate to "GAM Devices" in the sidebar
3. Click "Add Device"
4. Fill in the device details:
   - **Name**: A friendly name for the device
   - **IP Address**: The device's IP address
   - **Model**: Select from GAM-12-M, GAM-24-M, GAM-12-C, GAM-24-C
   - **SNMP Community**: Default is "public"
   - **SSH Credentials**: Username and password for device access
   - **Location**: Physical location (optional)

### Add a Subscriber

1. Navigate to "Subscribers"
2. Click "Add Subscriber"
3. Fill in subscriber information:
   - Name, email, phone
   - Service address
   - Endpoint MAC address

### Provision a Service

1. Navigate to "Provisioning"
2. Select:
   - Subscriber (from pending subscribers)
   - GAM Device
   - Available Port
   - Bandwidth Plan
3. Click "Provision"

The system will automatically:
- Configure the GAM port
- Assign a VLAN
- Apply bandwidth limits
- Update subscriber status to "active"

## Integration with Billing Systems

### Sonar Integration

Update your `.env` file:

```bash
SONAR_API_URL=https://your-sonar-instance.com/api
SONAR_API_KEY=your-api-key
SONAR_WEBHOOK_SECRET=your-webhook-secret
```

### Splynx Integration

Update your `.env` file:

```bash
SPLYNX_API_URL=https://your-splynx-instance.com/api/2.0
SPLYNX_API_KEY=your-api-key
SPLYNX_API_SECRET=your-api-secret
SPLYNX_WEBHOOK_SECRET=your-webhook-secret
```

After updating, restart the backend:

```bash
docker-compose -f docker-compose.dev.yml restart backend
```

## Common Operations

### View Logs

```bash
# All services
docker-compose -f docker-compose.dev.yml logs -f

# Specific service
docker-compose -f docker-compose.dev.yml logs -f backend
docker-compose -f docker-compose.dev.yml logs -f frontend
```

### Restart Services

```bash
# Restart all services
docker-compose -f docker-compose.dev.yml restart

# Restart specific service
docker-compose -f docker-compose.dev.yml restart backend
```

### Stop Services

```bash
# Stop all services (preserves data)
docker-compose -f docker-compose.dev.yml down

# Stop and remove volumes (deletes all data)
docker-compose -f docker-compose.dev.yml down -v
```

### Database Operations

```bash
# Create a new migration
docker-compose -f docker-compose.dev.yml exec backend alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose -f docker-compose.dev.yml exec backend alembic upgrade head

# Rollback migration
docker-compose -f docker-compose.dev.yml exec backend alembic downgrade -1

# Access PostgreSQL directly
docker-compose -f docker-compose.dev.yml exec postgres psql -U postgres -d positron_gam
```

### Backend Development

```bash
# Access backend container
docker-compose -f docker-compose.dev.yml exec backend bash

# Run tests
docker-compose -f docker-compose.dev.yml exec backend pytest

# Check code quality
docker-compose -f docker-compose.dev.yml exec backend flake8 app/
```

### Frontend Development

```bash
# Access frontend container
docker-compose -f docker-compose.dev.yml exec frontend sh

# Install new dependency
docker-compose -f docker-compose.dev.yml exec frontend npm install package-name

# Rebuild frontend
docker-compose -f docker-compose.dev.yml up -d --build frontend
```

## Troubleshooting

### Services won't start

```bash
# Check if ports are already in use
netstat -tuln | grep -E '5436|6380|8001|3001'

# If ports are in use, either:
# 1. Stop the conflicting services
# 2. Update ports in docker-compose.dev.yml
```

### Database connection errors

```bash
# Ensure PostgreSQL is running
docker-compose -f docker-compose.dev.yml ps postgres

# Check PostgreSQL logs
docker-compose -f docker-compose.dev.yml logs postgres

# Restart PostgreSQL
docker-compose -f docker-compose.dev.yml restart postgres
```

### Frontend not connecting to backend

```bash
# Check backend is running and healthy
curl http://localhost:8003/health

# Check frontend environment variables
docker-compose -f docker-compose.dev.yml exec frontend env | grep VITE

# Rebuild frontend with correct API URL
docker-compose -f docker-compose.dev.yml up -d --build frontend
```

### GAM device connection fails

1. **Verify network connectivity**:
   ```bash
   docker-compose -f docker-compose.dev.yml exec backend ping <gam-ip-address>
   ```

2. **Test SNMP**:
   ```bash
   docker-compose -f docker-compose.dev.yml exec backend snmpwalk -v2c -c public <gam-ip-address>
   ```

3. **Test SSH**:
   ```bash
   docker-compose -f docker-compose.dev.yml exec backend ssh username@<gam-ip-address>
   ```

4. **Check credentials**: Ensure SNMP community and SSH credentials are correct in the device configuration

## Performance Tuning

### For larger deployments (50+ devices):

1. **Increase worker processes** in `.env`:
   ```bash
   UVICORN_WORKERS=4
   ```

2. **Adjust database connection pool**:
   ```bash
   DB_POOL_SIZE=20
   DB_MAX_OVERFLOW=10
   ```

3. **Enable Redis caching**:
   ```bash
   REDIS_CACHE_TTL=300
   ```

## Security Recommendations

For production deployments:

1. **Change default passwords** in `.env`
2. **Use strong SECRET_KEY**
3. **Enable HTTPS** with proper SSL certificates
4. **Restrict CORS_ORIGINS** to your domain
5. **Use firewall** to restrict access to services
6. **Regular backups** of PostgreSQL database
7. **Keep dependencies updated**

## Next Steps

- Review the full [README.md](README.md) for detailed information
- Check [implementation_plan.md](implementation_plan.md) for roadmap
- Explore API documentation at http://localhost:8003/docs
- Join our community for support

## Getting Help

- Create an issue on GitHub
- Check the documentation in `docs/` directory
- Review logs for error messages
- Consult the API documentation

## Useful Commands Reference

```bash
# Full rebuild
docker-compose -f docker-compose.dev.yml up -d --build

# View resource usage
docker stats

# Clean up everything
docker-compose -f docker-compose.dev.yml down -v
docker system prune -a

# Backup database
docker-compose -f docker-compose.dev.yml exec postgres pg_dump -U postgres positron_gam > backup.sql

# Restore database
docker-compose -f docker-compose.dev.yml exec -T postgres psql -U postgres positron_gam < backup.sql
```
