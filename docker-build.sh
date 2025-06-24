#!/bin/bash

# Docker build script for Order Voice Backend

set -e

echo "🐳 Building Order Voice Backend Docker image..."

# Build the Docker image
docker build -t order-voice-backend:latest .

echo "✅ Docker image built successfully!"

# Optional: Tag for different environments
docker tag order-voice-backend:latest order-voice-backend:dev

echo "🏷️  Tagged image as order-voice-backend:dev"

# Show image info
echo "📊 Image information:"
docker images | grep order-voice-backend

echo ""
echo "🚀 To run the container:"
echo "   Development: docker-compose up"
echo "   Production:  docker-compose -f docker-compose.prod.yml up"
echo ""
echo "🔧 To run with custom environment:"
echo "   docker run -p 8000:8000 --env-file .env order-voice-backend:latest"
