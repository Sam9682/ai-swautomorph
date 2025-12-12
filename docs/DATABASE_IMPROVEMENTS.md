# Database Architecture and Improvements

## Overview

The AI-SwAutoMorph platform uses a comprehensive SQLite database with thread-safe connection management, automatic retry logic, and health monitoring to prevent database lock issues and ensure reliable operation across multiple concurrent users and deployments.

## Database Schema

### Core Tables

#### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT,
    suspended INTEGER DEFAULT 1,        -- 0=active, 1=suspended
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Applications Table
```sql
CREATE TABLE applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    git_url TEXT,                       -- Git repository URL
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### User Applications Assignment
```sql
CREATE TABLE user_applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    application_id INTEGER NOT NULL,
    url TEXT NOT NULL,                  -- Calculated URL with port
    http_port INTEGER,                  -- Calculated HTTP port
    https_port INTEGER,                 -- Calculated HTTPS port
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (application_id) REFERENCES applications (id),
    UNIQUE(user_id, application_id)
);
```

### Deployment Management Tables

#### Deployments Table
```sql
CREATE TABLE deployments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    application_name TEXT NOT NULL,
    status TEXT DEFAULT 'pending',      -- pending, running, cloning, cloned, completed, failed, timeout, error
    deployment_path TEXT,               -- Local deployment directory path
    git_url TEXT,                       -- Git repository URL
    server_id INTEGER,                  -- Target server for deployment
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (server_id) REFERENCES servers (id)
);
```

#### Servers Table
```sql
CREATE TABLE servers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    SERVER_IP TEXT UNIQUE NOT NULL,
    SERVER_NAME TEXT NOT NULL,
    SERVER_CAPACITY_USER_MAX INTEGER NOT NULL,     -- Maximum users per server
    SERVER_CAPACITY_APPLI_MAX INTEGER NOT NULL,    -- Maximum applications per server
    SERVER_STATUS TEXT DEFAULT 'STAND_BY',         -- STAND_BY, ACTIVE, MAINTENANCE
    SERVER_TYPE TEXT NOT NULL,                     -- primary, secondary, development, production
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Authentication and Security Tables

#### Authentication Tokens
```sql
CREATE TABLE auth_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token_hash TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

#### User Activity Logs
```sql
CREATE TABLE users_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    username TEXT NOT NULL,
    action TEXT NOT NULL,               -- login, logout, deploy, etc.
    datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

### Billing and Cost Management Tables

#### Application Costs
```sql
CREATE TABLE application_costs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER NOT NULL,
    cost_per_day REAL DEFAULT 1.0,     -- Daily cost in currency units
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (application_id) REFERENCES applications (id)
);
```

#### Billing Activities
```sql
CREATE TABLE billing_activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    application_id INTEGER NOT NULL,
    action TEXT NOT NULL,               -- start, stop
    started_at TIMESTAMP,               -- When application started
    stopped_at TIMESTAMP,               -- When application stopped
    duration_seconds INTEGER,           -- Total runtime in seconds
    cost_amount REAL,                   -- Calculated cost for this session
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (application_id) REFERENCES applications (id)
);
```

## Database Improvements

### 1. Thread-Safe Connection Manager

The `DatabaseManager` class provides thread-safe database access with connection pooling:

```python
class DatabaseManager:
    """Thread-safe database manager with connection pooling"""
    
    def __init__(self):
        self._local = threading.local()
    
    def _get_connection(self):
        """Get thread-local database connection"""
        if not hasattr(self._local, 'connection'):
            self._local.connection = sqlite3.connect(
                DB_PATH, 
                timeout=30.0,           # 30 second timeout
                check_same_thread=False
            )
            # Enable WAL mode for better concurrency
            self._local.connection.execute('PRAGMA journal_mode=WAL')
            # Set busy timeout
            self._local.connection.execute('PRAGMA busy_timeout=30000')
            # Enable foreign keys
            self._local.connection.execute('PRAGMA foreign_keys=ON')
        return self._local.connection
```

### 2. Context Manager for Safe Operations

```python
@contextmanager
def get_db_connection(self):
    """Context manager for database connections"""
    conn = self._get_connection()
    try:
        yield conn
    except Exception as e:
        conn.rollback()
        raise
    finally:
        # Keep connection for reuse (don't close)
        pass
```

### 3. Automatic Retry Logic

```python
def execute_query(self, query, params=None, fetch_one=False, fetch_all=False):
    """Execute a query with automatic retry on database lock"""
    max_retries = 3
    retry_delay = 0.1
    
    for attempt in range(max_retries):
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                if fetch_one:
                    result = cursor.fetchone()
                elif fetch_all:
                    result = cursor.fetchall()
                else:
                    result = cursor.lastrowid
                
                conn.commit()
                return result
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e) and attempt < max_retries - 1:
                time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                continue
            raise
```

### 4. WAL Mode Configuration

Write-Ahead Logging (WAL) mode provides several benefits:

- **Concurrent Reads**: Multiple readers don't block each other
- **Non-blocking Reads**: Readers don't block writers
- **Better Performance**: Reduced lock contention
- **Crash Recovery**: Better data integrity

```python
# Automatically enabled for all connections
self._local.connection.execute('PRAGMA journal_mode=WAL')
self._local.connection.execute('PRAGMA busy_timeout=30000')
self._local.connection.execute('PRAGMA foreign_keys=ON')
```

## Database Health Monitoring

### Health Check Functions

```python
def check_database_health():
    """Comprehensive database health check"""
    return {
        'connection_status': 'healthy|unhealthy',
        'wal_mode': True|False,
        'foreign_keys': True|False,
        'table_count': int,
        'total_size_mb': float,
        'last_vacuum': timestamp,
        'performance_metrics': {...}
    }

def get_database_stats():
    """Get detailed database statistics"""
    return {
        'tables': {
            'users': {'count': int, 'size_kb': float},
            'applications': {'count': int, 'size_kb': float},
            'deployments': {'count': int, 'size_kb': float},
            # ... other tables
        },
        'indexes': [...],
        'performance': {...}
    }
```

### Health Monitoring Endpoint

```bash
# Admin-only database health check
GET /api/health/database

Response:
{
  "health": {
    "connection_status": "healthy",
    "wal_mode": true,
    "foreign_keys": true,
    "table_count": 9,
    "total_size_mb": 2.5
  },
  "statistics": {
    "tables": {
      "users": {"count": 15, "size_kb": 45.2},
      "deployments": {"count": 127, "size_kb": 234.8}
    }
  }
}
```

## Port Allocation System

### Automatic Port Calculation

The platform automatically calculates unique ports for each user and application:

```python
def calculate_app_ports(user_id, app_id):
    """Calculate HTTP and HTTPS ports using deployControlPlan.sh logic"""
    PORT_RANGE_BEGIN = RANGE_START + user_id * RANGE_RESERVED
    HTTP_PORT = PORT_RANGE_BEGIN + app_id * 2
    HTTPS_PORT = HTTP_PORT + 1
    return HTTP_PORT, HTTPS_PORT
```

### Configuration Parameters

From `conf/deploy.ini`:
```ini
RANGE_START=8100                    # Starting port range
RANGE_RESERVED=100                  # Ports reserved per user
RANGE_START_CONTROLPLAN=80          # Control plan port range (HTTP)
RANGE_RESERVED_CONTROLPLAN=0        # Control plan ports per user
DOMAIN=www.swautomorph.com          # Primary domain
EMAIL=admin@swautomorph.com         # Admin email
GITEA_VERSION=1.21.3                # Gitea version
```

### URL Generation

URLs are automatically generated and stored in `user_applications`:
```python
HTTP_PORT, HTTPS_PORT = calculate_app_ports(user_id, app_id)
url = f'https://www.swautomorph.com:{HTTPS_PORT}'

# Store both URL and individual ports for flexibility
db_manager.execute_query(
    'INSERT INTO user_applications (user_id, application_id, url, http_port, https_port) VALUES (?, ?, ?, ?, ?)',
    (user_id, app_id, url, HTTP_PORT, HTTPS_PORT)
)
```

## Data Initialization

### Default Data Setup

The system automatically creates default data on first run:

#### Default Applications
```python
default_apps = [
    ('ai-foodflow', 'Food management system', 'git@github.com:Sam9682/ai-foodflow.git'),
    ('ai-haccp', 'HACCP compliance system', 'git@github.com:Sam9682/ai-haccp.git'),
    ('ai-checkinatwork', 'Check In for employees at work', 'git@github.com:Sam9682/ai-checkinatwork.git'),
    ('ai-staticwebsite', 'Simple static Web Site', 'git@github.com:Sam9682/ai-staticwebsite.git'),
    ('ai-transats', 'Transat Beach Management', 'git@github.com:Sam9682/ai-transats.git'),
    ('ai-beewoo', 'Simple Traffic Analyzer Web Site', 'git@github.com:Sam9682/ai-beewoo.git')
]
```

#### Default Admin User
```python
# Creates admin user with username: admin, password: password
admin_password_hash = generate_password_hash('password')
cursor.execute('''
    INSERT INTO users (username, email, password_hash, first_name, last_name, suspended)
    VALUES (?, ?, ?, ?, ?, ?)
''', ('admin', 'admin@swautomorph.com', admin_password_hash, 'System', 'Administrator', 0))
```

#### Default Server
```python
# Automatically detects current server IP and adds to servers table
current_ip = get_current_server_ip()
cursor.execute('''
    INSERT INTO servers (SERVER_IP, SERVER_NAME, SERVER_CAPACITY_USER_MAX, 
                       SERVER_CAPACITY_APPLI_MAX, SERVER_STATUS, SERVER_TYPE)
    VALUES (?, ?, ?, ?, ?, ?)
''', (current_ip, 'main-server', 10, 50, 'STAND_BY', 'primary'))
```

## Database Operations

### User Management

```python
# Create new user with automatic application assignment
def create_user(username, email, password, first_name='', last_name=''):
    # Insert user
    user_id = db_manager.execute_query(
        'INSERT INTO users (username, email, password_hash, first_name, last_name, suspended) VALUES (?, ?, ?, ?, ?, ?)',
        (username, email, password_hash, first_name, last_name, 0)
    )
    
    # Assign default applications
    assign_default_apps_to_user(user_id)
    
    # Create Gitea user (if available)
    create_gitea_user(username, email, password, first_name, last_name)
```

### Application Assignment

```python
def assign_default_apps_to_user(user_id):
    """Assign all applications to new user with calculated URLs"""
    apps = db_manager.execute_query('SELECT id, name FROM applications', fetch_all=True)
    
    for app in apps:
        app_id, app_name = app[0], app[1]
        HTTP_PORT, HTTPS_PORT = calculate_app_ports(user_id, app_id)
        url = f'https://www.swautomorph.com:{HTTPS_PORT}'
        
        db_manager.execute_query(
            'INSERT OR IGNORE INTO user_applications (user_id, application_id, url) VALUES (?, ?, ?)',
            (user_id, app_id, url)
        )
```

### Deployment Tracking

```python
def record_deployment(user_id, app_name, action, deployment_path=None, git_url=None, server_id=None):
    """Record deployment activity"""
    status = 'running' if action == 'start' else 'stopped' if action == 'stop' else 'completed'
    
    db_manager.execute_query('''
        INSERT INTO deployments (user_id, application_name, status, deployment_path, git_url, server_id)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, app_name, status, deployment_path, git_url, server_id))
```

### Billing Operations

```python
def record_billing_activity(user_id, app_name, action):
    """Record billing activity for cost tracking"""
    # Get application ID
    app = db_manager.execute_query(
        'SELECT id FROM applications WHERE name = ?', 
        (app_name,), fetch_one=True
    )
    
    if action == 'start':
        # Record start time
        db_manager.execute_query('''
            INSERT INTO billing_activities (user_id, application_id, action, started_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ''', (user_id, app[0], action))
    
    elif action == 'stop':
        # Calculate duration and cost
        # Update existing record with stop time and cost
        pass
```

## Performance Optimizations

### Indexes

The database includes strategic indexes for performance:

```sql
-- User lookups
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);

-- Application assignments
CREATE INDEX idx_user_applications_user_id ON user_applications(user_id);
CREATE INDEX idx_user_applications_app_id ON user_applications(application_id);

-- Deployment queries
CREATE INDEX idx_deployments_user_id ON deployments(user_id);
CREATE INDEX idx_deployments_app_name ON deployments(application_name);
CREATE INDEX idx_deployments_server_id ON deployments(server_id);

-- Billing queries
CREATE INDEX idx_billing_user_id ON billing_activities(user_id);
CREATE INDEX idx_billing_app_id ON billing_activities(application_id);
CREATE INDEX idx_billing_dates ON billing_activities(started_at, stopped_at);
```

### Query Optimization

- **Prepared Statements**: All queries use parameterized statements
- **Connection Reuse**: Thread-local connections reduce overhead
- **Batch Operations**: `executemany()` for bulk operations
- **Transaction Management**: Automatic commit/rollback handling

## Maintenance Operations

### Database Health Commands

```bash
# Check database health (CLI)
python3 ./scripts/cli.py db-health

# Mount S3 storage for backups
python3 ./scripts/cli.py mount-s3fs softfluid /mnt/s3

# Initialize database
python3 ./scripts/cli.py init-db
```

### Backup and Recovery

```bash
# Manual database backup
./deployControlPlan.sh backup_db

# Automated hourly backups (configured via cron)
# Backups stored in ./softfluid/db/backup/YYYYMMDD_HHMMSS/

# Recover from backup (interactive menu)
./deployControlPlan.sh --recover_db

# S3 sync for backups
aws s3 sync ./softfluid s3://softfluid --profile OVH-SWAUTOMORPH
```

### Database Reset

```bash
# Complete database reset
rm db/ai_swautomorph.db*
python3 ./scripts/cli.py init-db
```

## Troubleshooting

### Common Database Issues

1. **Database Locked Errors**:
   - Automatically handled by retry logic
   - WAL mode reduces lock contention
   - Thread-local connections prevent conflicts

2. **Performance Issues**:
   - Check database size and run VACUUM
   - Analyze query performance
   - Review index usage

3. **Corruption Issues**:
   - WAL mode provides better crash recovery
   - Regular backups prevent data loss
   - PRAGMA integrity_check for validation

### Monitoring Queries

```sql
-- Check database size
SELECT 
    name,
    COUNT(*) as row_count,
    (SELECT COUNT(*) FROM pragma_table_info(name)) as column_count
FROM sqlite_master 
WHERE type='table' 
GROUP BY name;

-- Check recent activity
SELECT 
    u.username,
    d.application_name,
    d.status,
    d.updated_at
FROM deployments d
JOIN users u ON d.user_id = u.id
ORDER BY d.updated_at DESC
LIMIT 10;

-- Check billing summary
SELECT 
    u.username,
    COUNT(ba.id) as sessions,
    SUM(ba.duration_seconds) as total_seconds,
    SUM(ba.cost_amount) as total_cost
FROM billing_activities ba
JOIN users u ON ba.user_id = u.id
GROUP BY u.username
ORDER BY total_cost DESC;
```

## Migration and Upgrades

### Schema Migrations

When adding new features, database migrations are handled automatically:

```python
def migrate_database():
    """Apply database migrations for new features"""
    # Check current schema version
    # Apply necessary ALTER TABLE statements
    # Update schema version
    pass
```

### Backward Compatibility

The database schema maintains backward compatibility:
- New columns use DEFAULT values
- Optional foreign keys allow gradual migration
- Legacy data is preserved during upgrades

## Security Considerations

### Data Protection

- **Password Hashing**: Werkzeug secure password hashing
- **Token Security**: Secure random token generation
- **SQL Injection Prevention**: Parameterized queries only
- **Access Control**: User-based data isolation

### Audit Trail

- **User Activity**: All login/logout events logged
- **Deployment History**: Complete deployment audit trail
- **Billing Records**: Immutable billing activity records
- **Admin Actions**: Administrative actions tracked

This comprehensive database architecture ensures reliable, scalable, and secure operation of the AI-SwAutoMorph platform while providing detailed tracking and monitoring capabilities.