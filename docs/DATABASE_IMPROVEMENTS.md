# 🗄️ Database Architecture & Improvements / Architecture et Améliorations de Base de Données

## English

<div class="center">
🚀 **Enhanced Database Architecture for AI-SwAutoMorph** 📊
</div>

### 📋 Table of Contents
- [🌟 Overview](#overview)
- [🏗️ Database Schema](#database-schema)
- [🔧 Thread-Safe Operations](#thread-safe-operations)
- [📊 Performance Optimizations](#performance-optimizations)
- [💰 Billing System](#billing-system)
- [🔍 Health Monitoring](#health-monitoring)
- [🔄 Backup & Recovery](#backup--recovery)
- [🛡️ Security Enhancements](#security-enhancements)

### 🌟 Overview

The AI-SwAutoMorph database has been significantly enhanced with thread-safe operations, WAL mode, connection pooling, and comprehensive billing tracking. The system now supports multi-server deployments with automatic capacity management, real-time health monitoring, and advanced security features.

#### 🎯 Key Improvements
- **🧵 Thread-Safe Operations**: Connection pooling with thread-local storage and singleton pattern
- **⚡ WAL Mode**: Write-Ahead Logging for better concurrency and performance
- **🔄 Automatic Retry**: Exponential backoff for database locks with jitter
- **📊 Health Monitoring**: Real-time database statistics and comprehensive health checks
- **💰 Billing Integration**: Comprehensive cost tracking, activity logging, and invoice generation
- **🖥️ Multi-Server Support**: Server capacity management, allocation, and load balancing
- **🔐 Enhanced Security**: Input validation, SQL injection prevention, and audit logging
- **📈 Performance Optimization**: Database indexes, query optimization, and connection pooling

### 🏗️ Database Schema

#### 📋 Core Tables

##### 👥 Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT,
    suspended INTEGER DEFAULT 1,  -- 0 = active, 1 = suspended
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_suspended ON users(suspended);
```

##### 📱 Applications Table
```sql
CREATE TABLE applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    git_url TEXT,
    git_remote_url TEXT,
    git_local_url TEXT,
    git_repo_size INTEGER DEFAULT 50,
    docker_build_duration INTEGER,
    docker_start_duration INTEGER,
    docker_stop_duration INTEGER,
    docker_ps_duration INTEGER,
    docker_compose_ports TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_applications_name ON applications(name);
CREATE INDEX idx_applications_git_url ON applications(git_url);
```

##### 🔗 User Applications Table
```sql
CREATE TABLE user_applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    application_id INTEGER NOT NULL,
    url TEXT NOT NULL,
    http_port INTEGER,
    https_port INTEGER,
    http_port2 INTEGER,
    https_port2 INTEGER,
    others_port INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (application_id) REFERENCES applications (id) ON DELETE CASCADE,
    UNIQUE(user_id, application_id)
);

-- Indexes for performance
CREATE INDEX idx_user_applications_user_id ON user_applications(user_id);
CREATE INDEX idx_user_applications_app_id ON user_applications(application_id);
CREATE INDEX idx_user_applications_ports ON user_applications(http_port, https_port);
```

##### 🚀 Deployments Table
```sql
CREATE TABLE deployments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    application_name TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    deployment_path TEXT,
    git_url TEXT,
    server_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (server_id) REFERENCES servers (id) ON DELETE SET NULL
);

-- Indexes for performance
CREATE INDEX idx_deployments_user_id ON deployments(user_id);
CREATE INDEX idx_deployments_app_name ON deployments(application_name);
CREATE INDEX idx_deployments_server_id ON deployments(server_id);
CREATE INDEX idx_deployments_status ON deployments(status);
CREATE INDEX idx_deployments_updated_at ON deployments(updated_at);
```

##### 🖥️ Servers Table
```sql
CREATE TABLE servers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    SERVER_IP TEXT UNIQUE NOT NULL,
    SERVER_NAME TEXT NOT NULL,
    SERVER_CAPACITY_USER_MAX INTEGER NOT NULL,
    SERVER_CAPACITY_APPLI_MAX INTEGER NOT NULL,
    SERVER_STATUS TEXT DEFAULT 'STAND_BY',  -- STAND_BY, ACTIVE, MAINTENANCE
    SERVER_TYPE TEXT NOT NULL,  -- primary, worker, backup
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_servers_status ON servers(SERVER_STATUS);
CREATE INDEX idx_servers_ip ON servers(SERVER_IP);
CREATE INDEX idx_servers_type ON servers(SERVER_TYPE);
```

#### 💰 Billing & Cost Tracking Tables

##### 💳 Application Costs Table
```sql
CREATE TABLE application_costs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER NOT NULL,
    cost_per_day REAL DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (application_id) REFERENCES applications (id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX idx_application_costs_app_id ON application_costs(application_id);
```

##### 📊 Billing Activities Table
```sql
CREATE TABLE billing_activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    application_id INTEGER NOT NULL,
    action TEXT NOT NULL,  -- START, STOP, RESTART, etc.
    started_at TIMESTAMP,
    stopped_at TIMESTAMP,
    duration_seconds INTEGER,
    cost_amount REAL,
    server_id INTEGER,
    resource_usage TEXT,  -- JSON field for resource metrics
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (application_id) REFERENCES applications (id) ON DELETE CASCADE,
    FOREIGN KEY (server_id) REFERENCES servers (id) ON DELETE SET NULL
);

-- Indexes for performance
CREATE INDEX idx_billing_activities_user_id ON billing_activities(user_id);
CREATE INDEX idx_billing_activities_app_id ON billing_activities(application_id);
CREATE INDEX idx_billing_activities_action ON billing_activities(action);
CREATE INDEX idx_billing_activities_created_at ON billing_activities(created_at);
CREATE INDEX idx_billing_activities_started_at ON billing_activities(started_at);
CREATE INDEX idx_billing_activities_stopped_at ON billing_activities(stopped_at);
```

##### 💳 Payment Modes Table
```sql
CREATE TABLE payment_modes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    payment_type TEXT NOT NULL,  -- bank_transfer, paypal, credit_card
    bank_account TEXT,
    paypal_email TEXT,
    card_last_four TEXT,
    card_type TEXT,  -- visa, mastercard, amex
    is_default INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX idx_payment_modes_user_id ON payment_modes(user_id);
CREATE INDEX idx_payment_modes_default ON payment_modes(is_default);
```

##### 🧾 Invoicing Table
```sql
CREATE TABLE invoicing (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    invoice_month TEXT NOT NULL,  -- YYYY-MM format
    total_amount REAL NOT NULL,
    status TEXT DEFAULT 'unpaid',  -- unpaid, paid, overdue, cancelled
    payment_date TIMESTAMP,
    payment_mode_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (payment_mode_id) REFERENCES payment_modes (id) ON DELETE SET NULL,
    UNIQUE(user_id, invoice_month)
);

-- Indexes for performance
CREATE INDEX idx_invoicing_user_id ON invoicing(user_id);
CREATE INDEX idx_invoicing_month ON invoicing(invoice_month);
CREATE INDEX idx_invoicing_status ON invoicing(status);
```

#### 🔐 Authentication & Logging Tables

##### 🔑 Auth Tokens Table
```sql
CREATE TABLE auth_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token_hash TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX idx_auth_tokens_user_id ON auth_tokens(user_id);
CREATE INDEX idx_auth_tokens_hash ON auth_tokens(token_hash);
CREATE INDEX idx_auth_tokens_expires ON auth_tokens(expires_at);
```

##### 📝 Users Logs Table
```sql
CREATE TABLE users_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    username TEXT NOT NULL,
    action TEXT NOT NULL,  -- login, logout, register, etc.
    ip_address TEXT,
    user_agent TEXT,
    datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX idx_users_logs_user_id ON users_logs(user_id);
CREATE INDEX idx_users_logs_action ON users_logs(action);
CREATE INDEX idx_users_logs_datetime ON users_logs(datetime);
```

### 🔧 Thread-Safe Operations

#### 🧵 Enhanced Database Manager Class
```python
class DatabaseManager:
    """Thread-safe database manager with connection pooling and singleton pattern"""
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._local = threading.local()
            self._connection_pool = {}
            self._pool_lock = threading.Lock()
            self._initialized = True
            self._setup_database()
    
    def _setup_database(self):
        """Initialize database with optimal settings"""
        with self.get_db_connection() as conn:
            # Enable WAL mode for better concurrency
            conn.execute('PRAGMA journal_mode=WAL')
            # Set busy timeout for locked database scenarios
            conn.execute('PRAGMA busy_timeout=30000')
            # Enable foreign keys
            conn.execute('PRAGMA foreign_keys=ON')
            # Optimize cache size
            conn.execute('PRAGMA cache_size=10000')
            # Set synchronous mode for performance
            conn.execute('PRAGMA synchronous=NORMAL')
            # Enable memory-mapped I/O
            conn.execute('PRAGMA mmap_size=268435456')  # 256MB
```

#### 🔄 Enhanced Connection Management
```python
def _get_connection(self):
    """Get thread-local database connection with pooling"""
    thread_id = threading.get_ident()
    
    if not hasattr(self._local, 'connection') or self._local.connection is None:
        with self._pool_lock:
            if thread_id in self._connection_pool:
                self._local.connection = self._connection_pool[thread_id]
            else:
                self._local.connection = sqlite3.connect(
                    DB_PATH, 
                    timeout=30.0,
                    check_same_thread=False,
                    isolation_level=None  # Autocommit mode
                )
                self._connection_pool[thread_id] = self._local.connection
                self._configure_connection(self._local.connection)
    
    return self._local.connection

def _configure_connection(self, conn):
    """Configure connection with optimal settings"""
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA busy_timeout=30000')
    conn.execute('PRAGMA foreign_keys=ON')
    conn.execute('PRAGMA cache_size=10000')
    conn.execute('PRAGMA synchronous=NORMAL')
    conn.execute('PRAGMA temp_store=MEMORY')
```

#### ⚡ Enhanced Automatic Retry Mechanism
```python
def execute_query(self, query, params=None, fetch_one=False, fetch_all=False):
    """Execute a query with enhanced retry mechanism and error handling"""
    max_retries = 5
    base_delay = 0.1
    max_delay = 2.0
    
    for attempt in range(max_retries):
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Log query for debugging (sanitized)
                self._log_query(query, params, attempt)
                
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
                # Exponential backoff with jitter
                delay = min(base_delay * (2 ** attempt) + random.uniform(0, 0.1), max_delay)
                time.sleep(delay)
                continue
            raise DatabaseError(f"Database operation failed after {attempt + 1} attempts: {str(e)}")
        except sqlite3.IntegrityError as e:
            raise DatabaseIntegrityError(f"Database integrity error: {str(e)}")
        except Exception as e:
            raise DatabaseError(f"Unexpected database error: {str(e)}")
```

### 📊 Performance Optimizations

#### ⚡ Enhanced WAL Mode Configuration
```sql
-- Enable Write-Ahead Logging for better concurrency
PRAGMA journal_mode=WAL;

-- Set busy timeout for locked database scenarios
PRAGMA busy_timeout=30000;

-- Enable foreign key constraints
PRAGMA foreign_keys=ON;

-- Optimize cache size (10MB)
PRAGMA cache_size=10000;

-- Set synchronous mode for performance
PRAGMA synchronous=NORMAL;

-- Enable memory-mapped I/O (256MB)
PRAGMA mmap_size=268435456;

-- Set temporary storage to memory
PRAGMA temp_store=MEMORY;

-- Optimize page size
PRAGMA page_size=4096;

-- Enable automatic index creation
PRAGMA automatic_index=ON;
```

#### 🔍 Comprehensive Database Indexes
```sql
-- User authentication and lookup indexes
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_suspended ON users(suspended);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

-- Application management indexes
CREATE INDEX IF NOT EXISTS idx_applications_name ON applications(name);
CREATE INDEX IF NOT EXISTS idx_applications_git_url ON applications(git_url);
CREATE INDEX IF NOT EXISTS idx_applications_created_at ON applications(created_at);

-- User application relationship indexes
CREATE INDEX IF NOT EXISTS idx_user_applications_user_id ON user_applications(user_id);
CREATE INDEX IF NOT EXISTS idx_user_applications_app_id ON user_applications(application_id);
CREATE INDEX IF NOT EXISTS idx_user_applications_ports ON user_applications(http_port, https_port);

-- Deployment tracking indexes
CREATE INDEX IF NOT EXISTS idx_deployments_user_id ON deployments(user_id);
CREATE INDEX IF NOT EXISTS idx_deployments_app_name ON deployments(application_name);
CREATE INDEX IF NOT EXISTS idx_deployments_server_id ON deployments(server_id);
CREATE INDEX IF NOT EXISTS idx_deployments_status ON deployments(status);
CREATE INDEX IF NOT EXISTS idx_deployments_updated_at ON deployments(updated_at);

-- Server management indexes
CREATE INDEX IF NOT EXISTS idx_servers_status ON servers(SERVER_STATUS);
CREATE INDEX IF NOT EXISTS idx_servers_ip ON servers(SERVER_IP);
CREATE INDEX IF NOT EXISTS idx_servers_type ON servers(SERVER_TYPE);

-- Billing and cost tracking indexes
CREATE INDEX IF NOT EXISTS idx_billing_activities_user_id ON billing_activities(user_id);
CREATE INDEX IF NOT EXISTS idx_billing_activities_app_id ON billing_activities(application_id);
CREATE INDEX IF NOT EXISTS idx_billing_activities_action ON billing_activities(action);
CREATE INDEX IF NOT EXISTS idx_billing_activities_created_at ON billing_activities(created_at);
CREATE INDEX IF NOT EXISTS idx_billing_activities_started_at ON billing_activities(started_at);
CREATE INDEX IF NOT EXISTS idx_billing_activities_stopped_at ON billing_activities(stopped_at);

-- Authentication and security indexes
CREATE INDEX IF NOT EXISTS idx_auth_tokens_user_id ON auth_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_auth_tokens_hash ON auth_tokens(token_hash);
CREATE INDEX IF NOT EXISTS idx_auth_tokens_expires ON auth_tokens(expires_at);

-- Audit and logging indexes
CREATE INDEX IF NOT EXISTS idx_users_logs_user_id ON users_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_users_logs_action ON users_logs(action);
CREATE INDEX IF NOT EXISTS idx_users_logs_datetime ON users_logs(datetime);

-- Composite indexes for complex queries
CREATE INDEX IF NOT EXISTS idx_billing_user_month ON billing_activities(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_deployment_user_status ON deployments(user_id, status);
CREATE INDEX IF NOT EXISTS idx_server_status_capacity ON servers(SERVER_STATUS, SERVER_CAPACITY_USER_MAX);
```

### 💰 Billing System

#### 📊 Enhanced Cost Calculation Logic
```python
def calculate_app_ports(user_id, app_id):
    """Calculate HTTP and HTTPS ports using deployControlPlan.sh logic with validation"""
    # Load configuration from deploy.ini
    config = load_deploy_config()
    RANGE_START, RANGE_RESERVED, RANGE_PORTS_PER_APPLICATION = config
    
    # Validate inputs
    if not isinstance(user_id, int) or user_id < 1:
        raise ValueError("Invalid user_id")
    if not isinstance(app_id, int) or app_id < 1:
        raise ValueError("Invalid app_id")
    
    PORT_RANGE_BEGIN = RANGE_START + user_id * RANGE_RESERVED
    HTTP_PORT = PORT_RANGE_BEGIN + app_id * RANGE_PORTS_PER_APPLICATION
    HTTPS_PORT = HTTP_PORT + 1
    HTTP_PORT2 = HTTPS_PORT + 1
    HTTPS_PORT2 = HTTP_PORT2 + 1
    
    # Validate port ranges
    if HTTP_PORT > 65535 or HTTPS_PORT2 > 65535:
        raise ValueError("Port allocation exceeds valid range")
    
    return HTTP_PORT, HTTPS_PORT, HTTP_PORT2, HTTPS_PORT2
```

#### 💳 Enhanced Billing Activity Recording
```python
def record_billing_activity(user_id, application_name, action, server_id=None):
    """Record comprehensive billing activity for cost tracking"""
    logger = logging.getLogger('billing_activities')
    
    try:
        logger.info(f"Recording billing activity: user_id={user_id}, app={application_name}, action={action}")
        
        # Get application ID with validation
        app_result = db_manager.execute_query(
            'SELECT id FROM applications WHERE name = ?', 
            (application_name,), fetch_one=True
        )
        if not app_result:
            logger.error(f"Application not found: {application_name}")
            return False
        
        application_id = app_result[0]
        
        if action.upper() == 'START':
            # Record start activity with server information
            activity_id = db_manager.execute_query('''
                INSERT INTO billing_activities 
                (user_id, application_id, action, started_at, server_id)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?)
            ''', (user_id, application_id, action.upper(), server_id))
            
            logger.info(f"START activity recorded with ID: {activity_id}")
            return True
        
        elif action.upper() == 'STOP':
            # Find the most recent start activity
            start_activity = db_manager.execute_query('''
                SELECT id, started_at, server_id FROM billing_activities
                WHERE user_id = ? AND application_id = ? 
                AND action = 'START' AND stopped_at IS NULL
                ORDER BY created_at DESC LIMIT 1
            ''', (user_id, application_id), fetch_one=True)
            
            if start_activity:
                start_id, started_at, activity_server_id = start_activity
                
                # Calculate duration and cost
                start_time = datetime.fromisoformat(started_at)
                stop_time = datetime.now()
                duration_seconds = int((stop_time - start_time).total_seconds())
                
                # Get cost per day with fallback
                cost_result = db_manager.execute_query(
                    'SELECT cost_per_day FROM application_costs WHERE application_id = ?',
                    (application_id,), fetch_one=True
                )
                cost_per_day = cost_result[0] if cost_result else 1.0
                
                # Calculate prorated cost (cost per day / 86400 seconds * duration)
                cost_amount = (cost_per_day / 86400) * duration_seconds
                
                # Update the start activity with stop information
                db_manager.execute_query('''
                    UPDATE billing_activities 
                    SET stopped_at = CURRENT_TIMESTAMP,
                        duration_seconds = ?,
                        cost_amount = ?
                    WHERE id = ?
                ''', (duration_seconds, cost_amount, start_id))
                
                logger.info(f"STOP activity recorded: duration={duration_seconds}s, cost=${cost_amount:.4f}")
                return True
            else:
                logger.warning(f"No matching START activity found for STOP: {application_name}")
                return False
        
        else:
            logger.warning(f"Unknown billing action: {action}")
            return False
            
    except Exception as e:
        logger.error(f"Error recording billing activity: {str(e)}")
        return False
```

### 🔍 Health Monitoring

#### 📊 Comprehensive Database Health Check
```python
def check_database_health():
    """Comprehensive database health check with detailed metrics"""
    health_status = {
        'status': 'healthy',
        'checks': {},
        'metrics': {},
        'timestamp': datetime.now().isoformat(),
        'version': '2.0'
    }
    
    try:
        start_time = time.time()
        
        # Basic connectivity test
        db_manager.execute_query('SELECT 1', fetch_one=True)
        health_status['checks']['connectivity'] = 'OK'
        health_status['metrics']['connectivity_time_ms'] = round((time.time() - start_time) * 1000, 2)
        
        # Check WAL mode
        wal_mode = db_manager.execute_query('PRAGMA journal_mode', fetch_one=True)
        health_status['checks']['wal_mode'] = wal_mode[0] if wal_mode else 'UNKNOWN'
        
        # Check foreign keys
        fk_status = db_manager.execute_query('PRAGMA foreign_keys', fetch_one=True)
        health_status['checks']['foreign_keys'] = 'ON' if fk_status and fk_status[0] else 'OFF'
        
        # Database file information
        if os.path.exists(DB_PATH):
            db_size = os.path.getsize(DB_PATH)
            health_status['metrics']['database_size_mb'] = round(db_size / (1024 * 1024), 2)
            
            # WAL file size
            wal_path = DB_PATH + '-wal'
            if os.path.exists(wal_path):
                wal_size = os.path.getsize(wal_path)
                health_status['metrics']['wal_size_mb'] = round(wal_size / (1024 * 1024), 2)
        
        # Cache statistics
        cache_stats = db_manager.execute_query('PRAGMA cache_size', fetch_one=True)
        health_status['metrics']['cache_size'] = cache_stats[0] if cache_stats else 0
        
        # Page statistics
        page_count = db_manager.execute_query('PRAGMA page_count', fetch_one=True)
        page_size = db_manager.execute_query('PRAGMA page_size', fetch_one=True)
        if page_count and page_size:
            health_status['metrics']['total_pages'] = page_count[0]
            health_status['metrics']['page_size_bytes'] = page_size[0]
        
        # Table counts and health
        tables = [
            'users', 'applications', 'user_applications', 'deployments', 
            'servers', 'billing_activities', 'auth_tokens', 'users_logs',
            'application_costs', 'payment_modes', 'invoicing'
        ]
        
        for table in tables:
            try:
                count = db_manager.execute_query(f'SELECT COUNT(*) FROM {table}', fetch_one=True)
                health_status['checks'][f'{table}_count'] = count[0] if count else 0
                
                # Check for recent activity (last 24 hours)
                if table in ['billing_activities', 'users_logs', 'deployments']:
                    recent = db_manager.execute_query(
                        f'SELECT COUNT(*) FROM {table} WHERE created_at > datetime("now", "-1 day")',
                        fetch_one=True
                    )
                    health_status['metrics'][f'{table}_recent_24h'] = recent[0] if recent else 0
                    
            except Exception as e:
                health_status['checks'][f'{table}_error'] = str(e)
        
        # Performance metrics
        health_status['metrics']['total_check_time_ms'] = round((time.time() - start_time) * 1000, 2)
        
        # Determine overall health
        error_count = sum(1 for key in health_status['checks'] if 'error' in key)
        if error_count > 0:
            health_status['status'] = 'degraded'
        
        if health_status['checks'].get('connectivity') != 'OK':
            health_status['status'] = 'unhealthy'
            
    except Exception as e:
        health_status['status'] = 'unhealthy'
        health_status['error'] = str(e)
        health_status['checks']['connectivity'] = 'FAILED'
    
    return health_status
```

#### 📈 Enhanced Database Statistics
```python
def get_database_stats():
    """Get comprehensive database statistics with performance metrics"""
    stats = {
        'timestamp': datetime.now().isoformat(),
        'version': '2.0'
    }
    
    try:
        # User statistics with activity metrics
        stats['users'] = {
            'total': db_manager.execute_query('SELECT COUNT(*) FROM users', fetch_one=True)[0],
            'active': db_manager.execute_query('SELECT COUNT(*) FROM users WHERE suspended = 0', fetch_one=True)[0],
            'suspended': db_manager.execute_query('SELECT COUNT(*) FROM users WHERE suspended = 1', fetch_one=True)[0],
            'registered_today': db_manager.execute_query(
                'SELECT COUNT(*) FROM users WHERE DATE(created_at) = DATE("now")', fetch_one=True
            )[0],
            'active_last_7_days': db_manager.execute_query(
                'SELECT COUNT(DISTINCT user_id) FROM users_logs WHERE datetime > datetime("now", "-7 days")', 
                fetch_one=True
            )[0]
        }
        
        # Application statistics with usage metrics
        stats['applications'] = {
            'total': db_manager.execute_query('SELECT COUNT(*) FROM applications', fetch_one=True)[0],
            'with_git_url': db_manager.execute_query(
                'SELECT COUNT(*) FROM applications WHERE git_url IS NOT NULL', fetch_one=True
            )[0],
            'deployed_today': db_manager.execute_query(
                'SELECT COUNT(DISTINCT application_name) FROM deployments WHERE DATE(created_at) = DATE("now")', 
                fetch_one=True
            )[0]
        }
        
        # Deployment statistics with status breakdown
        deployment_stats = db_manager.execute_query('''
            SELECT status, COUNT(*) FROM deployments 
            GROUP BY status
        ''', fetch_all=True)
        
        stats['deployments'] = {
            'total': db_manager.execute_query('SELECT COUNT(*) FROM deployments', fetch_one=True)[0],
            'by_status': {status: count for status, count in deployment_stats},
            'today': db_manager.execute_query(
                'SELECT COUNT(*) FROM deployments WHERE DATE(created_at) = DATE("now")', fetch_one=True
            )[0],
            'last_7_days': db_manager.execute_query(
                'SELECT COUNT(*) FROM deployments WHERE created_at > datetime("now", "-7 days")', fetch_one=True
            )[0]
        }
        
        # Server statistics with capacity metrics
        server_stats = db_manager.execute_query('''
            SELECT SERVER_STATUS, COUNT(*), 
                   AVG(SERVER_CAPACITY_USER_MAX), AVG(SERVER_CAPACITY_APPLI_MAX)
            FROM servers GROUP BY SERVER_STATUS
        ''', fetch_all=True)
        
        stats['servers'] = {
            'total': db_manager.execute_query('SELECT COUNT(*) FROM servers', fetch_one=True)[0],
            'by_status': {status: {'count': count, 'avg_user_capacity': round(avg_user, 2), 'avg_app_capacity': round(avg_app, 2)} 
                         for status, count, avg_user, avg_app in server_stats}
        }
        
        # Billing statistics with revenue metrics
        billing_stats = db_manager.execute_query('''
            SELECT 
                COUNT(*) as total_activities,
                COALESCE(SUM(cost_amount), 0) as total_revenue,
                COUNT(CASE WHEN action = 'START' THEN 1 END) as start_actions,
                COUNT(CASE WHEN action = 'STOP' THEN 1 END) as stop_actions,
                AVG(duration_seconds) as avg_duration_seconds
            FROM billing_activities 
            WHERE cost_amount IS NOT NULL
        ''', fetch_one=True)
        
        if billing_stats:
            stats['billing'] = {
                'total_activities': billing_stats[0],
                'total_revenue': round(billing_stats[1], 2),
                'start_actions': billing_stats[2],
                'stop_actions': billing_stats[3],
                'avg_duration_minutes': round(billing_stats[4] / 60, 2) if billing_stats[4] else 0
            }
        
        # Monthly revenue trend
        monthly_revenue = db_manager.execute_query('''
            SELECT strftime('%Y-%m', created_at) as month, 
                   COALESCE(SUM(cost_amount), 0) as revenue
            FROM billing_activities 
            WHERE cost_amount IS NOT NULL 
            AND created_at > datetime('now', '-12 months')
            GROUP BY strftime('%Y-%m', created_at)
            ORDER BY month DESC
            LIMIT 12
        ''', fetch_all=True)
        
        stats['billing']['monthly_revenue'] = [
            {'month': month, 'revenue': round(revenue, 2)} 
            for month, revenue in monthly_revenue
        ]
        
        # Invoice statistics
        invoice_stats = db_manager.execute_query('''
            SELECT status, COUNT(*), COALESCE(SUM(total_amount), 0)
            FROM invoicing GROUP BY status
        ''', fetch_all=True)
        
        stats['invoicing'] = {
            'by_status': {status: {'count': count, 'total_amount': round(amount, 2)} 
                         for status, count, amount in invoice_stats}
        }
        
    except Exception as e:
        stats['error'] = str(e)
    
    return stats
```

### 🔄 Backup & Recovery

#### 💾 Enhanced Automated Backup System
```bash
#!/bin/bash
# Enhanced backup script with compression and validation

BACKUP_DIR="./softfluid/db/backup"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_PATH="${BACKUP_DIR}/${TIMESTAMP}"
DB_FILE="./softfluid/db/ai_swautomorph.db"

# Create backup directory
mkdir -p "${BACKUP_PATH}"

# Database backup with validation
if [ -f "${DB_FILE}" ]; then
    echo "Starting database backup at $(date)"
    
    # Create SQLite dump
    sqlite3 "${DB_FILE}" ".backup ${BACKUP_PATH}/ai_swautomorph.db.backup"
    
    # Create SQL dump
    sqlite3 "${DB_FILE}" ".dump" > "${BACKUP_PATH}/complete_database.sql"
    
    # Create compressed backup
    tar -czf "${BACKUP_PATH}/backup.tar.gz" -C "${BACKUP_DIR}" "${TIMESTAMP}"
    
    # Validate backup integrity
    sqlite3 "${BACKUP_PATH}/ai_swautomorph.db.backup" "PRAGMA integrity_check;" > "${BACKUP_PATH}/integrity_check.log"
    
    # Generate backup manifest
    cat > "${BACKUP_PATH}/manifest.json" << EOF
{
    "timestamp": "${TIMESTAMP}",
    "source_db": "${DB_FILE}",
    "backup_size": $(stat -f%z "${BACKUP_PATH}/ai_swautomorph.db.backup" 2>/dev/null || stat -c%s "${BACKUP_PATH}/ai_swautomorph.db.backup"),
    "sql_dump_size": $(stat -f%z "${BACKUP_PATH}/complete_database.sql" 2>/dev/null || stat -c%s "${BACKUP_PATH}/complete_database.sql"),
    "integrity_check": "$(tail -1 ${BACKUP_PATH}/integrity_check.log)"
}
EOF
    
    # Sync to S3 with retry
    for i in {1..3}; do
        if aws s3 sync ./softfluid s3://softfluid --profile OVH-SWAUTOMORPH; then
            echo "S3 sync successful on attempt $i"
            break
        else
            echo "S3 sync failed on attempt $i, retrying..."
            sleep 5
        fi
    done
    
    # Cleanup old backups (keep last 30 days)
    find "${BACKUP_DIR}" -type d -name "20*" -mtime +30 -exec rm -rf {} \;
    
    echo "Backup completed successfully at $(date)"
else
    echo "Database file not found: ${DB_FILE}"
    exit 1
fi
```

#### 🔄 Enhanced Recovery Process
```python
def recover_database(backup_date, validate=True):
    """Enhanced database recovery with validation and rollback capability"""
    backup_dir = f"./softfluid/db/backup/{backup_date}"
    
    if not os.path.exists(backup_dir):
        raise FileNotFoundError(f"Backup directory {backup_dir} not found")
    
    # Load backup manifest
    manifest_path = os.path.join(backup_dir, 'manifest.json')
    if os.path.exists(manifest_path):
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        print(f"Backup manifest: {manifest}")
    
    # Create recovery point
    current_db = "softfluid/db/ai_swautomorph.db"
    if os.path.exists(current_db):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        recovery_backup = f"softfluid/db/ai_swautomorph.db.pre-recovery.{timestamp}"
        shutil.copy2(current_db, recovery_backup)
        print(f"Current database backed up to: {recovery_backup}")
    
    # Restore from backup
    backup_file = os.path.join(backup_dir, "ai_swautomorph.db.backup")
    sql_dump = os.path.join(backup_dir, "complete_database.sql")
    
    try:
        if os.path.exists(backup_file):
            # Restore from binary backup
            shutil.copy2(backup_file, current_db)
            print(f"Database restored from: {backup_file}")
        elif os.path.exists(sql_dump):
            # Restore from SQL dump
            if os.path.exists(current_db):
                os.remove(current_db)
            
            subprocess.run([
                "sqlite3", current_db, f".read {sql_dump}"
            ], check=True)
            print(f"Database restored from SQL dump: {sql_dump}")
        else:
            raise FileNotFoundError("No valid backup files found")
        
        # Validate restored database
        if validate:
            print("Validating restored database...")
            health_status = check_database_health()
            if health_status['status'] != 'healthy':
                raise Exception(f"Database validation failed: {health_status}")
            print("Database validation successful")
        
        print("Database recovery completed successfully")
        return True
        
    except Exception as e:
        print(f"Recovery failed: {str(e)}")
        # Attempt to restore from recovery backup
        if 'recovery_backup' in locals() and os.path.exists(recovery_backup):
            shutil.copy2(recovery_backup, current_db)
            print("Restored from recovery backup")
        raise
```

### 🛡️ Security Enhancements

#### 🔒 Input Validation and Sanitization
```python
def validate_and_sanitize_input(input_value, input_type, max_length=None):
    """Comprehensive input validation and sanitization"""
    if input_value is None:
        return None
    
    # Convert to string for processing
    value = str(input_value).strip()
    
    if input_type == 'username':
        # Username: alphanumeric, underscore, hyphen only
        if not re.match(r'^[a-zA-Z0-9_-]+$', value):
            raise ValueError("Username contains invalid characters")
        if len(value) < 3 or len(value) > 50:
            raise ValueError("Username must be 3-50 characters")
    
    elif input_type == 'email':
        # Email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, value):
            raise ValueError("Invalid email format")
    
    elif input_type == 'path':
        # Path validation - prevent directory traversal
        if '..' in value or value.startswith('/'):
            raise ValueError("Invalid path - directory traversal detected")
        value = os.path.normpath(value)
    
    elif input_type == 'sql_identifier':
        # SQL identifier (table/column names)
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', value):
            raise ValueError("Invalid SQL identifier")
    
    # Length validation
    if max_length and len(value) > max_length:
        raise ValueError(f"Input exceeds maximum length of {max_length}")
    
    # XSS prevention
    value = html.escape(value)
    
    return value
```

#### 🔍 SQL Injection Prevention
```python
def execute_safe_query(query_template, params, allowed_tables=None):
    """Execute query with comprehensive SQL injection prevention"""
    
    # Validate query template
    if not isinstance(query_template, str):
        raise ValueError("Query template must be a string")
    
    # Check for dangerous SQL keywords
    dangerous_keywords = [
        'DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE', 'EXEC', 'EXECUTE'
    ]
    
    query_upper = query_template.upper()
    for keyword in dangerous_keywords:
        if keyword in query_upper and not query_upper.startswith('CREATE INDEX'):
            raise ValueError(f"Dangerous SQL keyword detected: {keyword}")
    
    # Validate table names if provided
    if allowed_tables:
        for table in allowed_tables:
            if table not in ALLOWED_TABLES:
                raise ValueError(f"Table not allowed: {table}")
    
    # Validate parameters
    if params:
        validated_params = []
        for param in params:
            if isinstance(param, str):
                # Prevent SQL injection in string parameters
                if "'" in param or '"' in param or ';' in param:
                    param = param.replace("'", "''")  # Escape single quotes
                validated_params.append(param)
            else:
                validated_params.append(param)
        params = validated_params
    
    return db_manager.execute_query(query_template, params)
```

---

## Français

<div class="center">
🚀 **Architecture de Base de Données Améliorée pour AI-SwAutoMorph** 📊
</div>

### 📋 Table des Matières
- [🌟 Aperçu](#aperçu)
- [🏗️ Schéma de Base de Données](#schéma-de-base-de-données)
- [🔧 Opérations Thread-Safe](#opérations-thread-safe)
- [📊 Optimisations de Performance](#optimisations-de-performance)
- [💰 Système de Facturation](#système-de-facturation)
- [🔍 Surveillance de Santé](#surveillance-de-santé)
- [🔄 Sauvegarde et Récupération](#sauvegarde-et-récupération)
- [🛡️ Améliorations de Sécurité](#améliorations-de-sécurité)

### 🌟 Aperçu

La base de données AI-SwAutoMorph a été considérablement améliorée avec des opérations thread-safe, le mode WAL, la mise en pool de connexions et un suivi de facturation complet. Le système prend maintenant en charge les déploiements multi-serveurs avec gestion automatique de capacité, surveillance de santé en temps réel et fonctionnalités de sécurité avancées.

#### 🎯 Améliorations Clés
- **🧵 Opérations Thread-Safe** : Mise en pool de connexions avec stockage thread-local et pattern singleton
- **⚡ Mode WAL** : Write-Ahead Logging pour une meilleure concurrence et performance
- **🔄 Retry Automatique** : Backoff exponentiel pour les verrous de base de données avec jitter
- **📊 Surveillance de Santé** : Statistiques de base de données en temps réel et vérifications de santé complètes
- **💰 Intégration Facturation** : Suivi complet des coûts, journalisation d'activité et génération de factures
- **🖥️ Support Multi-Serveurs** : Gestion de capacité serveur, allocation et équilibrage de charge
- **🔐 Sécurité Renforcée** : Validation d'entrée, prévention d'injection SQL et journalisation d'audit
- **📈 Optimisation de Performance** : Index de base de données, optimisation de requêtes et mise en pool de connexions

### 🏗️ Schéma de Base de Données

Le schéma de base de données comprend des tables principales pour les utilisateurs, applications, déploiements, serveurs, et un système complet de facturation avec suivi des activités, modes de paiement, et facturation automatisée.

### 🔧 Opérations Thread-Safe

Le gestionnaire de base de données utilise un pattern singleton avec stockage thread-local et mise en pool de connexions pour assurer la sécurité des threads et des performances optimales.

### 📊 Optimisations de Performance

Le système utilise le mode WAL, des index complets, la mise en pool de connexions, et des mécanismes de retry automatique pour assurer des performances optimales même sous charge élevée.

### 💰 Système de Facturation

Le système de facturation enregistre automatiquement les activités START/STOP, calcule les durées et coûts avec précision à la minute, et supporte plusieurs modes de paiement avec facturation mensuelle automatisée.

### 🔍 Surveillance de Santé

La surveillance inclut des vérifications complètes de connectivité, statut WAL, contraintes de clés étrangères, taille de base de données, métriques de performance, et statistiques détaillées par table.

### 🔄 Sauvegarde et Récupération

Le système effectue des sauvegardes automatiques améliorées avec compression, validation d'intégrité, manifestes de sauvegarde, et synchronisation S3 avec retry. La récupération inclut la validation et les points de récupération.

### 🛡️ Améliorations de Sécurité

Les améliorations de sécurité incluent la validation et sanitisation complète des entrées, la prévention d'injection SQL, la protection contre la traversée de chemin, et la journalisation d'audit complète pour toutes les opérations.