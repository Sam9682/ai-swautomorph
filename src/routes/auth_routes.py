"""Authentication routes"""
from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from ..config import DB_PATH
from ..auth import generate_sso_token, invalidate_sso_token, validate_sso_token

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
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
                INSERT INTO users (username, email, password_hash, first_name, last_name, suspended)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (username, email, password_hash, first_name, last_name, 1))
            conn.commit()
            
            if request.is_json:
                return jsonify({'message': 'User registered successfully'}), 201
            return redirect(url_for('main.index'))
            
        except sqlite3.IntegrityError:
            return jsonify({'error': 'Username or email already exists'}), 409
        finally:
            conn.close()
    
    return render_template('register.html')

@auth_bp.route('/login', methods=['POST'])
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
        return redirect(url_for('main.dashboard'))
    
    return jsonify({'error': 'Invalid credentials'}), 401

@auth_bp.route('/logout')
def logout():
    # Invalidate SSO token
    if 'sso_token' in session:
        invalidate_sso_token(session['sso_token'])
    
    session.pop('user_id', None)
    session.pop('sso_token', None)
    return redirect(url_for('main.index'))

@auth_bp.route('/auth/sso', methods=['POST'])
def auth_sso():
    """SSO authentication endpoint for external applications"""
    data = request.get_json()
    sso_token = data.get('sso_token') if data else None
    
    if not sso_token:
        return jsonify({'detail': 'SSO token required'}), 400
    
    user_info = validate_sso_token(sso_token)
    
    if user_info:
        # Return format expected by React AuthContext
        return jsonify({
            'access_token': sso_token,
            'user': {
                'id': user_info['id'],
                'email': user_info['email'],
                'username': user_info['username'],
                'first_name': user_info['first_name'],
                'last_name': user_info['last_name']
            }
        }), 200
    else:
        return jsonify({'detail': 'Invalid or expired SSO token'}), 401