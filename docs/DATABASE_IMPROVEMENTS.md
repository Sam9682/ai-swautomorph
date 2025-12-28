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

### 🌟 Overview

The AI-SwAutoMorph database has been significantly enhanced with thread-safe operations, WAL mode, connection pooling, and comprehensive billing tracking. The system now supports multi-server deployments with automatic capacity management and real-time health monitoring.

#### 🎯 Key Improvements
- **🧵 Thread-Safe Operations**: Connection pooling with thread-local storage
- **⚡ WAL Mode**: Write-Ahead Logging for better concurrency
- **🔄 Automatic Retry**: Exponential backoff for database locks
- **📊 Health Monitoring**: Real-time database statistics and health checks
- **💰 Billing Integration**: Comprehensive cost tracking and activity logging
- **🖥️ Multi-Server Support**: Server capacity management and allocation
- **🔐 Enhanced Security**: Input validation and SQL injection prevention

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
    suspended INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
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
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (application_id) REFERENCES applications (id),
    UNIQUE(user_id, application_id)
);
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
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (server_id) REFERENCES servers (id)
);
```

##### 🖥️ Servers Table
```sql
CREATE TABLE servers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    SERVER_IP TEXT UNIQUE NOT NULL,
    SERVER_NAME TEXT NOT NULL,
    SERVER_CAPACITY_USER_MAX INTEGER NOT NULL,
    SERVER_CAPACITY_APPLI_MAX INTEGER NOT NULL,
    SERVER_STATUS TEXT DEFAULT 'STAND_BY',
    SERVER_TYPE TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
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
    FOREIGN KEY (application_id) REFERENCES applications (id)
);
```

##### 📊 Billing Activities Table
```sql
CREATE TABLE billing_activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    application_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    started_at TIMESTAMP,
    stopped_at TIMESTAMP,
    duration_seconds INTEGER,
    cost_amount REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (application_id) REFERENCES applications (id)
);
```

##### 💳 Payment Modes Table
```sql
CREATE TABLE payment_modes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    payment_type TEXT NOT NULL,
    bank_account TEXT,
    paypal_email TEXT,
    card_last_four TEXT,
    card_type TEXT,
    is_default INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

##### 🧾 Invoicing Table
```sql
CREATE TABLE invoicing (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    invoice_month TEXT NOT NULL,
    total_amount REAL NOT NULL,
    status TEXT DEFAULT 'unpaid',
    payment_date TIMESTAMP,
    payment_mode_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (payment_mode_id) REFERENCES payment_modes (id)
);
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
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

##### 📝 Users Logs Table
```sql
CREATE TABLE users_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    username TEXT NOT NULL,
    action TEXT NOT NULL,
    datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

### 🔧 Thread-Safe Operations

#### 🧵 Database Manager Class
```python
class DatabaseManager:
    """Thread-safe database manager with connection pooling"""
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
            self._initialized = True
```

#### 🔄 Connection Management
```python
def _get_connection(self):
    """Get thread-local database connection"""
    if not hasattr(self._local, 'connection'):
        self._local.connection = sqlite3.connect(
            DB_PATH, 
            timeout=30.0,  # 30 second timeout
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

#### ⚡ Automatic Retry Mechanism
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

### 📊 Performance Optimizations

#### ⚡ WAL Mode Configuration
```sql
-- Enable Write-Ahead Logging for better concurrency
PRAGMA journal_mode=WAL;

-- Set busy timeout for locked database scenarios
PRAGMA busy_timeout=30000;

-- Enable foreign key constraints
PRAGMA foreign_keys=ON;

-- Optimize cache size
PRAGMA cache_size=10000;

-- Set synchronous mode for performance
PRAGMA synchronous=NORMAL;
```

#### 🔍 Database Indexes
```sql
-- User authentication indexes
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);

-- Application lookup indexes
CREATE INDEX idx_applications_name ON applications(name);
CREATE INDEX idx_user_applications_user_id ON user_applications(user_id);
CREATE INDEX idx_user_applications_app_id ON user_applications(application_id);

-- Deployment tracking indexes
CREATE INDEX idx_deployments_user_id ON deployments(user_id);
CREATE INDEX idx_deployments_app_name ON deployments(application_name);
CREATE INDEX idx_deployments_server_id ON deployments(server_id);
CREATE INDEX idx_deployments_status ON deployments(status);

-- Billing and cost tracking indexes
CREATE INDEX idx_billing_activities_user_id ON billing_activities(user_id);
CREATE INDEX idx_billing_activities_app_id ON billing_activities(application_id);
CREATE INDEX idx_billing_activities_action ON billing_activities(action);
CREATE INDEX idx_billing_activities_created_at ON billing_activities(created_at);

-- Server management indexes
CREATE INDEX idx_servers_status ON servers(SERVER_STATUS);
CREATE INDEX idx_servers_ip ON servers(SERVER_IP);
```

### 💰 Billing System

#### 📊 Cost Calculation Logic
```python
def calculate_app_ports(user_id, app_id):
    """Calculate HTTP and HTTPS ports using deployControlPlan.sh logic"""
    PORT_RANGE_BEGIN = RANGE_START + user_id * RANGE_RESERVED
    HTTP_PORT = PORT_RANGE_BEGIN + app_id * RANGE_PORTS_PER_APPLICATION
    HTTPS_PORT = HTTP_PORT + 1
    HTTP_PORT2 = HTTPS_PORT + 1
    HTTPS_PORT2 = HTTP_PORT2 + 1
    return HTTP_PORT, HTTPS_PORT, HTTP_PORT2, HTTPS_PORT2
```

#### 💳 Billing Activity Recording
```python
def record_billing_activity(user_id, application_name, action):
    """Record billing activity for cost tracking"""
    # Get application ID
    app_data = db_manager.execute_query(
        'SELECT id FROM applications WHERE name = ?', 
        (application_name,), fetch_one=True
    )
    
    if not app_data:
        return
    
    application_id = app_data[0]
    
    if action.upper() == 'START':
        # Record start time
        db_manager.execute_query('''
            INSERT INTO billing_activities (user_id, application_id, action, started_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ''', (user_id, application_id, action.upper()))
    
    elif action.upper() == 'STOP':
        # Calculate duration and cost
        last_start = db_manager.execute_query('''
            SELECT id, started_at FROM billing_activities
            WHERE user_id = ? AND application_id = ? AND action = 'START'
            AND stopped_at IS NULL
            ORDER BY created_at DESC LIMIT 1
        ''', (user_id, application_id), fetch_one=True)
        
        if last_start:
            # Get cost per day
            cost_data = db_manager.execute_query(
                'SELECT cost_per_day FROM application_costs WHERE application_id = ?',
                (application_id,), fetch_one=True
            )
            cost_per_day = cost_data[0] if cost_data else 1.0
            
            # Update billing record with stop time and cost
            db_manager.execute_query('''
                UPDATE billing_activities 
                SET stopped_at = CURRENT_TIMESTAMP,
                    duration_seconds = (julianday(CURRENT_TIMESTAMP) - julianday(started_at)) * 86400,
                    cost_amount = (julianday(CURRENT_TIMESTAMP) - julianday(started_at)) * ?
                WHERE id = ?
            ''', (cost_per_day, last_start[0]))
```

### 🔍 Health Monitoring

#### 📊 Database Health Check
```python
def check_database_health():
    """Comprehensive database health check"""
    health_status = {
        'status': 'healthy',
        'checks': {},
        'timestamp': datetime.now().isoformat()
    }
    
    try:
        # Check database connectivity
        db_manager.execute_query('SELECT 1', fetch_one=True)
        health_status['checks']['connectivity'] = 'OK'
        
        # Check WAL mode
        wal_mode = db_manager.execute_query('PRAGMA journal_mode', fetch_one=True)
        health_status['checks']['wal_mode'] = wal_mode[0] if wal_mode else 'UNKNOWN'
        
        # Check foreign keys
        fk_status = db_manager.execute_query('PRAGMA foreign_keys', fetch_one=True)
        health_status['checks']['foreign_keys'] = 'ON' if fk_status and fk_status[0] else 'OFF'
        
        # Check database size
        db_size = os.path.getsize(DB_PATH) if os.path.exists(DB_PATH) else 0
        health_status['checks']['database_size_mb'] = round(db_size / (1024 * 1024), 2)
        
        # Check table counts
        tables = ['users', 'applications', 'deployments', 'servers', 'billing_activities']
        for table in tables:
            count = db_manager.execute_query(f'SELECT COUNT(*) FROM {table}', fetch_one=True)
            health_status['checks'][f'{table}_count'] = count[0] if count else 0
        
    except Exception as e:
        health_status['status'] = 'unhealthy'
        health_status['error'] = str(e)
    
    return health_status
```

#### 📈 Database Statistics
```python
def get_database_stats():
    """Get detailed database statistics"""
    stats = {}
    
    try:
        # User statistics
        stats['users'] = {
            'total': db_manager.execute_query('SELECT COUNT(*) FROM users', fetch_one=True)[0],
            'active': db_manager.execute_query('SELECT COUNT(*) FROM users WHERE suspended = 0', fetch_one=True)[0],
            'suspended': db_manager.execute_query('SELECT COUNT(*) FROM users WHERE suspended = 1', fetch_one=True)[0]
        }
        
        # Application statistics
        stats['applications'] = {
            'total': db_manager.execute_query('SELECT COUNT(*) FROM applications', fetch_one=True)[0],
            'with_git_url': db_manager.execute_query('SELECT COUNT(*) FROM applications WHERE git_url IS NOT NULL', fetch_one=True)[0]
        }
        
        # Deployment statistics
        stats['deployments'] = {
            'total': db_manager.execute_query('SELECT COUNT(*) FROM deployments', fetch_one=True)[0],
            'running': db_manager.execute_query('SELECT COUNT(*) FROM deployments WHERE status = "running"', fetch_one=True)[0],
            'completed': db_manager.execute_query('SELECT COUNT(*) FROM deployments WHERE status = "completed"', fetch_one=True)[0],
            'failed': db_manager.execute_query('SELECT COUNT(*) FROM deployments WHERE status = "failed"', fetch_one=True)[0]
        }
        
        # Server statistics
        stats['servers'] = {
            'total': db_manager.execute_query('SELECT COUNT(*) FROM servers', fetch_one=True)[0],
            'active': db_manager.execute_query('SELECT COUNT(*) FROM servers WHERE SERVER_STATUS = "ACTIVE"', fetch_one=True)[0],
            'standby': db_manager.execute_query('SELECT COUNT(*) FROM servers WHERE SERVER_STATUS = "STAND_BY"', fetch_one=True)[0]
        }
        
        # Billing statistics
        stats['billing'] = {
            'total_activities': db_manager.execute_query('SELECT COUNT(*) FROM billing_activities', fetch_one=True)[0],
            'total_revenue': db_manager.execute_query('SELECT COALESCE(SUM(cost_amount), 0) FROM billing_activities WHERE cost_amount IS NOT NULL', fetch_one=True)[0]
        }
        
    except Exception as e:
        stats['error'] = str(e)
    
    return stats
```

### 🔄 Backup & Recovery

#### 💾 Automated Backup System
```bash
# Hourly backup cron job
0 * * * * /home/ubuntu/ai-swautomorph/deployControlPlan.sh --backup_db >/dev/null 2>&1
```

#### 📦 Backup Process
```python
def backup_database():
    """Create comprehensive database backup"""
    datetime_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"./softfluid/db/backup/{datetime_str}"
    os.makedirs(backup_dir, exist_ok=True)
    
    db_file = "./softfluid/db/ai_swautomorph.db"
    
    if os.path.exists(db_file):
        # Get all table names
        tables = db_manager.execute_query(".tables", fetch_all=True)
        
        # Dump each table individually
        for table in tables:
            table_name = table[0]
            with open(f"{backup_dir}/{table_name}.sql", 'w') as f:
                # Export table structure and data
                dump_query = f".dump {table_name}"
                result = db_manager.execute_query(dump_query, fetch_all=True)
                f.write(result)
        
        # Create complete database dump
        with open(f"{backup_dir}/complete_database.sql", 'w') as f:
            dump_result = db_manager.execute_query(".dump", fetch_all=True)
            f.write(dump_result)
        
        # Copy database file
        shutil.copy2(db_file, f"{backup_dir}/ai_swautomorph.db.backup")
        
        # Sync to S3
        subprocess.run([
            "aws", "s3", "sync", "./softfluid", "s3://softfluid", 
            "--profile", "OVH-SWAUTOMORPH"
        ])
```

#### 🔄 Recovery Process
```python
def recover_database(backup_date):
    """Recover database from backup"""
    backup_dir = f"./softfluid/db/backup/{backup_date}"
    
    if not os.path.exists(backup_dir):
        raise FileNotFoundError(f"Backup directory {backup_dir} not found")
    
    # Backup current database
    if os.path.exists("softfluid/db/ai_swautomorph.db"):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.move(
            "softfluid/db/ai_swautomorph.db",
            f"softfluid/db/ai_swautomorph.db.pre-recovery.{timestamp}"
        )
    
    # Restore from complete dump
    complete_dump = f"{backup_dir}/complete_database.sql"
    if os.path.exists(complete_dump):
        subprocess.run([
            "sqlite3", "softfluid/db/ai_swautomorph.db", 
            f".read {complete_dump}"
        ])
    else:
        # Restore from backup file
        backup_file = f"{backup_dir}/ai_swautomorph.db.backup"
        if os.path.exists(backup_file):
            shutil.copy2(backup_file, "softfluid/db/ai_swautomorph.db")
        else:
            raise FileNotFoundError("No valid backup files found")
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

### 🌟 Aperçu

La base de données AI-SwAutoMorph a été considérablement améliorée avec des opérations thread-safe, le mode WAL, la mise en pool de connexions et un suivi de facturation complet. Le système prend maintenant en charge les déploiements multi-serveurs avec gestion automatique de capacité et surveillance de santé en temps réel.

#### 🎯 Améliorations Clés
- **🧵 Opérations Thread-Safe** : Mise en pool de connexions avec stockage thread-local
- **⚡ Mode WAL** : Write-Ahead Logging pour une meilleure concurrence
- **🔄 Retry Automatique** : Backoff exponentiel pour les verrous de base de données
- **📊 Surveillance de Santé** : Statistiques de base de données en temps réel et vérifications de santé
- **💰 Intégration Facturation** : Suivi complet des coûts et journalisation d'activité
- **🖥️ Support Multi-Serveurs** : Gestion et allocation de capacité serveur
- **🔐 Sécurité Renforcée** : Validation d'entrée et prévention d'injection SQL

### 🏗️ Schéma de Base de Données

#### 📋 Tables Principales

Les tables principales incluent les utilisateurs, applications, déploiements, serveurs, et un système complet de facturation avec suivi des activités, modes de paiement, et facturation automatisée.

### 🔧 Opérations Thread-Safe

Le gestionnaire de base de données utilise un pattern singleton avec stockage thread-local pour assurer la sécurité des threads et la mise en pool des connexions.

### 📊 Optimisations de Performance

Le système utilise le mode WAL, des index optimisés, et des mécanismes de retry automatique pour assurer des performances optimales même sous charge élevée.

### 💰 Système de Facturation

Le système de facturation enregistre automatiquement les activités START/STOP, calcule les durées et coûts, et supporte plusieurs modes de paiement avec facturation mensuelle automatisée.

### 🔍 Surveillance de Santé

La surveillance inclut des vérifications de connectivité, statut WAL, contraintes de clés étrangères, taille de base de données, et statistiques détaillées par table.

### 🔄 Sauvegarde et Récupération

Le système effectue des sauvegardes automatiques toutes les heures avec synchronisation S3, et fournit des outils de récupération avec sélection interactive de la date de sauvegarde.