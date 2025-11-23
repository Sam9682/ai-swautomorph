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

# Interactive menu for deployment mode selection using Python simple-term-menu
show_deployment_menu() {
    # Check if simple-term-menu is available
    if ! python3 -c "from simple_term_menu import TerminalMenu" 2>/dev/null; then
        echo "Installing simple-term-menu..."
        pip3 install simple-term-menu >/dev/null 2>&1 || {
            echo "Failed to install simple-term-menu. Using fallback menu."
            echo "Select deployment mode:"
            echo "1) Locally (no Docker)"
            echo "2) Docker"
            echo "3) Both"
            read -p "Enter your choice (1-3): " choice
            case $choice in
                1) echo "locally" ;;
                2) echo "docker" ;;
                3) echo "both" ;;
                *) echo "both" ;;
            esac
            return
        }
    fi
    
    # Use Python simple-term-menu for interactive selection
    python3 << 'EOF'
from simple_term_menu import TerminalMenu

options = ["Locally (no Docker)", "Docker", "Both"]
terminal_menu = TerminalMenu(
    options,
    title="🚀 Select deployment mode:",
    menu_cursor="▶ ",
    menu_cursor_style=("fg_cyan", "bold"),
    menu_highlight_style=("bg_cyan", "fg_black"),
    cycle_cursor=True
)

menu_entry_index = terminal_menu.show()

if menu_entry_index == 0:
    print("locally")
elif menu_entry_index == 1:
    print("docker")
elif menu_entry_index == 2:
    print("both")
else:
    print("both")
EOF
}

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
    # print 80 '-' to seperate a new line
    echo "--------------------------------------------------------------------------------"
    echo "📊 Locally Service Status:"
    check_flask_status
    check_nginx_status
    check_gitea_status
    echo "--------------------------------------------------------------------------------"
    echo "📊 Docker Compose Status:"
    check_docker_status
}

check_flask_status() {
    if [ -f "app.pid" ]; then
        PID=$(cat app.pid)
        if kill -0 "$PID" 2>/dev/null; then
            echo "  ✅ Flask application: Running (PID: $PID)"
        else
            echo "  ❌ Flask application: Not running (stale PID: $PID)"
        fi
    else
        echo "  ❌ Flask application: Not running (no PID file)"
    fi
}

check_nginx_status() {
    if systemctl is-active --quiet nginx; then
        echo "  ✅ Nginx: Running"
        if [ -f "/etc/nginx/sites-enabled/ai-swautomorph" ]; then
            echo "  ✅ $NAME_OF_APPLICATION site: Configured"
        else
            echo "  ⚠️ $NAME_OF_APPLICATION site: Not configured"
        fi
    else
        echo "  ❌ Nginx: Not running"
    fi
}

check_gitea_status() {
    if systemctl is-active --quiet gitea 2>/dev/null; then
        echo "  ✅ Gitea: Running on http://localhost:3000"
    else
        echo "  ❌ Gitea: Not running"
    fi
}

check_docker_status() {
    if command -v docker-compose &> /dev/null; then
        HTTP_PORT=$((HTTP_PORT)) HTTPS_PORT=$((HTTPS_PORT + 363)) USER_ID=$USER_ID docker-compose ps
    else
        echo "  ❌ Docker Compose not installed"
    fi
}

# Stop services
stop_services() {
    echo "🛑 Stopping $NAME_OF_APPLICATION services..."
    
    if [ "$LOCAL_MODE" = "locally" ]; then
        stop_flask_service
        remove_nginx_config
        stop_nginx_service
        remove_gitea
    elif [ "$LOCAL_MODE" = "docker" ]; then
        stop_docker_services
    else
        stop_flask_service
        remove_nginx_config
        stop_nginx_service
        remove_gitea
        stop_docker_services
    fi
    
    echo "  ✅ Services stopped"
}

# Remove Gitea installation
remove_gitea() {
    echo "🗑️ Removing Gitea installation..."
    
    # Stop and disable Gitea service
    sudo systemctl stop gitea 2>/dev/null || true
    sudo systemctl disable gitea 2>/dev/null || true
    
    # Remove systemd service file
    sudo rm -f /etc/systemd/system/gitea.service
    sudo systemctl daemon-reload
    
    # Remove Gitea binary
    sudo rm -f /usr/local/bin/gitea
    
    # Remove configuration and data
    sudo rm -rf /etc/gitea
    sudo rm -rf /var/lib/gitea
    sudo rm -rf /home/ubuntu/admin
    
    # Remove git user
    sudo userdel git 2>/dev/null || true
    sudo groupdel git 2>/dev/null || true
    
    echo "  ✅ Gitea removed successfully"
}

stop_flask_service() {
    if [ -f "app.pid" ]; then
        PID=$(cat app.pid)
        if kill -0 "$PID" 2>/dev/null; then
            kill "$PID"
            echo "  ✅ Flask application stopped (PID: $PID)"
        else
            echo "  ⚠️ Flask process not running (PID: $PID)"
        fi
        rm -f app.pid
    else
        echo "  ⚠️ No app.pid file found"
    fi
}

remove_nginx_config() {
    if [ -f "/etc/nginx/sites-enabled/ai-swautomorph" ]; then
        sudo rm -f /etc/nginx/sites-enabled/ai-swautomorph
        # Only reload nginx if it's running
        if systemctl is-active --quiet nginx; then
            sudo nginx -t && sudo systemctl reload nginx
        fi
        echo "  ✅ Nginx configuration removed"
    fi
}

stop_nginx_service() {
    if systemctl is-active --quiet nginx; then
        sudo systemctl stop nginx
        echo "  ✅ Nginx service stopped"
    else
        echo "  ⚠️ Nginx service was not running"
    fi
}

stop_docker_services() {
    HTTP_PORT=$((HTTP_PORT)) HTTPS_PORT=$((HTTPS_PORT + 363)) USER_ID=$USER_ID docker-compose down
}

# Show logs
show_logs() {
    echo "📋 $NAME_OF_APPLICATION Service Logs:"
    show_flask_logs
    show_nginx_logs
    show_docker_logs
}

show_flask_logs() {
    LOG_FILE="logs/app_logs_$(date +%Y%m%d).log"
    if [ -f "$LOG_FILE" ]; then
        echo "  🐍 Flask Application Logs ($LOG_FILE):"
        cat "$LOG_FILE"
    else
        echo "  ❌ No Flask log file found ($LOG_FILE)"
        # Try to find any app logs in logs directory
        if ls logs/app_logs_*.log 1> /dev/null 2>&1; then
            echo "📋 Available log files:"
            ls -la logs/app_logs_*.log
        fi
    fi
}

show_nginx_logs() {
    echo ""
    echo "🌐 Nginx Error Logs (last 20 lines):"
    sudo tail -n 20 /var/log/nginx/error.log 2>/dev/null || echo "  ❌ Cannot access Nginx logs"
}

show_docker_logs() {
    HTTP_PORT=$((HTTP_PORT)) HTTPS_PORT=$((HTTPS_PORT + 363)) USER_ID=$USER_ID docker-compose logs -f
}

# Restart services
restart_services() {
    echo "🔄 Restarting $NAME_OF_APPLICATION services..."
    
    if [ "$LOCAL_MODE" = "locally" ]; then
        restart_flask_service
        reload_nginx_config
    elif [ "$LOCAL_MODE" = "docker" ]; then
        restart_docker_services
    else
        restart_flask_service
        reload_nginx_config
        restart_docker_services
    fi
    
    echo "✅ Services restarted"
}

restart_flask_service() {
    stop_flask_service
    echo "  🚀 Starting Flask application..."
    # Create logs directory if it doesn't exist
    mkdir -p logs
    # Start Flask with date-based log file
    LOG_FILE="logs/app_logs_$(date +%Y%m%d).log"
    nohup python3 app.py > "$LOG_FILE" 2>&1 &
    echo $! > app.pid
}

reload_nginx_config() {
    if systemctl is-active --quiet nginx; then
        sudo nginx -t && sudo systemctl reload nginx
    else
        sudo systemctl start nginx
        sudo nginx -t
    fi
}

restart_docker_services() {
    HTTP_PORT=$((HTTP_PORT)) HTTPS_PORT=$((HTTPS_PORT + 363)) USER_ID=$USER_ID docker-compose restart
}

# Start services
start_services() {
    echo "🚀 Starting $NAME_OF_APPLICATION deployment..."
    
    if [ "$LOCAL_MODE" = "locally" ]; then
        start_local_deployment
    elif [ "$LOCAL_MODE" = "docker" ]; then
        start_docker_deployment
    else
        start_local_deployment
        start_docker_deployment
    fi
}

start_local_deployment() {
    echo "💻 Starting local deployment..."
    install_python_dependencies
    setup_gitea
    create_gitea_admin_user
    start_flask_application
    configure_nginx
    configure_firewall
}

# Setup Gitea for local development
setup_gitea() {
    echo "🔧 Checking Gitea installation..."
    
    # Check if Gitea is already running
    if systemctl is-active --quiet gitea 2>/dev/null; then
        echo "  ✅ Gitea is already running"
        return 0
    fi
    
    # Check if already configured
    if [ -f "/etc/gitea/app.ini" ]; then
        echo "  ✅ Gitea is already configured"
        sudo systemctl start gitea 2>/dev/null || true
        if systemctl is-active --quiet gitea; then
            echo "  ✅ Gitea is running on http://localhost:3000"
            # Try to reset admin password if user exists
            create_gitea_admin_user
        fi
        return 0
    fi
    
    # Check if Gitea is installed
    if ! command -v gitea &> /dev/null; then
        echo "  📦 Installing Gitea..."
        
        # Download and install Gitea
        wget -O /tmp/gitea https://dl.gitea.io/gitea/1.21.3/gitea-1.21.3-linux-amd64
        sudo mv /tmp/gitea /usr/local/bin/gitea
        sudo chmod +x /usr/local/bin/gitea
        
        # Create gitea user
        sudo adduser --system --shell /bin/bash --gecos 'Git Version Control' --group --disabled-password --home /home/git git || true
        
        # Create directories
        sudo mkdir -p /var/lib/gitea/{custom,data,log}
        sudo chown -R git:git /var/lib/gitea/
        sudo chmod -R 750 /var/lib/gitea/
        
        # Create systemd service
        sudo tee /etc/systemd/system/gitea.service > /dev/null << 'EOF'
[Unit]
Description=Gitea (Git with a cup of tea)
After=syslog.target
After=network.target

[Service]
RestartSec=2s
Type=simple
User=git
Group=git
WorkingDirectory=/var/lib/gitea/
ExecStart=/usr/local/bin/gitea web --config /etc/gitea/app.ini
Restart=always
Environment=USER=git HOME=/home/git GITEA_WORK_DIR=/var/lib/gitea

[Install]
WantedBy=multi-user.target
EOF
        
        # Create config directory
        sudo mkdir -p /etc/gitea
        sudo chown root:git /etc/gitea
        sudo chmod 770 /etc/gitea
        
        echo "  ✅ Gitea installed successfully"
        configure_gitea
    fi
    
    # Start Gitea service
    echo "🚀 Starting Gitea service..."
    sudo systemctl daemon-reload
    sudo systemctl enable gitea
    sudo systemctl start gitea
    
    # Wait for Gitea to start
    sleep 5
    
    if systemctl is-active --quiet gitea; then
        echo "  ✅ Gitea is running on http://localhost:3000"
        echo "  📝 Complete initial setup at http://localhost:3000/install"
        echo "  📝 Recommended admin credentials: admin/password"
    else
        echo "  ❌ Failed to start Gitea"
    fi
}

# Configure Gitea with predefined settings
configure_gitea() {
    echo "  ⚙️ Configuring Gitea..."
    
    # Create required directories
    sudo mkdir -p /home/ubuntu/admin/data/gitea-repositories
    sudo mkdir -p /home/ubuntu/admin/db
    sudo mkdir -p /home/ubuntu/admin
    sudo chown -R git:git /home/ubuntu/admin
    
    # Create Gitea configuration
    sudo tee /etc/gitea/app.ini > /dev/null << 'EOF'
[database]
DB_TYPE = sqlite3
PATH = /home/ubuntu/admin/db/gitea.db

[repository]
ROOT = /home/ubuntu/admin/data/gitea-repositories

[server]
DOMAIN = www.swautomorph.com
HTTP_ADDR = 0.0.0.0
HTTP_PORT = 3000
ROOT_URL = https://www.swautomorph.com/gitea/

[mailer]
ENABLED = false

[service]
DISABLE_REGISTRATION = false
REQUIRE_SIGNIN_VIEW = false

[log]
MODE = file
LEVEL = Info
ROOT_PATH = /var/lib/gitea/log

[security]
INSTALL_LOCK = true
DISABLE_QUERY_AUTH_TOKEN = true

[git.lfs]
START_SERVER = true
CONTENT_PATH = /home/ubuntu/admin
EOF
    
    sudo chown git:git /etc/gitea/app.ini
    sudo chmod 640 /etc/gitea/app.ini
    
    echo "  ✅ Gitea configured successfully"
}

# Setup Gitea admin user and API token
create_gitea_admin_user() {
    echo "👤 Setting up Gitea admin access..."
    
    # Wait for Gitea to be fully ready
    sleep 15
    
    # Set environment variables for Gitea CLI
    export GITEA_WORK_DIR=/var/lib/gitea
    export USER=git
    export HOME=/home/git
    
    # Create gitadmin user
    echo "👤 Creating gitadmin user..."
    sudo -u git -E /usr/local/bin/gitea admin user create \
        --username gitadmin \
        --password password \
        --email admin@swautomorph.com \
        --admin \
        --config /etc/gitea/app.ini \
        --work-path /var/lib/gitea 2>/dev/null || true
    
    echo "  🔑 Gitea Admin Credentials:"
    echo "      Username: gitadmin"
    echo "      Password: password"
    echo "      URL: http://www.swautomorph.com/gitea"
    
    # Try to generate API token
    setup_api_token
}

# Setup API token for admin user
setup_api_token() {
    echo "  🔑 Setting up API token..."
    
    # Try to generate API token for admin user with all required scopes
    TOKEN=$(sudo -u git -E /usr/local/bin/gitea admin user generate-access-token \
        --username gitadmin \
        --token-name "api-access" \
        --scopes "write:admin,write:user,write:repository" \
        --config /etc/gitea/app.ini \
        --work-path /var/lib/gitea 2>/dev/null | grep -o '[a-f0-9]\{40\}')
    
    if [ -n "$TOKEN" ]; then
        echo "$TOKEN" > /tmp/gitea_admin_token
        chmod 600 /tmp/gitea_admin_token
        echo "✅ API token created and saved to /tmp/gitea_admin_token"
    else
        echo "      ⚠️ Could not generate API token automatically"
        echo "      📝 Manual steps to create API token:"
        echo "          1. Login to Gitea at http://localhost:3000"
        echo "          2. Go to Settings > Applications > Generate New Token"
        echo "          3. Save the token to /tmp/gitea_admin_token"
    fi
}

start_docker_deployment() {
    echo "🐳 Starting Docker deployment..."
    cleanup_docker
    HTTP_PORT=$((HTTP_PORT)) HTTPS_PORT=$((HTTPS_PORT + 363)) USER_ID=$USER_ID docker-compose up -d --build
    echo "  ✅ Docker services started"
}

install_python_dependencies() {
    if [ -f "requirements.txt" ]; then
        echo "  📦 Installing Python dependencies..."
        pip3 install -r requirements.txt
    fi
}

start_flask_application() {
    echo "  🚀 Starting Flask application..."
    # Stop any existing Flask processes on port 5000
    pkill -f "python3 app.py" || true
    sleep 2
    # Create logs directory if it doesn't exist
    mkdir -p logs
    # Start Flask on port 5001 to avoid conflicts with date-based log file
    LOG_FILE="logs/app_logs_$(date +%Y%m%d).log"
    FLASK_RUN_PORT=5001 nohup python3 app.py > "$LOG_FILE" 2>&1 &
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
    server_name localhost www.swautomorph.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name localhost www.swautomorph.com;
    
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
    
    location /gitea/ {
        proxy_pass http://127.0.0.1:3000/;
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
    if systemctl is-active --quiet nginx; then
        sudo nginx -t && sudo systemctl reload nginx
    else
        sudo systemctl start nginx
        sudo nginx -t
    fi
}

configure_firewall() {
    echo "🔥 Configuring firewall for internet access..."
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    sudo ufw allow 3000/tcp
    sudo ufw --force enable
}

cleanup_docker() {
    echo "🧹 Cleaning up..."
    HTTP_PORT=$((HTTP_PORT)) HTTPS_PORT=$((HTTPS_PORT + 363)) USER_ID=$USER_ID docker-compose down --remove-orphans
}

# Validate user input
validate_user_id() {
    if ! [[ "$USER_ID" =~ ^[a-zA-Z0-9_-]+$ ]]; then
        echo "  ❌ Error: user_id must be alphanumeric (letters, numbers, underscore, hyphen)"
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
        sudo apt update && sudo apt install -y nginx wget
        sudo systemctl enable nginx
        echo "✅ Nginx installed successfully"
    fi
}

check_docker_requirements() {
    if ! command -v docker &> /dev/null; then
        echo "  ❌ Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo "  ❌ Docker Compose is not installed. Please install Docker Compose first."
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
    mkdir -p data ssl logs db
    chmod 755 data ssl logs db
}

setup_ssl_certificates() {
    if [ ! -f ssl/cert.pem ] || [ ! -f ssl/key.pem ]; then
        echo "🔐 Generating SSL certificates..."
        ./generate_ssl.sh
    else
        echo "  ✅ SSL certificates already exist"
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
        echo "  ✅ Environment file created (.env)"
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
    echo "  ps           - Show service status (Locally and Docker)"
    echo "  logs         - Show service logs  (Flask + Nginx Docker)" 
}

# Main function - orchestrates the deployment process
main() {
    calculate_ports
    show_environment 

    # Show interactive menu for start, stop, restart commands if no LOCAL_MODE specified
    if [[ "$COMMAND" =~ ^(start|stop|restart)$ ]] && [ "$LOCAL_MODE" = "0" ]; then
        SELECTED_MODE=$(show_deployment_menu)
        if [ "$SELECTED_MODE" = "locally" ]; then
            LOCAL_MODE="locally"
        elif [ "$SELECTED_MODE" = "docker" ]; then
            LOCAL_MODE="docker"
        else
            LOCAL_MODE="both"
        fi
    fi

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