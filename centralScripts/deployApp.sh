#!/bin/bash
# ${NAME_OF_APPLICATION} Production Deployment Script

set -e

# Load configuration
source ./conf/deploy.ini

# Global Parameters
COMMAND=${1:-help}
USER_ID=${2:-0}
USER_NAME=${3:-"user"}
USER_EMAIL=${4:-"user@swautomorph.com"}
DESCRIPTION=${5:-"Basic Information Display"}

# Configuration
DOMAIN=${DOMAIN:-"www.swautomorph.com"}
EMAIL=${EMAIL:-"user@swautomorph.com"}
ENV_FILE=".env.prod"

# Calculate ports (convert alphanumeric USER_ID to numeric for port calculation)
calculate_ports() {
    PORT_RANGE_BEGIN=$((APPLICATION_IDENTITY_NUMBER * 100 + RANGE_START))
    PORT=$((PORT_RANGE_BEGIN + USER_ID * RANGE_RESERVED))
    HTTPS_PORT=$((PORT + 1))
}

# Display environment variables for operations
show_environment() {
    local operation=$1
    echo "🔍 Starting $operation operation..."
    echo "Environment Variables:"
    echo "  USER_ID=${USER_ID}"
    echo "  USER_NAME=${USER_NAME}"
    echo "  USER_EMAIL=${USER_EMAIL}"
    echo "  PORT=${PORT}"
    echo "  HTTPS_PORT=${HTTPS_PORT}"
    echo ""
}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   log_error "This script should not be run as root"
   exit 1
fi

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    log_info "Prerequisites check passed ✅"
}

# Generate secure passwords
generate_secrets() {
    log_info "Generating secure secrets..."
    
    if [[ ! -f "$ENV_FILE" ]]; then
        log_info "Creating production environment file..."
        
        # Generate secure passwords
        DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
        JWT_SECRET=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
        
        cat > "$ENV_FILE" << EOF
# Database Configuration (SQLite)
DATABASE_URL=sqlite:///./data/ai_haccp.db

# Security
JWT_SECRET=$JWT_SECRET

# Domain Configuration
DOMAIN=$DOMAIN
API_URL=https://$DOMAIN
SSL_EMAIL=$EMAIL

# Frontend
REACT_APP_API_URL=https://$DOMAIN
EOF
        
        chmod 600 "$ENV_FILE"
        log_info "Environment file created with secure passwords ✅"
    else
        log_warn "Environment file already exists, skipping generation"
    fi
}

# Setup SSL certificates
setup_ssl() {
    log_info "Setting up SSL certificates..."
    
    if [[ ! -d "ssl" ]]; then
        mkdir -p ssl
        
        # Check if certbot is installed
        if command -v certbot &> /dev/null; then
            log_info "Obtaining SSL certificate for $DOMAIN..."
            
            # Stop nginx if running
            sudo systemctl stop nginx 2>/dev/null || true
            
            # Get certificate
            sudo certbot certonly --standalone \
                -d "$DOMAIN" \
                --email "$EMAIL" \
                --agree-tos \
                --non-interactive \
                --quiet
            
            # Copy certificates
            sudo cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ssl/
            sudo cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem" ssl/
            sudo chown -R $USER:$USER ssl/
            
            log_info "SSL certificates obtained ✅"
        else
            log_warn "Certbot not found. Creating self-signed certificates for testing..."
            
            # Create self-signed certificate for testing
            openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
                -keyout ssl/privkey.pem \
                -out ssl/fullchain.pem \
                -subj "/C=US/ST=State/L=City/O=Organization/CN=$DOMAIN"
            
            log_warn "Self-signed certificate created. Replace with real certificate for production!"
        fi
    else
        log_info "SSL directory already exists, skipping certificate generation"
    fi
}

# Build and deploy
deploy_services() {
    log_info "Building and deploying services..."

    # Stop existing services
    PORT=$((PORT_RANGE_BEGIN + USER_ID * RANGE_RESERVED)) HTTPS_PORT=$((PORT_RANGE_BEGIN + USER_ID * RANGE_RESERVED + 1)) USER_ID=$USER_ID docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
    
    # Build images
    log_info "Building Docker images..."
    PORT=$((PORT_RANGE_BEGIN + USER_ID * RANGE_RESERVED)) HTTPS_PORT=$((PORT_RANGE_BEGIN + USER_ID * RANGE_RESERVED + 1)) USER_ID=$USER_ID docker-compose -f docker-compose.prod.yml build --no-cache --build-arg PIP_UPGRADE=1
    
    # Start services
    log_info "Starting production services..."
    PORT=$((PORT_RANGE_BEGIN + USER_ID * RANGE_RESERVED)) HTTPS_PORT=$((PORT_RANGE_BEGIN + USER_ID * RANGE_RESERVED + 1)) USER_ID=$USER_ID docker-compose -f docker-compose.prod.yml --env-file "$ENV_FILE" up -d
    
    # Wait for services to be ready
    log_info "Waiting for services to start..."
    sleep 30
    
    # Check service health
    if docker-compose -f docker-compose.prod.yml ps | grep -q "Up"; then
        log_info "Services deployed successfully ✅"
    else
        log_error "Some services failed to start"
        docker-compose -f docker-compose.prod.yml logs
        exit 1
    fi
}

# Verify deployment
verify_deployment() {
    log_info "Verifying deployment..."
    
    # Check if services are running
    if ! docker-compose -f docker-compose.prod.yml ps | grep -q "Up"; then
        log_error "Services are not running properly"
        return 1
    fi
    
    # Test API health endpoint
    sleep 10
    if curl -f -s "http://www.swautomorph.com:${PORT}/health" > /dev/null; then
        log_info "API health check passed ✅"
    else
        log_warn "API health check failed, but services are running"
    fi
    
    log_info "Deployment verification completed"
}

# Setup firewall
setup_firewall() {
    log_info "Configuring firewall..."
    
    if command -v ufw &> /dev/null; then
        # Configure UFW if available
        sudo ufw --force reset
        sudo ufw default deny incoming
        sudo ufw default allow outgoing
        sudo ufw allow ssh
        sudo ufw allow ${PORT}/tcp
        sudo ufw allow ${HTTPS_PORT}/tcp
        sudo ufw --force enable
        
        log_info "Firewall configured ✅"
    else
        log_warn "UFW not found, skipping firewall configuration"
    fi
}

# Create backup script
create_backup_script() {
    log_info "Creating backup script..."
    
    cat > ./scripts/backup.sh << 'EOF'
#!/bin/bash
# ${NAME_OF_APPLICATION} Backup Script

BACKUP_DIR="backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/ai_haccp_backup_$DATE"

mkdir -p "$BACKUP_DIR"

echo "Creating backup: $BACKUP_FILE"
PORT=$((PORT_RANGE_BEGIN + USER_ID * RANGE_RESERVED)) HTTPS_PORT=$((PORT_RANGE_BEGIN + USER_ID * RANGE_RESERVED + 1)) USER_ID=$USER_ID docker-compose -f docker-compose.prod.yml exec -T api cp /app/data/ai_haccp.db /tmp/backup.db
docker cp $(docker-compose -f docker-compose.prod.yml ps -q api):/tmp/backup.db "$BACKUP_FILE.db"

if [[ $? -eq 0 ]]; then
    echo "Backup created successfully: $BACKUP_FILE"
    
    # Keep only last 7 backups
    ls -t "$BACKUP_DIR"/ai_haccp_backup_*.db | tail -n +8 | xargs -r rm
    echo "Old backups cleaned up"
else
    echo "Backup failed!"
    exit 1
fi
EOF
    
    chmod +x ./scripts/backup.sh
    log_info "Backup script created ✅"
}

# Main deployment process
start() {
    log_info "Starting ${NAME_OF_APPLICATION} production deployment..."
    
    check_prerequisites
    generate_secrets
    setup_ssl
    deploy_services
    verify_deployment
    setup_firewall
    create_backup_script
    
    echo ""
    echo "🎉 Deployment completed successfully!"
    echo "=================================="
    echo "🌐 Web Interface: https://$DOMAIN"
    echo "📚 API Documentation: https://$DOMAIN/docs"
    echo "🔑 Demo Login: admin@ai-automorph.com / password"
    echo ""
    echo "📋 Next Steps:"
    echo "1. Test the application at https://$DOMAIN"
    echo "2. Change default demo password"
    echo "3. Configure DNS to point to this server"
    echo "4. Set up automated backups: ./scripts/backup.sh"
    echo "5. Monitor logs: docker-compose -f docker-compose.prod.yml logs -f"
    echo ""
    echo "🔧 Management Commands:"
    echo "- View logs: make logs"
    echo "- Backup database: ./scripts/backup.sh"
    echo "- Stop services: make stop"
    echo "- Update application: git pull && make prod"
}

# Stop services
stop_services() {
    log_info "Stopping ${NAME_OF_APPLICATION} services..."
    PORT=$((PORT_RANGE_BEGIN + USER_ID * RANGE_RESERVED)) HTTPS_PORT=$((PORT_RANGE_BEGIN + USER_ID * RANGE_RESERVED + 1)) USER_ID=$USER_ID docker-compose -f docker-compose.prod.yml down
    log_info "Services stopped successfully ✅"
}

# Restart services
restart_services() {
    log_info "Restarting ${NAME_OF_APPLICATION} services..."
    PORT=$((PORT_RANGE_BEGIN + USER_ID * RANGE_RESERVED)) HTTPS_PORT=$((PORT_RANGE_BEGIN + USER_ID * RANGE_RESERVED + 1)) USER_ID=$USER_ID docker-compose -f docker-compose.prod.yml restart
    log_info "Services restarted successfully ✅"
}

# Show logs
show_logs() {
    log_info "Showing ${NAME_OF_APPLICATION} service logs..."
    PORT=$((PORT_RANGE_BEGIN + USER_ID * RANGE_RESERVED)) HTTPS_PORT=$((PORT_RANGE_BEGIN + USER_ID * RANGE_RESERVED + 1)) USER_ID=$USER_ID docker-compose -f docker-compose.prod.yml logs -f
}

# Check service status
check_status() {
    # Get parameters
    params=$(jq -n --arg user_id "$USER_ID" \
                  --arg user_name "$USER_NAME" \
                  --arg user_email "$USER_EMAIL" \
                  --arg port "$PORT" \
                  --arg https_port "$HTTPS_PORT" \
                  '{
                    "USER_ID": $user_id,
                    "USER_NAME": $user_name,
                    "USER_EMAIL": $user_email,
                    "PORT": $port,
                    "HTTPS_PORT": $https_port
                  }')
    
    # Check docker-compose status
    docker_status="IS_NOT_RUNNING"
    if PORT=$((PORT_RANGE_BEGIN + USER_ID * RANGE_RESERVED)) HTTPS_PORT=$((PORT_RANGE_BEGIN + USER_ID * RANGE_RESERVED + 1)) USER_ID=$USER_ID docker-compose -f docker-compose.prod.yml ps | grep -q "Up"; then
        docker_status="IS_RUNNING"
    fi
    
    # Get git remote URLs
    git_remotes=$(git remote -v 2>/dev/null | awk '{print $2}' | sort -u | jq -R . | jq -s .)
    
    # Output JSON
    jq -n --argjson params "$params" \
          --arg docker_status "$docker_status" \
          --argjson git_remotes "$git_remotes" \
          '{
            "environment_vars": $params,
            "docker_compose_ps": $docker_status,
            "git_remote": $git_remotes
          }'
}

# Main function - orchestrates the deployment process
main() {
    calculate_ports

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
            echo "🚀 ${NAME_OF_APPLICATION} Production Deployment"
            echo "=================================="

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