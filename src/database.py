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
    
    # Add suspended column if it doesn't exist
    cursor.execute("PRAGMA table_info(users)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'suspended' not in columns:
        cursor.execute('ALTER TABLE users ADD COLUMN suspended INTEGER DEFAULT 0')
    
    # Applications table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            description TEXT,
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
    
    # Insert default applications if none exist
    cursor.execute('SELECT COUNT(*) FROM applications')
    if cursor.fetchone()[0] == 0:
        default_apps = [
            ('AI FoodFlow', 'http://ai-foodflow.swautomorph.com:5001', 'Food management system'),
            ('AI HACCP', 'https://ai-haccp.swautomorph.com:8102/', 'HACCP compliance system')
        ]
        cursor.executemany('INSERT INTO applications (name, url, description) VALUES (?, ?, ?)', default_apps)
    
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