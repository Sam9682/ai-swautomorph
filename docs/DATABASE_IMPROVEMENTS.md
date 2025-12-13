# Database Architecture and Improvements / Architecture et Améliorations de Base de Données

## English

### Overview

The AI-SwAutoMorph platform uses a comprehensive SQLite database with thread-safe connection management, automatic retry logic, and health monitoring to prevent database lock issues and ensure reliable operation across multiple concurrent users and deployments. The database supports multi-language applications and multi-server deployment architecture.

### Database Schema

#### Core Tables

##### Users Table
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

##### Applications Table
```sql
CREATE TABLE applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    git_url TEXT,                       -- Git repository URL
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

##### User Applications Assignment
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

#### Deployment Management Tables

##### Deployments Table
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

##### Servers Table
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

#### Authentication and Security Tables

##### Authentication Tokens
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

##### User Activity Logs
```sql
CREATE TABLE users_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    username TEXT NOT NULL,
    action TEXT NOT NULL,               -- login, logout, deploy, language_change, etc.
    datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

#### Billing and Cost Management Tables

##### Application Costs
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

##### Billing Activities
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

### Database Improvements

#### 1. Thread-Safe Connection Manager

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

#### 2. Context Manager for Safe Operations

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

#### 3. Automatic Retry Logic

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

#### 4. Multi-Language Session Support

```python
def log_user_action(self, user_id, username, action, language=None):
    """Log user actions including language changes"""
    action_detail = f"{action}"
    if language:
        action_detail = f"{action}_{language}"
    
    self.execute_query(
        'INSERT INTO users_logs (user_id, username, action) VALUES (?, ?, ?)',
        (user_id, username, action_detail)
    )
```

### Port Allocation System

#### Automatic Port Calculation

The platform automatically calculates unique ports for each user and application:

```python
def calculate_app_ports(user_id, app_id):
    """Calculate HTTP and HTTPS ports using deployControlPlan.sh logic"""
    RANGE_START = 8100
    RANGE_RESERVED = 100
    
    PORT_RANGE_BEGIN = RANGE_START + user_id * RANGE_RESERVED
    HTTP_PORT = PORT_RANGE_BEGIN + app_id * 2
    HTTPS_PORT = HTTP_PORT + 1
    return HTTP_PORT, HTTPS_PORT
```

#### URL Generation with Multi-Language Support

```python
def generate_application_url(user_id, app_id, app_name, language='en'):
    """Generate application URL with language context"""
    HTTP_PORT, HTTPS_PORT = calculate_app_ports(user_id, app_id)
    base_url = f'https://www.swautomorph.com:{HTTPS_PORT}'
    
    # Store URL with language context if needed
    return base_url
```

### Database Health Monitoring

#### Health Check Functions

```python
def check_database_health():
    """Comprehensive database health check with language support"""
    return {
        'connection_status': 'healthy|unhealthy',
        'wal_mode': True|False,
        'foreign_keys': True|False,
        'table_count': int,
        'total_size_mb': float,
        'last_vacuum': timestamp,
        'language_support': True,
        'performance_metrics': {
            'avg_query_time': float,
            'concurrent_connections': int,
            'lock_wait_time': float
        }
    }
```

#### Multi-Language Statistics

```python
def get_language_usage_stats():
    """Get statistics on language usage"""
    return {
        'total_users': int,
        'english_users': int,
        'french_users': int,
        'language_switches_today': int,
        'most_popular_language': 'en|fr'
    }
```

### Data Initialization

#### Default Data Setup with Multi-Language

```python
def initialize_default_data():
    """Initialize default applications and admin user"""
    
    # Default applications with bilingual descriptions
    default_apps = [
        ('ai-foodflow', 'Food management system / Système de gestion alimentaire', 
         'git@github.com:Sam9682/ai-foodflow.git'),
        ('ai-haccp', 'HACCP compliance system / Système de conformité HACCP', 
         'git@github.com:Sam9682/ai-haccp.git'),
        ('ai-checkinatwork', 'Employee check-in system / Système de pointage employés', 
         'git@github.com:Sam9682/ai-checkinatwork.git'),
        ('ai-staticwebsite', 'Simple static website / Site web statique simple', 
         'git@github.com:Sam9682/ai-staticwebsite.git'),
        ('ai-transats', 'Beach management system / Système de gestion de plage', 
         'git@github.com:Sam9682/ai-transats.git'),
        ('ai-beewoo', 'Traffic analyzer / Analyseur de trafic', 
         'git@github.com:Sam9682/ai-beewoo.git')
    ]
    
    # Create admin user with default language preference
    admin_password_hash = generate_password_hash('password')
    cursor.execute('''
        INSERT INTO users (username, email, password_hash, first_name, last_name, suspended)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', ('admin', 'admin@swautomorph.com', admin_password_hash, 'System', 'Administrator', 0))
```

### Performance Optimizations

#### Indexes for Multi-Language Support

```sql
-- User lookups with language context
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_created_at ON users(created_at);

-- Application assignments with port information
CREATE INDEX idx_user_applications_user_id ON user_applications(user_id);
CREATE INDEX idx_user_applications_app_id ON user_applications(application_id);
CREATE INDEX idx_user_applications_ports ON user_applications(http_port, https_port);

-- Deployment queries with server allocation
CREATE INDEX idx_deployments_user_id ON deployments(user_id);
CREATE INDEX idx_deployments_app_name ON deployments(application_name);
CREATE INDEX idx_deployments_server_id ON deployments(server_id);
CREATE INDEX idx_deployments_status ON deployments(status);

-- Billing queries with time-based analysis
CREATE INDEX idx_billing_user_id ON billing_activities(user_id);
CREATE INDEX idx_billing_app_id ON billing_activities(application_id);
CREATE INDEX idx_billing_dates ON billing_activities(started_at, stopped_at);

-- User activity logs with action filtering
CREATE INDEX idx_users_logs_user_id ON users_logs(user_id);
CREATE INDEX idx_users_logs_action ON users_logs(action);
CREATE INDEX idx_users_logs_datetime ON users_logs(datetime);
```

---

## Français

### Aperçu

La plateforme AI-SwAutoMorph utilise une base de données SQLite complète avec gestion de connexions thread-safe, logique de retry automatique et surveillance de santé pour prévenir les problèmes de verrouillage de base de données et assurer un fonctionnement fiable avec plusieurs utilisateurs et déploiements simultanés. La base de données supporte les applications multi-langues et l'architecture de déploiement multi-serveurs.

### Schéma de Base de Données

#### Tables Principales

##### Table Users
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT,
    suspended INTEGER DEFAULT 1,        -- 0=actif, 1=suspendu
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

##### Table Applications
```sql
CREATE TABLE applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    git_url TEXT,                       -- URL du dépôt Git
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

##### Attribution Applications Utilisateur
```sql
CREATE TABLE user_applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    application_id INTEGER NOT NULL,
    url TEXT NOT NULL,                  -- URL calculée avec port
    http_port INTEGER,                  -- Port HTTP calculé
    https_port INTEGER,                 -- Port HTTPS calculé
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (application_id) REFERENCES applications (id),
    UNIQUE(user_id, application_id)
);
```

#### Tables de Gestion de Déploiement

##### Table Deployments
```sql
CREATE TABLE deployments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    application_name TEXT NOT NULL,
    status TEXT DEFAULT 'pending',      -- pending, running, cloning, cloned, completed, failed, timeout, error
    deployment_path TEXT,               -- Chemin du répertoire de déploiement local
    git_url TEXT,                       -- URL du dépôt Git
    server_id INTEGER,                  -- Serveur cible pour déploiement
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (server_id) REFERENCES servers (id)
);
```

##### Table Servers
```sql
CREATE TABLE servers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    SERVER_IP TEXT UNIQUE NOT NULL,
    SERVER_NAME TEXT NOT NULL,
    SERVER_CAPACITY_USER_MAX INTEGER NOT NULL,     -- Maximum d'utilisateurs par serveur
    SERVER_CAPACITY_APPLI_MAX INTEGER NOT NULL,    -- Maximum d'applications par serveur
    SERVER_STATUS TEXT DEFAULT 'STAND_BY',         -- STAND_BY, ACTIVE, MAINTENANCE
    SERVER_TYPE TEXT NOT NULL,                     -- primary, secondary, development, production
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Améliorations de Base de Données

#### 1. Gestionnaire de Connexions Thread-Safe

La classe `DatabaseManager` fournit un accès thread-safe à la base de données avec pool de connexions :

```python
class DatabaseManager:
    """Gestionnaire de base de données thread-safe avec pool de connexions"""
    
    def __init__(self):
        self._local = threading.local()
    
    def _get_connection(self):
        """Obtenir une connexion de base de données thread-local"""
        if not hasattr(self._local, 'connection'):
            self._local.connection = sqlite3.connect(
                DB_PATH, 
                timeout=30.0,           # Timeout de 30 secondes
                check_same_thread=False
            )
            # Activer le mode WAL pour une meilleure concurrence
            self._local.connection.execute('PRAGMA journal_mode=WAL')
            # Définir le timeout busy
            self._local.connection.execute('PRAGMA busy_timeout=30000')
            # Activer les clés étrangères
            self._local.connection.execute('PRAGMA foreign_keys=ON')
        return self._local.connection
```

#### 2. Support Multi-Langues pour Sessions

```python
def log_user_action(self, user_id, username, action, language=None):
    """Enregistrer les actions utilisateur incluant les changements de langue"""
    action_detail = f"{action}"
    if language:
        action_detail = f"{action}_{language}"
    
    self.execute_query(
        'INSERT INTO users_logs (user_id, username, action) VALUES (?, ?, ?)',
        (user_id, username, action_detail)
    )
```

### Système d'Allocation de Ports

#### Calcul Automatique de Ports

La plateforme calcule automatiquement des ports uniques pour chaque utilisateur et application :

```python
def calculate_app_ports(user_id, app_id):
    """Calculer les ports HTTP et HTTPS en utilisant la logique deployControlPlan.sh"""
    RANGE_START = 8100
    RANGE_RESERVED = 100
    
    PORT_RANGE_BEGIN = RANGE_START + user_id * RANGE_RESERVED
    HTTP_PORT = PORT_RANGE_BEGIN + app_id * 2
    HTTPS_PORT = HTTP_PORT + 1
    return HTTP_PORT, HTTPS_PORT
```

### Surveillance de Santé de Base de Données

#### Fonctions de Vérification de Santé

```python
def check_database_health():
    """Vérification complète de santé de base de données avec support langue"""
    return {
        'connection_status': 'healthy|unhealthy',
        'wal_mode': True|False,
        'foreign_keys': True|False,
        'table_count': int,
        'total_size_mb': float,
        'last_vacuum': timestamp,
        'language_support': True,
        'performance_metrics': {
            'avg_query_time': float,
            'concurrent_connections': int,
            'lock_wait_time': float
        }
    }
```

#### Statistiques Multi-Langues

```python
def get_language_usage_stats():
    """Obtenir les statistiques d'utilisation des langues"""
    return {
        'total_users': int,
        'english_users': int,
        'french_users': int,
        'language_switches_today': int,
        'most_popular_language': 'en|fr'
    }
```