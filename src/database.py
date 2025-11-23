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
            SERVER_STATUS TEXT DEFAULT 'active',
            SERVER_TYPE TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert default applications if none exist
    cursor.execute('SELECT COUNT(*) FROM applications')
    if cursor.fetchone()[0] == 0:
        # Port calculation constants
        PORT_RANGE_BEGIN = 6000
        RANGE_RESERVED = 100
        
        default_apps = [
            ('ai-foodflow', 'Food management system', 'git@github.com:Sam9682/ai-foodflow.git'),
            ('ai-haccp', 'HACCP compliance system', 'git@github.com:Sam9682/ai-haccp.git'),
            ('ai-checkinatwork', 'Check In for employees at work', 'git@github.com:Sam9682/ai-checkinatwork.git'),
            ('ai-staticwebsite', 'Simple static Web Site', 'git@github.com:Sam9682/ai-staticwebsite.git')
        ]
        cursor.executemany('INSERT INTO applications (name, description, git_url) VALUES (?, ?, ?)', default_apps)
    
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
        ''', (current_ip, 'main-server', 10, 50, 'active', 'primary'))
    
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
            base_port = 6000 + (admin_id * 10)
            if app_name == 'ai-haccp':
                url = f'https://www.swautomorph.com:{base_port + 201}'
            elif app_name == 'ai-foodflow':
                url = f'https://www.swautomorph.com:{base_port + 101}'
            elif app_name == 'ai-checkinatwork':
                url = f'https://www.swautomorph.com:{base_port + 301}'
            elif app_name == 'ai-staticwebsite':
                url = f'https://www.swautomorph.com:{base_port + 401}'
            else:
                url = f'https://www.swautomorph.com:{base_port}'
            cursor.execute('INSERT INTO user_applications (user_id, application_id, url) VALUES (?, ?, ?)', (admin_id, app_id, url))
    
    conn.commit()
    conn.close()

def assign_default_apps_to_user(user_id):
    """Assign default applications to a new user"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get all applications
    cursor.execute('SELECT id, name FROM applications')
    apps = cursor.fetchall()
    
    # Assign all applications to the user with calculated URLs
    for app in apps:
        app_id, app_name = app[0], app[1]
        # Calculate URL based on user_id and app
        base_port = 6000 + (user_id * 10)
        if app_name == 'ai-haccp':
            url = f'https://www.swautomorph.com:{base_port + 201}'
        elif app_name == 'ai-foodflow':
            url = f'https://www.swautomorph.com:{base_port + 101}'
        elif app_name == 'ai-checkinatwork':
            url = f'https://www.swautomorph.com:{base_port + 301}'
        elif app_name == 'ai-staticwebsite':
            url = f'https://www.swautomorph.com:{base_port + 401}'
        else:
            url = f'https://www.swautomorph.com:{base_port}'
        cursor.execute('''
            INSERT OR IGNORE INTO user_applications (user_id, application_id, url) 
            VALUES (?, ?, ?)
        ''', (user_id, app_id, url))
    
    conn.commit()
    conn.close()

def assign_app_to_all_users(app_id, app_name):
    """Assign a new application to all existing users"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get all user IDs
    cursor.execute('SELECT id FROM users')
    user_ids = cursor.fetchall()
    
    # Assign application to all users with calculated URLs
    for user_id in user_ids:
        uid = user_id[0]
        # Calculate URL based on user_id and app
        base_port = 6000 + (uid * 10)
        if app_name == 'ai-haccp':
            url = f'https://www.swautomorph.com:{base_port + 201}'
        elif app_name == 'ai-foodflow':
            url = f'https://www.swautomorph.com:{base_port + 101}'
        elif app_name == 'ai-checkinatwork':
            url = f'https://www.swautomorph.com:{base_port + 301}'
        elif app_name == 'ai-staticwebsite':
            url = f'https://www.swautomorph.com:{base_port + 401}'
        else:
            url = f'https://www.swautomorph.com:{base_port}'
        cursor.execute('''
            INSERT OR IGNORE INTO user_applications (user_id, application_id, url) 
            VALUES (?, ?, ?)
        ''', (uid, app_id, url))
    
    conn.commit()
    conn.close()