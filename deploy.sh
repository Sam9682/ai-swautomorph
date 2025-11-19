#!/bin/bash

# AI-SwAutoMorph Production Deployment Script

# Handle command line arguments
COMMAND=${1:-help}
USER_ID=${2:-1}
USER_NAME=${3:-"User"}
USER_EMAIL=${4:-"user@example.com"}
DESCRIPTION=${5:-"Basic Information Display"}
# Compute var RANGE_START = APPLICATION_IDENTITY_NUMBER * 100 + 6000
APPLICATION_IDENTITY_NUMBER=0
RANGE_START=6000
PORT_RANGE_BEGIN=$((APPLICATION_IDENTITY_NUMBER * 100 + RANGE_START))

set -e

# Handle command line arguments
COMMAND=${1:-help}

case $COMMAND in
    "ps")
        echo "📊 AI-SwAutoMorph Service Status:"
        if command -v docker-compose &> /dev/null; then
            PORT=$((PORT_RANGE_BEGIN + USER_ID)) HTTPS_PORT=$((PORT_RANGE_BEGIN + USER_ID + 1)) USER_ID=$USER_ID docker-compose ps
        else
            echo "❌ Docker Compose not installed"
        fi
        exit 0
        ;;
    "stop")
        echo "🛑 Stopping AI-SwAutoMorph services..."
        PORT=$((PORT_RANGE_BEGIN + USER_ID)) HTTPS_PORT=$((PORT_RANGE_BEGIN + USER_ID + 1)) USER_ID=$USER_ID docker-compose down
        echo "✅ Services stopped"
        exit 0
        ;;
    "logs")
        PORT=$((PORT_RANGE_BEGIN + USER_ID)) HTTPS_PORT=$((PORT_RANGE_BEGIN + USER_ID + 1)) USER_ID=$USER_ID docker-compose logs -f
        exit 0
        ;;
    "restart")
        echo "🔄 Restarting AI-SwAutoMorph services..."
        PORT=$((PORT_RANGE_BEGIN + USER_ID)) HTTPS_PORT=$((PORT_RANGE_BEGIN + USER_ID + 1)) USER_ID=$USER_ID docker-compose restart
        echo "✅ Services restarted"
        exit 0
        ;;
    "start")
        echo "🚀 Starting AI-SwAutoMorph deployment..."
        ;;
    *)
        echo "Usage: $0 [start|stop|restart|ps|logs]"
        echo "  start        - Start services including building (default)"
        echo "  stop         - Stop all services"
        echo "  restart      - Restart all services, docker style"
        echo "  ps           - Show service status"
        echo "  logs         - Show service logs"
        exit 1
        ;;
esac

# Validate user_id
if ! [[ "$USER_ID" =~ ^[0-9]+$ ]]; then
    echo "❌ Error: user_id must be a number"
    exit 1
fi

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

# Generate SSL certificates if they don't exist
if [ ! -f ssl/cert.pem ] || [ ! -f ssl/key.pem ]; then
    echo "🔐 Generating SSL certificates..."
    ./generate_ssl.sh
else
    echo "✅ SSL certificates already exist"
fi

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
PORT=$((PORT_RANGE_BEGIN + USER_ID)) HTTPS_PORT=$((PORT_RANGE_BEGIN + USER_ID + 1)) USER_ID=$USER_ID docker-compose down --remove-orphans 2>/dev/null || true

# Build and start services
echo "🔨 Building Docker images..."
PORT=$((PORT_RANGE_BEGIN + USER_ID)) HTTPS_PORT=$((PORT_RANGE_BEGIN + USER_ID + 1)) USER_ID=$USER_ID docker-compose build --no-cache

echo "🚀 Starting services..."
PORT=$((PORT_RANGE_BEGIN + USER_ID)) HTTPS_PORT=$((PORT_RANGE_BEGIN + USER_ID + 1)) USER_ID=$USER_ID docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check if services are running
ACTUAL_PORT=${PORT_START:-$((PORT_RANGE_BEGIN + USER_ID))}
ACTUAL_HTTPS_PORT=${HTTPS_PORT:-$((PORT_RANGE_BEGIN + USER_ID + 1))}

if PORT=$ACTUAL_PORT HTTPS_PORT=$ACTUAL_HTTPS_PORT USER_ID=$USER_ID docker-compose ps | grep -q "Up"; then
    echo "✅ Services are running!"
    echo ""
    echo "🌐 Application URLs (User ID: $USER_ID):"
    echo "   Web Interface: https://localhost:$ACTUAL_HTTPS_PORT"
    echo "   HTTP Interface: http://localhost:$ACTUAL_PORT"
    echo "   API Endpoint:  https://localhost:$ACTUAL_HTTPS_PORT/api"
    echo ""
    echo "🔧 Port Configuration:"
    echo "   HTTP Port:  $ACTUAL_PORT"
    echo "   HTTPS Port: $ACTUAL_HTTPS_PORT"
    echo "   User ID:    $USER_ID"
    echo ""
    echo "📋 Management Commands:"
    echo "   View logs:     ./deploy.sh logs"
    echo "   Stop services: ./deploy.sh stop"
    echo "   Restart:       ./deploy.sh restart"
    echo "   Check status:  ./deploy.sh ps"
    echo ""
    echo "📊 Service Status:"
    PORT=$ACTUAL_PORT HTTPS_PORT=$ACTUAL_HTTPS_PORT USER_ID=$USER_ID docker-compose ps
else
    echo "❌ Failed to start services. Check logs:"
    PORT=$ACTUAL_PORT HTTPS_PORT=$ACTUAL_HTTPS_PORT USER_ID=$USER_ID docker-compose logs
    exit 1
fi

echo ""
echo "🎉 Deployment completed successfully!"
echo "📖 Check the user guide at: https://www.swautomorph.com/static/userguide.html"
echo ""
echo "🔒 HTTPS Security:"
echo "   ✅ SSL/TLS encryption enabled"
echo "   ✅ HTTP to HTTPS redirect active"
echo "   ✅ Security headers configured"
echo "   ⚠️  Using self-signed certificate (browser warning expected)"
echo "   📝 For production: Replace with CA-signed certificate"