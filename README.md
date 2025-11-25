# AI-SwAutoMorph

## Objective

AI-SwAutoMorph is a centralized application deployment and management platform designed for GenAI agents. It provides automated deployment, lifecycle management, and SSO authentication for web applications through multiple interfaces (Web, CLI, API, MCP).

**Core Purpose**: Enable GenAI agents to autonomously deploy, manage, and access web applications without human intervention.

## Features

- 🔐 User registration and authentication
- 🌐 Web-based dashboard
- 📱 Application management with database storage
- 🔑 SSO Identity Provider with token-based authentication
- 🚀 **Application deployment system** (Clone, Start, Stop, Monitor)
- 🐳 Docker containerization
- 🖥️ Command-line interface (CLI)
- 🔌 REST API endpoints
- 🤖 MCP (Model Context Protocol) support
- 📖 Comprehensive user guide

## Automated Installation

### Prerequisites Check
```bash
# Verify system requirements
which python3 && which pip && which docker && which docker-compose
```

### One-Command Installation
```bash
# Clone and deploy (fully automated)
git clone https://github.com/your-repo/ai-swautomorph.git
cd ai-swautomorph
./deploy.sh
```

### Manual Installation Steps
```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Initialize database
python3 ./scripts/cli.py init-db

# 3. Start application
python3 app.py
```

### Docker Installation
```bash
# Single command deployment
docker-compose up -d
```

## Configuration

### Environment Variables
```bash
# Required for production
export SECRET_KEY="your-secret-key-here"
export FLASK_ENV="production"
```

### Database Initialization
```bash
# Initialize database schema
python3 ./scripts/cli.py init-db
```

### SSL Certificate Setup
```bash
# Auto-generate self-signed certificate
./scripts/generate_ssl.sh

# Or use Let's Encrypt for production
sudo ./scripts/setup_letsencrypt.sh
```

## API Access for GenAI Agents

### User Registration
```bash
curl -X POST https://localhost:5000/register \
  -H "Content-Type: application/json" \
  -d '{"username":"agent","email":"agent@example.com","password":"secure_pass"}'
```

### Application Management
```bash
# List applications
curl https://localhost:5000/api/applications

# Add application
curl -X POST https://localhost:5000/api/applications \
  -H "Content-Type: application/json" \
  -d '{"name":"MyApp","url":"http://myapp.com","git_url":"https://github.com/user/myapp.git"}'

# Deploy application
curl -X POST https://localhost:5000/api/deploy \
  -H "Content-Type: application/json" \
  -d '{"application_name":"MyApp","action":"start"}'
```

### CLI Interface
```bash
# Register user
python3 ./scripts/cli.py register --username agent --email agent@example.com --password secure_pass

# List applications
python3 ./scripts/cli.py list-apps

# Deploy application
python3 ./scripts/cli.py deploy --name MyApp --action start
```

### MCP Protocol
```bash
# Start MCP server for agent communication
python3 mcp_server.py
```

## Verification

### Health Check
```bash
# Verify installation
curl https://localhost:5000/health

# Expected response: {"status":"healthy"}
```

### Service Status
```bash
# Check all services
docker-compose ps

# Check application logs
docker-compose logs app
```

## Default Configuration

- **Web Interface**: https://localhost:5000
- **API Endpoint**: https://localhost:5000/api
- **MCP Server**: localhost:8080
- **Database**: SQLite (users.db)
- **Deployment Directory**: /home/ubuntu/deployments/

## Troubleshooting

### Common Issues
```bash
# Port conflicts
sudo netstat -tulpn | grep :5000

# Permission issues
sudo chown -R $USER:$USER /home/ubuntu/deployments/

# Database issues
rm users.db && python3 ./scripts/cli.py init-db
```

### Reset Installation
```bash
# Complete reset
docker-compose down -v
rm users.db
./deploy.sh
```