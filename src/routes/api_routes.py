"""API routes"""
from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash
import sqlite3
import os
import shutil
import requests
from ..config import DB_PATH

api_bp = Blueprint('api', __name__, url_prefix='/api')

def create_gitea_user(username, email, password, first_name='', last_name=''):
    """Create user in Gitea server"""
    try:
        # Gitea API endpoint
        gitea_url = 'http://localhost:3000/api/v1/admin/users'
        
        # Admin credentials (you may want to configure these)
        admin_token = get_gitea_admin_token()
        
        if not admin_token:
            print(f"[GITEA] Failed to get admin token for user creation: {username}")
            return False
        
        # User data for Gitea
        user_data = {
            'username': username,
            'email': email,
            'password': password,
            'full_name': f"{first_name} {last_name}".strip(),
            'must_change_password': False,
            'send_notify': False
        }
        
        headers = {
            'Authorization': f'token {admin_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(gitea_url, json=user_data, headers=headers, timeout=10)
        
        if response.status_code == 201:
            print(f"[GITEA] User {username} created successfully")
            return True
        else:
            print(f"[GITEA] Failed to create user {username}: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"[GITEA] Error creating user {username}: {str(e)}")
        return False

def get_gitea_admin_token():
    """Get or create admin token for Gitea API access"""
    try:
        # Try to get existing token from file
        token_file = '/tmp/gitea_admin_token'
        if os.path.exists(token_file):
            with open(token_file, 'r') as f:
                return f.read().strip()
        
        # If no token file, return None (manual setup required)
        print("[GITEA] No admin token found. Manual Gitea setup required.")
        return None
        
    except Exception as e:
        print(f"[GITEA] Error getting admin token: {str(e)}")
        return None

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
        cursor.execute('SELECT id, name, description, git_url FROM applications ORDER BY name')
        apps = [{'id': row[0], 'name': row[1], 'description': row[2], 'git_url': row[3]} 
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
        description = data.get('description', '')
        
        if not name:
            return jsonify({'error': 'Name required'}), 400
        
        git_url = data.get('git_url', '')
        cursor.execute('INSERT INTO applications (name, description, git_url) VALUES (?, ?, ?)',
                      (name, description, git_url))
        app_id = cursor.lastrowid
        
        # Assign new application to all existing users with URLs
        from ..database import assign_app_to_all_users
        assign_app_to_all_users(app_id, name)
        
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
        description = data.get('description', '')
        
        if not name:
            return jsonify({'error': 'Name required'}), 400
        
        git_url = data.get('git_url', '')
        cursor.execute('''
            UPDATE applications SET name = ?, description = ?, git_url = ?
            WHERE id = ?
        ''', (name, description, git_url, app_id))
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
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            # Assign default applications to new user
            from ..database import assign_default_apps_to_user
            assign_default_apps_to_user(user_id)
            
            # Create user in Gitea
            create_gitea_user(username, email, password, first_name, last_name)
            
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

@api_bp.route('/deployments', methods=['GET', 'POST'])
def api_deployments():
    import logging
    
    # Log API call
    user_id = session.get('user_id', 'anonymous')
    method = request.method
    remote_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    user_agent = request.headers.get('User-Agent', 'Unknown')
    
    print(f"[DEPLOYMENT API] {method} /api/deployments - User: {user_id}, IP: {remote_ip}, UA: {user_agent[:50]}")
    
    if 'user_id' not in session:
        print(f"[DEPLOYMENT API] FAILED - Authentication required from {remote_ip}")
        return jsonify({'error': 'Authentication required'}), 401
    
    if request.method == 'GET':
        print(f"[DEPLOYMENT API] GET - Fetching deployments for user {user_id}")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, application_name, status, deployment_path, git_url, created_at, updated_at
            FROM deployments WHERE user_id = ? ORDER BY updated_at DESC
        ''', (session['user_id'],))
        deployments = [{
            'id': row[0],
            'application_name': row[1],
            'status': row[2],
            'deployment_path': row[3],
            'git_url': row[4],
            'created_at': row[5],
            'updated_at': row[6]
        } for row in cursor.fetchall()]
        conn.close()
        print(f"[DEPLOYMENT API] GET - Returning {len(deployments)} deployments for user {user_id}")
        return jsonify(deployments)
    
    elif request.method == 'POST':
        import subprocess
        import os
        data = request.get_json()
        action = data.get('action')
        app_name = data.get('application_name')
        git_url = data.get('git_url')
        
        print(f"[DEPLOYMENT API] POST - User {user_id} requesting action '{action}' for app '{app_name}'")
        
        if not all([action, app_name]):
            print(f"[DEPLOYMENT API] POST - FAILED - Missing action or app_name for user {user_id}")
            return jsonify({'error': 'Action and application name required'}), 400
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get username for deployment path
        cursor.execute('SELECT username FROM users WHERE id = ?', (session['user_id'],))
        user = cursor.fetchone()
        username = user[0] if user else f'user_{session["user_id"]}'
        
        deployment_path = f'/home/ubuntu/deployments/{username}/{app_name.lower().replace(" ", "-")}'
        print(f"[DEPLOYMENT API] POST - Deployment path: {deployment_path}")
        
        try:
            if action == 'clone':
                if not git_url:
                    print(f"[DEPLOYMENT API] CLONE - FAILED - No git_url provided for user {user_id}")
                    return jsonify({'error': 'Git URL required for clone action'}), 400
                
                print(f"[DEPLOYMENT API] CLONE - Starting clone from {git_url} to {deployment_path}")
                
                # Remove existing directory if it exists
                if os.path.exists(deployment_path):
                    print(f"[DEPLOYMENT API] CLONE - Removing existing directory: {deployment_path}")
                    import shutil
                    shutil.rmtree(deployment_path)
                else:
                    print(f"[DEPLOYMENT API] CLONE - Directory doesn't exist, creating new: {deployment_path}")
                
                # Create full directory path recursively
                print(f"[DEPLOYMENT API] CLONE - Creating directory structure: {deployment_path}")
                os.makedirs(deployment_path, exist_ok=True)
                print(f"[DEPLOYMENT API] CLONE - Directory created successfully")
                
                # Clone repository with proper Git environment
                print(f"[DEPLOYMENT API] CLONE - Executing git clone command")
                git_env = os.environ.copy()
                git_env.update({
                    'GIT_CONFIG_NOSYSTEM': '1',
                    'HOME': '/home/ubuntu',
                    'USER': 'ubuntu'
                })
                result = subprocess.run(['git', 'clone', git_url, deployment_path], 
                                      capture_output=True, text=True, timeout=600, env=git_env)
                print(f"[DEPLOYMENT API] CLONE - Git clone completed with return code: {result.returncode}")
                
                command_output = f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
                
                if result.returncode == 0:
                    status = 'cloned'
                    error_msg = None
                    print(f"[DEPLOYMENT API] CLONE - SUCCESS - Repository cloned to {deployment_path}")
                else:
                    status = 'failed'
                    error_msg = f'Git clone failed: {result.stderr}'
                    print(f"[DEPLOYMENT API] CLONE - FAILED - {error_msg}")
                    deployment_path = None
                
                # Record deployment
                print(f"[DEPLOYMENT API] CLONE - Recording deployment in database with status: {status}")
                cursor.execute('''
                    INSERT OR REPLACE INTO deployments 
                    (user_id, application_name, status, deployment_path, git_url)
                    VALUES (?, ?, ?, ?, ?)
                ''', (session['user_id'], app_name, status, deployment_path, git_url))
                print(f"[DEPLOYMENT API] CLONE - Database record created")
                
                if status == 'failed':
                    conn.commit()
                    conn.close()
                    return jsonify({'error': error_msg, 'logs': command_output}), 400
                
            elif action in ['start', 'stop', 'restart', 'ps', 'logs']:
                # Check if deployment exists
                print(f"[DEPLOYMENT API] {action.upper()} - Looking for existing deployment for app '{app_name}'")
                cursor.execute('''
                    SELECT deployment_path FROM deployments 
                    WHERE user_id = ? AND application_name = ? AND status != 'failed'
                    ORDER BY updated_at DESC LIMIT 1
                ''', (session['user_id'], app_name))
                
                deployment = cursor.fetchone()
                if not deployment:
                    print(f"[DEPLOYMENT API] {action.upper()} - FAILED - No deployment found for app '{app_name}'")
                    return jsonify({'error': 'Application not deployed. Clone first.'}), 400
                
                local_mode = data.get('locally', False)  # Default to local mode

                if local_mode:
                    deploy_path = deployment[0]
                else:
                    deploy_path = deployment_path
                deploy_script = os.path.join(deploy_path, 'deploy.sh')
                print(f"[DEPLOYMENT API] {action.upper()} - Found deployment at: {deploy_path}")
                print(f"[DEPLOYMENT API] {action.upper()} - Looking for deploy script: {deploy_script}")
                
                if not os.path.exists(deploy_script):
                    print(f"[DEPLOYMENT API] {action.upper()} - FAILED - deploy.sh not found at {deploy_script}")
                    return jsonify({'error': f'deploy.sh not found in {deploy_script}'}), 400
                
                # Get user details for deploy.sh
                cursor.execute('SELECT username, email, first_name, last_name FROM users WHERE id = ?', (session['user_id'],))
                user_details = cursor.fetchone()
                user_name = f"{user_details[2] or ''} {user_details[3] or ''}" if user_details else 'User'
                user_email = user_details[1] if user_details else 'user@example.com'
                
                # Execute deploy.sh with action and user environment variables
                print(f"[DEPLOYMENT API] {action.upper()} - Executing: {deploy_script} {action} '' {session['user_id']} '{user_name}' {user_email}")
                print(f"[DEPLOYMENT API] {action.upper()} - Working directory: {deploy_path}")
                result = subprocess.run([deploy_script, action, str(session['user_id']), user_name, user_email], 
                                          cwd=deploy_path, capture_output=True, text=True, timeout=600)
                print(f"[DEPLOYMENT API] {action.upper()} - Command completed with return code: {result.returncode}")
                
                command_output = f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
                
                status = 'running' if action == 'start' else 'stopped' if action == 'stop' else 'completed'
                
                # Update deployment status
                cursor.execute('''
                    UPDATE deployments SET status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND application_name = ?
                ''', (status, session['user_id'], app_name))
                print(f"[DEPLOYMENT API] {action.upper()} - Database status updated = {status} for application {app_name}")
                
                # Record billing activity for start/stop actions
                if action in ['start', 'stop'] and result.returncode == 0:
                    from .billing_routes import record_billing_activity
                    record_billing_activity(session['user_id'], app_name, action)
                    print(f"[DEPLOYMENT API] {action.upper()} - Billing activity recorded for user {session['user_id']} and app {app_name}")
            
            conn.commit()
            conn.close()
            
            print(f"[DEPLOYMENT API] POST - SUCCESS - Action '{action}' completed for app '{app_name}' by user {user_id}")
            return jsonify({
                'message': f'{action.capitalize()} completed for {app_name}',
                'status': status,
                'logs': command_output if 'command_output' in locals() else 'No output captured'
            }), 202
            
        except subprocess.TimeoutExpired:
            print(f"[DEPLOYMENT API] POST - TIMEOUT - Action '{action}' timed out for app '{app_name}' by user {user_id}")
            conn.close()
            return jsonify({'error': 'Operation timed out'}), 408
        except Exception as e:
            print(f"[DEPLOYMENT API] POST - ERROR - Action '{action}' failed for app '{app_name}' by user {user_id}: {str(e)}")
            conn.close()
            return jsonify({'error': str(e)}), 500

@api_bp.route('/deployments/<int:deployment_id>/logs')
def api_deployment_logs(deployment_id):
    # Log API call
    user_id = session.get('user_id', 'anonymous')
    remote_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    
    print(f"[DEPLOYMENT LOGS] GET /api/deployments/{deployment_id}/logs - User: {user_id}, IP: {remote_ip}")
    
    if 'user_id' not in session:
        print(f"[DEPLOYMENT LOGS] FAILED - Authentication required from {remote_ip}")
        return jsonify({'error': 'Authentication required'}), 401
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT deployment_path FROM deployments 
        WHERE id = ? AND user_id = ?
    ''', (deployment_id, session['user_id']))
    
    deployment = cursor.fetchone()
    conn.close()
    
    if not deployment:
        print(f"[DEPLOYMENT LOGS] FAILED - Deployment {deployment_id} not found for user {user_id}")
        return jsonify({'error': 'Deployment not found'}), 404
    
    log_file = os.path.join(deployment[0], 'deployment.log')
    
    try:
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                logs = f.read()
        else:
            logs = 'No logs available'
        
        print(f"[DEPLOYMENT LOGS] SUCCESS - Returned logs for deployment {deployment_id} to user {user_id}")
        return jsonify({'logs': logs})
    except Exception as e:
        print(f"[DEPLOYMENT LOGS] ERROR - Failed to read logs for deployment {deployment_id} by user {user_id}: {str(e)}")
        return jsonify({'error': f'Failed to read logs: {str(e)}'}), 500

@api_bp.route('/qchat', methods=['POST'])
def api_qchat():
    from ..automorph_application import process_qchat_request
    import time
    
    # Log API call details
    user_id = session.get('user_id', '0')
    remote_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    user_agent = request.headers.get('User-Agent', 'Unknown')
    timestamp = time.strftime('%Y-%m-%d-%H:%M:%S')
    
    print(f"[Q CHAT API] {timestamp} - POST /api/qchat - User: {user_id}, IP: {remote_ip}, UA: {user_agent[:50]}")
    
    if 'user_id' not in session:
        print(f"[Q CHAT API] FAILED - Authentication required from {remote_ip}")
        return jsonify({'error': 'Authentication required'}), 401
    
    data = request.get_json()
    message = data.get('message', '').strip()
    auto_approve = data.get('auto_approve', True)
    app_name = data.get('application_name', '')
    app_folder = data.get('application_folder', '')
    gitea_url = data.get('gitea_url', '')
    github_url = data.get('github_url', '')
    userid = data.get('userid', '0')
    username = data.get('username', 'anonymous')
    
    print(f"[Q CHAT API] User {username} - Message length: {len(message)} chars, Auto-approve: {auto_approve}")
    print(f"[Q CHAT API] User {username} - App: {app_name}, Folder: {app_folder}, Gitea: {gitea_url}, GitHub: {github_url}")
    print(f"[Q CHAT API] User {username} - Message preview: {message[:100]}{'...' if len(message) > 100 else ''}")
    
    if not message:
        print(f"[Q CHAT API] FAILED - Empty message from user {user_id}")
        return jsonify({'error': 'Message required'}), 400
    
    try:
        # Use automorph_application module to process the request
        result = process_qchat_request(message, auto_approve, app_name, app_folder, gitea_url, userid, username)
        
        if 'error' in result:
            print(f"[Q CHAT API] User {user_id} - ERROR: {result['error']}")
            return jsonify(result), 500
        
        response_data = {
            'response': result['response'],
            'command_executed': result['command_executed'],
            'branch_name': result.get('branch_name'),
            'auto_approve_used': auto_approve,
            'execution_time': result['execution_time'],
            'success': result['success']
        }
        
        print(f"[Q CHAT API] User {user_id} - SUCCESS - Automorph processing completed")
        return jsonify(response_data)
        
    except Exception as e:
        print(f"[Q CHAT API] User {user_id} - EXCEPTION - {type(e).__name__}: {str(e)}")
        import traceback
        print(f"[Q CHAT API] User {user_id} - TRACEBACK: {traceback.format_exc()}")
        return jsonify({'error': f'Automorph Q Chat error: {str(e)}'}), 500

@api_bp.route('/qchat_question', methods=['POST'])
def api_qchat_question():
    from ..automorph_application import process_qchat_question
    import time
    
    # Log API call details
    user_id = session.get('user_id', 'anonymous')
    remote_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    
    print(f"[VIRTUAL ADVISOR API] {timestamp} - POST /api/qchat_question - User: {user_id}, IP: {remote_ip}")
    
    if 'user_id' not in session:
        print(f"[VIRTUAL ADVISOR API] FAILED - Authentication required from {remote_ip}")
        return jsonify({'error': 'Authentication required'}), 401
    
    data = request.get_json()
    message = data.get('message', '').strip()
    
    print(f"[VIRTUAL ADVISOR API] User {user_id} - Message length: {len(message)} chars")
    print(f"[VIRTUAL ADVISOR API] User {user_id} - Message preview: {message[:100]}{'...' if len(message) > 100 else ''}")
    
    if not message:
        print(f"[VIRTUAL ADVISOR API] FAILED - Empty message from user {user_id}")
        return jsonify({'error': 'Message required'}), 400
    
    try:
        # Use automorph_application module to process the question
        result = process_qchat_question(message)
        
        if 'error' in result:
            print(f"[VIRTUAL ADVISOR API] User {user_id} - ERROR: {result['error']}")
            return jsonify(result), 500
        
        response_data = {
            'response': result['response'],
            'execution_time': result['execution_time'],
            'success': result['success']
        }
        
        print(f"[VIRTUAL ADVISOR API] User {user_id} - SUCCESS - Question processing completed")
        return jsonify(response_data)
        
    except Exception as e:
        print(f"[VIRTUAL ADVISOR API] User {user_id} - EXCEPTION - {type(e).__name__}: {str(e)}")
        import traceback
        print(f"[VIRTUAL ADVISOR API] User {user_id} - TRACEBACK: {traceback.format_exc()}")
        return jsonify({'error': f'Virtual Advisor error: {str(e)}'}), 500