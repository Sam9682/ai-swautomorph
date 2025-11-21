"""Database initialization and management"""
import sqlite3
from werkzeug.security import generate_password_hash
from .config import DB_PATH

def init_db():
    """Initialize database with required tables"""
    conn = sqlite3.connect(DB_PATH)
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
            suspended INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Applications table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Insert default applications if none exist
    cursor.execute('SELECT COUNT(*) FROM applications')
    if cursor.fetchone()[0] == 0:
        # Port calculation constants
        PORT_RANGE_BEGIN = 6000
        RANGE_RESERVED = 100
        
        default_apps = [
            ('ai-foodflow', f'https://www.swautomorph.com:{PORT_RANGE_BEGIN + 1 * RANGE_RESERVED +1}', 'Food management system', 'git@github.com:Sam9682/ai-foodflow.git'),
            ('ai-haccp', f'https://www.swautomorph.com:{PORT_RANGE_BEGIN + 2 * RANGE_RESERVED +1}', 'HACCP compliance system', 'git@github.com:Sam9682/ai-haccp.git'),
            ('ai-checkinatwork', f'https://www.swautomorph.com:{PORT_RANGE_BEGIN + 3 * RANGE_RESERVED +1}', 'Check In for employees at work', 'git@github.com:Sam9682/ai-checkinatwork.git'),
            ('ai-staticwebsite', f'https://www.swautomorph.com:{PORT_RANGE_BEGIN + 4 * RANGE_RESERVED +1}', 'Simple static Web Site', 'git@github.com:Sam9682/ai-staticwebsite.git')
        ]
        cursor.executemany('INSERT INTO applications (name, url, description, git_url) VALUES (?, ?, ?, ?)', default_apps)
    
    # Create default admin user if none exists
    cursor.execute('SELECT COUNT(*) FROM users WHERE username = ?', ('admin',))
    if cursor.fetchone()[0] == 0:
        admin_password_hash = generate_password_hash('password')
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, first_name, last_name)
            VALUES (?, ?, ?, ?, ?)
        ''', ('admin', 'admin@swautomorph.com', admin_password_hash, 'System', 'Administrator'))
        
        # Get admin user ID and assign all applications
        admin_id = cursor.lastrowid
        cursor.execute('SELECT id FROM applications')
        app_ids = cursor.fetchall()
        for app_id in app_ids:
            cursor.execute('INSERT INTO user_applications (user_id, application_id) VALUES (?, ?)', (admin_id, app_id[0]))
    
    conn.commit()
    conn.close()

def assign_default_apps_to_user(user_id):
    """Assign default applications to a new user"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get all application IDs
    cursor.execute('SELECT id FROM applications')
    app_ids = cursor.fetchall()
    
    # Assign all applications to the user
    for app_id in app_ids:
        cursor.execute('''
            INSERT OR IGNORE INTO user_applications (user_id, application_id) 
            VALUES (?, ?)
        ''', (user_id, app_id[0]))
    
    conn.commit()
    conn.close()

def assign_app_to_all_users(app_id):
    """Assign a new application to all existing users"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get all user IDs
    cursor.execute('SELECT id FROM users')
    user_ids = cursor.fetchall()
    
    # Assign application to all users
    for user_id in user_ids:
        cursor.execute('''
            INSERT OR IGNORE INTO user_applications (user_id, application_id) 
            VALUES (?, ?)
        ''', (user_id[0], app_id))
    
    conn.commit()
    conn.close()