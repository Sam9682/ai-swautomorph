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
            ('ai-swautomorph', f'https://www.swautomorph.com:{PORT_RANGE_BEGIN + 1 * RANGE_RESERVED +1}', 'Food management system', 'git@github.com:Sam9682/ai-foodflow.git'),
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
    
    conn.commit()
    conn.close()