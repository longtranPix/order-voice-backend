# Docker Deployment Guide

## Overview

This guide provides instructions for deploying the Order Voice Backend API using Docker and Docker Compose. The application is configured to run on port 8000 with enhanced security, health checks, and production-ready settings.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- At least 1GB RAM available
- Port 8000 available on the host

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd order-voice-backend
```

### 2. Environment Configuration

Ensure your `.env` file is properly configured:

```env
# Teable API Configuration
TEABLE_BASE_URL=https://app.teable.vn/api
TEABLE_TOKEN=Bearer your_token_here
TEABLE_TABLE_ID=your_table_id
TEABLE_USER_VIEW_ID=your_view_id
TEABLE_TOKEN_LIST_TABLE_ID=your_token_list_table_id

# Invoice API Configuration
CREATE_INVOICE_URL=https://api-vinvoice.viettel.vn/services/einvoiceapplication/api/InvoiceAPI/InvoiceWS/createInvoice
GET_PDF_URL=https://api-vinvoice.viettel.vn/services/einvoiceapplication/api/InvoiceAPI/InvoiceUtilsWS/getInvoiceRepresentationFile

# OpenRouter API Configuration
OPENROUTER_API_KEY=your_openrouter_key

# Server Configuration
PORT=8000
HOST=0.0.0.0
```

### 3. Build and Run

```bash
# Build and start the application
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

### 4. Verify Deployment

```bash
# Health check
curl http://localhost:8000/health

# API documentation
curl http://localhost:8000/docs
```

## Docker Configuration

### Dockerfile Features

- **Base Image**: Python 3.10 slim for optimal size and security
- **Security**: Non-root user execution
- **Health Checks**: Built-in health monitoring
- **Optimization**: Multi-stage build with dependency caching
- **Port**: Configured for port 8000 as per user preference

### Docker Compose Features

- **Service Name**: `order-voice-backend`
- **Port Mapping**: Host 8000 → Container 8000
- **Environment**: Loads from `.env` file
- **Volumes**: Persistent logs directory
- **Health Checks**: Automatic container health monitoring
- **Restart Policy**: `unless-stopped` for reliability
- **Network**: Isolated bridge network

## Production Deployment

### 1. Environment Variables

For production, consider using Docker secrets or external configuration:

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  order-voice-backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - PORT=8000
      - PYTHONUNBUFFERED=1
    secrets:
      - teable_token
      - openrouter_key
    volumes:
      - ./logs:/app/logs
      - /etc/ssl/certs:/etc/ssl/certs:ro
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
        reservations:
          memory: 512M
          cpus: '0.25'

secrets:
  teable_token:
    external: true
  openrouter_key:
    external: true
```

### 2. Reverse Proxy Setup

Example Nginx configuration:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 3. SSL/TLS Configuration

For HTTPS, use a reverse proxy with SSL termination or configure the application with SSL certificates.

## Management Commands

### Container Management

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart services
docker-compose restart

# View logs
docker-compose logs -f order-voice-backend

# Execute commands in container
docker-compose exec order-voice-backend bash
```

### Monitoring

```bash
# Check container health
docker-compose ps

# Monitor resource usage
docker stats order-voice-backend

# View health check logs
docker inspect order-voice-backend | grep Health -A 10
```

### Updates and Maintenance

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Clean up old images
docker image prune -f
```

## Troubleshooting

### Common Issues

#### Port Already in Use
```bash
# Check what's using port 8000
lsof -i :8000

# Kill process if needed
sudo kill -9 <PID>
```

#### Container Won't Start
```bash
# Check logs
docker-compose logs order-voice-backend

# Check container status
docker-compose ps

# Rebuild container
docker-compose build --no-cache order-voice-backend
```

#### Health Check Failing
```bash
# Check health endpoint manually
curl http://localhost:8000/health

# Check container logs
docker-compose logs order-voice-backend

# Restart container
docker-compose restart order-voice-backend
```

### Log Analysis

```bash
# View recent logs
docker-compose logs --tail=100 order-voice-backend

# Follow logs in real-time
docker-compose logs -f order-voice-backend

# Search logs for errors
docker-compose logs order-voice-backend | grep ERROR
```

## Security Considerations

### 1. Environment Variables
- Never commit `.env` files with sensitive data
- Use Docker secrets in production
- Rotate API keys regularly

### 2. Network Security
- Use custom networks to isolate containers
- Implement proper firewall rules
- Consider using a VPN for sensitive deployments

### 3. Container Security
- Application runs as non-root user
- Minimal base image reduces attack surface
- Regular security updates for base images

## Performance Optimization

### 1. Resource Limits
```yaml
deploy:
  resources:
    limits:
      memory: 1G
      cpus: '0.5'
```

### 2. Caching
- Docker layer caching for faster builds
- Application-level caching where appropriate

### 3. Monitoring
- Health checks for automatic recovery
- Log aggregation for debugging
- Resource monitoring for optimization

## Backup and Recovery

### 1. Data Backup
```bash
# Backup logs
tar -czf logs-backup-$(date +%Y%m%d).tar.gz logs/

# Backup configuration
cp .env .env.backup
```

### 2. Disaster Recovery
```bash
# Quick recovery
docker-compose down
docker-compose up -d

# Full rebuild
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Support

For issues and questions:
1. Check the logs: `docker-compose logs order-voice-backend`
2. Verify configuration: Review `.env` and `docker-compose.yml`
3. Test connectivity: `curl http://localhost:8000/health`
4. Restart services: `docker-compose restart`
