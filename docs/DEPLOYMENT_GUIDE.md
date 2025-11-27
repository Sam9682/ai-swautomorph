# Application Deployment Guide

## Overview

The AI-SwAutoMorph platform now supports deploying applications directly from the dashboard. Users can clone, start, stop, and monitor applications in their own isolated directories.

## Features

### For All Users
- **Clone Applications**: Clone git repositories to your personal deployment directory
- **Start/Stop Applications**: Control application lifecycle using deployApp.sh scripts
- **Status Monitoring**: Check deployment status and view logs
- **Isolated Deployments**: Each user gets their own deployment directory

### For Administrators
- **Manage Git URLs**: Add git repository URLs to applications
- **Monitor All Deployments**: View deployment status across all users

## How It Works

### Directory Structure
```
/home/ubuntu/deployments/
├── username1/
│   ├── ai-haccp/
│   │   ├── deployApp.sh
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

1. **Clone**: Downloads the git repository to `/home/ubuntu/deployments/{username}/{app-name}/`
2. **Deploy Commands**: Runs `deployApp.sh` with the specified command (start/stop/status/restart)
3. **Monitoring**: Tracks deployment status and provides logs

## Usage

### From Dashboard

1. **Clone Application**:
   - Click the "📥 Clone" button on any application card
   - The system will clone the git repository to your user directory
   - Status will show as "cloning" then "cloned" when complete

2. **Start Application**:
   - Click the "▶️ Start" button
   - Runs `./deployApp.sh start` in the application directory
   - Status updates to show progress

3. **Stop Application**:
   - Click the "⏹️ Stop" button
   - Runs `./deployApp.sh stop` in the application directory

4. **Check Status**:
   - Click the "📊 Status" button
   - Runs `./deployApp.sh status` and shows current state

5. **View Logs**:
   - Click the "📋 Logs" button
   - Opens modal with deployment status and logs

### API Endpoints

#### Get Deployments
```bash
GET /api/deployments
```

#### Create Deployment
```bash
POST /api/deployments
Content-Type: application/json

{
  "action": "clone|start|stop|status|restart",
  "application_name": "AI HACCP",
  "git_url": "https://github.com/Sam9682/ai-haccp.git"  // Required for clone
}
```

#### Get Deployment Logs
```bash
GET /api/deployments/{deployment_id}/logs
```

## Requirements

### Application Requirements
Applications must include a `deployApp.sh` script that supports:
- `./deployApp.sh start` - Start the application
- `./deployApp.sh stop` - Stop the application  
- `./deployApp.sh status` - Show application status
- `./deployApp.sh restart` - Restart the application

### System Requirements
- Git installed on the system
- Docker and Docker Compose (if applications use containers)
- Sufficient disk space for application deployments
- Network access to git repositories

## Security Considerations

- Each user has isolated deployment directories
- Git repositories are cloned with user permissions
- Deployment commands run with limited privileges
- Logs are only accessible to the deployment owner

## Troubleshooting

### Common Issues

1. **Clone Failed**:
   - Check git URL is accessible
   - Verify network connectivity
   - Ensure sufficient disk space

2. **Deploy Commands Fail**:
   - Verify `deployApp.sh` exists and is executable
   - Check application dependencies are installed
   - Review deployment logs for specific errors

3. **Permission Issues**:
   - Ensure deployment directory is writable
   - Check file permissions on cloned repository

### Status Meanings

- `pending`: Command queued for execution
- `running`: Command currently executing
- `cloning`: Git clone in progress
- `cloned`: Repository successfully cloned
- `completed`: Command completed successfully
- `failed`: Command failed with error
- `timeout`: Command exceeded time limit
- `error`: System error occurred

## Example Applications

### AI HACCP
- Repository: `https://github.com/Sam9682/ai-haccp.git`
- Supports full deployment lifecycle
- Includes Docker containerization

### AI FoodFlow  
- Repository: `https://github.com/Sam9682/ai-foodflow.git`
- Web-based food management system
- Requires database setup

## Configuration

### Adding New Applications

1. Go to Applications tab (admin only)
2. Click "Add New Application"
3. Fill in:
   - Application Name
   - URL (where it will be accessible)
   - Description
   - Git Repository URL
4. Save application

### Updating Git URLs

1. Click edit button on application card
2. Update "Git Repository URL" field
3. Save changes

## Monitoring

### Dashboard View
- Real-time status updates
- Deployment history
- Log access

### System Monitoring
- Check `/home/ubuntu/deployments/` for disk usage
- Monitor system resources during deployments
- Review application logs for issues

## Best Practices

1. **Test Locally**: Test deployApp.sh scripts before adding to platform
2. **Resource Management**: Monitor disk space and memory usage
3. **Regular Cleanup**: Remove old/unused deployments
4. **Backup Important Data**: Keep backups of critical application data
5. **Security Updates**: Keep applications and dependencies updated