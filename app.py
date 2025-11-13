#!/usr/bin/env python3
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from datetime import datetime, timedelta
import json
import secrets
import hashlib

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

DB_PATH = 'ai_swautomorph.db'

# Language translations
TRANSLATIONS = {
    'en': {
        'login': 'Login',
        'register': 'Register',
        'username': 'Username',
        'email': 'Email',
        'password': 'Password',
        'first_name': 'First Name',
        'last_name': 'Last Name',
        'dashboard': 'Dashboard',
        'logout': 'Logout',
        'welcome': 'Welcome',
        'available_applications': 'Available Applications',
        'add_new_application': 'Add New Application',
        'application_name': 'Application Name',
        'url': 'URL',
        'description': 'Description',
        'add_application': 'Add Application',
        'no_apps': 'No applications available yet.',
        'already_account': 'Already have an account?',
        'no_account': "Don't have an account?",
        'login_here': 'Login here',
        'register_here': 'Register here',
        'open_application': 'Open Application',
        'no_description': 'No description available'
    },
    'fr': {
        'login': 'Connexion',
        'register': 'Inscription',
        'username': "Nom d'utilisateur",
        'email': 'Email',
        'password': 'Mot de passe',
        'first_name': 'Prénom',
        'last_name': 'Nom',
        'dashboard': 'Tableau de bord',
        'logout': 'Déconnexion',
        'welcome': 'Bienvenue',
        'available_applications': 'Applications disponibles',
        'add_new_application': 'Ajouter une nouvelle application',
        'application_name': "Nom de l'application",
        'url': 'URL',
        'description': 'Description',
        'add_application': 'Ajouter une application',
        'no_apps': 'Aucune application disponible pour le moment.',
        'already_account': 'Vous avez déjà un compte ?',
        'no_account': "Vous n'avez pas de compte ?",
        'login_here': 'Connectez-vous ici',
        'register_here': 'Inscrivez-vous ici',
        'open_application': "Ouvrir l'application",
        'no_description': 'Aucune description disponible'
    }
}

def get_language():
    return session.get('language', 'en')

def get_text(key):
    lang = get_language()
    return TRANSLATIONS.get(lang, {}).get(key, TRANSLATIONS['en'].get(key, key))

@app.context_processor
def inject_language():
    return {'get_text': get_text, 'current_lang': get_language()}

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
        from werkzeug.security import generate_password_hash
        admin_password_hash = generate_password_hash('password')
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, first_name, last_name)
            VALUES (?, ?, ?, ?, ?)
        ''', ('admin', 'admin@swautomorph.com', admin_password_hash, 'System', 'Administrator'))
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')
        
        if not all([username, email, password]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        try:
            password_hash = generate_password_hash(password)
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, first_name, last_name)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, email, password_hash, first_name, last_name))
            conn.commit()
            
            if request.is_json:
                return jsonify({'message': 'User registered successfully'}), 201
            return redirect(url_for('index'))
            
        except sqlite3.IntegrityError:
            return jsonify({'error': 'Username or email already exists'}), 409
        finally:
            conn.close()
    
    return render_template('register.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json() if request.is_json else request.form
    username = data.get('username')
    password = data.get('password')
    
    if not all([username, password]):
        return jsonify({'error': 'Missing credentials'}), 400
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, password_hash, suspended FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()
    
    if user and not user[2] and check_password_hash(user[1], password):
        session['user_id'] = user[0]
        
        # Generate SSO token
        token = generate_sso_token(user[0])
        session['sso_token'] = token
        
        if request.is_json:
            return jsonify({'message': 'Login successful', 'sso_token': token}), 200
        return redirect(url_for('dashboard'))
    
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/logout')
def logout():
    # Invalidate SSO token
    if 'sso_token' in session:
        invalidate_sso_token(session['sso_token'])
    
    session.pop('user_id', None)
    session.pop('sso_token', None)
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get username for admin check
    cursor.execute('SELECT username FROM users WHERE id = ?', (session['user_id'],))
    user = cursor.fetchone()
    username = user[0] if user else ''
    
    # Get applications based on user role
    if username == 'admin':
        # Admin sees all applications
        cursor.execute('SELECT id, name, url, description FROM applications ORDER BY name')
    else:
        # Regular users see only assigned applications
        cursor.execute('''
            SELECT a.id, a.name, a.url, a.description 
            FROM applications a
            JOIN user_applications ua ON a.id = ua.application_id
            WHERE ua.user_id = ?
            ORDER BY a.name
        ''', (session['user_id'],))
    
    applications = cursor.fetchall()
    conn.close()
    
    # Get SSO token for the user
    sso_token = session.get('sso_token', '')
    
    return render_template('dashboard.html', applications=applications, username=username, sso_token=sso_token)

@app.route('/api/applications', methods=['GET', 'POST'])
def api_applications():
    if request.method == 'GET':
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, url, description FROM applications ORDER BY name')
        apps = [{'id': row[0], 'name': row[1], 'url': row[2], 'description': row[3]} 
                for row in cursor.fetchall()]
        conn.close()
        return jsonify(apps)
    
    elif request.method == 'POST':
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Check if user is admin
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT username FROM users WHERE id = ?', (session['user_id'],))
        user = cursor.fetchone()
        
        if not user or user[0] != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.get_json()
        name = data.get('name')
        url = data.get('url')
        description = data.get('description', '')
        
        if not all([name, url]):
            return jsonify({'error': 'Name and URL required'}), 400
        
        cursor.execute('INSERT INTO applications (name, url, description) VALUES (?, ?, ?)',
                      (name, url, description))
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Application added successfully'}), 201

@app.route('/api/applications/<int:app_id>', methods=['PUT', 'DELETE'])
def api_application_actions(app_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    # Check if user is admin
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT username FROM users WHERE id = ?', (session['user_id'],))
    user = cursor.fetchone()
    
    if not user or user[0] != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    if request.method == 'PUT':
        data = request.get_json()
        name = data.get('name')
        url = data.get('url')
        description = data.get('description', '')
        
        if not all([name, url]):
            return jsonify({'error': 'Name and URL required'}), 400
        
        cursor.execute('''
            UPDATE applications SET name = ?, url = ?, description = ?
            WHERE id = ?
        ''', (name, url, description, app_id))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Application updated successfully'})
    
    elif request.method == 'DELETE':
        cursor.execute('DELETE FROM applications WHERE id = ?', (app_id,))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Application deleted successfully'})

@app.route('/set_language/<language>')
def set_language(language):
    if language in ['en', 'fr']:
        session['language'] = language
    return redirect(request.referrer or url_for('index'))

def generate_sso_token(user_id):
    """Generate a new SSO token for the user"""
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    expires_at = datetime.now() + timedelta(weeks=1)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Remove existing tokens for this user
    cursor.execute('DELETE FROM auth_tokens WHERE user_id = ?', (user_id,))
    
    # Insert new token
    cursor.execute('''
        INSERT INTO auth_tokens (user_id, token_hash, expires_at)
        VALUES (?, ?, ?)
    ''', (user_id, token_hash, expires_at))
    
    conn.commit()
    conn.close()
    
    return token

def invalidate_sso_token(token):
    """Invalidate an SSO token"""
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM auth_tokens WHERE token_hash = ?', (token_hash,))
    conn.commit()
    conn.close()

def validate_sso_token(token):
    """Validate an SSO token and return user info"""
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT u.id, u.username, u.email, u.first_name, u.last_name, t.expires_at
        FROM auth_tokens t
        JOIN users u ON t.user_id = u.id
        WHERE t.token_hash = ? AND t.expires_at > datetime('now')
    ''', (token_hash,))
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {
            'id': result[0],
            'username': result[1],
            'email': result[2],
            'first_name': result[3],
            'last_name': result[4],
            'expires_at': result[5]
        }
    return None

@app.route('/sso/validate', methods=['POST'])
def sso_validate():
    """SSO endpoint for applications to validate tokens"""
    import logging
    
    # Log validation request
    remote_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    user_agent = request.headers.get('User-Agent', 'Unknown')
    
    data = request.get_json()
    token = data.get('token') if data else None
    
    print(f"[SSO VALIDATE] IP: {remote_ip}, User-Agent: {user_agent}, Token: {'Present' if token else 'Missing'}")
    
    if not token:
        print(f"[SSO VALIDATE] FAILED - No token provided from {remote_ip}")
        return jsonify({'error': 'Token required'}), 400
    
    user_info = validate_sso_token(token)
    
    if user_info:
        print(f"[SSO VALIDATE] SUCCESS - User: {user_info['username']} from {remote_ip}")
        return jsonify({
            'valid': True,
            'user': user_info
        }), 200
    else:
        print(f"[SSO VALIDATE] FAILED - Invalid token from {remote_ip}")
        return jsonify({'valid': False}), 401

@app.route('/sso/app/<app_name>')
def sso_app_login(app_name):
    """SSO login endpoint that redirects to application with token"""
    if 'user_id' not in session or 'sso_token' not in session:
        return redirect(url_for('index'))
    
    # Get application URL
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT url FROM applications WHERE name = ?', (app_name,))
    app = cursor.fetchone()
    conn.close()
    
    if not app:
        return jsonify({'error': 'Application not found'}), 404
    
    app_url = app[0]
    sso_token = session['sso_token']
    
    # Redirect to application with SSO token
    redirect_url = f"{app_url}?sso_token={sso_token}"
    return redirect(redirect_url)

@app.route('/api/auth/status')
def auth_status():
    return jsonify({
        'authenticated': 'user_id' in session,
        'sso_token': session.get('sso_token', '')
    })

@app.route('/sso/auth')
def sso_auth():
    """SSO authentication endpoint - redirects to login if not authenticated"""
    redirect_uri = request.args.get('redirect_uri')
    client_id = request.args.get('client_id', 'ai-haccp')
    
    if not redirect_uri:
        return jsonify({'error': 'redirect_uri parameter required'}), 400
    
    # Store SSO request in session
    session['sso_redirect_uri'] = redirect_uri
    session['sso_client_id'] = client_id
    
    # If user is already authenticated, redirect back with token
    if 'user_id' in session and 'sso_token' in session:
        return redirect(f"{redirect_uri}?token={session['sso_token']}&state=success")
    
    # Otherwise redirect to login page
    return redirect(url_for('sso_login_page'))

@app.route('/sso/login')
def sso_login_page():
    """SSO login page"""
    redirect_uri = session.get('sso_redirect_uri')
    if not redirect_uri:
        return redirect(url_for('index'))
    
    return render_template('sso_login.html', redirect_uri=redirect_uri)

@app.route('/sso/authenticate', methods=['POST'])
def sso_authenticate():
    """SSO authentication handler"""
    username = request.form.get('username')
    password = request.form.get('password')
    redirect_uri = session.get('sso_redirect_uri')
    
    if not all([username, password, redirect_uri]):
        return render_template('sso_login.html', 
                             error='Missing credentials', 
                             redirect_uri=redirect_uri)
    
    # Authenticate user
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, password_hash, suspended FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()
    
    if user and not user[2] and check_password_hash(user[1], password):
        # Generate SSO token
        session['user_id'] = user[0]
        token = generate_sso_token(user[0])
        session['sso_token'] = token
        
        # Clear SSO session data
        session.pop('sso_redirect_uri', None)
        session.pop('sso_client_id', None)
        
        # Redirect back to client with token
        return redirect(f"{redirect_uri}?token={token}&state=success")
    else:
        return render_template('sso_login.html', 
                             error='Invalid credentials', 
                             redirect_uri=redirect_uri)

@app.route('/api/users', methods=['GET', 'POST'])
def api_users():
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    # Check if user is admin
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT username FROM users WHERE id = ?', (session['user_id'],))
    user = cursor.fetchone()
    
    if not user or user[0] != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    if request.method == 'GET':
        # Get all users
        cursor.execute('SELECT id, username, email, first_name, last_name, suspended, created_at FROM users ORDER BY username')
        users = [{
            'id': row[0],
            'username': row[1], 
            'email': row[2],
            'first_name': row[3],
            'last_name': row[4],
            'suspended': bool(row[5]),
            'created_at': row[6]
        } for row in cursor.fetchall()]
        conn.close()
        return jsonify(users)
    
    elif request.method == 'POST':
        # Add new user
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')
        
        if not all([username, email, password]):
            return jsonify({'error': 'Username, email and password required'}), 400
        
        try:
            password_hash = generate_password_hash(password)
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, first_name, last_name)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, email, password_hash, first_name, last_name))
            conn.commit()
            conn.close()
            return jsonify({'message': 'User created successfully'}), 201
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({'error': 'Username or email already exists'}), 409

@app.route('/api/users/<int:user_id>', methods=['PUT', 'DELETE'])
def api_user_actions(user_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    # Check if user is admin
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT username FROM users WHERE id = ?', (session['user_id'],))
    user = cursor.fetchone()
    
    if not user or user[0] != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    if request.method == 'PUT':
        data = request.get_json()
        action = data.get('action')
        
        if action == 'suspend':
            cursor.execute('UPDATE users SET suspended = 1 WHERE id = ?', (user_id,))
        elif action == 'unsuspend':
            cursor.execute('UPDATE users SET suspended = 0 WHERE id = ?', (user_id,))
        elif action == 'update':
            username = data.get('username')
            email = data.get('email')
            first_name = data.get('first_name', '')
            last_name = data.get('last_name', '')
            
            if not all([username, email]):
                return jsonify({'error': 'Username and email required'}), 400
            
            try:
                cursor.execute('''
                    UPDATE users SET username = ?, email = ?, first_name = ?, last_name = ?
                    WHERE id = ?
                ''', (username, email, first_name, last_name, user_id))
            except sqlite3.IntegrityError:
                conn.close()
                return jsonify({'error': 'Username or email already exists'}), 409
        
        conn.commit()
        conn.close()
        return jsonify({'message': 'User updated successfully'})
    
    elif request.method == 'DELETE':
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
        return jsonify({'message': 'User deleted successfully'})

@app.route('/api/users/<int:user_id>/applications', methods=['GET', 'POST', 'DELETE'])
def api_user_applications(user_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    # Check if user is admin
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT username FROM users WHERE id = ?', (session['user_id'],))
    user = cursor.fetchone()
    
    if not user or user[0] != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    if request.method == 'GET':
        # Get assigned applications for user
        cursor.execute('''
            SELECT a.id, a.name FROM applications a
            JOIN user_applications ua ON a.id = ua.application_id
            WHERE ua.user_id = ?
        ''', (user_id,))
        assigned = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]
        
        # Get all applications
        cursor.execute('SELECT id, name FROM applications ORDER BY name')
        all_apps = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]
        
        conn.close()
        return jsonify({'assigned': assigned, 'all': all_apps})
    
    elif request.method == 'POST':
        data = request.get_json()
        app_id = data.get('application_id')
        
        if not app_id:
            return jsonify({'error': 'Application ID required'}), 400
        
        try:
            cursor.execute('INSERT INTO user_applications (user_id, application_id) VALUES (?, ?)',
                          (user_id, app_id))
            conn.commit()
            conn.close()
            return jsonify({'message': 'Application assigned successfully'})
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({'error': 'Application already assigned'}), 409
    
    elif request.method == 'DELETE':
        data = request.get_json()
        app_id = data.get('application_id')
        
        if not app_id:
            return jsonify({'error': 'Application ID required'}), 400
        
        cursor.execute('DELETE FROM user_applications WHERE user_id = ? AND application_id = ?',
                      (user_id, app_id))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Application unassigned successfully'})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5002, debug=os.environ.get('FLASK_ENV') == 'development')