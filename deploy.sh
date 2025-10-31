#!/bin/bash

# AI-SwAutoMorph Production Deployment Script

set -e

echo "🚀 Starting AI-SwAutoMorph deployment..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data ssl logs

# Set proper permissions
chmod 755 data ssl logs

# Generate secret key if not exists
if [ ! -f .env ]; then
    echo "🔑 Generating environment configuration..."
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    cat > .env << EOF
SECRET_KEY=${SECRET_KEY}
FLASK_ENV=production
EOF
    echo "✅ Environment file created (.env)"
fi

# Build and start services
echo "🔨 Building Docker images..."
docker-compose build

echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    echo "✅ Services are running!"
    echo ""
    echo "🌐 Application URLs:"
    echo "   Web Interface: http://localhost"
    echo "   API Endpoint:  http://localhost/api"
    echo ""
    echo "📋 Management Commands:"
    echo "   View logs:     docker-compose logs -f"
    echo "   Stop services: docker-compose down"
    echo "   CLI access:    python3 cli.py --help"
    echo ""
    echo "📊 Service Status:"
    docker-compose ps
else
    echo "❌ Failed to start services. Check logs:"
    docker-compose logs
    exit 1
fi

echo ""
echo "🎉 Deployment completed successfully!"
echo "📖 Check the user guide at: http://localhost/static/userguide.html"