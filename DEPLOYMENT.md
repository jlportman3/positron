# Deployment Guide

## Production Deployment

### Prerequisites

- Docker and Docker Compose
- Domain name with SSL certificate
- Firewall configured
- Minimum 2 CPU cores, 4GB RAM, 20GB storage

### Production Setup

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd positron
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   nano .env
   ```

   Update the following for production:
   ```bash
   # Security
   SECRET_KEY=<generate-strong-random-key>
   DEBUG=false

   # Database
   POSTGRES_PASSWORD=<strong-password>
   DATABASE_URL=postgresql://postgres:<strong-password>@postgres:5432/positron_gam

   # CORS
   CORS_ORIGINS=["https://your-domain.com"]

   # API Keys (if using)
   SONAR_API_KEY=<your-key>
   SPLYNX_API_KEY=<your-key>
   ```

3. **SSL Certificates**

   Place your SSL certificates in `./nginx/certs/`:
   ```bash
   mkdir -p nginx/certs
   # Copy your SSL certificate and key
   cp /path/to/fullchain.pem nginx/certs/
   cp /path/to/privkey.pem nginx/certs/
   ```

4. **Production Docker Compose**

   Create `docker-compose.prod.yml`:
   ```yaml
   version: '3.8'

   services:
     postgres:
       image: postgres:15
       restart: always
       environment:
         POSTGRES_DB: ${POSTGRES_DB}
         POSTGRES_USER: ${POSTGRES_USER}
         POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
       volumes:
         - postgres_data:/var/lib/postgresql/data
       networks:
         - positron_network

     redis:
       image: redis:7-alpine
       restart: always
       volumes:
         - redis_data:/data
       networks:
         - positron_network

     backend:
       build:
         context: ./backend
         dockerfile: Dockerfile
       restart: always
       environment:
         - DATABASE_URL=${DATABASE_URL}
         - REDIS_URL=${REDIS_URL}
         - SECRET_KEY=${SECRET_KEY}
         - DEBUG=false
       depends_on:
         - postgres
         - redis
       networks:
         - positron_network

     frontend:
       build:
         context: ./frontend
         dockerfile: Dockerfile
       restart: always
       depends_on:
         - backend
       networks:
         - positron_network

     nginx:
       image: nginx:alpine
       restart: always
       ports:
         - "80:80"
         - "443:443"
       volumes:
         - ./nginx/nginx.conf:/etc/nginx/nginx.conf
         - ./nginx/certs:/etc/nginx/certs
       depends_on:
         - frontend
         - backend
       networks:
         - positron_network

   volumes:
     postgres_data:
     redis_data:

   networks:
     positron_network:
       driver: bridge
   ```

5. **Start Production Services**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

6. **Run Migrations**
   ```bash
   docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
   ```

### Nginx Configuration for Production

Create `nginx/nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }

    upstream frontend {
        server frontend:3001;
    }

    # HTTP redirect to HTTPS
    server {
        listen 80;
        server_name your-domain.com;
        return 301 https://$server_name$request_uri;
    }

    # HTTPS server
    server {
        listen 443 ssl http2;
        server_name your-domain.com;

        ssl_certificate /etc/nginx/certs/fullchain.pem;
        ssl_certificate_key /etc/nginx/certs/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;

        # API
        location /api/ {
            proxy_pass http://backend/api/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Frontend
        location / {
            proxy_pass http://frontend/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

### Monitoring and Maintenance

1. **View Logs**
   ```bash
   docker-compose -f docker-compose.prod.yml logs -f
   ```

2. **Backup Database**
   ```bash
   docker-compose -f docker-compose.prod.yml exec postgres \
     pg_dump -U postgres positron_gam > backup-$(date +%Y%m%d).sql
   ```

3. **Update Application**
   ```bash
   git pull
   docker-compose -f docker-compose.prod.yml up -d --build
   docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
   ```

4. **Health Checks**
   ```bash
   curl https://your-domain.com/health
   curl https://your-domain.com/api/v1/health
   ```

### Security Checklist

- [ ] Changed all default passwords
- [ ] Generated strong SECRET_KEY
- [ ] Configured SSL/TLS certificates
- [ ] Restricted CORS origins
- [ ] Enabled firewall (allow only 80, 443, SSH)
- [ ] Set up automated backups
- [ ] Configured log rotation
- [ ] Disabled DEBUG mode
- [ ] Updated all dependencies
- [ ] Set up monitoring/alerting

### Scaling

For high-traffic deployments:

1. **Add more backend workers**:
   ```yaml
   backend:
     deploy:
       replicas: 4
   ```

2. **Use external Redis/PostgreSQL** for better performance

3. **Add load balancer** in front of Nginx

4. **Enable caching** with Redis

### Troubleshooting Production

**Service won't start:**
```bash
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs service_name
```

**Database issues:**
```bash
docker-compose -f docker-compose.prod.yml exec postgres psql -U postgres
```

**SSL certificate issues:**
- Verify certificate files exist in nginx/certs/
- Check certificate expiration: `openssl x509 -in fullchain.pem -noout -dates`

**Performance issues:**
- Check resource usage: `docker stats`
- Review application logs
- Monitor database queries
- Check Redis connections
