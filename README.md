# AI-SwAutoMorph

A centralized application management platform with user authentication and multi-access support (Web, CLI, API, MCP).

## Features

- 🔐 User registration and authentication
- 🌐 Web-based dashboard
- 📱 Application management with database storage
- 🔑 SSO Identity Provider with token-based authentication
- 🐳 Docker containerization
- 🖥️ Command-line interface (CLI)
- 🔌 REST API endpoints
- 🤖 MCP (Model Context Protocol) support
- 📖 Comprehensive user guide

## Quick Start

### 1. Production Deployment
```bash
./deploy.sh
```

### 2. Manual Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database
python3 cli.py init-db

# Start application
python3 app.py
```

### 3. Docker Development
```bash
docker-compose up -d
```

## Access Methods

### Web Interface
- URL: `http://www.swautomorph.com`
- Features: Registration, login, dashboard, application management

### CLI Tool
```bash
# Register user
python3 cli.py register

# List applications
python3 cli.py list-apps

# Add application
python3 cli.py add-app --name "My App" --url "http://myapp.swautomorph.com"
```

### REST API
```bash
# Register user
curl -X POST http://www.swautomorph.com:5000/register \
  -H "Content-Type: application/json" \
  -d '{"username":"user","email":"user@example.com","password":"pass"}'

# List applications
curl http://www.swautomorph.com:5000/api/applications

# Validate SSO token
curl -X POST http://www.swautomorph.com:5000/sso/validate \
  -H "Content-Type: application/json" \
  -d '{"token":"your_sso_token_here"}'
```

### SSO Integration
```bash
# Validate token via CLI
python3 cli.py validate-token --token "your_token_here"

# Access application with SSO
# Users click application links in dashboard, automatically redirected with token
# Example: http://ai-haccp.swautomorph.com?sso_token=abc123...
```

### MCP Protocol
```bash
# Start MCP server
python3 mcp_server.py
```

## Project Structure

```
ai-swautomorph/
├── app.py                 # Main Flask application
├── cli.py                 # Command-line interface
├── mcp_server.py          # MCP protocol server
├── deploy.sh              # Production deployment script
├── requirements.txt       # Python dependencies
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Docker Compose setup
├── nginx.conf             # Nginx reverse proxy config
├── templates/             # HTML templates
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   └── dashboard.html
└── static/                # Static assets
    ├── css/style.css
    ├── js/app.js
    └── userguide.html
```

## Default Applications

The system comes with two default applications:
- **AI FoodFlow**: `http://ai-foodflow.swautomorph.com`
- **AI HACCP**: `http://ai-haccp.swautomorph.com`

## Environment Variables

- `SECRET_KEY`: Flask secret key (change in production)
- `FLASK_ENV`: Environment mode (development/production)

## Database Schema

### Users Table
- id, username, email, password_hash, first_name, last_name, created_at

### Applications Table
- id, name, url, description, created_at

### Auth Tokens Table (SSO)
- id, user_id, token_hash, expires_at, created_at

## Security Notes

- Change default SECRET_KEY in production
- Use HTTPS for production deployments
- Implement proper firewall rules
- Regular database backups recommended
- SSO tokens expire after 1 week automatically
- Tokens are hashed in database for security
- Only one active token per user (new login invalidates previous token)

## Documentation

Complete user guide available at: `http://www.swautomorph.com/static/userguide.html`

## License

MIT License - See LICENSE file for details