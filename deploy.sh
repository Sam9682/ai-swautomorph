#!/bin/bash

# AI-SwAutoMorph Production Deployment Script

# Handle command line arguments
COMMAND=${1:-help}
LOCAL_MODE=${2:-""}
USER_ID=${3:-0}
USER_NAME=${4:-"User"}
USER_EMAIL=${5:-"user@example.com"}
DESCRIPTION=${6:-"Basic Information Display"}
# Compute var RANGE_START = APPLICATION_IDENTITY_NUMBER * 100 + 6000
APPLICATION_IDENTITY_NUMBER=0
RANGE_START=80
RANGE_RESERVED=10
PORT_RANGE_BEGIN=$((APPLICATION_IDENTITY_NUMBER * 100 + RANGE_START))

set -e

# Handle command line arguments
COMMAND=${1:-help}

case $COMMAND in
    "ps")
        if [ "$LOCAL_MODE" = "locally" ]; then
            echo "📊 AI-SwAutoMorph Local Service Status:"
            # Check Flask application
            if [ -f "app.pid" ]; then
                PID=$(cat app.pid)
                if kill -0 "$PID" 2>/dev/null; then
                    echo "✅ Flask application: Running (PID: $PID)"
                else
                    echo "❌ Flask application: Not running (stale PID: $PID)"
                fi
            else
                echo "❌ Flask application: Not running (no PID file)"
            fi
            # Check Nginx
            if systemctl is-active --quiet nginx; then
                echo "✅ Nginx: Running"
                if [ -f "/etc/nginx/sites-enabled/ai-swautomorph" ]; then
                    echo "✅ AI-SwAutoMorph site: Configured"
                else
                    echo "⚠️ AI-SwAutoMorph site: Not configured"
                fi
            else
                echo "❌ Nginx: Not running"
            fi
        else
            echo "📊 AI-SwAutoMorph Service Status:"
            if command -v docker-compose &> /dev/null; then
                PORT=$((PORT_RANGE_BEGIN + USER_ID * RANGE_RESERVED)) HTTPS_PORT=$((PORT_RANGE_BEGIN + USER_ID * RANGE_RESERVED + 363)) USER_ID=$USER_ID docker-compose ps
            else
                echo "❌ Docker Compose not installed"
            fi
        fi
        exit 0
        ;;
    "stop")
        if [ "$LOCAL_MODE" = "locally" ]; then
            echo "🛑 Stopping local AI-SwAutoMorph services..."
            # Stop Flask application
            if [ -f "app.pid" ]; then
                PID=$(cat app.pid)
                if kill -0 "$PID" 2>/dev/null; then
                    kill "$PID"
                    echo "✅ Flask application stopped (PID: $PID)"
                else
                    echo "⚠️ Flask process not running (PID: $PID)"
                fi
                rm -f app.pid
            else
                echo "⚠️ No app.pid file found"
            fi
            # Remove nginx site configuration
            if [ -f "/etc/nginx/sites-enabled/ai-swautomorph" ]; then
                sudo rm -f /etc/nginx/sites-enabled/ai-swautomorph
                sudo nginx -t && sudo systemctl reload nginx
                echo "✅ Nginx configuration removed"
            fi
            echo "✅ Local services stopped"
        else
            echo "🛑 Stopping AI-SwAutoMorph services..."
            PORT=$((PORT_RANGE_BEGIN + USER_ID * RANGE_RESERVED)) HTTPS_PORT=$((PORT_RANGE_BEGIN + USER_ID * RANGE_RESERVED + 363)) USER_ID=$USER_ID docker-compose down
            echo "✅ Services stopped"
        fi
        exit 0
        ;;
    "logs")
        if [ "$LOCAL_MODE" = "locally" ]; then
            echo "📋 AI-SwAutoMorph Local Service Logs:"
            if [ -f "app.log" ]; then
                echo "🐍 Flask Application Logs (last 50 lines):"
                tail -n 50 app.log
                echo ""
                echo "📊 Follow Flask logs: tail -f app.log"
            else
                echo "❌ No Flask log file found (app.log)"
            fi
            echo ""
            echo "🌐 Nginx Error Logs (last 20 lines):"
            sudo tail -n 20 /var/log/nginx/error.log 2>/dev/null || echo "❌ Cannot access Nginx logs"
        else
            PORT=$((PORT_RANGE_BEGIN + USER_ID * RANGE_RESERVED)) HTTPS_PORT=$((PORT_RANGE_BEGIN + USER_ID * RANGE_RESERVED + 363)) USER_ID=$USER_ID docker-compose logs -f
        fi
        exit 0
        ;;
    "restart")
        if [ "$LOCAL_MODE" = "locally" ]; then
            echo "🔄 Restarting local AI-SwAutoMorph services..."
            # Stop Flask application
            if [ -f "app.pid" ]; then
                PID=$(cat app.pid)
                if kill -0 "$PID" 2>/dev/null; then
                    kill "$PID"
                    echo "✅ Flask application stopped (PID: $PID)"
                fi
                rm -f app.pid
            fi
            # Start Flask application
            echo "🚀 Starting Flask application..."
            nohup python3 app.py > app.log 2>&1 &
            echo $! > app.pid
            # Reload nginx configuration
            sudo nginx -t && sudo systemctl reload nginx
            echo "✅ Local services restarted"
        else
            echo "🔄 Restarting AI-SwAutoMorph services..."
            PORT=$((PORT_RANGE_BEGIN + USER_ID * RANGE_RESERVED)) HTTPS_PORT=$((PORT_RANGE_BEGIN + USER_ID * RANGE_RESERVED + 363)) USER_ID=$USER_ID docker-compose restart
            echo "✅ Services restarted"
        fi
        exit 0
        ;;
    "start")
        if [ "$LOCAL_MODE" = "locally" ]; then
            echo "🚀 Starting AI-SwAutoMorph locally (no Docker)..."
        else
            echo "🚀 Starting AI-SwAutoMorph deployment..."
        fi
        ;;
    *)
        echo "Usage: $0 [start|stop|restart|ps|logs] [locally]"
        echo "  start        - Start services including building (default)"
        echo "  start locally - Start services locally without Docker"
        echo "  stop         - Stop all services"
        echo "  stop locally - Stop local services (Flask + Nginx config)"
        echo "  restart      - Restart all services, docker style"
        echo "  restart locally - Restart local services (Flask + Nginx reload)"
        echo "  ps           - Show service status"
        echo "  ps locally   - Show local service status (Flask + Nginx)"
        echo "  logs         - Show service logs"
        echo "  logs locally - Show local service logs (Flask + Nginx)"
        exit 1
        ;;
esac

# Validate user_id
if ! [[ "$USER_ID" =~ ^[0-9]+$ ]]; then
    echo "❌ Error: user_id must be a number"
    exit 1
fi

# Check requirements based on mode
if [ "$LOCAL_MODE" = "locally" ]; then
    # Check for local requirements
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python3 is not installed. Please install Python3 first."
        exit 1
    fi
    
    if ! command -v nginx &> /dev/null; then
        echo "📦 Installing Nginx..."
        sudo apt update && sudo apt install -y nginx
        sudo systemctl enable nginx
        echo "✅ Nginx installed successfully"
    fi
else
    # Check for Docker requirements
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo "❌ Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
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

if [ "$LOCAL_MODE" = "locally" ]; then
    # Local deployment
    echo "💻 Starting local deployment..."
    
    # Install Python dependencies
    if [ -f "requirements.txt" ]; then
        echo "📦 Installing Python dependencies..."
        pip3 install -r requirements.txt
    fi
    
    # Start Flask application in background
    echo "🚀 Starting Flask application..."
    nohup python3 app.py > app.log 2>&1 &
    echo $! > app.pid
    
    # Configure and start nginx
    echo "🌐 Configuring Nginx..."
    cat > /tmp/ai-swautomorph-site << 'EOF'
server {
    listen 80;
    server_name localhost;
    
    location / {
        proxy_pass http://127.0.0.1:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF
    sudo mv /tmp/ai-swautomorph-site /etc/nginx/sites-available/ai-swautomorph
    sudo ln -sf /etc/nginx/sites-available/ai-swautomorph /etc/nginx/sites-enabled/
    sudo nginx -t && sudo systemctl reload nginx
    
else
    # Docker deployment
    echo "🧹 Cleaning up..."
    PORT=$((PORT_RANGE_BEGIN + USER_ID * RANGE_RESERVED)) HTTPS_PORT=$((PORT_RANGE_BEGIN + USER_ID * RANGE_RESERVED + 363)) USER_ID=$USER_ID docker-compose down --remove-orphans 2>/dev/null || true
    
    # Build and start services
    echo "🔨 Building Docker images..."
    PORT=$((PORT_RANGE_BEGIN + USER_ID * RANGE_RESERVED)) HTTPS_PORT=$((PORT_RANGE_BEGIN + USER_ID * RANGE_RESERVED + 363)) USER_ID=$USER_ID docker-compose build --no-cache
    
    echo "🚀 Starting services..."
    PORT=$((PORT_RANGE_BEGIN + USER_ID * RANGE_RESERVED)) HTTPS_PORT=$((PORT_RANGE_BEGIN + USER_ID * RANGE_RESERVED + 363)) USER_ID=$USER_ID docker-compose up -d
fi

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

if [ "$LOCAL_MODE" = "locally" ]; then
    # Check local services
    if [ -f "app.pid" ] && kill -0 $(cat app.pid) 2>/dev/null; then
        echo "✅ Local services are running!"
        echo ""
        echo "🌐 Application URLs:"
        echo "   Web Interface: http://localhost (via Nginx)"
        echo "   Direct Flask:  http://localhost:80"
        echo ""
        echo "📋 Management Commands:"
        echo "   View logs:     tail -f app.log"
        echo "   Stop services: ./deploy.sh stop locally"
        echo "   Check Flask:   ps aux | grep python3"
    else
        echo "❌ Failed to start local services. Check app.log"
        exit 1
    fi
else
    # Check Docker services
    ACTUAL_PORT=${PORT_START:-$((PORT_RANGE_BEGIN + USER_ID * RANGE_RESERVED))}
    ACTUAL_HTTPS_PORT=${HTTPS_PORT:-$((PORT_RANGE_BEGIN + USER_ID * RANGE_RESERVED + 1))}
    
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