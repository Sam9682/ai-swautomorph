"""Database initialization and management"""
import sqlite3
import threading
import time
import os
import configparser
from contextlib import contextmanager
from werkzeug.security import generate_password_hash
from .config import DB_PATH

# Load deploy.ini configuration
def load_deploy_config():
    """Load configuration from deploy.ini file"""
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'conf', 'deploy.ini')
    
    # Default values
    NAME_OF_APPLICATION = "ai-swautomorph"
    APPLICATION_IDENTITY_NUMBER = 0
    RANGE_START = 6000
    RANGE_RESERVED = 10
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                content = f.read()
            
            # Parse key=value pairs
            for line in content.split('\n'):
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"')
                    
                    if key == 'NAME_OF_APPLICATION':
                        NAME_OF_APPLICATION = value
                    elif key == 'APPLICATION_IDENTITY_NUMBER':
                        APPLICATION_IDENTITY_NUMBER = int(value)
                    elif key == 'RANGE_START':
                        RANGE_START = int(value)
                    elif key == 'RANGE_RESERVED':
                        RANGE_RESERVED = int(value)
        except Exception as e:
            print(f"Warning: Could not load deploy.ini: {e}")
    
    return NAME_OF_APPLICATION, APPLICATION_IDENTITY_NUMBER, RANGE_START, RANGE_RESERVED

# Load configuration values
NAME_OF_APPLICATION, APPLICATION_IDENTITY_NUMBER, RANGE_START, RANGE_RESERVED = load_deploy_config()

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
            # Don't close the connection, keep it for reuse
            pass
    
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
    
    def execute_many(self, query, params_list):
        """Execute multiple queries in a single transaction"""
        max_retries = 3
        retry_delay = 0.1
        
        for attempt in range(max_retries):
            try:
                with self.get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.executemany(query, params_list)
                    conn.commit()
                    return cursor.rowcount
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    time.sleep(retry_delay * (2 ** attempt))
                    continue
                raise

# Global database manager instance
db_manager = DatabaseManager()

def init_db():
    """Initialize database with required tables"""
    with db_manager.get_db_connection() as conn:
        cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            first_name TEXT,
            last_name TEXT,
            suspended INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Applications table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            git_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Authentication tokens table for SSO
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS auth_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token_hash TEXT UNIQUE NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # User application assignments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            application_id INTEGER NOT NULL,
            url TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (application_id) REFERENCES applications (id),
            UNIQUE(user_id, application_id)
        )
    ''')
    
    # Deployments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS deployments (
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
        )
    ''')
    
    # Servers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS servers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            SERVER_IP TEXT UNIQUE NOT NULL,
            SERVER_NAME TEXT NOT NULL,
            SERVER_CAPACITY_USER_MAX INTEGER NOT NULL,
            SERVER_CAPACITY_APPLI_MAX INTEGER NOT NULL,
            SERVER_STATUS TEXT DEFAULT 'STAND_BY',
            SERVER_TYPE TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Application costs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS application_costs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id INTEGER NOT NULL,
            cost_per_day REAL DEFAULT 1.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (application_id) REFERENCES applications (id)
        )
    ''')
    
    # Billing activities table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS billing_activities (
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
        )
    ''')
    
    # Insert default applications if none exist
    cursor.execute('SELECT COUNT(*) FROM applications')
    if cursor.fetchone()[0] == 0:
        # Port calculation constants
        
        default_apps = [
            ('ai-foodflow', 'Food management system', 'git@github.com:Sam9682/ai-foodflow.git'),
            ('ai-haccp', 'HACCP compliance system', 'git@github.com:Sam9682/ai-haccp.git'),
            ('ai-checkinatwork', 'Check In for employees at work', 'git@github.com:Sam9682/ai-checkinatwork.git'),
            ('ai-staticwebsite', 'Simple static Web Site', 'git@github.com:Sam9682/ai-staticwebsite.git'),
            ('ai-transats', 'Transat Beach Management', 'git@github.com:Sam9682/ai-transats.git'),
            ('ai-beewoo', 'Simple Traffic Analyzer Web Site', 'git@github.com:Sam9682/ai-beewoo.git')
        ]
        cursor.executemany('INSERT INTO applications (name, description, git_url) VALUES (?, ?, ?)', default_apps)
        
        # Insert default costs for applications
        cursor.execute('SELECT id FROM applications')
        app_ids = cursor.fetchall()
        for app_id in app_ids:
            cursor.execute('INSERT INTO application_costs (application_id, cost_per_day) VALUES (?, ?)', (app_id[0], 1.0))
    
    # Insert current server if none exists
    cursor.execute('SELECT COUNT(*) FROM servers')
    if cursor.fetchone()[0] == 0:
        import socket
        try:
            # Get current server IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            current_ip = s.getsockname()[0]
            s.close()
        except:
            current_ip = "127.0.0.1"
        
        cursor.execute('''
            INSERT INTO servers (SERVER_IP, SERVER_NAME, SERVER_CAPACITY_USER_MAX, SERVER_CAPACITY_APPLI_MAX, SERVER_STATUS, SERVER_TYPE)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (current_ip, 'main-server', 10, 50, 'STAND_BY', 'primary'))
    
    # Create default admin user if none exists
    cursor.execute('SELECT COUNT(*) FROM users WHERE username = ?', ('admin',))
    if cursor.fetchone()[0] == 0:
        admin_password_hash = generate_password_hash('password')
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, first_name, last_name, suspended)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ('admin', 'admin@swautomorph.com', admin_password_hash, 'System', 'Administrator', 0))
        
        # Get admin user ID and assign all applications with URLs
        admin_id = cursor.lastrowid
        cursor.execute('SELECT id, name FROM applications')
        apps = cursor.fetchall()
        for app in apps:
            app_id, app_name = app[0], app[1]
            # Calculate URL based on admin user_id (1) and app
            base_port = RANGE_START + (admin_id * 10)
            url = f'https://www.swautomorph.com:{base_port + (app_id * 2) + 1}'
            cursor.execute('INSERT INTO user_applications (user_id, application_id, url) VALUES (?, ?, ?)', (admin_id, app_id, url))
        
        # Ensure costs exist for all applications
        cursor.execute('SELECT id FROM applications')
        app_ids = cursor.fetchall()
        for app_id in app_ids:
            cursor.execute('SELECT COUNT(*) FROM application_costs WHERE application_id = ?', (app_id[0],))
            if cursor.fetchone()[0] == 0:
                cursor.execute('INSERT INTO application_costs (application_id, cost_per_day) VALUES (?, ?)', (app_id[0], 1.0))
    
        conn.commit()

def assign_default_apps_to_user(user_id):
    """Assign default applications to a new user"""
    with db_manager.get_db_connection() as conn:
        cursor = conn.cursor()
    
    # Get all applications
    cursor.execute('SELECT id, name FROM applications')
    apps = cursor.fetchall()
    
    # Assign all applications to the user with calculated URLs
    for app in apps:
        app_id, app_name = app[0], app[1]
        # Calculate URL based on user_id and app
        base_port = RANGE_START + (user_id * 10)
        url = f'https://www.swautomorph.com:{base_port + (app_id * 2) + 1}'
        cursor.execute('''
            INSERT OR IGNORE INTO user_applications (user_id, application_id, url) 
            VALUES (?, ?, ?)
        ''', (user_id, app_id, url))
    
        conn.commit()

def assign_app_to_all_users(app_id, app_name):
    """Assign a new application to all existing users"""
    with db_manager.get_db_connection() as conn:
        cursor = conn.cursor()
    
    # Get all user IDs
    cursor.execute('SELECT id FROM users')
    user_ids = cursor.fetchall()
    
    # Assign application to all users with calculated URLs
    for user_id in user_ids:
        uid = user_id[0]
        # Calculate URL based on user_id and app
        base_port = RANGE_START + (uid * 10)
        url = f'https://www.swautomorph.com:{base_port + (app_id * 2) + 1}'
        cursor.execute('''
            INSERT OR IGNORE INTO user_applications (user_id, application_id, url) 
            VALUES (?, ?, ?)
        ''', (uid, app_id, url))
    
        conn.commit()