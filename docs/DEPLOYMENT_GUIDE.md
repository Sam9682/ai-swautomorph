# Application Deployment Guide

## Overview

The AI-SwAutoMorph platform supports deploying applications across multiple servers with automatic capacity management, real-time monitoring, and GenAI-powered code evolution. Users can clone, start, stop, and monitor applications in their own isolated directories with full multi-server support.

## Features

### For All Users
- **Clone Applications**: Clone git repositories to your personal deployment directory
- **Multi-Server Deployment**: Automatic server allocation based on capacity
- **Start/Stop Applications**: Control application lifecycle using deployApp.sh scripts
- **Real-time Monitoring**: Live status updates and streaming logs
- **GenAI Code Evolution**: Modify applications using natural language through Q Chat
- **Isolated Deployments**: Each user gets their own deployment directory
- **Billing Tracking**: Automatic cost tracking for application usage

### For Administrators
- **Server Management**: Add, configure, and monitor multiple deployment servers
- **User Management**: Create users, manage permissions, and track usage
- **Application Management**: Add git repository URLs and manage application catalog
- **Database Administration**: Direct database access and health monitoring
- **Cost Management**: Configure application costs and view billing reports

## Multi-Server Architecture

### Server Types and Status
- **STAND_BY**: Server ready for new deployments
- **ACTIVE**: Server currently hosting deployments
- **MAINTENANCE**: Server temporarily unavailable

### Capacity Management
```
Server Constraints:
- SERVER_CAPACITY_USER_MAX: Maximum users per server
- SERVER_CAPACITY_APPLI_MAX: Maximum applications per server
```

### Automatic Server Allocation
The platform automatically selects the optimal server based on:
1. Current server capacity utilization
2. Server status (prefers STAND_BY over ACTIVE)
3. Network connectivity and performance

## How It Works

### Directory Structure
```
/home/ubuntu/deployments/
├── username1/
│   ├── ai-haccp/
│   │   ├── deployApp.sh
│   │   ├── ssl/                  # Auto-synced SSL certificates
│   │   └── [application files]
│   └── ai-foodflow/
│       ├── deployApp.sh
│       └── [application files]
└── username2/
    └── ai-haccp/
        ├── deployApp.sh
        └── [application files]
```

### Deployment Process

1. **Server Allocation**: System selects optimal server based on capacity
2. **Clone**: Downloads the git repository to `/home/ubuntu/deployments/{username}/{app-name}/`
3. **SSL Sync**: Automatically copies SSL certificates to deployment directory
4. **Deploy Commands**: Runs `deployApp.sh` with the specified command (start/stop/status/restart)
5. **Monitoring**: Tracks deployment status and provides real-time logs
6. **Billing**: Records usage for cost tracking

## Usage

### From Dashboard

1. **Clone Application**:
   - Click the "📥 Clone" button on any application card
   - System automatically allocates optimal server
   - Repository cloned with SSL certificates synced
   - Status shows as "cloning" then "cloned" when complete

2. **Start Application**:
   - Click the "▶️ Start" button
   - Runs `./deployApp.sh start {user_id} "{user_name}" {user_email}` 
   - Real-time status updates and streaming logs available
   - Billing tracking automatically starts

3. **Stop Application**:
   - Click the "⏹️ Stop" button
   - Runs `./deployApp.sh stop` in the application directory
   - Billing tracking automatically stops and calculates costs

4. **Check Status**:
   - Click the "📊 Status" button
   - Runs `./deployApp.sh ps` and shows current state with JSON output
   - Real-time application health monitoring

5. **View Logs**:
   - Click the "📋 Logs" button
   - Opens modal with deployment status and streaming logs
   - Real-time log updates using Server-Sent Events

6. **GenAI Code Evolution**:
   - Select application and click "Virtual Developer" toggle
   - Use natural language to request code modifications
   - System creates Git branch, modifies code, and redeploys automatically

### API Endpoints

#### Server Management
```bash
# Get available servers
GET /api/servers

# Allocate server for deployment
POST /api/server/allocate
Content-Type: application/json
{
  "application_name": "AI HACCP"
}
```

#### Deployment Management
```bash
# Get user deployments
GET /api/deployments

# Create deployment with server allocation
POST /api/deployments
Content-Type: application/json
{
  "action": "clone|start|stop|status|restart|ps|logs",
  "application_name": "AI HACCP",
  "git_url": "https://github.com/Sam9682/ai-haccp.git",
  "server_id": 1,
  "stream": true  // Optional: enable real-time streaming
}
```

#### GenAI Integration
```bash
# Q Chat for code modification
POST /api/qchat
Content-Type: application/json
{
  "message": "Add a health check endpoint",
  "auto_approve": true,
  "application_name": "AI HACCP",
  "application_folder": "/home/ubuntu/deployments/user/ai-haccp",
  "gitea_url": "http://localhost:3000/gitadmin/branch-name",
  "userid": "1",
  "username": "user"
}

# Virtual Advisor questions (streaming)
POST /api/qchat_question
Content-Type: application/json
{
  "message": "How do I restart the application?",
  "application_name": "AI HACCP",
  "application_folder": "/home/ubuntu/deployments/user/ai-haccp"
}
```

#### Get Deployment Logs
```bash
GET /api/deployments/{deployment_id}/logs
```

## Requirements

### Application Requirements
Applications must include a `deployApp.sh` script that supports:
- `./deployApp.sh start {user_id} "{user_name}" {user_email}` - Start the application
- `./deployApp.sh stop` - Stop the application  
- `./deployApp.sh ps` - Show application status (JSON format preferred)
- `./deployApp.sh restart {user_id} "{user_name}" {user_email}` - Restart the application
- `./deployApp.sh logs` - Show application logs

### System Requirements
- Git installed on all deployment servers
- Docker and Docker Compose (if applications use containers)
- SSH access between servers for remote deployment
- SSL certificates for HTTPS support
- Sufficient disk space for application deployments
- Network access to git repositories

### Server Requirements
- Ubuntu/Linux operating system
- SSH server configured with key-based authentication
- Docker and Docker Compose installed
- Git client installed
- Network connectivity to main platform server

## Security Considerations

- Each user has isolated deployment directories
- Git repositories are cloned with user permissions
- SSL certificates automatically synced to all deployments
- SSH key-based authentication for remote server access
- Deployment commands run with limited privileges
- Logs are only accessible to the deployment owner
- Server capacity limits prevent resource exhaustion

## GenAI Code Evolution

### Virtual Developer
The Virtual Developer can modify application code using natural language:

1. **Request Processing**: Analyzes user request and application structure
2. **Branch Creation**: Creates timestamped Git branch: `{user_id}-automorph-{app_name}-{timestamp}`
3. **Code Modification**: Uses Q Chat to generate and apply code changes
4. **Testing**: Runs application tests if available
5. **Deployment**: Automatically redeploys with new changes
6. **Tracking**: Updates database with Git branch and deployment status

### Virtual DevOps Team
Context-aware assistants for application management:

- **START**: Guides through application startup process
- **STOP**: Handles graceful application shutdown
- **PS**: Provides detailed status information
- **RESTART**: Manages application restart procedures
- **LOGS**: Retrieves and analyzes application logs

### Context Templates
Pre-built templates in `/shared/*_context.md` provide:
- Step-by-step instructions for each operation
- Environment variable substitution
- Error handling procedures
- Best practices for each action type

## Billing and Cost Management

### Automatic Cost Tracking
- **Start Events**: Billing begins when application starts
- **Stop Events**: Billing ends and calculates total cost
- **Duration Tracking**: Precise usage time measurement
- **Cost Calculation**: Based on `cost_per_day` configuration (default: $1.00/day)

### Cost Configuration
```sql
-- Application costs can be configured per application
INSERT INTO application_costs (application_id, cost_per_day) VALUES (1, 2.50);
```

### Billing Reports
- Per-user usage summaries
- Per-application cost analysis
- Historical billing data
- Real-time cost tracking

## Troubleshooting

### Common Issues

1. **Clone Failed**:
   - Check git URL is accessible from target server
   - Verify network connectivity between servers
   - Ensure sufficient disk space on target server
   - Check SSH key authentication for remote servers

2. **Deploy Commands Fail**:
   - Verify `deployApp.sh` exists and is executable
   - Check application dependencies are installed on target server
   - Review deployment logs for specific errors
   - Ensure Docker/Docker Compose is available if needed

3. **Server Allocation Issues**:
   - Check server capacity limits in database
   - Verify server status is STAND_BY or ACTIVE
   - Ensure network connectivity to target servers
   - Review server health and resource availability

4. **SSL Certificate Issues**:
   - Verify SSL certificates exist in `/home/ubuntu/ai-swautomorph/ssl/`
   - Check certificate file permissions
   - Ensure rsync/SSH access for remote certificate sync

### Status Meanings

- `pending`: Command queued for execution
- `running`: Command currently executing
- `cloning`: Git clone in progress
- `cloned`: Repository successfully cloned
- `completed`: Command completed successfully
- `failed`: Command failed with error
- `timeout`: Command exceeded time limit
- `error`: System error occurred

### Deployment Status JSON Format

The `deployApp.sh ps` command should return JSON format:
```json
{
  "docker_compose_ps": "IS_RUNNING|IS_NOT_RUNNING",
  "application_status": "healthy|unhealthy",
  "port_status": "open|closed",
  "additional_info": "..."
}
```

## Example Applications

### AI HACCP
- Repository: `https://github.com/Sam9682/ai-haccp.git`
- Supports full deployment lifecycle
- Includes Docker containerization
- HACCP compliance management system

### AI FoodFlow  
- Repository: `https://github.com/Sam9682/ai-foodflow.git`
- Web-based food management system
- Requires database setup
- Multi-user restaurant management

### AI CheckInAtWork
- Repository: `https://github.com/Sam9682/ai-checkinatwork.git`
- Employee check-in system
- Time tracking and management
- Mobile-friendly interface

## Configuration

### Adding New Applications

1. Go to Applications tab (admin only)
2. Click "Add New Application"
3. Fill in:
   - Application Name
   - Description
   - Git Repository URL
4. Save application
5. System automatically assigns to all users with calculated URLs

### Server Management

1. Go to Admin panel → Servers
2. Add new server with:
   - Server IP address
   - Server name
   - User capacity limit
   - Application capacity limit
   - Server type (primary/secondary)
3. Ensure SSH key access is configured

### Port Allocation

Ports are automatically calculated using:
```
PORT_RANGE_BEGIN = RANGE_START + user_id * RANGE_RESERVED
HTTP_PORT = PORT_RANGE_BEGIN + app_id * 2
HTTPS_PORT = HTTP_PORT + 1
```

Default configuration:
- RANGE_START: 8100
- RANGE_RESERVED: 100 (ports per user)

## Monitoring

### Dashboard View
- Real-time status updates every 10 seconds
- Deployment history and logs
- Server capacity utilization
- Cost tracking and billing information

### System Monitoring
- Check `/home/ubuntu/deployments/` for disk usage across servers
- Monitor server resources during deployments
- Review application logs for issues
- Track database performance and health

### Health Endpoints
```bash
# Application health
GET /health

# Database health (admin only)
GET /api/health/database
```

## Best Practices

1. **Resource Management**: Monitor disk space and memory usage across servers
2. **Regular Cleanup**: Remove old/unused deployments to free resources
3. **Backup Important Data**: Keep backups of critical application data
4. **Security Updates**: Keep applications and dependencies updated
5. **Server Maintenance**: Regular server health checks and updates
6. **Cost Monitoring**: Review billing reports and optimize usage
7. **Git Branch Management**: Regular cleanup of automorph branches
8. **SSL Certificate Renewal**: Monitor certificate expiration dates

## Advanced Features

### Streaming Deployment Logs
Enable real-time log streaming by adding `"stream": true` to deployment requests:
```javascript
// JavaScript example for real-time logs
const eventSource = new EventSource('/api/deployments/stream');
eventSource.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log(data.chunk); // Real-time log output
};
```

### Database Administration
Admin users can access database tables directly:
```bash
# View table data
GET /api/database/tables/deployments

# Add records
POST /api/database/tables/servers
{
  "SERVER_IP": "192.168.1.100",
  "SERVER_NAME": "production-server-2",
  "SERVER_CAPACITY_USER_MAX": 20,
  "SERVER_CAPACITY_APPLI_MAX": 100,
  "SERVER_STATUS": "STAND_BY",
  "SERVER_TYPE": "production"
}
```

### Multi-Language Support
The platform supports multiple languages (English/French) with automatic detection and session-based language switching.