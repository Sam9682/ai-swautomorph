#!/bin/bash

# AI-SwAutoMorph Production Deployment Script
# Organized with functions for better maintainability

set -e

# Global Variables
NAME_OF_APPLICATION="ai-swautomorph"
APPLICATION_IDENTITY_NUMBER=0
RANGE_START=80
RANGE_RESERVED=10

# Global Parameters
COMMAND=${1:-help}
LOCAL_MODE=${2:-0}
USER_ID=${3:-0}
USER_NAME=${4:-"user"}
USER_EMAIL=${5:-"user@swautomorph.com"}
DESCRIPTION=${6:-"Basic Information Display"}

# Configuration
DOMAIN=${DOMAIN:-"www.swautomorph.com"}
EMAIL=${EMAIL:-"user@swautomorph.com"}
ENV_FILE=".env.prod"

# Calculate ports (convert alphanumeric USER_ID to numeric for port calculation)
calculate_ports() {
    PORT_RANGE_BEGIN=$((APPLICATION_IDENTITY_NUMBER * 100 + RANGE_START))
    HTTP_PORT=$((PORT_RANGE_BEGIN + USER_ID * RANGE_RESERVED))
    HTTPS_PORT=$((HTTP_PORT + 1))
}

# Display environment variables for operations
show_environment() {
    local operation=$1
    echo "🔍 Starting $operation operation..."
    echo "Environment Variables:"
    echo "  LOCAL_MODE=${LOCAL_MODE}"
    echo "  USER_ID=${USER_ID}"
    echo "  USER_NAME=${USER_NAME}"
    echo "  USER_EMAIL=${USER_EMAIL}"
    echo "  PORT=${HTTP_PORT}"
    echo "  HTTPS_PORT=${HTTPS_PORT}"
    echo ""
}

# Check service status
check_status() {
    if [ "$LOCAL_MODE" = "locally" ]; then
        echo "📊 $NAME_OF_APPLICATION Local Service Status:"
        check_flask_status
        check_nginx_status
    else
        echo "📊 $NAME_OF_APPLICATION Service Status:"
        check_docker_status
    fi
}

check_flask_status() {
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
}

check_nginx_status() {
    if systemctl is-active --quiet nginx; then
        echo "✅ Nginx: Running"
        if [ -f "/etc/nginx/sites-enabled/ai-swautomorph" ]; then
            echo "✅ $NAME_OF_APPLICATION site: Configured"
        else
            echo "⚠️ $NAME_OF_APPLICATION site: Not configured"
        fi
    else
        echo "❌ Nginx: Not running"
    fi
}

check_docker_status() {
    if command -v docker-compose &> /dev/null; then
        HTTP_PORT=$((HTTP_PORT)) HTTPS_PORT=$((HTTPS_PORT + 363)) USER_ID=$USER_ID docker-compose ps
    else
        echo "❌ Docker Compose not installed"
    fi
}

# Stop services
stop_services() {
    if [ "$LOCAL_MODE" = "locally" ]; then
        echo "🛑 Stopping local $NAME_OF_APPLICATION services..."
        stop_flask_service
        remove_nginx_config
        echo "✅ Local services stopped"
    else
        echo "🛑 Stopping $NAME_OF_APPLICATION services..."
        stop_docker_services
        echo "✅ Services stopped"
    fi
}

stop_flask_service() {
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
}

remove_nginx_config() {
    if [ -f "/etc/nginx/sites-enabled/ai-swautomorph" ]; then
        sudo rm -f /etc/nginx/sites-enabled/ai-swautomorph
        sudo nginx -t && sudo systemctl reload nginx
        echo "✅ Nginx configuration removed"
    fi
}

stop_docker_services() {
    HTTP_PORT=$((HTTP_PORT)) HTTPS_PORT=$((HTTPS_PORT + 363)) USER_ID=$USER_ID docker-compose down
}

# Show logs
show_logs() {
    if [ "$LOCAL_MODE" = "locally" ]; then
        echo "📋 $NAME_OF_APPLICATION Local Service Logs:"
        show_flask_logs
        show_nginx_logs
    else
        show_docker_logs
    fi
}

show_flask_logs() {
    if [ -f "app.log" ]; then
        echo "🐍 Flask Application Logs:"
        cat app.log
    else
        echo "❌ No Flask log file found (app.log)"
    fi
}

show_nginx_logs() {
    echo ""
    echo "🌐 Nginx Error Logs (last 20 lines):"
    sudo tail -n 20 /var/log/nginx/error.log 2>/dev/null || echo "❌ Cannot access Nginx logs"
}

show_docker_logs() {
    HTTP_PORT=$((HTTP_PORT)) HTTPS_PORT=$((HTTPS_PORT + 363)) USER_ID=$USER_ID docker-compose logs -f
}

# Restart services
restart_services() {
    if [ "$LOCAL_MODE" = "locally" ]; then
        echo "🔄 Restarting local $NAME_OF_APPLICATION services..."
        restart_flask_service
        reload_nginx_config
        echo "✅ Local services restarted"
    else
        echo "🔄 Restarting $NAME_OF_APPLICATION services..."
        restart_docker_services
        echo "✅ Services restarted"
    fi
}

restart_flask_service() {
    stop_flask_service
    echo "🚀 Starting Flask application..."
    nohup python3 app.py > app.log 2>&1 &
    echo $! > app.pid
}

reload_nginx_config() {
    sudo nginx -t && sudo systemctl reload nginx
}

restart_docker_services() {
    HTTP_PORT=$((HTTP_PORT)) HTTPS_PORT=$((HTTPS_PORT + 363)) USER_ID=$USER_ID docker-compose restart
}

# Start services
start_services() {
    if [ "$LOCAL_MODE" = "locally" ]; then
        echo "🚀 Starting $NAME_OF_APPLICATION locally (no Docker)..."
        start_local_deployment
    else
        echo "🚀 Starting $NAME_OF_APPLICATION deployment..."
        start_docker_deployment
    fi
}

start_local_deployment() {
    echo "💻 Starting local deployment..."
    install_python_dependencies
    start_flask_application
    configure_nginx
    configure_firewall
}

start_docker_deployment() {
    echo "🐳 Starting Docker deployment..."
    cleanup_docker
    HTTP_PORT=$((HTTP_PORT)) HTTPS_PORT=$((HTTPS_PORT + 363)) USER_ID=$USER_ID docker-compose up -d --build
    echo "✅ Docker services started"
}

install_python_dependencies() {
    if [ -f "requirements.txt" ]; then
        echo "📦 Installing Python dependencies..."
        pip3 install -r requirements.txt
    fi
}

start_flask_application() {
    echo "🚀 Starting Flask application..."
    # Stop any existing Flask processes on port 5000
    pkill -f "python3 app.py" || true
    sleep 2
    # Start Flask on port 5001 to avoid conflicts
    FLASK_RUN_PORT=5001 nohup python3 app.py > app.log 2>&1 &
    echo $! > app.pid
}

configure_nginx() {
    echo "🌐 Configuring Nginx..."
    create_nginx_config
    enable_nginx_site
    test_and_reload_nginx
}

create_nginx_config() {
    cat > /tmp/ai-swautomorph-site << 'EOF'
server {
    listen 80;
    server_name _;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name _;
    
    ssl_certificate /home/ubuntu/ai-swautomorph/ssl/cert.pem;
    ssl_certificate_key /home/ubuntu/ai-swautomorph/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF
}

enable_nginx_site() {
    sudo mv /tmp/ai-swautomorph-site /etc/nginx/sites-available/ai-swautomorph
    sudo ln -sf /etc/nginx/sites-available/ai-swautomorph /etc/nginx/sites-enabled/
}

test_and_reload_nginx() {
    sudo nginx -t && sudo systemctl reload nginx
}

configure_firewall() {
    echo "🔥 Configuring firewall for internet access..."
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    sudo ufw --force enable
}

cleanup_docker() {
    echo "🧹 Cleaning up..."
    HTTP_PORT=$((HTTP_PORT)) HTTPS_PORT=$((HTTPS_PORT + 363)) USER_ID=$USER_ID docker-compose down --remove-orphans
}

# Validate user input
validate_user_id() {
    if ! [[ "$USER_ID" =~ ^[a-zA-Z0-9_-]+$ ]]; then
        echo "❌ Error: user_id must be alphanumeric (letters, numbers, underscore, hyphen)"
        exit 1
    fi
}

# Check system requirements
check_requirements() {
    if [ "$LOCAL_MODE" = "locally" ]; then
        check_local_requirements
    else
        check_docker_requirements
    fi
}

check_local_requirements() {
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
}

check_docker_requirements() {
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo "❌ Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
}

# Setup directories and certificates
setup_environment() {
    create_directories
    setup_ssl_certificates
    generate_environment_file
}

create_directories() {
    echo "📁 Creating directories..."
    mkdir -p data ssl logs
    chmod 755 data ssl logs
}

setup_ssl_certificates() {
    if [ ! -f ssl/cert.pem ] || [ ! -f ssl/key.pem ]; then
        echo "🔐 Generating SSL certificates..."
        ./generate_ssl.sh
    else
        echo "✅ SSL certificates already exist"
    fi
}

generate_environment_file() {
    if [ ! -f .env ]; then
        echo "🔑 Generating environment configuration..."
        SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
        cat > .env << EOF
SECRET_KEY=${SECRET_KEY}
FLASK_ENV=production
EOF
        echo "✅ Environment file created (.env)"
    fi
}

# Start env
start() {
    validate_user_id
    check_requirements
    setup_environment
    start_services
    echo "🎉 Deployment completed successfully!"
}

# Show usage information
show_usage() {
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
}

# Main function - orchestrates the deployment process
main() {
    calculate_ports
    show_environment 

    case $COMMAND in
        "ps")
            check_status
            exit 0
            ;;
        "stop")
            stop_services
            exit 0
            ;;
        "logs")
            show_logs
            exit 0
            ;;
        "restart")
            restart_services
            exit 0
            ;;
        "start")
            start
            exit 0
            ;;
        *)
            show_usage
            exit 1
            ;;
    esac
}

# Execute main function
main "$@"