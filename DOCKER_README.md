# Docker Configuration for Order Voice Backend

This document explains how to build and run the Order Voice Backend using Docker.

## Quick Start

### 1. Development Environment

```bash
# Build and run with docker-compose
docker-compose up --build

# Or run in detached mode
docker-compose up -d --build
```

### 2. Production Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your actual values
nano .env

# Run production setup
docker-compose -f docker-compose.prod.yml up -d --build
```

## Files Overview

### Docker Files
- `dockerfile` - Main Docker image definition
- `docker-compose.yml` - Development environment
- `docker-compose.prod.yml` - Production environment with nginx
- `.dockerignore` - Files to exclude from Docker build
- `nginx.conf` - Nginx reverse proxy configuration

### Scripts
- `docker-build.sh` - Build script for the Docker image

### Configuration
- `.env.example` - Environment variables template
- `.env` - Your actual environment variables (create from template)

## Environment Variables

### Required Variables
```env
TEABLE_TOKEN=Bearer your_token_here
TEABLE_TABLE_ID=your_table_id
```

### Optional Variables
```env
DEBUG=false
ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com
WHISPER_MODEL_SIZE=small
WHISPER_COMPUTE_TYPE=int8
WHISPER_DEVICE=cpu
```

## Docker Commands

### Build Image
```bash
# Using the build script
./docker-build.sh

# Manual build
docker build -t order-voice-backend:latest .
```

### Run Container
```bash
# Development
docker-compose up

# Production
docker-compose -f docker-compose.prod.yml up

# Manual run
docker run -p 8000:8000 --env-file .env order-voice-backend:latest
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f order-voice-api

# Production
docker-compose -f docker-compose.prod.yml logs -f
```

### Stop Services
```bash
# Development
docker-compose down

# Production
docker-compose -f docker-compose.prod.yml down

# Remove volumes (careful!)
docker-compose down -v
```

## Production Deployment

### 1. Setup Environment
```bash
# Create production environment file
cp .env.example .env

# Edit with production values
nano .env
```

### 2. SSL Configuration (Optional)
```bash
# Create SSL directory
mkdir ssl

# Add your SSL certificates
cp your-cert.pem ssl/cert.pem
cp your-key.pem ssl/key.pem

# Update nginx.conf to enable HTTPS
```

### 3. Deploy
```bash
# Deploy with nginx reverse proxy
docker-compose -f docker-compose.prod.yml up -d --build

# Check status
docker-compose -f docker-compose.prod.yml ps
```

## Monitoring and Maintenance

### Health Checks
The application includes health checks:
- HTTP endpoint: `GET /`
- Docker health check: Built into containers
- Nginx health check: Monitors backend connectivity

### Resource Limits
- **Development**: 2GB RAM, 1 CPU
- **Production**: 4GB RAM, 2 CPU

### Persistent Data
- Whisper models: Cached in Docker volumes
- Application logs: Stored in Docker volumes

### Backup Volumes
```bash
# Backup model cache
docker run --rm -v order-voice-backend_whisper_models:/data -v $(pwd):/backup alpine tar czf /backup/whisper_models.tar.gz -C /data .

# Restore model cache
docker run --rm -v order-voice-backend_whisper_models:/data -v $(pwd):/backup alpine tar xzf /backup/whisper_models.tar.gz -C /data
```

## Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Check what's using port 8000
   lsof -i :8000
   
   # Use different port
   docker-compose up -p 8001:8000
   ```

2. **Memory issues**
   ```bash
   # Increase Docker memory limit
   # Docker Desktop: Settings > Resources > Memory
   
   # Check container memory usage
   docker stats
   ```

3. **Model download issues**
   ```bash
   # Clear model cache
   docker volume rm order-voice-backend_whisper_models
   
   # Rebuild with fresh cache
   docker-compose up --build
   ```

4. **Permission issues**
   ```bash
   # Check container logs
   docker-compose logs order-voice-api
   
   # Run as root (not recommended for production)
   docker run --user root -p 8000:8000 order-voice-backend:latest
   ```

### Logs and Debugging
```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f order-voice-api

# Enter container for debugging
docker-compose exec order-voice-api bash

# Check container resource usage
docker stats order-voice-backend
```

## Security Considerations

1. **Environment Variables**: Never commit `.env` files with real credentials
2. **User Permissions**: Container runs as non-root user
3. **Network Security**: Use nginx reverse proxy in production
4. **SSL/TLS**: Configure HTTPS for production deployments
5. **Rate Limiting**: Nginx includes rate limiting configuration

## Performance Optimization

1. **Model Caching**: Whisper models are cached in Docker volumes
2. **Resource Limits**: Configured for optimal performance
3. **Multi-stage Builds**: Could be added for smaller images
4. **Health Checks**: Ensure service availability

For more information, see the main project documentation.
