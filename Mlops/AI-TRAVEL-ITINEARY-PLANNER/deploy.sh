#!/bin/bash

# AI Travel Itinerary Planner - Deployment Script

echo "🚀 Starting AI Travel Itinerary Planner deployment..."

# Stop and remove existing container
echo "🛑 Stopping existing container..."
docker stop travel-planner-app || true
docker rm travel-planner-app || true

# Build the Docker image
echo "🔨 Building Docker image..."
docker build -t travel-planner .

if [ $? -ne 0 ]; then
    echo "❌ Docker build failed!"
    exit 1
fi

# Run the container
echo "🏃 Starting container..."
docker run -d \
    --name travel-planner-app \
    --restart unless-stopped \
    -p 8501:8501 \
    --env-file .env \
    travel-planner

if [ $? -eq 0 ]; then
    echo "✅ Deployment successful!"
    echo "📱 Application is running on http://localhost:8501"
    echo ""
    echo "📊 Check logs with: docker logs -f travel-planner-app"
    echo "🛑 Stop with: docker stop travel-planner-app"
else
    echo "❌ Container failed to start!"
    exit 1
fi
