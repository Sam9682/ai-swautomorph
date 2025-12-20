#!/bin/bash

# AI-SwAutoMorph Production Deployment Script
# Organized with functions for better maintainability

set -e

# Load configuration from deploy.ini
load_config() {
    local config_file="./conf/deploy.ini"
    if [ -f "$config_file" ]; then
        echo "📋 Loading configuration from $config_file"
        # Source the config file, ignoring comments and empty lines
        while IFS='=' read -r key value; do
            # Skip comments and empty lines
            [[ $key =~ ^[[:space:]]*# ]] && continue
            [[ -z $key ]] && continue
            # Remove leading/trailing whitespace and export
            key=$(echo "$key" | xargs)
            value=$(echo "$value" | xargs)
            if [[ -n $key && -n $value ]]; then
                export "$key"="$value"
            fi
        done < "$config_file"
        echo "  ✅ Configuration loaded successfully"
    else
        echo "  ⚠️ Configuration file $config_file not found, using defaults"
    fi
}

# Load configuration first
load_config

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Status symbols with colors
OK="${GREEN}[OK]${NC}"
ERROR="${RED}[ERROR]${NC}"
WARN="${YELLOW}[WARN]${NC}"
INFO="${BLUE}[INFO]${NC}"

# Global Variables (with fallback defaults)
NAME_OF_APPLICATION=${NAME_OF_APPLICATION:-"ai-swautomorph"}
APPLICATION_IDENTITY_NUMBER=${APPLICATION_IDENTITY_NUMBER:-0}
RANGE_START_CONTROLPLAN=${RANGE_START_CONTROLPLAN:-80}
RANGE_RESERVED_CONTROLPLAN=${RANGE_RESERVED_CONTROLPLAN:-0}

# Global Parameters (command line args override config)
COMMAND=${1:-help}
LOCAL_MODE=${2:-0}
USER_ID=${3:-${DEFAULT_USER_ID:-0}}
USER_NAME=${4:-${DEFAULT_USER_NAME:-"admin"}}
USER_EMAIL=${5:-${DEFAULT_USER_EMAIL:-"admin@swautomorph.com"}}
DESCRIPTION=${6:-${DEFAULT_DESCRIPTION:-"Basic Admin user for Control Plan"}}

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
            read -p "Enter your choice (1-2): " choice
            case $choice in
                1) echo -e " $YELLOW locally" ;;
                2) echo -e " $YELLOW docker" ;;
                *) echo "locally" ;;
            esac
            return
        }
    fi
    
    # Use Python simple-term-menu for interactive selection
    python3 << 'EOF'
from simple_term_menu import TerminalMenu

options = ["Locally (no Docker)", "Docker"]
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
else:
    print("locally")
EOF
}

# Configuration (loaded from deploy.ini with fallback defaults)
DOMAIN=${DOMAIN:-"www.swautomorph.com"}
EMAIL=${EMAIL:-"admin@swautomorph.com"}
ENV_FILE=${ENV_FILE:-".env.prod"}
SSL_CERT_PATH=${SSL_CERT_PATH:-"/home/ubuntu/ai-swautomorph/ssl/STAR_swautomorph_com.crt"}
SSL_KEY_PATH=${SSL_KEY_PATH:-"/home/ubuntu/ai-swautomorph/ssl/privateKey_STAR_swautomorph_com.key"}
GITEA_VERSION=${GITEA_VERSION:-"1.21.3"}
GITEA_ADMIN_USER=${GITEA_ADMIN_USER:-"gitadmin"}
GITEA_ADMIN_PASSWORD=${GITEA_ADMIN_PASSWORD:-"password"}
GITEA_ADMIN_EMAIL=${GITEA_ADMIN_EMAIL:-"admin@swautomorph.com"}

# Calculate ports (convert alphanumeric USER_ID to numeric for port calculation)
calculate_ports() {
    HTTP_PORT=${RANGE_START_CONTROLPLAN}
    HTTPS_PORT=$((HTTP_PORT + 1))
    HTTPS_PORT2=$((HTTPS_PORT + 1))
}

# Display environment variables for operations
show_environment() {
    local operation=$1
    echo "🔍 Starting $operation operation..."
    echo -e "${CYAN}[STATUS]${NC} Environment Variables:"
    echo "  LOCAL_MODE=${LOCAL_MODE}"
    echo "  USER_ID=${USER_ID}"
    echo "  USER_NAME=${USER_NAME}"
    echo "  USER_EMAIL=${USER_EMAIL}"
    echo "  HTTP_PORT=${HTTP_PORT}"
    echo "  HTTPS_PORT=${HTTPS_PORT}"
    echo "  HTTPS_PORT2=${HTTPS_PORT2}"
    echo ""
}

# Check service status
check_status() {
    # print 80 '-' to seperate a new line
    echo "--------------------------------------------------------------------------------"
    echo -e "${CYAN}[STATUS]${NC} Locally Service Status:"
    check_flask_status
    check_nginx_status
    check_gitea_status
    echo "--------------------------------------------------------------------------------"
    echo -e "${CYAN}[STATUS]${NC} Docker Compose Status:"
    check_docker_status
}

check_flask_status() {
    if [ -f "${PID_FILE:-./conf/app.pid}" ]; then
        PID=$(cat "${PID_FILE:-./conf/app.pid}")
        if kill -0 "$PID" 2>/dev/null; then
            PROCESS_OWNER=$(ps -o user= -p "$PID" 2>/dev/null || echo "unknown")
            echo -e "  $OK Flask application: Running (PID: $PID, Owner: $PROCESS_OWNER)"
        else
            echo -e "  $ERROR Flask application: Not running (stale PID: $PID)"
        fi
    else
        echo -e "  $ERROR Flask application: Not running (no PID file)"
    fi
    
    # Check for any other Flask processes
    OTHER_PIDS=$(pgrep -f "python3 ControlPlanFlaskApp.py" 2>/dev/null || true)
    if [ -n "$OTHER_PIDS" ]; then
        echo -e "  $WARN Other Flask processes found: $OTHER_PIDS"
        for pid in $OTHER_PIDS; do
            OWNER=$(ps -o user= -p "$pid" 2>/dev/null || echo "unknown")
            echo -e "    PID: $pid, Owner: $OWNER"
        done
    fi
}

check_nginx_status() {
    if systemctl is-active --quiet nginx; then
        echo -e "  $OK Nginx: Running"
        if [ -f "${NGINX_SITES_ENABLED:-/etc/nginx/sites-enabled}/${NGINX_SITE_NAME:-ai-swautomorph}" ]; then
            echo -e "  $OK $NAME_OF_APPLICATION site: Configured"
        else
            echo -e "  $WARN $NAME_OF_APPLICATION site: Not configured"
        fi
    else
        echo -e "  $ERROR Nginx: Not running"
    fi
}

check_gitea_status() {
    if systemctl is-active --quiet gitea 2>/dev/null; then
        echo -e "  $OK Gitea: Running on http://localhost:${GITEA_PORT:-3000}"
    else
        echo -e "  $ERROR Gitea: Not running"
    fi
}

check_docker_status() {
    if command -v docker-compose &> /dev/null; then
        HTTP_PORT=$HTTP_PORT HTTPS_PORT=$((HTTPS_PORT + ${DOCKER_PORT_OFFSET:-363})) HTTPS_PORT2=$((HTTPS_PORT2 + ${DOCKER_PORT_OFFSET:-363})) USER_ID=$USER_ID docker-compose ps
    else
        echo "  ❌ Docker Compose not installed"
    fi
}

# Provide guidance for manual process cleanup
provide_cleanup_guidance() {
    echo ""
    echo -e "${YELLOW}[CLEANUP GUIDANCE]${NC} If processes couldn't be stopped automatically:"
    echo "  1. Check running processes: ps aux | grep 'python3 ControlPlanFlaskApp.py'"
    echo "  2. Kill specific PID: sudo kill -9 <PID>"
    echo "  3. Kill all Flask processes: sudo pkill -9 -f 'python3 ControlPlanFlaskApp.py'"
    echo "  4. Check process ownership: ps -o pid,user,cmd -C python3"
    echo ""
}

# Database backup function
backup_database() {
    echo "💾 Creating database backup..."
    
    # Create backup directory with timestamp
    DATETIME=$(date +"%Y%m%d_%H%M%S")
    BACKUP_DIR="./softfluid/db/backup/$DATETIME"
    mkdir -p "$BACKUP_DIR"
    
    # Database file path
    DB_FILE="./softfluid/db/ai_swautomorph.db"
    
    if [ -f "$DB_FILE" ]; then
        echo "  📋 Backing up database tables..."
        
        # Get all table names
        TABLES=$(sqlite3 "$DB_FILE" ".tables")
        
        # Dump each table
        for table in $TABLES; do
            echo "    📄 Dumping table: $table"
            sqlite3 "$DB_FILE" ".dump $table" > "$BACKUP_DIR/${table}.sql"
        done
        
        # Create complete database dump
        echo "    💿 Creating complete database dump..."
        sqlite3 "$DB_FILE" ".dump" > "$BACKUP_DIR/complete_database.sql"
        
        # Copy the database file itself
        cp "$DB_FILE" "$BACKUP_DIR/ai_swautomorph.db.backup"
        
        echo -e "  $OK Database backup completed: $BACKUP_DIR"
        echo "    📁 Files created:"
        ls -la "$BACKUP_DIR" | sed 's/^/      /'
        
        # Sync to S3
        echo "  ☁️ Syncing to S3..."
        aws s3 sync ./softfluid s3://softfluid --profile OVH-SWAUTOMORPH
    else
        echo -e "  $WARN Database file $DB_FILE not found - skipping backup"
    fi
}

# Database recovery function
recover_database() {
    echo "🔄 Database Recovery Tool"
    
    BACKUP_BASE_DIR="./softfluid/db/backup"
    
    if [ ! -d "$BACKUP_BASE_DIR" ]; then
        echo -e "  $ERROR No backup directory found at $BACKUP_BASE_DIR"
        exit 1
    fi
    
    # List available backup dates
    BACKUP_DATES=($(ls -1 "$BACKUP_BASE_DIR" | sort -r))
    
    if [ ${#BACKUP_DATES[@]} -eq 0 ]; then
        echo -e "  $ERROR No backup folders found"
        exit 1
    fi
    
    # Use simple-term-menu for backup selection
    if python3 -c "from simple_term_menu import TerminalMenu" 2>/dev/null; then
        # Create temporary file with backup dates
        printf '%s\n' "${BACKUP_DATES[@]}" > /tmp/backup_dates.txt
        
        SELECTED_BACKUP=$(python3 << 'EOF'
from simple_term_menu import TerminalMenu

with open('/tmp/backup_dates.txt', 'r') as f:
    backup_dates = [line.strip() for line in f if line.strip()]

terminal_menu = TerminalMenu(
    backup_dates,
    title="📅 Select backup to restore:",
    menu_cursor="▶ ",
    menu_cursor_style=("fg_green", "bold"),
    menu_highlight_style=("bg_green", "fg_black"),
    cycle_cursor=True
)

menu_entry_index = terminal_menu.show()
if menu_entry_index is not None:
    print(backup_dates[menu_entry_index])
EOF
)
        rm -f /tmp/backup_dates.txt
    else
        # Fallback to numbered selection
        echo "📅 Available backup dates:"
        for i in "${!BACKUP_DATES[@]}"; do
            echo "  $((i+1))) ${BACKUP_DATES[$i]}"
        done
        
        read -p "Select backup to restore (1-${#BACKUP_DATES[@]}): " choice
        
        if ! [[ "$choice" =~ ^[0-9]+$ ]] || [ "$choice" -lt 1 ] || [ "$choice" -gt ${#BACKUP_DATES[@]} ]; then
            echo -e "  $ERROR Invalid selection"
            exit 1
        fi
        
        SELECTED_BACKUP="${BACKUP_DATES[$((choice-1))]}"
    fi
    
    if [ -z "$SELECTED_BACKUP" ]; then
        echo -e "  $WARN No backup selected - operation cancelled"
        exit 0
    fi
    
    BACKUP_DIR="$BACKUP_BASE_DIR/$SELECTED_BACKUP"
    
    echo "🔧 Restoring from backup: $SELECTED_BACKUP"
    
    # Backup current database if it exists
    if [ -f "softfluid/db/ai_swautomorph.db" ]; then
        mv "softfluid/db/ai_swautomorph.db" "softfluid/db/ai_swautomorph.db.pre-recovery.$(date +%Y%m%d_%H%M%S)"
        echo "  💾 Current database backed up"
    fi
    
    # Restore from complete dump if available
    if [ -f "$BACKUP_DIR/complete_database.sql" ]; then
        sqlite3 "softfluid/db/ai_swautomorph.db" < "$BACKUP_DIR/complete_database.sql"
        echo -e "  $OK Database restored from complete dump"
    elif [ -f "$BACKUP_DIR/ai_swautomorph.db.backup" ]; then
        cp "$BACKUP_DIR/ai_swautomorph.db.backup" "softfluid/db/ai_swautomorph.db"
        echo -e "  $OK Database restored from backup file"
    else
        echo -e "  $ERROR No valid backup files found in $BACKUP_DIR"
        exit 1
    fi
    
    echo -e "  $OK Database recovery completed successfully"
}

# Stop services
stop_services() {
    echo "🛑 Stopping $NAME_OF_APPLICATION services..."
    
    # Remove backup cron job
    remove_backup_cron
    
    # Create database backup before stopping services
    backup_database
    
    CLEANUP_NEEDED=false
    
    if [ "$LOCAL_MODE" = "locally" ]; then
        stop_flask_service || CLEANUP_NEEDED=true
        remove_nginx_config
        stop_nginx_service
        confirm_gitea_stop
    elif [ "$LOCAL_MODE" = "docker" ]; then
        stop_docker_services
    else
        stop_flask_service || CLEANUP_NEEDED=true
        remove_nginx_config
        stop_nginx_service
        confirm_gitea_stop
        stop_docker_services
    fi
    
    if [ "$CLEANUP_NEEDED" = "true" ]; then
        provide_cleanup_guidance
    fi
    
    echo -e "  $OK Services stop process completed"
}

# Confirm Gitea stop with user menu
confirm_gitea_stop() {
    if systemctl is-active --quiet gitea 2>/dev/null; then
        echo "⚠️ Gitea is currently running"
        
        # Auto-select "No" when STOP command is used (non-interactive mode)
        if [[ "$COMMAND" =~ ^(stop|-k|--stop)$ ]]; then
            echo "  🔧 Auto-selecting: No, keep Gitea configuration (but nginx is stopped)"
            CHOICE="no"
        fi
        # Check if simple-term-menu is available
        if python3 -c "from simple_term_menu import TerminalMenu" 2>/dev/null; then
            # Use Python simple-term-menu for interactive selection
            CHOICE=$(python3 << 'EOF'
from simple_term_menu import TerminalMenu

options = ["No, keep Gitea configuration (but nginx is stopped)","Yes, stop and remove Gitea configuration"]
terminal_menu = TerminalMenu(
options,
title="🔧 Do you want to stop Gitea service?",
menu_cursor="▶ ",
menu_cursor_style=("fg_red", "bold"),
menu_highlight_style=("bg_red", "fg_yellow"),
cycle_cursor=True
)

menu_entry_index = terminal_menu.show()
print("no" if menu_entry_index == 0 else "yes")
EOF
)
        else
            # Fallback to simple prompt
            echo "Do you want to stop and remove Gitea configuration?"
            echo "1) Yes, stop and remove Gitea configuration"
            echo "2) No, keep Gitea configuration (but nginx is stopped)"
            read -p "Enter your choice (1-2): " choice
            case $choice in
                1) CHOICE="yes" ;;
                *) CHOICE="no" ;;
            esac
        fi
        
        if [ "$CHOICE" = "yes" ]; then
            remove_gitea
        else
            echo "  ⏭️ Skipping Gitea stop - service will continue running"
        fi
    else
        echo "  ℹ️ Gitea is not running - skipping"
    fi
}

# Remove Gitea installation
remove_gitea() {
    echo "🗑️ Stopping and removing Gitea installation..."
    
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
    
    echo "  ✅ Gitea stopped and removed successfully"
}

stop_flask_service() {
    local success=true
    
    # First try to stop using PID file
    if [ -f "./conf/app.pid" ]; then
        PID=$(cat ./conf/app.pid)
        if kill -0 "$PID" 2>/dev/null; then
            if kill "$PID" 2>/dev/null; then
                sleep 2
                # Force kill if still running
                if kill -0 "$PID" 2>/dev/null; then
                    if kill -9 "$PID" 2>/dev/null; then
                        echo "  ✅ Flask application force stopped (PID: $PID)"
                    else
                        echo "  ⚠️ Could not force stop Flask process (PID: $PID) - permission denied"
                        success=false
                    fi
                else
                    echo "  ✅ Flask application stopped (PID: $PID)"
                fi
            else
                echo "  ⚠️ Could not stop Flask process (PID: $PID) - permission denied"
                success=false
            fi
        else
            echo "  ⚠️ Flask process not running (stale PID: $PID)"
        fi
        rm -f ./conf/app.pid
    else
        echo "  ⚠️ No ./conf/app.pid file found"
    fi
    
    # Force kill any remaining Flask processes with better error handling
    FLASK_PIDS=$(pgrep -f "python3 ControlPlanFlaskApp.py" 2>/dev/null || true)
    if [ -n "$FLASK_PIDS" ]; then
        echo "  🔥 Attempting to stop remaining Flask processes: $FLASK_PIDS"
        # Try regular pkill first
        if pkill -f "python3 ControlPlanFlaskApp.py" 2>/dev/null; then
            sleep 2
            # Check if any processes are still running
            REMAINING_PIDS=$(pgrep -f "python3 ControlPlanFlaskApp.py" 2>/dev/null || true)
            if [ -n "$REMAINING_PIDS" ]; then
                echo "  🔥 Force killing remaining processes: $REMAINING_PIDS"
                # Try force kill with better error handling
                if pkill -9 -f "python3 ControlPlanFlaskApp.py" 2>/dev/null; then
                    echo "  ✅ All Flask processes terminated"
                else
                    echo "  ⚠️ Some Flask processes could not be terminated (permission denied)"
                    echo "  💡 Try running with sudo or kill processes manually: sudo pkill -9 -f 'python3 ControlPlanFlaskApp.py'"
                    success=false
                fi
            else
                echo "  ✅ All Flask processes terminated"
            fi
        else
            echo "  ⚠️ Could not terminate Flask processes (permission denied)"
            echo "  💡 Try running with sudo: sudo pkill -f 'python3 ControlPlanFlaskApp.py'"
            success=false
        fi
    fi
    
    # Return appropriate exit code
    if [ "$success" = "false" ]; then
        return 1
    fi
    return 0
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
    HTTP_PORT=$HTTP_PORT HTTPS_PORT=$((HTTPS_PORT + 363)) HTTPS_PORT2=$((HTTPS_PORT2 + 363)) USER_ID=$USER_ID docker-compose down
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
    HTTP_PORT=$HTTP_PORT HTTPS_PORT=$((HTTPS_PORT + 363)) HTTPS_PORT2=$((HTTPS_PORT2 + 363)) USER_ID=$USER_ID docker-compose logs -f
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
    echo "  🔄 Restarting Flask application..."
    
    # Use the improved stop function
    if ! stop_flask_service; then
        echo "  ⚠️ Some processes could not be stopped, but continuing with restart..."
    fi
    
    echo "  🚀 Starting Flask application..."
    # Create required directories
    mkdir -p logs conf
    
    # Start Flask with date-based log file
    LOG_FILE="logs/app_logs_$(date +%Y%m%d).log"
    
    if FLASK_RUN_PORT=5000 nohup python3 ControlPlanFlaskApp.py > "$LOG_FILE" 2>&1 & then
        NEW_PID=$!
        echo $NEW_PID > ./conf/app.pid
        
        # Wait a moment and check if the process started successfully
        sleep 2
        if kill -0 "$NEW_PID" 2>/dev/null; then
            echo "  ✅ Flask application restarted successfully (PID: $NEW_PID)"
        else
            echo "  ❌ Flask application failed to restart (check logs: $LOG_FILE)"
            rm -f ./conf/app.pid
            return 1
        fi
    else
        echo "  ❌ Failed to restart Flask application"
        return 1
    fi
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
    HTTP_PORT=$HTTP_PORT HTTPS_PORT=$((HTTPS_PORT + 363)) HTTPS_PORT2=$((HTTPS_PORT2 + 363)) USER_ID=$USER_ID docker-compose restart
}

# Start services
start_services() {
    echo "🚀 Starting $NAME_OF_APPLICATION deployment..."
    
    if [ "$LOCAL_MODE" = "locally" ]; then
        start_local_deployment
    elif [ "$LOCAL_MODE" = "docker" ]; then
        start_docker_deployment
    fi
}

start_local_deployment() {
    echo "💻 Starting local deployment..."
    install_python_dependencies
    
    # Setup Gitea (will skip if already configured) - non-blocking
    setup_gitea || echo "  ⚠️ Gitea setup failed - continuing with core services"
    
    # Always start Flask and Nginx regardless of Gitea status
    echo "🚀 Starting core services..."
    start_flask_application
    configure_nginx
    configure_firewall
    
    echo "✅ Local deployment completed successfully!"
}

# Setup Gitea for local development
setup_gitea() {
    echo "🔧 Checking Gitea installation..."
    
    # Check if Gitea is already running
    if systemctl is-active --quiet gitea 2>/dev/null; then
        echo "  ✅ Gitea is already running - skipping setup"
        return 0
    fi
    
    # Check if already configured
    if [ -f "/etc/gitea/app.ini" ]; then
        echo "  ✅ Gitea is already configured - starting service"
        sudo systemctl start gitea 2>/dev/null || true
        if systemctl is-active --quiet gitea; then
            echo "  ✅ Gitea is running on http://localhost:3000"
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

    # Only create admin user if Gitea started successfully
    if systemctl is-active --quiet gitea; then
        create_gitea_admin_user
    fi
    
    # Start Gitea service
    echo "🚀 Starting Gitea service..."
    sudo systemctl daemon-reload
    sudo systemctl enable gitea
    sudo systemctl start gitea
    
    # Wait for Gitea to start with timeout
    echo "  ⏳ Waiting for Gitea to start..."
    for i in {1..20}; do
        if systemctl is-active --quiet gitea; then
            echo "  ✅ Gitea service is active"
            break
        fi
        sleep 1
    done
    
    if systemctl is-active --quiet gitea; then
        echo "  ✅ Gitea is running on http://localhost:3000"
    else
        echo "  ❌ Failed to start Gitea - continuing without it"
        return 1
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

[repository]
ENABLE_PUSH_CREATE_USER = true
ENABLE_PUSH_CREATE_ORG = true
EOF
    
    sudo chown git:git /etc/gitea/app.ini
    sudo chmod 640 /etc/gitea/app.ini
    
    echo "  ✅ Gitea configured successfully"
}

# Setup Gitea admin user and API token
create_gitea_admin_user() {
    echo "👤 Setting up Gitea admin access..."
    
    # Wait for Gitea to be ready with timeout
    echo "  ⏳ Waiting for Gitea to be ready..."
    for i in {1..30}; do
        if curl -s http://localhost:3000 >/dev/null 2>&1; then
            echo "  ✅ Gitea is responding"
            break
        fi
        sleep 1
    done
    
    # Set environment variables for Gitea CLI
    export GITEA_WORK_DIR=/var/lib/gitea
    export USER=git
    export HOME=/home/git
    
    # Create gitadmin user with timeout
    echo "👤 Creating gitadmin user..."
    timeout 10 sudo -u git -E /usr/local/bin/gitea admin user create \
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
    
    # Try to generate API token with timeout
    setup_api_token
}

# Setup API token for admin user
setup_api_token() {
    echo "  🔑 Setting up API token..."
    
    # Try to generate API token with timeout
    timeout 10 sudo -u git -E /usr/local/bin/gitea admin user generate-access-token \
        --username gitadmin \
        --token-name "api-access" \
        --scopes "write:admin,write:user,write:repository" \
        --config /etc/gitea/app.ini \
        --work-path /var/lib/gitea 2>/dev/null | grep -o '[a-f0-9]\{40\}' > /tmp/gitea_token_temp 2>/dev/null || true
    
    if [ -f "/tmp/gitea_token_temp" ] && [ -s "/tmp/gitea_token_temp" ]; then
        TOKEN=$(cat /tmp/gitea_token_temp)
        echo "$TOKEN" > /tmp/gitea_admin_token
        chmod 600 /tmp/gitea_admin_token
        rm -f /tmp/gitea_token_temp
        echo "  ✅ API token created and saved to /tmp/gitea_admin_token"
    else
        rm -f /tmp/gitea_token_temp
        echo "  ⚠️ Could not generate API token automatically (timeout or error)"
        echo "  📝 Manual token creation: Login to http://localhost:3000 > Settings > Applications"
    fi
}

start_docker_deployment() {
    echo "🐳 Starting Docker deployment..."
    cleanup_docker
    HTTP_PORT=$HTTP_PORT HTTPS_PORT=$((HTTPS_PORT + 363)) HTTPS_PORT2=$((HTTPS_PORT2 + 363)) USER_ID=$USER_ID docker-compose up -d --build
    echo "  ✅ Docker services started"
}

install_python_dependencies() {
    if [ -f "requirements.txt" ]; then
        echo "  📦 Installing Python dependencies..."
        pip3 install -r requirements.txt --break-system-packages
    fi
}

start_flask_application() {
    echo "  🚀 Starting Flask application..."
    
    # Stop any existing Flask processes with better error handling
    EXISTING_PIDS=$(pgrep -f "python3 ControlPlanFlaskApp.py" 2>/dev/null || true)
    if [ -n "$EXISTING_PIDS" ]; then
        echo "  ⚠️ Found existing Flask processes: $EXISTING_PIDS"
        echo "  🛑 Attempting to stop existing processes..."
        
        # Try graceful shutdown first
        if pkill -f "python3 ControlPlanFlaskApp.py" 2>/dev/null; then
            echo "  ✅ Sent termination signal to existing processes"
            sleep 3
            
            # Check if any processes are still running
            REMAINING_PIDS=$(pgrep -f "python3 ControlPlanFlaskApp.py" 2>/dev/null || true)
            if [ -n "$REMAINING_PIDS" ]; then
                echo "  ⚠️ Some processes still running: $REMAINING_PIDS"
                echo "  💀 Attempting force kill..."
                
                # Try force kill, but don't fail if it doesn't work
                if pkill -9 -f "python3 ControlPlanFlaskApp.py" 2>/dev/null; then
                    echo "  ✅ Force killed remaining processes"
                else
                    echo "  ⚠️ Could not force kill some processes (permission denied)"
                    echo "  💡 Continuing with startup - new process will use different port if needed"
                fi
            fi
        else
            echo "  ⚠️ Could not send termination signal (permission denied)"
            echo "  💡 Continuing with startup - will try to start on available port"
        fi
    fi
    
    # Create required directories
    mkdir -p logs conf
    
    # Start Flask on port 5000 with date-based log file
    LOG_FILE="logs/app_logs_$(date +%Y%m%d).log"
    echo "  🚀 Starting new Flask instance..."
    
    # Try to start Flask, handle port conflicts gracefully
    if FLASK_RUN_PORT=5000 nohup python3 ControlPlanFlaskApp.py > "$LOG_FILE" 2>&1 & then
        NEW_PID=$!
        echo $NEW_PID > ./conf/app.pid
        
        # Wait a moment and check if the process started successfully
        sleep 2
        if kill -0 "$NEW_PID" 2>/dev/null; then
            echo "  ✅ Flask application started successfully (PID: $NEW_PID)"
        else
            echo "  ❌ Flask application failed to start (check logs: $LOG_FILE)"
            rm -f ./conf/app.pid
            return 1
        fi
    else
        echo "  ❌ Failed to start Flask application"
        return 1
    fi
}

configure_nginx() {
    echo "🌐 Configuring Nginx..."
    # Setup ModSecurity configuration if not already done
    setup_modsecurity_config
    # Check and enable ModSecurity module
    check_and_enable_modsecurity
    create_nginx_config
    enable_nginx_site
    test_and_reload_nginx
}

setup_modsecurity_config() {
    source ./setup_modsecurity_config.sh
}

check_and_enable_modsecurity() {
    # Check if ModSecurity module exists
    if [ -f "/usr/lib/nginx/modules/ngx_http_modsecurity_module.so" ] || [ -f "/etc/nginx/modules/ngx_http_modsecurity_module.so" ]; then
        enable_modsecurity_module
        MODSECURITY_AVAILABLE=true
    else
        echo "  ⚠️ ModSecurity module not found, using basic reverse proxy configuration"
        MODSECURITY_AVAILABLE=false
    fi
}

enable_modsecurity_module() {
    # Add load_module directive to main nginx.conf if not already present
    if ! grep -q "load_module modules/ngx_http_modsecurity_module.so" /etc/nginx/nginx.conf; then
        sudo sed -i '1i load_module modules/ngx_http_modsecurity_module.so;' /etc/nginx/nginx.conf
        echo "  ✅ ModSecurity module enabled in nginx.conf"
    fi
}

create_nginx_config() {
    # Create base configuration
    cat > /tmp/ai-swautomorph-site << EOF
server {
    listen 80;
    server_name localhost www.swautomorph.com;
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl;
    server_name localhost www.swautomorph.com;
    
    ssl_certificate ${SSL_CERT_PATH:-/home/ubuntu/ai-swautomorph/ssl/STAR_swautomorph_com.crt};
    ssl_certificate_key ${SSL_KEY_PATH:-/home/ubuntu/ai-swautomorph/ssl/privateKey_STAR_swautomorph_com.key};
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
EOF

    # Add ModSecurity configuration only if available
    if [ "${MODSECURITY_AVAILABLE:-false}" = "true" ]; then
        cat >> /tmp/ai-swautomorph-site << EOF
    
    # WAF Protection
    modsecurity on;
    modsecurity_rules_file ${MODSECURITY_CONF_DIR:-/etc/nginx/modsec}/main.conf;
EOF
        echo "  ✅ ModSecurity WAF protection enabled"
    else
        echo "  ⚠️ Using basic reverse proxy without WAF protection"
    fi

    # Add location blocks
    cat >> /tmp/ai-swautomorph-site << EOF
    
    location / {
        proxy_pass http://127.0.0.1:${FLASK_PORT:-5000};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    location /gitea/ {
        proxy_pass http://127.0.0.1:${GITEA_PORT:-3000}/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
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
        echo "  ✅ Nginx is running - reloading configuration"
        sudo nginx -t && sudo systemctl reload nginx
    else
        echo "  🚀 Starting Nginx service"
        sudo systemctl start nginx
        sudo nginx -t
    fi
    echo "  ✅ Nginx configured successfully"
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
    HTTP_PORT=$HTTP_PORT HTTPS_PORT=$((HTTPS_PORT + 363)) HTTPS_PORT2=$((HTTPS_PORT2 + 363)) USER_ID=$USER_ID docker-compose down --remove-orphans
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
        echo "📦 Installing Nginx with ModSecurity..."
        install_nginx_with_modsecurity
        echo "✅ Nginx with ModSecurity installed successfully"
    fi
}

install_nginx_with_modsecurity() {
    sudo apt update
    
    # Install nginx and ModSecurity components
    sudo apt install -y nginx wget git
    
    # Try to install nginx-module-security (may not be available on all systems)
    sudo apt install -y libmodsecurity3 2>/dev/null || {
        echo "  ⚠️ libmodsecurity3 not available, installing alternative packages"
        sudo apt install -y libmodsecurity-dev modsecurity-crs 2>/dev/null || true
    }
    
    # Create ModSecurity directories
    sudo mkdir -p ${MODSECURITY_CONF_DIR:-/etc/nginx/modsec}
    
    # Download OWASP CRS rules if not available via package
    if [ ! -d "${MODSECURITY_RULES_DIR:-/usr/share/modsecurity-crs}" ]; then
        sudo git clone https://github.com/coreruleset/coreruleset.git ${MODSECURITY_RULES_DIR:-/usr/share/modsecurity-crs}
        cd ${MODSECURITY_RULES_DIR:-/usr/share/modsecurity-crs}
        sudo git checkout ${OWASP_CRS_VERSION:-v3.3.5}
    fi
    
    # Configure ModSecurity
    setup_modsecurity_config
    
    # Check if ModSecurity module is available before enabling
    check_and_enable_modsecurity
    
    sudo systemctl enable nginx
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
    mkdir -p data ssl logs softfluid/db
    chmod 755 data ssl logs softfluid/db
}

setup_ssl_certificates() {
    if [ ! -f ssl/cert.pem ] || [ ! -f ssl/key.pem ]; then
        echo "🔐 Generating SSL certificates..."
        ./scripts/generate_ssl.sh
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

# Show usage information
help() {
    echo "🚀 AI-SwAutoMorph Deployment Script"
    echo "Usage: $0 [COMMAND] [MODE] [USER_ID] [USER_NAME] [USER_EMAIL] [DESCRIPTION]"
    echo ""
    echo "COMMANDS:"
    echo "  start     - Deploy and start all services (Flask app, Nginx, Gitea)"
    echo "              • Sets up SSL certificates and environment"
    echo "              • Installs dependencies and configures services"
    echo "              • Opens firewall ports (80, 443, 3000)"
    echo "              • Creates deployment directories and logs"
    echo "              • Sets up hourly database backup cron job"
    echo ""
    echo "  stop      - Stop all running services and clean up"
    echo "  -o        - Stop all running services and clean up (alias for stop)"
    echo "  --stop    - Stop all running services and clean up (alias for stop)"
    echo "              • Removes hourly database backup cron job"
    echo "              • Creates final database backup in ./softfluid/db/backup/\$DATETIME/"
    echo "              • Stops Flask application and removes PID file"
    echo "              • Removes Nginx site configuration"
    echo "              • Optionally stops and removes Gitea (interactive)"
    echo "              • Stops Docker containers if running"
    echo ""
    echo "  restart   - Restart all services without full redeployment"
    echo "  -r        - Restart all services without full redeployment (alias for restart)"
    echo "  --restart - Restart all services without full redeployment (alias for restart)"
    echo "              • Restarts Flask application with new PID"
    echo "              • Reloads Nginx configuration"
    echo "              • Restarts Docker containers if in Docker mode"
    echo ""
    echo "  ps        - Show status of all services"
    echo "  -p        - Show status of all services (alias for ps)"
    echo "  --ps      - Show status of all services (alias for ps)"
    echo "              • Flask application status and PID"
    echo "              • Nginx service status and site configuration"
    echo "              • Gitea service status"
    echo "              • Docker Compose container status"
    echo ""
    echo "  logs      - Display logs from all services"
    echo "  -l        - Display logs from all services (alias for logs)"
    echo "  --logs    - Display logs from all services (alias for logs)"
    echo "              • Flask application logs (current day)"
    echo "              • Nginx error logs (last 20 lines)"
    echo "              • Docker Compose logs (if running)"
    echo ""
    echo "  --recover_db - Recover database from backup"
    echo "              • Lists available backup dates for selection"
    echo "              • Restores softfluid/db/ai_swautomorph.db from selected backup"
    echo "              • Backs up current database before recovery"
    echo ""
    echo "  backup_db    - Create database backup manually"
    echo "  --backup_database - Create database backup manually (alias for backup_db)"
    echo "              • Creates timestamped backup in ./softfluid/db/backup/"
    echo "              • Dumps all database tables individually"
    echo "              • Creates complete database dump"
    echo "              • Syncs backup to S3 using OVH-SWAUTOMORPH profile"
    echo ""
    echo "  help      - Show this help menu"
    echo "  --help    - Show this help menu (alias for help)"
    echo "  -h        - Show this help menu (short alias for help)"
    echo ""
    echo "MODES:"
    echo "  locally   - Deploy without Docker (direct system installation)"
    echo "              • Installs services directly on the host system"
    echo "              • Uses system Python, Nginx, and Gitea"
    echo "              • Suitable for production deployments"
    echo ""
    echo "  docker    - Deploy using Docker containers"
    echo "              • Uses docker-compose.yml configuration"
    echo "              • Isolated container environment"
    echo "              • Suitable for development and testing"
    echo ""
    echo "  [empty]   - Interactive mode (shows deployment menu)"
    echo "              • Prompts user to select deployment mode"
    echo "              • Uses simple-term-menu for better UX"
    echo ""
    echo "PARAMETERS:"
    echo "  USER_ID      - Alphanumeric user identifier (default: 0)"
    echo "                 Used for port calculation and user isolation"
    echo ""
    echo "  USER_NAME    - Display name for the user (default: 'admin')"
    echo "                 Used in configuration and logging"
    echo ""
    echo "  USER_EMAIL   - User email address (default: 'admin@swautomorph.com')"
    echo "                 Used for SSL certificates and notifications"
    echo ""
    echo "  DESCRIPTION  - Deployment description (default: 'Basic Information Display')"
    echo "                 Used for documentation and logging purposes"
    echo ""
    echo "EXAMPLES:"
    echo "  $0 start                    # Interactive mode - shows deployment menu"
    echo "  $0 start locally            # Deploy locally without Docker"
    echo "  $0 start docker             # Deploy using Docker containers"
    echo "  $0 start locally 123 john   # Deploy locally for user 'john' with ID '123'"
    echo "  $0 stop                     # Stop all services (interactive Gitea removal)"
    echo "  $0 stop locally             # Stop all services started "locally" (interactive Gitea removal)"
    echo "  $0 restart locally          # Restart local services"
    echo "  $0 ps                       # Check status of all services"
    echo "  $0 logs                     # View logs from all services"
    echo "  $0 help                     # Show this help menu"
    echo "  $0 --help                   # Show this help menu"
    echo "  $0 -h                       # Show this help menu"
    echo ""
    echo "PORTS:"
    echo "  HTTP:  Calculated as 80 + (USER_ID * 100)"
    echo "  HTTPS: HTTP + 1"
    echo "  Gitea: 3000 (fixed)"
    echo "  Flask: 5000 (fixed for local mode)"
    echo ""
    echo "SERVICES:"
    echo "  • Flask Web Application (Python)"
    echo "  • Nginx Reverse Proxy (HTTPS/SSL)"
    echo "  • Gitea Git Repository Server"
    echo "  • Docker Containers (optional)"
    echo ""
    echo "ACCESS URLS:"
    echo "  • Main App: https://www.swautomorph.com"
    echo "  • Gitea:    https://www.swautomorph.com/gitea"
    echo "  • Local:    https://localhost (with SSL certificates)"
}

# Setup crontab for automatic backups
setup_backup_cron() {
    echo "⏰ Setting up hourly database backup cron job..."
    SCRIPT_PATH=$(realpath "$0")
    CRON_JOB="0 * * * * $SCRIPT_PATH --backup_db >/dev/null 2>&1"
    
    # Remove existing backup job if any
    (crontab -l 2>/dev/null | grep -v "$SCRIPT_PATH --backup_db") | crontab -
    
    # Add new backup job
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    
    echo "  ✅ Hourly backup cron job added"
}

# Remove backup cron job
remove_backup_cron() {
    echo "⏰ Removing database backup cron job..."
    SCRIPT_PATH=$(realpath "$0")
    
    # Remove backup job
    (crontab -l 2>/dev/null | grep -v "$SCRIPT_PATH --backup_db") | crontab -
    
    echo "  ✅ Backup cron job removed"
}

# Start env
start() {
    validate_user_id
    check_requirements
    setup_environment
    start_services
    setup_backup_cron
    echo "🎉 Deployment completed successfully!"
}

# Main function - orchestrates the deployment process
main() {
    calculate_ports
    show_environment 

    # Show interactive menu for start, stop, restart commands if no LOCAL_MODE specified
    if [[ "$COMMAND" =~ ^(start|-s|--start|stop|-o|--stop|restart|-r|--restart)$ ]] && [ "$LOCAL_MODE" = "0" ]; then
        SELECTED_MODE=$(show_deployment_menu)
        if [ "$SELECTED_MODE" = "locally" ]; then
            LOCAL_MODE="locally"
        elif [ "$SELECTED_MODE" = "docker" ]; then
            LOCAL_MODE="docker"
        fi
    fi

    case $COMMAND in
        "ps"|"-p"|"--ps")
            check_status
            exit 0
            ;;
        "stop"|"-k"|"--stop")
            stop_services
            exit 0
            ;;
        "logs"|"-l"|"--logs")
            show_logs
            exit 0
            ;;
        "recover_db"|"--recover_db")
            recover_database
            exit 0
            ;;
        "backup_db"|"--backup_db")
            backup_database
            exit 0
            ;;
        "restart"|"-r"|"--restart")
            restart_services
            exit 0
            ;;
        "start"|"-s"|"--start")
            start
            exit 0
            ;;
        "help"|"--help"|"-h")
            help
            exit 0
            ;;
        *)
            echo "❌ Unknown command: $COMMAND"
            echo ""
            help
            exit 1
            ;;
    esac
}

# Execute main function
main "$@"