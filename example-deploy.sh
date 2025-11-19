#!/bin/bash

# Example deploy.sh script for applications
# This script should be included in each application repository

set -e

COMMAND=${1:-help}
APP_NAME="example-app"
LOG_FILE="deploy.log"

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

case $COMMAND in
    "start")
        log "🚀 Starting $APP_NAME..."
        
        # Example: Start with Docker Compose
        if [ -f "docker-compose.yml" ]; then
            docker-compose up -d
            log "✅ $APP_NAME started with Docker Compose"
        # Example: Start Python application
        elif [ -f "app.py" ]; then
            nohup python3 app.py > app.log 2>&1 &
            echo $! > app.pid
            log "✅ $APP_NAME started (PID: $(cat app.pid))"
        # Example: Start Node.js application
        elif [ -f "package.json" ]; then
            npm install
            nohup npm start > app.log 2>&1 &
            echo $! > app.pid
            log "✅ $APP_NAME started (PID: $(cat app.pid))"
        else
            log "❌ No supported application type found"
            exit 1
        fi
        ;;
        
    "stop")
        log "🛑 Stopping $APP_NAME..."
        
        # Stop Docker Compose
        if [ -f "docker-compose.yml" ]; then
            docker-compose down
            log "✅ $APP_NAME stopped (Docker Compose)"
        # Stop process by PID
        elif [ -f "app.pid" ]; then
            PID=$(cat app.pid)
            if kill -0 "$PID" 2>/dev/null; then
                kill "$PID"
                rm -f app.pid
                log "✅ $APP_NAME stopped (PID: $PID)"
            else
                log "⚠️ Process not running (PID: $PID)"
                rm -f app.pid
            fi
        else
            log "⚠️ No running process found"
        fi
        ;;
        
    "status")
        log "📊 Checking $APP_NAME status..."
        
        # Check Docker Compose status
        if [ -f "docker-compose.yml" ]; then
            if docker-compose ps | grep -q "Up"; then
                log "✅ $APP_NAME is running (Docker Compose)"
                docker-compose ps
            else
                log "❌ $APP_NAME is not running (Docker Compose)"
            fi
        # Check process status
        elif [ -f "app.pid" ]; then
            PID=$(cat app.pid)
            if kill -0 "$PID" 2>/dev/null; then
                log "✅ $APP_NAME is running (PID: $PID)"
            else
                log "❌ $APP_NAME is not running (stale PID: $PID)"
                rm -f app.pid
            fi
        else
            log "❌ $APP_NAME is not running"
        fi
        ;;
        
    "restart")
        log "🔄 Restarting $APP_NAME..."
        $0 stop
        sleep 2
        $0 start
        ;;
        
    "logs")
        log "📋 Showing $APP_NAME logs..."
        if [ -f "app.log" ]; then
            tail -n 50 app.log
        elif [ -f "docker-compose.yml" ]; then
            docker-compose logs --tail=50
        else
            log "No logs found"
        fi
        ;;
        
    *)
        echo "Usage: $0 [start|stop|restart|status|logs]"
        echo "  start    - Start the application"
        echo "  stop     - Stop the application"
        echo "  restart  - Restart the application"
        echo "  status   - Show application status"
        echo "  logs     - Show application logs"
        exit 1
        ;;
esac

log "Command '$COMMAND' completed"