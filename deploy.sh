#!/bin/bash

# Order Voice Backend Deployment Script
# Deploys the application on port 8001 with static token configuration

set -e

echo "🚀 Deploying Order Voice Backend on port 8001..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created. Please review the configuration."
fi

# Show current configuration
echo ""
echo "📋 Current Configuration:"
echo "   Port: 8001"
echo "   Token: $(grep TEABLE_TOKEN .env | cut -d'=' -f2 | cut -c1-20)..."
echo "   Table ID: $(grep TEABLE_TABLE_ID .env | cut -d'=' -f2)"
echo ""

# Build and deploy
echo "🔨 Building and starting containers..."
docker-compose down 2>/dev/null || true
docker-compose up --build -d

# Wait for service to be ready
echo "⏳ Waiting for service to start..."
sleep 10

# Check if service is running
if curl -f http://localhost:8001/ >/dev/null 2>&1; then
    echo "✅ Service is running successfully!"
    echo ""
    echo "🌐 Service URLs:"
    echo "   API: http://localhost:8001"
    echo "   Health: http://localhost:8001/"
    echo "   Docs: http://localhost:8001/docs"
    echo ""
    echo "📊 Container Status:"
    docker-compose ps
else
    echo "❌ Service failed to start. Checking logs..."
    docker-compose logs --tail=20
    exit 1
fi

echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "📝 Useful commands:"
echo "   View logs: docker-compose logs -f"
echo "   Stop service: docker-compose down"
echo "   Restart: docker-compose restart"
