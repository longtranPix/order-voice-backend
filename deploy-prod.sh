#!/bin/bash

# Order Voice Backend Production Deployment Script
# Deploys with nginx reverse proxy on port 8001

set -e

echo "🚀 Deploying Order Voice Backend (Production) on port 8001..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created. Please review the configuration."
fi

# Show current configuration
echo ""
echo "📋 Production Configuration:"
echo "   Port: 8001 (with nginx reverse proxy)"
echo "   Token: $(grep TEABLE_TOKEN .env | cut -d'=' -f2 | cut -c1-20)..."
echo "   Table ID: $(grep TEABLE_TABLE_ID .env | cut -d'=' -f2)"
echo ""

# Build and deploy with production configuration
echo "🔨 Building and starting production containers..."
docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
docker-compose -f docker-compose.prod.yml up --build -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 15

# Check if service is running
if curl -f http://localhost:8001/ >/dev/null 2>&1; then
    echo "✅ Production service is running successfully!"
    echo ""
    echo "🌐 Service URLs:"
    echo "   API (via nginx): http://localhost:8001"
    echo "   Health: http://localhost:8001/"
    echo "   Docs: http://localhost:8001/docs"
    echo ""
    echo "📊 Container Status:"
    docker-compose -f docker-compose.prod.yml ps
else
    echo "❌ Service failed to start. Checking logs..."
    docker-compose -f docker-compose.prod.yml logs --tail=20
    exit 1
fi

echo ""
echo "🎉 Production deployment completed successfully!"
echo ""
echo "📝 Useful commands:"
echo "   View logs: docker-compose -f docker-compose.prod.yml logs -f"
echo "   Stop service: docker-compose -f docker-compose.prod.yml down"
echo "   Restart: docker-compose -f docker-compose.prod.yml restart"
