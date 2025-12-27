# Smartbook Deployment Guide

This guide covers deploying Smartbook to production using modern cloud infrastructure.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Database Setup](#database-setup)
4. [Application Deployment](#application-deployment)
5. [Production Checklist](#production-checklist)
6. [Monitoring & Maintenance](#monitoring--maintenance)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Accounts & Services

- **Cloud Provider**: AWS, Azure, or Google Cloud
- **Database**: PostgreSQL 14+ (managed service recommended)
- **Domain**: Registered domain for HTTPS
- **Email Service**: SendGrid, AWS SES, or similar
- **ROS1000 Access**: Credentials from Lombardy Region

### Required Software

- Python 3.12+
- UV package manager
- Docker (for containerized deployment)
- PostgreSQL client tools

---

## Environment Setup

### 1. Clone Repository

```bash
git clone https://github.com/bedotech/smartbook.git
cd smartbook
```

### 2. Install UV

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 3. Create `.env` File

```bash
cp .env.example .env
```

**Required Environment Variables**:

```env
# Application
APP_NAME=Smartbook
DEBUG=false
VERSION=0.1.0

# Database
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/smartbook
DATABASE_ECHO=false

# Security
SECRET_KEY=your-256-bit-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
MAGIC_LINK_TOKEN_BYTES=32

# CORS
CORS_ORIGINS=["https://app.smartbook.app"]

# ROS1000 (per-tenant, but can set defaults)
ROS1000_WSDL_URL=https://alloggiatiweb.poliziadistato.it/service?wsdl

# Email (SMTP)
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=SG.your-sendgrid-api-key
SMTP_FROM_EMAIL=noreply@smartbook.app
```

**Generate Secret Key**:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## Database Setup

### Option 1: Managed PostgreSQL (Recommended)

#### AWS RDS
```bash
aws rds create-db-instance \
  --db-instance-identifier smartbook-prod \
  --db-instance-class db.t3.medium \
  --engine postgres \
  --engine-version 14.7 \
  --master-username smartbook \
  --master-user-password <strong-password> \
  --allocated-storage 100 \
  --storage-encrypted \
  --backup-retention-period 30 \
  --multi-az
```

#### Azure Database for PostgreSQL
```bash
az postgres server create \
  --resource-group smartbook-rg \
  --name smartbook-prod \
  --location westeurope \
  --admin-user smartbook \
  --admin-password <strong-password> \
  --sku-name GP_Gen5_2 \
  --version 14 \
  --storage-size 102400 \
  --backup-retention 30
```

### Option 2: Self-Hosted PostgreSQL

```bash
# Install PostgreSQL
sudo apt update
sudo apt install postgresql-14 postgresql-contrib

# Create database and user
sudo -u postgres psql
CREATE DATABASE smartbook;
CREATE USER smartbook WITH ENCRYPTED PASSWORD 'strong-password';
GRANT ALL PRIVILEGES ON DATABASE smartbook TO smartbook;
```

### Database Migrations

```bash
# Install dependencies
uv sync

# Run migrations
uv run alembic upgrade head

# Verify
uv run alembic current
```

---

## Application Deployment

### Option 1: Docker (Recommended)

#### Build Image

Create `Dockerfile`:
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install UV
RUN pip install uv

# Copy project files
COPY pyproject.toml uv.lock ./
COPY src ./src

# Install dependencies
RUN uv sync --frozen

# Expose port
EXPOSE 8000

# Run application
CMD ["uv", "run", "uvicorn", "smartbook.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and push:
```bash
docker build -t smartbook:latest .
docker tag smartbook:latest your-registry/smartbook:latest
docker push your-registry/smartbook:latest
```

#### Run with Docker Compose

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  app:
    image: your-registry/smartbook:latest
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - db
    restart: always

  db:
    image: postgres:14
    environment:
      POSTGRES_DB: smartbook
      POSTGRES_USER: smartbook
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
    restart: always

volumes:
  pgdata:
```

Deploy:
```bash
docker-compose up -d
```

### Option 2: Kubernetes

Create `k8s/deployment.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: smartbook
spec:
  replicas: 3
  selector:
    matchLabels:
      app: smartbook
  template:
    metadata:
      labels:
        app: smartbook
    spec:
      containers:
      - name: smartbook
        image: your-registry/smartbook:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: smartbook-secrets
              key: database-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
```

Deploy:
```bash
kubectl apply -f k8s/
```

### Option 3: Systemd Service

Create `/etc/systemd/system/smartbook.service`:
```ini
[Unit]
Description=Smartbook API
After=network.target postgresql.service

[Service]
Type=notify
User=smartbook
Group=smartbook
WorkingDirectory=/opt/smartbook
Environment="PATH=/opt/smartbook/.venv/bin"
ExecStart=/usr/local/bin/uv run uvicorn smartbook.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable smartbook
sudo systemctl start smartbook
```

---

## NGINX Reverse Proxy

Create `/etc/nginx/sites-available/smartbook`:
```nginx
upstream smartbook_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name api.smartbook.app;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.smartbook.app;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/api.smartbook.app/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.smartbook.app/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Proxy Configuration
    location / {
        proxy_pass http://smartbook_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=100r/m;
    limit_req zone=api_limit burst=20 nodelay;
}
```

Enable:
```bash
sudo ln -s /etc/nginx/sites-available/smartbook /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### SSL Certificate (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d api.smartbook.app
```

---

## Production Checklist

### Security

- [ ] All secrets moved to environment variables
- [ ] HTTPS enforced (no HTTP)
- [ ] Strong database password (20+ characters)
- [ ] Firewall configured (only 80, 443 open)
- [ ] Database encryption at rest enabled
- [ ] Regular security updates scheduled
- [ ] Secret key rotated from default
- [ ] CORS configured for production domain only
- [ ] Rate limiting enabled
- [ ] Audit logging configured

### Performance

- [ ] Database indexes created
- [ ] Connection pooling configured
- [ ] CDN configured for static assets
- [ ] Gzip compression enabled
- [ ] Application deployed on multiple instances
- [ ] Load balancer configured

### Monitoring

- [ ] Application logs centralized (CloudWatch, Datadog, etc.)
- [ ] Error tracking configured (Sentry, Rollbar, etc.)
- [ ] Uptime monitoring configured (UptimeRobot, Pingdom, etc.)
- [ ] Database monitoring enabled
- [ ] Alerts configured for critical errors
- [ ] Performance monitoring (APM) enabled

### Backup & Recovery

- [ ] Automated daily database backups
- [ ] Backup retention policy configured (30 days minimum)
- [ ] Backup restoration tested
- [ ] Disaster recovery plan documented
- [ ] Data replication configured (multi-region)

### Compliance

- [ ] GDPR compliance reviewed
- [ ] Privacy policy published
- [ ] Terms of service published
- [ ] Data processing agreement prepared
- [ ] ROS1000 credentials from Lombardy Region
- [ ] Legal review completed

---

## Monitoring & Maintenance

### Health Checks

Configure health check monitoring:
```bash
# Uptime monitoring
curl https://api.smartbook.app/api/health

# Expected response:
# {"status":"healthy","service":"smartbook-api","version":"0.1.0"}
```

### Log Management

Centralize logs:
```bash
# CloudWatch (AWS)
aws logs create-log-group --log-group-name /smartbook/app

# View logs
aws logs tail /smartbook/app --follow
```

### Database Maintenance

Regular maintenance tasks:
```bash
# Vacuum (weekly)
psql -U smartbook -d smartbook -c "VACUUM ANALYZE;"

# Check table sizes
psql -U smartbook -d smartbook -c "SELECT tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size FROM pg_tables WHERE schemaname = 'public' ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"

# Check index usage
psql -U smartbook -d smartbook -c "SELECT schemaname, tablename, indexname, idx_scan FROM pg_stat_user_indexes WHERE idx_scan = 0 ORDER BY schemaname, tablename;"
```

### Scaling

Horizontal scaling (multiple instances):
```bash
# Docker Compose
docker-compose up --scale app=3 -d

# Kubernetes
kubectl scale deployment smartbook --replicas=5
```

Vertical scaling (larger instances):
```bash
# Update instance type
aws rds modify-db-instance \
  --db-instance-identifier smartbook-prod \
  --db-instance-class db.t3.large \
  --apply-immediately
```

---

## Troubleshooting

### Application Won't Start

Check logs:
```bash
# Docker
docker logs smartbook-app

# Systemd
sudo journalctl -u smartbook -f

# Check database connection
uv run python -c "from smartbook.domain.database import engine; print('DB OK')"
```

### High Memory Usage

```bash
# Check memory usage
docker stats smartbook-app

# Analyze memory profile
uv run python -m memory_profiler smartbook/main.py
```

### Slow API Responses

```bash
# Check database query performance
psql -U smartbook -d smartbook -c "SELECT query, mean_exec_time, calls FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"

# Add missing indexes
psql -U smartbook -d smartbook -c "CREATE INDEX CONCURRENTLY idx_guests_booking_id ON guests(booking_id);"
```

### ROS1000 Submission Failures

Check compliance records:
```bash
# View failed submissions
psql -U smartbook -d smartbook -c "SELECT id, booking_id, error_message, retry_count FROM compliance_records WHERE status = 'failed' ORDER BY created_at DESC LIMIT 10;"
```

### Database Connection Pool Exhausted

Increase pool size in `.env`:
```env
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40
```

---

## Rollback Procedure

In case of critical issues:

```bash
# 1. Stop new deployments
kubectl rollout pause deployment/smartbook

# 2. Rollback to previous version
kubectl rollout undo deployment/smartbook

# 3. Verify rollback
kubectl rollout status deployment/smartbook

# 4. Rollback database migrations (if needed)
uv run alembic downgrade -1
```

---

## Support

For deployment support:
- **Documentation**: This file
- **Issues**: https://github.com/bedotech/smartbook/issues
- **Email**: support@smartbook.app
