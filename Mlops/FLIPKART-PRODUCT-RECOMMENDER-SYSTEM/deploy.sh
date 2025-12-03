#!/bin/bash

# Flipkart Product Recommender - GCP Deployment Script
# Run this script on your GCP E2 instance after cloning the repo

set -e

echo "🚀 Starting Flipkart App Deployment..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "Creating .env template. Please add your API keys."
    cat > .env << 'EOF'
GROQ_API_KEY=your_groq_api_key_here
HUGGINGFACEHUB_API_TOKEN=your_huggingface_token_here
EOF
    echo "⚠️  Please edit .env file with your actual API keys, then run this script again."
    exit 1
fi

# Stop and remove existing container if running
if docker ps -a | grep -q flipkart-app; then
    echo "🛑 Stopping existing container..."
    docker stop flipkart-app || true
    docker rm flipkart-app || true
fi

# Remove old image
if docker images | grep -q flipkart-recommender; then
    echo "🗑️  Removing old image..."
    docker rmi flipkart-recommender || true
fi

# Build new image
echo "🏗️  Building Docker image..."
docker build -t flipkart-recommender .

# Run container
echo "▶️  Starting container..."
docker run -d \
  --name flipkart-app \
  --restart unless-stopped \
  -p 5000:5000 \
  --env-file .env \
  flipkart-recommender

# Wait for container to start
echo "⏳ Waiting for app to start..."
sleep 5

# Check if running
if docker ps | grep -q flipkart-app; then
    echo "✅ Flipkart app is running!"
    echo ""
    echo "📊 Container status:"
    docker ps | grep flipkart-app
    echo ""
    echo "📝 View logs with: docker logs -f flipkart-app"
    echo ""

    # Get external IP
    EXTERNAL_IP=$(curl -s ifconfig.me)
    echo "🌐 Access your app at: http://${EXTERNAL_IP}:5000"
else
    echo "❌ Failed to start container. Check logs:"
    docker logs flipkart-app
    exit 1
fi
