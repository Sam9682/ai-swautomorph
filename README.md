# AI-SwAutoMorph

## Objective

AI-SwAutoMorph is a centralized application deployment and management platform designed for GenAI agents. It provides automated deployment, lifecycle management, and SSO authentication for web applications through multiple interfaces (Web, CLI, API, MCP).

**Core Purpose**: Enable GenAI agents to autonomously deploy, manage, and access web applications without human intervention.

## Features

- 🔐 User registration and authentication with Gitea integration
- 🌐 Web-based dashboard with multi-language support (EN/FR)
- 📱 Application management with SQLite database storage
- 🔑 SSO Identity Provider with token-based authentication
- 🚀 **Application deployment system** (Clone, Start, Stop, Monitor, Logs)
- 🐳 Docker containerization with docker-compose
- 🖥️ Command-line interface (CLI) with comprehensive commands
- 🔌 REST API endpoints with streaming support
- 🤖 MCP (Model Context Protocol) support
- 🛡️ ModSecurity WAF protection with OWASP CRS rules
- 🔄 Automated database backups with S3 sync
- 💰 Billing and cost tracking system
- 🤖 Q Chat Developer and DevOps AI assistants
- 📊 Database health monitoring and statistics
- 🌐 Multi-server deployment support
- 📖 Comprehensive user guide and documentation

## Installation Methods

### Prerequisites Check
```bash
# Verify system requirements
which python3 && which pip && which docker && which docker-compose
```

### Interactive Deployment (Recommended)
```bash
# Clone repository
git clone https://github.com/your-repo/ai-swautomorph.git
cd ai-swautomorph

# Interactive deployment with menu selection
./deployControlPlan.sh start
```

### Local System Deployment
```bash
# Deploy directly on host system (production)
./deployControlPlan.sh start locally

# With custom user parameters
./deployControlPlan.sh start locally 123 "John Doe" "john@example.com" "Production Deployment"
```

### Docker Deployment
```bash
# Deploy using Docker containers (development/testing)
./deployControlPlan.sh start docker

# Or direct docker-compose
docker-compose up -d --build
```

### Manual Installation Steps
```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Initialize database
python3 ./scripts/cli.py init-db

# 3. Start application
python3 src/app.py
```

## Configuration

### Environment Variables
```bash
# Automatically generated during deployment
SECRET_KEY="auto-generated-32-byte-hex"
FLASK_ENV="production"
```

### Configuration File
```bash
# Edit deployment configuration
vim ./conf/deploy.ini

# Key settings:
DOMAIN="www.swautomorph.com"
EMAIL="admin@swautomorph.com"
GITEA_VERSION="1.21.3"
MODSECURITY_CONF_DIR="/etc/nginx/modsec"
```

### Database Initialization
```bash
# Initialize database schema
python3 ./scripts/cli.py init-db

# Check database health
python3 ./scripts/cli.py db-health
```

### SSL Certificate Setup
```bash
# Auto-generate self-signed certificate
./scripts/generate_ssl.sh

# Or use production certificates (place in ssl/ directory)
# - STAR_swautomorph_com.crt
# - privateKey_STAR_swautomorph_com.key
```

## API Access for GenAI Agents

### User Registration
```bash
curl -X POST https://www.swautomorph.com/register \
  -H "Content-Type: application/json" \
  -d '{"username":"agent","email":"agent@example.com","password":"secure_pass","first_name":"AI","last_name":"Agent"}'
```

### Application Management
```bash
# List applications
curl https://www.swautomorph.com/api/applications

# Add application (admin required)
curl -X POST https://www.swautomorph.com/api/applications \
  -H "Content-Type: application/json" \
  -H "Cookie: session=your-session-cookie" \
  -d '{"name":"MyApp","description":"My Application","git_url":"https://github.com/user/myapp.git"}'

# Deploy application with streaming
curl -X POST https://www.swautomorph.com/api/deployments \
  -H "Content-Type: application/json" \
  -H "Cookie: session=your-session-cookie" \
  -d '{"application_name":"MyApp","action":"clone","git_url":"https://github.com/user/myapp.git","server_id":1,"stream":true}'

# Application lifecycle management
curl -X POST https://www.swautomorph.com/api/deployments \
  -H "Content-Type: application/json" \
  -H "Cookie: session=your-session-cookie" \
  -d '{"application_name":"MyApp","action":"start"}'
```

### Server Management
```bash
# List servers
curl https://www.swautomorph.com/api/servers

# Allocate server for deployment
curl -X POST https://www.swautomorph.com/api/server/allocate \
  -H "Content-Type: application/json" \
  -H "Cookie: session=your-session-cookie" \
  -d '{"application_name":"MyApp"}'
```

### AI Assistant Integration
```bash
# Q Chat Developer (code modifications)
curl -X POST https://www.swautomorph.com/api/qchat_developer \
  -H "Content-Type: application/json" \
  -H "Cookie: session=your-session-cookie" \
  -d '{"message":"Add a new API endpoint for user management","application_name":"MyApp","application_folder":"/path/to/app"}'

# Q Chat DevOps (deployment operations)
curl -X POST https://www.swautomorph.com/api/qchat_devops \
  -H "Content-Type: application/json" \
  -H "Cookie: session=your-session-cookie" \
  -d '{"message":"[START] Start the application","application_name":"MyApp","application_folder":"/path/to/app"}'
```

### CLI Interface
```bash
# Register user
python3 ./scripts/cli.py register --username agent --email agent@example.com --password secure_pass

# List applications
python3 ./scripts/cli.py list-apps

# Add application
python3 ./scripts/cli.py add-app --name MyApp --url https://myapp.com --description "My Application"

# Validate SSO token
python3 ./scripts/cli.py validate-token --token your-sso-token

# Database health check
python3 ./scripts/cli.py db-health

# Mount S3 storage
python3 ./scripts/cli.py mount-s3fs softfluid /mnt/s3
```

### MCP Protocol
```bash
# Start MCP server for agent communication
python3 ./scripts/mcp_server.py
```

## Service Management

### Service Status
```bash
# Check all services status
./deployControlPlan.sh ps

# View service logs
./deployControlPlan.sh logs

# Restart services
./deployControlPlan.sh restart

# Stop services
./deployControlPlan.sh stop
```

### Health Checks
```bash
# API health check
curl https://www.swautomorph.com/api/auth/status

# Database health check (admin required)
curl https://www.swautomorph.com/api/health/database

# Check Docker services
docker-compose ps
```

### Database Management
```bash
# Create manual backup
./deployControlPlan.sh backup_db

# Recover from backup
./deployControlPlan.sh --recover_db

# Database health check
python3 ./scripts/cli.py db-health
```

## Default Configuration

- **Web Interface**: https://www.swautomorph.com (or https://localhost)
- **API Endpoint**: https://www.swautomorph.com/api
- **Gitea Server**: https://www.swautomorph.com/gitea (port 3000)
- **MCP Server**: Available via scripts/mcp_server.py
- **Database**: SQLite (softfluid/db/ai_swautomorph.db)
- **Deployment Directory**: /home/ubuntu/deployments/[username]/[appname]
- **SSL Certificates**: ssl/ directory
- **Logs**: logs/ directory with daily rotation
- **Backups**: softfluid/db/backup/ with S3 sync

## Architecture

### Directory Structure
```
ai-swautomorph/
├── src/                    # Main application source
│   ├── routes/            # Flask route blueprints
│   ├── app.py            # Main Flask application
│   ├── database.py       # Database management
│   └── config.py         # Configuration settings
├── scripts/               # CLI tools and utilities
├── templates/            # HTML templates
├── static/               # CSS, JS, and static files
├── ssl/                  # SSL certificates
├── logs/                 # Application logs
├── softfluid/db/         # Database and backups
├── conf/                 # Configuration files
└── deployControlPlan.sh  # Main deployment script
```

### Key Components

- **Flask Application**: Multi-blueprint architecture with modular routes
- **Database**: SQLite with WAL mode for better concurrency
- **Authentication**: Session-based with SSO token support
- **Deployment**: Multi-server support with capacity management
- **Security**: ModSecurity WAF with OWASP CRS rules
- **Monitoring**: Health checks and database statistics
- **AI Integration**: Q Chat for development and DevOps tasks

## Troubleshooting

### Common Issues
```bash
# Check service status
./deployControlPlan.sh ps

# View detailed logs
./deployControlPlan.sh logs

# Port conflicts
sudo netstat -tulpn | grep -E ':(80|443|3000|5000)'

# Permission issues
sudo chown -R ubuntu:ubuntu /home/ubuntu/deployments/
sudo chown -R ubuntu:ubuntu /home/ubuntu/ai-swautomorph/

# Database issues
python3 ./scripts/cli.py db-health
./deployControlPlan.sh --recover_db

# SSL certificate issues
./scripts/generate_ssl.sh
./scripts/fix_ssl_chain.sh
```

### Reset Installation
```bash
# Stop all services
./deployControlPlan.sh stop

# Complete reset (Docker)
docker-compose down -v
docker system prune -f

# Complete reset (Local)
sudo systemctl stop nginx gitea
sudo rm -rf /etc/nginx/sites-enabled/ai-swautomorph
rm -rf softfluid/db/ai_swautomorph.db

# Restart deployment
./deployControlPlan.sh start
```

### Debug Mode
```bash
# Enable debug logging
export FLASK_DEBUG=1
export FLASK_ENV=development

# Run with verbose output
./deployControlPlan.sh start locally 2>&1 | tee deployment.log
```