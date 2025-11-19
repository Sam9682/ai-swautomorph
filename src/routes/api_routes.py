"""API routes"""
from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash
import sqlite3
from ..config import DB_PATH

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/auth/status')
def auth_status():
    return jsonify({
        'authenticated': 'user_id' in session,
        'sso_token': session.get('sso_token', '')
    })

@api_bp.route('/applications', methods=['GET', 'POST'])
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

@api_bp.route('/applications/<int:app_id>', methods=['PUT', 'DELETE'])
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

@api_bp.route('/users', methods=['GET', 'POST'])
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

@api_bp.route('/users/<int:user_id>', methods=['PUT', 'DELETE'])
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

@api_bp.route('/users/<int:user_id>/applications', methods=['GET', 'POST', 'DELETE'])
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