#!/usr/bin/env python3
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from datetime import datetime
import json

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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert default applications if none exist
    cursor.execute('SELECT COUNT(*) FROM applications')
    if cursor.fetchone()[0] == 0:
        default_apps = [
            ('AI FoodFlow', 'http://ai-foodflow.swautomorph.com', 'Food management system'),
            ('AI HACCP', 'http://ai-haccp.swautomorph.com', 'HACCP compliance system')
        ]
        cursor.executemany('INSERT INTO applications (name, url, description) VALUES (?, ?, ?)', default_apps)
    
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
    cursor.execute('SELECT id, password_hash FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()
    
    if user and check_password_hash(user[1], password):
        session['user_id'] = user[0]
        if request.is_json:
            return jsonify({'message': 'Login successful'}), 200
        return redirect(url_for('dashboard'))
    
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT name, url, description FROM applications ORDER BY name')
    applications = cursor.fetchall()
    
    # Get username for admin check
    cursor.execute('SELECT username FROM users WHERE id = ?', (session['user_id'],))
    user = cursor.fetchone()
    username = user[0] if user else ''
    conn.close()
    
    return render_template('dashboard.html', applications=applications, username=username)

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
        
        data = request.get_json()
        name = data.get('name')
        url = data.get('url')
        description = data.get('description', '')
        
        if not all([name, url]):
            return jsonify({'error': 'Name and URL required'}), 400
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO applications (name, url, description) VALUES (?, ?, ?)',
                      (name, url, description))
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Application added successfully'}), 201

@app.route('/set_language/<language>')
def set_language(language):
    if language in ['en', 'fr']:
        session['language'] = language
    return redirect(request.referrer or url_for('index'))

@app.route('/api/auth/status')
def auth_status():
    return jsonify({'authenticated': 'user_id' in session})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=os.environ.get('FLASK_ENV') == 'development')