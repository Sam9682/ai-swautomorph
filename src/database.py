"""Database initialization and management"""
# import sqlite3  # COMMENTED OUT - Using PostgreSQL now
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
    
    # Default values matching deployControlPlan.sh
    NAME_OF_APPLICATION = "ai-swautomorph"
    APPLICATION_IDENTITY_NUMBER = 0
    RANGE_START = 6000
    RANGE_RESERVED = 100
    RANGE_START_CONTROLPLAN = 80
    RANGE_RESERVED_CONTROLPLAN = 0
    RANGE_PORTS_PER_APPLICATION = 4
    
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
                    elif key == 'RANGE_START_CONTROLPLAN':
                        RANGE_START_CONTROLPLAN = int(value)
                    elif key == 'RANGE_RESERVED_CONTROLPLAN':
                        RANGE_RESERVED_CONTROLPLAN = int(value)
                    elif key == 'RANGE_PORTS_PER_APPLICATION':
                        RANGE_PORTS_PER_APPLICATION = int(value)
        except Exception as e:
            print(f"Warning: Could not load deploy.ini: {e}")
    
    return NAME_OF_APPLICATION, APPLICATION_IDENTITY_NUMBER, RANGE_START, RANGE_RESERVED, RANGE_START_CONTROLPLAN, RANGE_RESERVED_CONTROLPLAN, RANGE_PORTS_PER_APPLICATION

# Load configuration values
NAME_OF_APPLICATION, APPLICATION_IDENTITY_NUMBER, RANGE_START, RANGE_RESERVED, RANGE_START_CONTROLPLAN, RANGE_RESERVED_CONTROLPLAN, RANGE_PORTS_PER_APPLICATION = load_deploy_config()

def calculate_app_ports(user_id, app_id):
    """Calculate HTTP and HTTPS ports using the same logic as deployControlPlan.sh"""
    PORT_RANGE_BEGIN = RANGE_START + user_id * RANGE_RESERVED
    HTTP_PORT = PORT_RANGE_BEGIN + app_id * RANGE_PORTS_PER_APPLICATION
    HTTPS_PORT = HTTP_PORT + 1
    HTTP_PORT2 = HTTPS_PORT + 1
    HTTPS_PORT2 = HTTP_PORT2 + 1
    return HTTP_PORT, HTTPS_PORT, HTTP_PORT2, HTTPS_PORT2

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
            # self._local.connection = sqlite3.connect(
            #     DB_PATH, 
            #     timeout=30.0,  # 30 second timeout
            #     check_same_thread=False
            # )  # COMMENTED OUT - Using PostgreSQL now
            raise NotImplementedError("SQLite3 database is deprecated. Use PostgreSQL database_postgres.py instead.")
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
            # except sqlite3.OperationalError as e:  # COMMENTED OUT - Using PostgreSQL now
            except Exception as e:
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
            # except sqlite3.OperationalError as e:  # COMMENTED OUT - Using PostgreSQL now
            except Exception as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    time.sleep(retry_delay * (2 ** attempt))
                    continue
                raise

# Global database manager instance
db_manager = DatabaseManager()

def init_db():
    """Initialize database with required tables - DEPRECATED: Use database_postgres.py instead"""
    raise NotImplementedError("SQLite3 database is deprecated. Use PostgreSQL database_postgres.py init_db() instead.")
    # COMMENTED OUT - All SQLite3 database initialization code
    # The entire function has been commented out as it's SQLite3 specific
    # Use src/database_postgres.py init_db() function instead

def assign_default_apps_to_user(user_id):
    """Assign default applications to a new user - DEPRECATED: Use database_postgres.py instead"""
    raise NotImplementedError("SQLite3 database is deprecated. Use PostgreSQL database_postgres.py functions instead.")
    # COMMENTED OUT - All SQLite3 database operations

def assign_app_to_all_users(app_id, app_name):
    """Assign a new application to all existing users - DEPRECATED: Use database_postgres.py instead"""
    raise NotImplementedError("SQLite3 database is deprecated. Use PostgreSQL database_postgres.py functions instead.")
    # COMMENTED OUT - All SQLite3 database operations

def get_config_value(key, parent=None, default_value=None):
    """Get configuration value from database - DEPRECATED: Use database_postgres.py instead"""
    raise NotImplementedError("SQLite3 database is deprecated. Use PostgreSQL database_postgres.py functions instead.")
    # COMMENTED OUT - All SQLite3 database operations