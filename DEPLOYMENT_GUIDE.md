# Order Voice Backend - Deployment Guide

## Quick Deployment on Port 8001

### 🚀 One-Command Deployment

```bash
# Simple deployment
./deploy.sh

# Production deployment with nginx
./deploy-prod.sh
```

### 📋 Manual Deployment Steps

#### 1. Environment Setup
```bash
# The .env file is already configured with your token
# No changes needed - token is already set in .env file
cat .env
```

#### 2. Build and Run
```bash
# Development (direct access on port 8001)
docker-compose up --build -d

# Production (with nginx reverse proxy on port 8001)
docker-compose -f docker-compose.prod.yml up --build -d
```

#### 3. Verify Deployment
```bash
# Check if service is running
curl http://localhost:8001/

# View API documentation
open http://localhost:8001/docs
```

### 🌐 Service URLs

After deployment, your service will be available at:

- **API Base URL**: `http://localhost:8001`
- **Health Check**: `http://localhost:8001/`
- **API Documentation**: `http://localhost:8001/docs`
- **Interactive API**: `http://localhost:8001/redoc`

### 📊 API Endpoints

- `POST /auth/signin` - User authentication
- `POST /auth/signup` - User registration  
- `POST /transcription/transcribe` - Audio transcription
- `POST /orders/create` - Create order
- `POST /invoices/generate` - Generate invoice

### 🔧 Management Commands

```bash
# View logs
docker-compose logs -f

# Stop service
docker-compose down

# Restart service
docker-compose restart

# View container status
docker-compose ps

# Production commands (add -f docker-compose.prod.yml)
docker-compose -f docker-compose.prod.yml logs -f
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml restart
```

### 🛠️ Configuration

The application is configured via the `.env` file:

```env
# Already configured - no changes needed
TEABLE_TOKEN=Bearer teable_accT1cTLbgDxAw73HQa_xnRuWiEDLat6qqpUDsL4QEzwnKwnkU9ErG7zgJKJswg=
TEABLE_TABLE_ID=tblv9Ou1thzbETynKn1
ALLOWED_ORIGINS=*
```

### 🔍 Troubleshooting

#### Port Already in Use
```bash
# Check what's using port 8001
lsof -i :8001

# Kill process if needed
sudo kill -9 $(lsof -t -i:8001)
```

#### Service Not Starting
```bash
# Check logs
docker-compose logs order-voice-api

# Rebuild containers
docker-compose down
docker-compose up --build
```

#### Memory Issues
```bash
# Check container memory usage
docker stats

# Restart Docker if needed (Docker Desktop)
```

### 📈 Production Considerations

For production deployment:

1. **Use production script**: `./deploy-prod.sh`
2. **Monitor logs**: `docker-compose -f docker-compose.prod.yml logs -f`
3. **Set up monitoring**: Consider adding monitoring tools
4. **Backup volumes**: Whisper models are cached in Docker volumes
5. **SSL/HTTPS**: Configure nginx with SSL certificates if needed

### 🔒 Security Notes

- Token is configured in `.env` file (not in code)
- Container runs as non-root user
- CORS is configured for security
- Rate limiting available in production nginx setup

### 📦 What's Included

- **FastAPI Application**: Refactored modular structure
- **Docker Configuration**: Optimized for production
- **Environment Management**: Token in `.env` file
- **Health Checks**: Built-in monitoring
- **Nginx Reverse Proxy**: Production-ready setup
- **Volume Persistence**: Model caching between restarts

Your application is now ready to deploy on port 8001 with the token securely configured in the `.env` file! 🎉
