#!/bin/bash

# AI-SwAutoMorph Production Deployment Script

set -e

# Handle command line arguments
COMMAND=${1:-help}

case $COMMAND in
    "status")
        echo "📊 AI-SwAutoMorph Service Status:"
        if command -v docker-compose &> /dev/null; then
            docker-compose ps
        else
            echo "❌ Docker Compose not installed"
        fi
        exit 0
        ;;
    "stop")
        echo "🛑 Stopping AI-SwAutoMorph services..."
        docker-compose down
        echo "✅ Services stopped"
        exit 0
        ;;
    "logs")
        docker-compose logs -f
        exit 0
        ;;
    "restart")
        echo "🔄 Restarting AI-SwAutoMorph services..."
        docker-compose restart
        echo "✅ Services restarted"
        exit 0
        ;;
    "deploy"|"start")
        echo "🚀 Starting AI-SwAutoMorph deployment..."
        ;;
    *)
        echo "Usage: $0 [deploy|start|stop|restart|status|logs]"
        echo "  deploy/start - Deploy and start services (default)"
        echo "  stop         - Stop all services"
        echo "  restart      - Restart all services"
        echo "  status       - Show service status"
        echo "  logs         - Show service logs"
        exit 1
        ;;
esac

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

# Clean up existing containers
echo "🧹 Cleaning up..."
docker-compose down --remove-orphans 2>/dev/null || true

# Build and start services
echo "🔨 Building Docker images..."
docker-compose build --no-cache

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
    echo "   Web Interface: http://www.swautomorph.com"
    echo "   API Endpoint:  http://www.swautomorph.com/api"
    echo ""
    echo "📋 Management Commands:"
    echo "   View logs:     ./deploy.sh logs"
    echo "   Stop services: ./deploy.sh stop"
    echo "   Restart:       ./deploy.sh restart"
    echo "   Check status:  ./deploy.sh status"
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
echo "📖 Check the user guide at: http://www.swautomorph.com/static/userguide.html"