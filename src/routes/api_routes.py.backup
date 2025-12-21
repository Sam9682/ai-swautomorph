"""API routes"""
from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash
import sqlite3
import os
import shutil
import requests
from ..config import DB_PATH
from ..database import db_manager
from ..db_health import check_database_health, get_database_stats

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

@api_bp.route('/health/database')
def database_health():
    """Database health check endpoint"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    # Check if user is admin
    user = db_manager.execute_query(
        'SELECT username FROM users WHERE id = ?', 
        (session['user_id'],), fetch_one=True
    )
    
    if not user or user[0] != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    health_status = check_database_health()
    db_stats = get_database_stats()
    
    return jsonify({
        'health': health_status,
        'statistics': db_stats
    })

@api_bp.route('/applications', methods=['GET', 'POST'])
def api_applications():
    if request.method == 'GET':
        apps_data = db_manager.execute_query(
            'SELECT id, name, description, git_url, git_repo_size FROM applications ORDER BY name',
            fetch_all=True
        )
        apps = [{'id': row[0], 'name': row[1], 'description': row[2], 'git_url': row[3], 'git_repo_size': row[4] or 50} 
                for row in apps_data]
        return jsonify(apps)
    
    elif request.method == 'POST':
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Check if user is admin
        user = db_manager.execute_query(
            'SELECT username FROM users WHERE id = ?', 
            (session['user_id'],), fetch_one=True
        )
        
        if not user or user[0] != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.get_json()
        name = data.get('name')
        description = data.get('description', '')
        
        if not name:
            return jsonify({'error': 'Name required'}), 400
        
        git_url = data.get('git_url', '')
        git_repo_size = data.get('git_repo_size', 50)
        app_id = db_manager.execute_query(
            'INSERT INTO applications (name, description, git_url, git_repo_size) VALUES (?, ?, ?, ?)',
            (name, description, git_url, git_repo_size)
        )
        
        # Assign new application to all existing users with URLs
        from ..database import assign_app_to_all_users
        assign_app_to_all_users(app_id, name)
        
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
        git_repo_size = data.get('git_repo_size', 50)
        cursor.execute('''
            UPDATE applications SET name = ?, description = ?, git_url = ?, git_repo_size = ?
            WHERE id = ?
        ''', (name, description, git_url, git_repo_size, app_id))
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
            # Calculate ports for the user and application
            from ..database import calculate_app_ports
            HTTP_PORT, HTTPS_PORT = calculate_app_ports(user_id, app_id)
            
            # Get application name for URL generation
            cursor.execute('SELECT name FROM applications WHERE id = ?', (app_id,))
            app_result = cursor.fetchone()
            if not app_result:
                conn.close()
                return jsonify({'error': 'Application not found'}), 404
            
            app_name = app_result[0]
            url = f'https://www.swautomorph.com:{HTTPS_PORT}'
            
            cursor.execute('INSERT INTO user_applications (user_id, application_id, url, http_port, https_port) VALUES (?, ?, ?, ?, ?)',
                          (user_id, app_id, url, HTTP_PORT, HTTPS_PORT))
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
    from flask import Response, stream_with_context
    import json
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
        deployments_data = db_manager.execute_query('''
            SELECT id, application_name, status, deployment_path, git_url, created_at, updated_at, server_id
            FROM deployments WHERE user_id = ? ORDER BY updated_at DESC
        ''', (session['user_id'],), fetch_all=True)
        
        deployments = [{
            'id': row[0],
            'application_name': row[1],
            'status': row[2],
            'deployment_path': row[3],
            'git_url': row[4],
            'created_at': row[5],
            'updated_at': row[6],
            'server_id': row[7]
        } for row in deployments_data]
        
        print(f"[DEPLOYMENT API] GET - Returning {len(deployments)} deployments for user {user_id}")
        return jsonify(deployments)
    
    elif request.method == 'POST':
        import subprocess
        import os
        import shutil
        data = request.get_json()
        action = data.get('action')
        app_name = data.get('application_name')
        git_url = data.get('git_url')
        server_id = data.get('server_id')
        
        print(f"[DEPLOYMENT API] POST - User {user_id} requesting action '{action}' for app '{app_name}'")
        
        if not all([action, app_name]):
            print(f"[DEPLOYMENT API] POST - FAILED - Missing action or app_name for user {user_id}")
            return jsonify({'error': 'Action and application name required'}), 400
        
        # Get username for deployment path
        user = db_manager.execute_query(
            'SELECT username FROM users WHERE id = ?', 
            (session['user_id'],), fetch_one=True
        )
        username = user[0] if user else f'user_{session["user_id"]}'
        
        deployment_path = f'/home/ubuntu/deployments/{username}/{app_name.lower().replace(" ", "-")}'
        print(f"[DEPLOYMENT API] POST - Deployment path: {deployment_path}")
        
        try:
            if action == 'clone':
                if not git_url:
                    print(f"[DEPLOYMENT API] CLONE - FAILED - No git_url provided for user {user_id}")
                    return jsonify({'error': 'Git URL required for clone action'}), 400
                
                if not server_id:
                    print(f"[DEPLOYMENT API] CLONE - FAILED - No server_id provided for user {user_id}")
                    return jsonify({'error': 'Server ID required for clone action'}), 400
                
                print(f"[DEPLOYMENT API] CLONE - Starting clone from {git_url} to {deployment_path}")
                
                # Get current server IP and target server IP
                import socket
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    s.connect(("8.8.8.8", 80))
                    current_server_ip = s.getsockname()[0]
                    s.close()
                except:
                    current_server_ip = "127.0.0.1"
                
                # Get target server IP
                target_server = db_manager.execute_query(
                    'SELECT SERVER_IP FROM servers WHERE id = ?', 
                    (server_id,), fetch_one=True
                )
                
                if not target_server:
                    print(f"[DEPLOYMENT API] CLONE - FAILED - Server {server_id} not found")
                    return jsonify({'error': f'Server {server_id} not found'}), 400
                
                target_server_ip = target_server[0]
                is_local_server = (target_server_ip == current_server_ip or target_server_ip == "127.0.0.1" or target_server_ip == "localhost")
                
                print(f"[DEPLOYMENT API] CLONE - Current server: {current_server_ip}, Target server: {target_server_ip}, Local: {is_local_server}")
                
                if is_local_server:
                    # Execute locally
                    print(f"[DEPLOYMENT API] CLONE - Executing locally")
                    
                    # Remove existing directory if it exists
                    if os.path.exists(deployment_path):
                        print(f"[DEPLOYMENT API] CLONE - Removing existing directory: {deployment_path}")
                        shutil.rmtree(deployment_path)
                    
                    # Create full directory path recursively
                    print(f"[DEPLOYMENT API] CLONE - Creating directory structure: {deployment_path}")
                    os.makedirs(deployment_path, exist_ok=True)
                    
                    # Clone repository with proper Git environment
                    git_env = os.environ.copy()
                    git_env.update({
                        'GIT_CONFIG_NOSYSTEM': '1',
                        'HOME': '/home/ubuntu',
                        'USER': 'ubuntu'
                    })
                    result = subprocess.run(['git', 'clone', '--recurse-submodules', git_url, deployment_path], 
                                          capture_output=True, text=True, timeout=600, env=git_env)
                else:
                    # Execute on remote server via SSH
                    print(f"[DEPLOYMENT API] CLONE - Executing on remote server {target_server_ip}")
                    
                    ssh_commands = [
                        f"rm -rf {deployment_path}",
                        f"mkdir -p {deployment_path}",
                        f"cd {os.path.dirname(deployment_path)} && git clone --recurse-submodules {git_url} {os.path.basename(deployment_path)}"
                    ]
                    
                    ssh_command = f"ssh -o StrictHostKeyChecking=no ubuntu@{target_server_ip} '{'; '.join(ssh_commands)}'"
                    result = subprocess.run(ssh_command, shell=True, capture_output=True, text=True, timeout=600)

                # Build command output only for non-empty content
                output_parts = []
                if result.stdout and result.stdout.strip():
                    output_parts.append(f"STDOUT:\n{result.stdout}")
                if result.stderr and result.stderr.strip():
                    output_parts.append(f"STDERR:\n{result.stderr}")
                command_output = "\n\n".join(output_parts) if output_parts else "No output"
                
                if result.returncode == 0:
                    status = 'cloned'
                    error_msg = None
                    print(f"[DEPLOYMENT API] CLONE - SUCCESS - Repository cloned to {deployment_path}")
                    
                    # Copy SSL certificates to cloned application
                    try:
                        ssl_source_dir = '/home/ubuntu/ai-swautomorph/ssl/'
                        ssl_dest_dir = os.path.join(deployment_path, 'ssl')
                        
                        if is_local_server:
                            # Local server - direct copy
                            print(f"[DEPLOYMENT API] CLONE - Copying SSL certificates locally to {ssl_dest_dir}")
                            os.makedirs(ssl_dest_dir, exist_ok=True)
                            
                            # Copy specific SSL files
                            ssl_files = [
                                'STAR_swautomorph_com.crt',
                                'privateKey_STAR_swautomorph_com.key'
                            ]
                            
                            for ssl_file in ssl_files:
                                src_file = os.path.join(ssl_source_dir, ssl_file)
                                if os.path.exists(src_file):
                                    shutil.copy2(src_file, ssl_dest_dir)
                                    print(f"[DEPLOYMENT API] CLONE - Copied {ssl_file} to {ssl_dest_dir}")
                        else:
                            # Remote server - rsync via SSH
                            print(f"[DEPLOYMENT API] CLONE - Copying SSL certificates to remote server {target_server_ip}")
                            
                            # Create ssl directory on remote server
                            ssh_mkdir = f"ssh -o StrictHostKeyChecking=no ubuntu@{target_server_ip} 'mkdir -p {ssl_dest_dir}'"
                            subprocess.run(ssh_mkdir, shell=True, capture_output=True, text=True, timeout=60)
                            
                            # Rsync SSL certificates
                            rsync_cmd = f"rsync -avz -e 'ssh -o StrictHostKeyChecking=no' {ssl_source_dir}STAR_swautomorph_com.crt {ssl_source_dir}privateKey_STAR_swautomorph_com.key ubuntu@{target_server_ip}:{ssl_dest_dir}/"
                            rsync_result = subprocess.run(rsync_cmd, shell=True, capture_output=True, text=True, timeout=120)
                            
                            if rsync_result.returncode == 0:
                                print(f"[DEPLOYMENT API] CLONE - SSL certificates copied successfully to {target_server_ip}:{ssl_dest_dir}")
                            else:
                                print(f"[DEPLOYMENT API] CLONE - WARNING - SSL certificate copy failed: {rsync_result.stderr}")
                                
                    except Exception as ssl_error:
                        print(f"[DEPLOYMENT API] CLONE - WARNING - SSL certificate copy failed: {str(ssl_error)}")
                        # Don't fail the entire clone operation for SSL copy issues
                        
                else:
                    status = 'failed'
                    error_msg = f'Git clone failed: {result.stderr}'
                    print(f"[DEPLOYMENT API] CLONE - FAILED - {error_msg}")
                    deployment_path = None
                
                # Record deployment
                print(f"[DEPLOYMENT API] CLONE - Recording deployment in database with status: {status}")
                
                # Check if record exists for this user, app, and server
                existing_record = db_manager.execute_query('''
                    SELECT id FROM deployments 
                    WHERE user_id = ? AND application_name = ? AND server_id = ?
                ''', (session['user_id'], app_name, server_id), fetch_one=True)
                
                if existing_record:
                    # Update existing record
                    db_manager.execute_query('''
                        UPDATE deployments SET status = ?, deployment_path = ?, git_url = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = ? AND application_name = ? AND server_id = ?
                    ''', (status, deployment_path, git_url, session['user_id'], app_name, server_id))
                    print(f"[DEPLOYMENT API] CLONE - Database record updated")
                else:
                    # Insert new record
                    db_manager.execute_query('''
                        INSERT INTO deployments 
                        (user_id, application_name, status, deployment_path, git_url, server_id)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (session['user_id'], app_name, status, deployment_path, git_url, server_id))
    
                
                if status == 'failed':
                    return jsonify({'error': error_msg, 'logs': command_output}), 400
                
            elif action in ['start', 'stop', 'restart', 'ps', 'logs']:
                # Check if deployment exists
                print(f"[DEPLOYMENT API] {action.upper()} - Looking for existing deployment for app '{app_name}'")
                deployment = db_manager.execute_query('''
                    SELECT deployment_path FROM deployments 
                    WHERE user_id = ? AND application_name = ? AND status != 'failed'
                    ORDER BY updated_at DESC LIMIT 1
                ''', (session['user_id'], app_name), fetch_one=True)
                
                if not deployment:
                    print(f"[DEPLOYMENT API] {action.upper()} - FAILED - No deployment found for app '{app_name}'")
                    return jsonify({'error': 'Application not deployed. Clone first.'}), 400
                
                # Debug deployment data type and content
                print(f"[DEPLOYMENT API] {action.upper()} - DEBUG - deployment type: {type(deployment)}, content: {deployment}")
                
                # Extract deployment path safely
                deploy_path = None
                try:
                    if deployment:
                        if isinstance(deployment, (list, tuple)) and len(deployment) > 0:
                            deploy_path = str(deployment[0])
                        elif hasattr(deployment, '__getitem__'):
                            deploy_path = str(deployment[0])
                        elif isinstance(deployment, str):
                            deploy_path = deployment
                        else:
                            print(f"[DEPLOYMENT API] {action.upper()} - ERROR - Unexpected deployment type: {type(deployment)}")
                            return jsonify({'error': f'Invalid deployment data type: {type(deployment)}'}), 500
                    
                    if not deploy_path:
                        print(f"[DEPLOYMENT API] {action.upper()} - ERROR - Could not extract deployment path")
                        return jsonify({'error': 'Could not extract deployment path'}), 500
                        
                    print(f"[DEPLOYMENT API] {action.upper()} - DEBUG - Extracted deploy_path: {deploy_path} (type: {type(deploy_path)})")
                    
                except Exception as path_error:
                    print(f"[DEPLOYMENT API] {action.upper()} - ERROR - Path extraction failed: {str(path_error)}")
                    return jsonify({'error': f'Path extraction failed: {str(path_error)}'}), 500
                
                # Debug the deploy_path before using it in os.path.join
                print(f"[DEPLOYMENT API] {action.upper()} - DEBUG - About to call os.path.join with deploy_path: {deploy_path} (type: {type(deploy_path)})")
                
                try:
                    deploy_script = os.path.join(deploy_path, 'deployApp.sh')
                except Exception as join_error:
                    print(f"[DEPLOYMENT API] {action.upper()} - ERROR - os.path.join failed: {str(join_error)}")
                    print(f"[DEPLOYMENT API] {action.upper()} - ERROR - deploy_path value: {repr(deploy_path)}")
                    return jsonify({'error': f'Path join failed: {str(join_error)}'}), 500
                print(f"[DEPLOYMENT API] {action.upper()} - Found deployment at: {deploy_path}")
                print(f"[DEPLOYMENT API] {action.upper()} - Looking for deploy script: {deploy_script}")
                
                if not os.path.exists(deploy_script):
                    print(f"[DEPLOYMENT API] {action.upper()} - FAILED - deployApp.sh not found at {deploy_script}")
                    return jsonify({'error': f'deployApp.sh not found in {deploy_script}'}), 400
                
                # Get user details for deployApp.sh
                user_details = db_manager.execute_query(
                    'SELECT username, email, first_name, last_name FROM users WHERE id = ?', 
                    (session['user_id'],), fetch_one=True
                )
                user_name = f"{user_details[2] or ''} {user_details[3] or ''}" if user_details else 'User'
                user_email = user_details[1] if user_details else 'user@example.com'
                
                # Check if streaming is requested
                stream_output = data.get('stream', False)
                
                if stream_output:
                    # Stream output in real-time
                    def generate():
                        import re
                        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
                        
                        try:
                            process = subprocess.Popen(
                                [deploy_script, action, str(session['user_id']), user_name, user_email],
                                cwd=deploy_path, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, bufsize=1
                            )
                            
                            for line in iter(process.stdout.readline, ''):
                                if line:
                                    clean_line = ansi_escape.sub('', line.rstrip())
                                    if clean_line:
                                        yield f"data: {json.dumps({'chunk': clean_line})}\n\n"
                            
                            process.wait()
                            status = 'running' if action == 'start' else 'stopped' if action == 'stop' else 'completed'
                            
                            db_manager.execute_query('''
                                UPDATE deployments SET status = ?, updated_at = CURRENT_TIMESTAMP
                                WHERE user_id = ? AND application_name = ?
                            ''', (status, session['user_id'], app_name))
                            
                            if action in ['start', 'stop'] and process.returncode == 0:
                                from .billing_routes import record_billing_activity
                                record_billing_activity(session['user_id'], app_name, action)
                            
                            yield f"data: {json.dumps({'done': True, 'success': process.returncode == 0})}\n\n"
                        except Exception as e:
                            yield f"data: {json.dumps({'error': str(e)})}\n\n"
                    
                    return Response(stream_with_context(generate()), mimetype='text/event-stream',
                                   headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})
                else:
                    # Execute deployApp.sh with action and user environment variables
                    print(f"[DEPLOYMENT API] {action.upper()} - Executing: {deploy_script} {action} '' {session['user_id']} '{user_name}' {user_email}")
                    print(f"[DEPLOYMENT API] {action.upper()} - Working directory: {deploy_path}")
                    result = subprocess.run([deploy_script, action, str(session['user_id']), user_name, user_email], 
                                              cwd=deploy_path, capture_output=True, text=True, timeout=600)
                    print(f"[DEPLOYMENT API] {action.upper()} - Command completed with return code: {result.returncode}")
                    
                    # Build command output only for non-empty content
                    output_parts = []
                    if result.stdout and result.stdout.strip():
                        output_parts.append(f"STDOUT:\n{result.stdout}")
                    if result.stderr and result.stderr.strip():
                        output_parts.append(f"STDERR:\n{result.stderr}")
                    command_output = "\n\n".join(output_parts) if output_parts else "No output"
                    
                    status = 'running' if action == 'start' else 'stopped' if action == 'stop' else 'completed'
                    
                    # Update deployment status
                    db_manager.execute_query('''
                        UPDATE deployments SET status = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = ? AND application_name = ?
                    ''', (status, session['user_id'], app_name))
                    print(f"[DEPLOYMENT API] {action.upper()} - Database status updated = {status} for application {app_name}")
                    
                    # Record billing activity for start/stop actions
                    if action in ['start', 'stop'] and result.returncode == 0:
                        from .billing_routes import record_billing_activity
                        record_billing_activity(session['user_id'], app_name, action)
                        print(f"[DEPLOYMENT API] {action.upper()} - Billing activity recorded for user {session['user_id']} and app {app_name}")
            
            print(f"[DEPLOYMENT API] POST - SUCCESS - Action '{action}' completed for app '{app_name}' by user {user_id}")
            return jsonify({
                'message': f'{action.capitalize()} completed for {app_name}',
                'status': status,
                'logs': command_output if 'command_output' in locals() else 'No output captured'
            }), 202
            
        except subprocess.TimeoutExpired:
            print(f"[DEPLOYMENT API] POST - TIMEOUT - Action '{action}' timed out for app '{app_name}' by user {user_id}")
            return jsonify({'error': 'Operation timed out'}), 408
        except Exception as e:
            print(f"[DEPLOYMENT API] POST - ERROR - Action '{action}' failed for app '{app_name}' by user {user_id}: {str(e)}")
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
    
    deployment = db_manager.execute_query('''
        SELECT deployment_path FROM deployments 
        WHERE id = ? AND user_id = ?
    ''', (deployment_id, session['user_id']), fetch_one=True)
    
    if not deployment:
        print(f"[DEPLOYMENT LOGS] FAILED - Deployment {deployment_id} not found for user {user_id}")
        return jsonify({'error': 'Deployment not found'}), 404
    
    # Extract deployment path safely
    if isinstance(deployment, (list, tuple)) and len(deployment) > 0:
        deploy_path = str(deployment[0])
    elif hasattr(deployment, '__getitem__'):
        deploy_path = str(deployment[0])
    else:
        deploy_path = str(deployment)
    
    log_file = os.path.join(deploy_path, 'deployment.log')
    
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

@api_bp.route('/qchat_developer', methods=['POST'])
def api_qchat_developer():
    from flask import Response, stream_with_context
    import json
    import subprocess
    import re
    import time
    
    user_id = session.get('user_id', 'anonymous')
    
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    data = request.get_json()
    message = data.get('message', '').strip()
    application_name = data.get('application_name', '')
    application_folder = data.get('application_folder', '')
    
    if not message:
        return jsonify({'error': 'Message required'}), 400
    
    user_details = db_manager.execute_query(
        'SELECT username, email, first_name, last_name FROM users WHERE id = ?', 
        (session['user_id'],), fetch_one=True
    )
    
    username = user_details[0] if user_details else 'user'
    user_email = user_details[1] if user_details else 'user@example.com'
    user_name = f"{user_details[2] or ''} {user_details[3] or ''}" if user_details else 'User'
    description = f"Application: {application_name}, Path: {application_folder}" if application_name else ''
    
    def generate():
        import datetime
        
        try:
            yield f"data: {json.dumps({'chunk': 'Starting Q Chat Developer session...'})}\n\n"
            
            # Build prompt directly here
            timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            branch_name = f"{session['user_id']}-automorph-{application_name}-{timestamp}"
            
            # Use provided app folder or default REPO_DIR
            repo_dir = application_folder if application_folder else "/home/ubuntu/deployments/"
            repo_github_url = f"git@github.com:Sam9682/{application_name}" if application_name else "git@github.com:Sam9682/"
            repo_gitea_url = f"http://gitadmin:password@localhost:3000/gitadmin/{branch_name}"
            
            yield f"data: {json.dumps({'chunk': f'App: {application_name}, Folder: {repo_dir}'})}\n\n"
            
            prompt = f"""
You are an autonomous Operations/code agent running on a Linux server
with access to the local filesystem and shell commands.

The application source code is located in the following git repository:
  REPO_DIR = "{repo_dir}"

This repository is the one used by docker-compose to run the application.
The deployment command is executed from the repo root:
  docker-compose up -d --build

There is a local Github instance reachable with the Git URL:
  GITHUB_REMOTE_URL = "{repo_github_url}"

Your goal is to:
  - modify the source code according to the user request,
  - commit the changes on a new branch,
  - push this branch to the local Gitea remote,
  - rebuild and redeploy the running application with docker-compose.

USER REQUEST (what must be changed in the app):
\"\"\"{message}\"\"\"

Follow these steps EXACTLY:

1. Change directory to the repository:
   cd {repo_dir}

2. Check that the working tree is clean (no uncommitted changes).
   If there are local changes, STOP and print a clear error message,
   do NOT try to auto-commit existing local changes.

3. Ensure that a git remote named 'gitea' exists and points to:
     {repo_gitea_url}
   - If 'gitea' does not exist, add it:
       git remote add gitea {repo_gitea_url}
   - If 'gitea' exists but with a different URL, update it:
       git remote set-url gitea {repo_gitea_url}

4. Fetch from 'origin':
     git pull origin

5. Determine the default branch (prefer 'main', otherwise 'master', otherwise stay on current).
   Then create and checkout a new local branch named:
     {branch_name}
   starting from the default branch, for example:
     git checkout -b {branch_name}

6. Inspect the codebase to find the relevant files (e.g. main app entrypoints, routes, services, etc.)
   and implement the USER REQUEST in a minimal, clean and maintainable way.
   - Update only the necessary files.
   - Keep coding style consistent with the existing project.

7. If there is a test suite (for example 'pytest', 'npm test', 'pnpm test', 'make test', etc.),
   try to detect it and run it.
   - If tests FAIL, revert the modifications or reset the branch to the previous state,
     and STOP with a clear error message (do NOT push a broken branch).

8. Stage and commit the changes with a clear message that includes the user request, e.g.:
     git status
     git add .
     git commit -m "Auto-update: {message}"

9. Push the new branch to the 'gitea' remote:
     git push gitea --all

10. Update table Application from swautomorph.db localted in ~/swautomorph/softfluid/db/ folder, 
    set the field 'gitea_url' of Deployments table to the value '{repo_gitea_url}' where application_name = '{application_name}'

11. Rebuild and redeploy the running application by executing:
      deployApp.sh stop
      deployApp.sh start {session['user_id']} {user_name}
    from the repository root ({repo_dir}).

12. At the end, print a short summary including:
    - the branch name,
    - the git commit hash,
    - the result of the docker-compose command (success or failure),
    - and any warnings (e.g. tests were not found, tests were skipped, etc.).

If ANY step fails, explain clearly which step failed and why.
"""
            
            # Find qchat command
            qchat_paths = ['/home/ubuntu/.local/bin/qchat', '/usr/local/bin/qchat', '/usr/bin/qchat', 'qchat']
            qchat_cmd = None
            for path in qchat_paths:
                try:
                    result = subprocess.run([path, '--version'], capture_output=True, timeout=5)
                    if result.returncode == 0:
                        qchat_cmd = path
                        break
                except:
                    continue
            
            if not qchat_cmd:
                yield f"data: {json.dumps({'error': 'Q Chat not found in paths: ' + str(qchat_paths)})}\n\n"
                return
            
            yield f"data: {json.dumps({'chunk': f'Found Q Chat at: {qchat_cmd}'})}\n\n"
            
            cmd_args = [qchat_cmd, 'chat', '--trust-all-tools', prompt]
            qchat_env = os.environ.copy()
            qchat_env.update({'HOME': '/home/ubuntu', 'USER': 'ubuntu', 'PATH': '/home/ubuntu/.local/bin:' + qchat_env.get('PATH', '')})
            
            yield f"data: {json.dumps({'chunk': 'Executing Q Chat command...'})}\n\n"
            
            process = subprocess.Popen(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                      text=True, bufsize=1, env=qchat_env)
            
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            
            for line in iter(process.stdout.readline, ''):
                if line:
                    clean_line = ansi_escape.sub('', line.rstrip())
                    if clean_line and 'Thinking...' not in clean_line:
                        yield f"data: {json.dumps({'chunk': clean_line})}\n\n"
            
            process.wait()
            yield f"data: {json.dumps({'done': True, 'success': process.returncode == 0, 'returncode': process.returncode})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'error': f'Exception in generate(): {str(e)}'})}\n\n"
    
    return Response(stream_with_context(generate()), mimetype='text/event-stream',
                   headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})

@api_bp.route('/qchat_operations', methods=['POST'])
def api_qchat_operations():
    from flask import Response, stream_with_context
    import json
    import subprocess
    import re
    import time
    import sys
    import os
    
    user_id = session.get('user_id', 'anonymous')
    
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    data = request.get_json()
    message = data.get('message', '').strip()
    application_name = data.get('application_name', '')
    application_folder = data.get('application_folder', '')
    
    if not message:
        return jsonify({'error': 'Message required'}), 400
    
    user_details = db_manager.execute_query(
        'SELECT username, email, first_name, last_name FROM users WHERE id = ?', 
        (session['user_id'],), fetch_one=True
    )
    
    username = user_details[0] if user_details else 'user'
    user_email = user_details[1] if user_details else 'user@example.com'
    user_name = f"{user_details[2] or ''} {user_details[3] or ''}" if user_details else 'User'
    description = f"Application: {application_name}, Path: {application_folder}" if application_name else ''
    
    def generate():
        import os
        
        try:
            yield f"data: {json.dumps({'chunk': 'Starting Q Chat DevOps session...'})}\n\n"
            
            # Build prompt directly here instead of calling process_qchat_devops
            # Detect application management actions
            bracket_match = re.search(r'\[(START|STOP|RESTART|PS|LOGS)\]', message.upper())
            
            detected_action = None
            
            if bracket_match:
                detected_action = bracket_match.group(1).lower()
                yield f"data: {json.dumps({'chunk': f'Detected bracketed action: {detected_action.upper()}'})}\n\n"
            else:
                # Fallback to keyword detection
                action_keywords = {
                    'start': ['start', 'deploy', 'launch', 'run'],
                    'stop': ['stop', 'shutdown', 'halt', 'terminate'],
                    'restart': ['restart', 'reboot', 'reload'],
                    'ps': ['status', 'ps', 'check', 'running'],
                    'logs': ['logs', 'log', 'output', 'console']
                }
                
                question_lower = message.lower()
                
                for action, keywords in action_keywords.items():
                    if any(keyword in question_lower for keyword in keywords):
                        detected_action = action
                        break
            
            # Load context from shared folder if action detected
            if detected_action:
                context_file = f"/home/ubuntu/ai-swautomorph/shared/{detected_action.upper()}_context.md"
                
                if os.path.exists(context_file):
                    yield f"data: {json.dumps({'chunk': f'Loading context from {detected_action.upper()}_context.md'})}\n\n"
                    
                    with open(context_file, 'r') as f:
                        context_template = f.read()
                    
                    # Get application ID from database for APPLICATION_IDENTITY_NUMBER
                    application_id = 0  # Default fallback
                    if application_name:
                        app_data = db_manager.execute_query(
                            'SELECT id FROM applications WHERE name = ?', 
                            (application_name,), fetch_one=True
                        )
                        if app_data:
                            application_id = app_data[0]
                            yield f"data: {json.dumps({'chunk': f'Found application ID: {application_id} for {application_name}'})}\n\n"
                        else:
                            yield f"data: {json.dumps({'chunk': f'Warning: Application {application_name} not found in database, using ID 0'})}\n\n"
                    
                    # Load configuration values from database.py
                    from ..database import load_deploy_config
                    NAME_OF_APPLICATION, _, RANGE_START, RANGE_RESERVED, RANGE_START_CONTROLPLAN, RANGE_RESERVED_CONTROLPLAN = load_deploy_config()
                    
                    # Replace placeholders
                    context = context_template.replace('{USER_ID}', str(session['user_id']))
                    context = context.replace('{USER_NAME}', user_name)
                    context = context.replace('{USER_EMAIL}', user_email)
                    context = context.replace('{DESCRIPTION}', description)
                    context = context.replace('{TAIL_LINES}', '100')
                    
                    # Add configuration variables to context
                    config_vars = f"""
**Configuration Variables:**
- NAME_OF_APPLICATION: {NAME_OF_APPLICATION}
- APPLICATION_IDENTITY_NUMBER: {application_id}
- RANGE_START: {RANGE_START}
- RANGE_RESERVED: {RANGE_RESERVED}
- RANGE_START_CONTROLPLAN: {RANGE_START_CONTROLPLAN}
- RANGE_RESERVED_CONTROLPLAN: {RANGE_RESERVED_CONTROLPLAN}

**Port Calculation (for verification):**
```bash
USER_ID={session['user_id']}
RANGE_START={RANGE_START}
RANGE_RESERVED={RANGE_RESERVED}
APPLICATION_IDENTITY_NUMBER={application_id}
PORT_RANGE_BEGIN=$((RANGE_START + USER_ID * RANGE_RESERVED))
HTTP_PORT=$((PORT_RANGE_BEGIN + APPLICATION_IDENTITY_NUMBER * 2))
HTTPS_PORT=$((HTTP_PORT + 1))
echo "PORT_RANGE_BEGIN: $PORT_RANGE_BEGIN"
echo "HTTP_PORT: $HTTP_PORT"
echo "HTTPS_PORT: $HTTPS_PORT"
```

"""
                    
                    # Extract application folder from description if present
                    app_folder = ''
                    if 'Path:' in description:
                        parts = description.split('Path:')
                        if len(parts) > 1:
                            app_folder = parts[1].strip()
                    
                    prompt = f"""
You are an autonomous DevOps agent with access to execute shell commands on a Linux server.

The user has requested an application management action.

User Request: {message}

{'Application Folder: ' + app_folder if app_folder else ''}

{config_vars}

Follow the instructions below to execute the {detected_action.upper()} action:

{context}

IMPORTANT: Execute all commands in the application folder: {app_folder if app_folder else '/home/ubuntu/deployments/[username]/[appname]'}

Execute all required steps and provide a clear summary of the results.
"""
                else:
                    yield f"data: {json.dumps({'chunk': f'Context file not found: {context_file}, using default Q&A mode'})}\n\n"
                    prompt = f"""
You are a helpful Virtual Advisor assistant. Answer the user's question clearly and concisely.
Do not execute any commands or modify any files. Just provide helpful information and guidance.

User Question: {message}

Provide a helpful and informative response.
"""
            else:
                # Simple prompt for Q&A without code execution
                prompt = f"""
You are a helpful Virtual Advisor assistant. Answer the user's question clearly and concisely.
Do not execute any commands or modify any files. Just provide helpful information and guidance.

User Question: {message}

Provide a helpful and informative response.
"""
            
            # Find qchat command
            qchat_paths = ['/home/ubuntu/.local/bin/qchat', '/usr/local/bin/qchat', '/usr/bin/qchat', 'qchat']
            qchat_cmd = None
            for path in qchat_paths:
                try:
                    result = subprocess.run([path, '--version'], capture_output=True, timeout=5)
                    if result.returncode == 0:
                        qchat_cmd = path
                        break
                except:
                    continue
            
            if not qchat_cmd:
                yield f"data: {json.dumps({'error': 'Q Chat not found in paths: ' + str(qchat_paths)})}\n\n"
                return
            
            yield f"data: {json.dumps({'chunk': f'Found Q Chat at: {qchat_cmd}'})}\n\n"
            
            # Use --trust-all-tools if action detected (needs command execution)
            cmd_args = [qchat_cmd, 'chat']
            if detected_action:
                cmd_args.append('--trust-all-tools')
            cmd_args.append(prompt)
            
            qchat_env = os.environ.copy()
            qchat_env.update({'HOME': '/home/ubuntu', 'USER': 'ubuntu', 'PATH': '/home/ubuntu/.local/bin:' + qchat_env.get('PATH', '')})
            
            yield f"data: {json.dumps({'chunk': 'Executing Q Chat command...'})}\n\n"
            
            process = subprocess.Popen(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                      text=True, bufsize=1, env=qchat_env)
            
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            
            for line in iter(process.stdout.readline, ''):
                if line:
                    clean_line = ansi_escape.sub('', line.rstrip())
                    if clean_line and 'Thinking...' not in clean_line:
                        yield f"data: {json.dumps({'chunk': clean_line})}\n\n"
            
            process.wait()
            
            # Record billing activity for START and STOP actions if successful
            if (detected_action == 'start' or detected_action == 'stop') and process.returncode == 0 and application_name:
                try:
                    from .billing_routes import record_billing_activity
                    record_billing_activity(session['user_id'], application_name, detected_action)
                    yield f"data: {json.dumps({'chunk': f'Billing activity recorded for {detected_action.upper()} action on {application_name}'})}\n\n"
                except Exception as billing_error:
                    yield f"data: {json.dumps({'chunk': f'Warning: Failed to record billing activity: {str(billing_error)}'})}\n\n"
            
            yield f"data: {json.dumps({'done': True, 'success': process.returncode == 0, 'returncode': process.returncode})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'error': f'Exception in generate(): {str(e)}'})}\n\n"
    
    return Response(stream_with_context(generate()), mimetype='text/event-stream',
                   headers={
                       'Cache-Control': 'no-cache',
                       'X-Accel-Buffering': 'no',
                       'Connection': 'keep-alive'
                   })

@api_bp.route('/database/tables/<table_name>', methods=['GET', 'POST'])
def api_database_table(table_name):
    """Database table management endpoint"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    # Check if user is admin
    user = db_manager.execute_query(
        'SELECT username FROM users WHERE id = ?', 
        (session['user_id'],), fetch_one=True
    )
    
    if not user or user[0] != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    # Validate table name to prevent SQL injection
    allowed_tables = [
        'users', 'applications', 'auth_tokens', 'user_applications', 
        'deployments', 'servers', 'application_costs', 'billing_activities', 'users_logs'
    ]
    
    if table_name not in allowed_tables:
        return jsonify({'error': 'Invalid table name'}), 400
    
    if request.method == 'GET':
        try:
            # Get table structure
            columns_data = db_manager.execute_query(
                f'PRAGMA table_info({table_name})', fetch_all=True
            )
            columns = [col[1] for col in columns_data]  # col[1] is the column name
            
            # Get table data
            rows = db_manager.execute_query(
                f'SELECT * FROM {table_name} ORDER BY id DESC LIMIT 100', fetch_all=True
            )
            
            return jsonify({
                'columns': columns,
                'rows': rows
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            # Build INSERT query dynamically
            columns = list(data.keys())
            placeholders = ', '.join(['?' for _ in columns])
            column_names = ', '.join(columns)
            values = [data[col] for col in columns]
            
            query = f'INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})'
            db_manager.execute_query(query, values)
            
            return jsonify({'message': 'Record added successfully'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@api_bp.route('/servers', methods=['GET', 'POST'])
def api_servers():
    """Server management endpoint"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    # Check if user is admin
    user = db_manager.execute_query(
        'SELECT username FROM users WHERE id = ?', 
        (session['user_id'],), fetch_one=True
    )
    
    if not user or user[0] != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    if request.method == 'GET':
        servers = db_manager.execute_query('''
            SELECT id, SERVER_IP, SERVER_NAME, SERVER_CAPACITY_USER_MAX, 
                   SERVER_CAPACITY_APPLI_MAX, SERVER_STATUS, SERVER_TYPE, created_at
            FROM servers ORDER BY id
        ''', fetch_all=True)
        
        servers_list = [{
            'id': row[0],
            'SERVER_IP': row[1],
            'SERVER_NAME': row[2],
            'SERVER_CAPACITY_USER_MAX': row[3],
            'SERVER_CAPACITY_APPLI_MAX': row[4],
            'SERVER_STATUS': row[5],
            'SERVER_TYPE': row[6],
            'created_at': row[7]
        } for row in servers]
        
        return jsonify(servers_list)
    
    elif request.method == 'POST':
        data = request.get_json()
        
        try:
            db_manager.execute_query('''
                INSERT INTO servers (SERVER_IP, SERVER_NAME, SERVER_CAPACITY_USER_MAX, 
                                   SERVER_CAPACITY_APPLI_MAX, SERVER_STATUS, SERVER_TYPE)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (data['SERVER_IP'], data['SERVER_NAME'], data['SERVER_CAPACITY_USER_MAX'],
                  data['SERVER_CAPACITY_APPLI_MAX'], data['SERVER_STATUS'], data['SERVER_TYPE']))
            
            return jsonify({'message': 'Server created successfully'}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@api_bp.route('/servers/<int:server_id>', methods=['PUT', 'DELETE'])
def api_server_actions(server_id):
    """Server update/delete endpoint"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    # Check if user is admin
    user = db_manager.execute_query(
        'SELECT username FROM users WHERE id = ?', 
        (session['user_id'],), fetch_one=True
    )
    
    if not user or user[0] != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    if request.method == 'PUT':
        data = request.get_json()
        
        try:
            db_manager.execute_query('''
                UPDATE servers SET SERVER_IP = ?, SERVER_NAME = ?, 
                                 SERVER_CAPACITY_USER_MAX = ?, SERVER_CAPACITY_APPLI_MAX = ?,
                                 SERVER_STATUS = ?, SERVER_TYPE = ?
                WHERE id = ?
            ''', (data['SERVER_IP'], data['SERVER_NAME'], data['SERVER_CAPACITY_USER_MAX'],
                  data['SERVER_CAPACITY_APPLI_MAX'], data['SERVER_STATUS'], data['SERVER_TYPE'], server_id))
            
            return jsonify({'message': 'Server updated successfully'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'DELETE':
        # Check if server is ACTIVE
        server = db_manager.execute_query(
            'SELECT SERVER_STATUS FROM servers WHERE id = ?', 
            (server_id,), fetch_one=True
        )
        
        if not server:
            return jsonify({'error': 'Server not found'}), 404
        
        if server[0] == 'ACTIVE':
            return jsonify({'error': 'Cannot delete ACTIVE server'}), 400
        
        try:
            db_manager.execute_query('DELETE FROM servers WHERE id = ?', (server_id,))
            return jsonify({'message': 'Server deleted successfully'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@api_bp.route('/server/allocate', methods=['POST'])
def api_server_allocate():
    """Allocate server for deployment based on capacity constraints"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    data = request.get_json()
    application_name = data.get('application_name')
    
    if not application_name:
        return jsonify({'error': 'Application name required'}), 400
    
    try:
        # Find available server based on capacity constraints
        servers = db_manager.execute_query('''
            SELECT id, SERVER_CAPACITY_USER_MAX, SERVER_CAPACITY_APPLI_MAX 
            FROM servers 
            WHERE SERVER_STATUS = 'STAND_BY' OR SERVER_STATUS = 'ACTIVE'
            ORDER BY SERVER_STATUS ASC
        ''', fetch_all=True)
        
        if not servers:
            return jsonify({'error': 'No standby servers available'}), 503
        
        for server in servers:
            server_id, user_max, appli_max = server
            
            # Check current usage for this server
            user_count = db_manager.execute_query('''
                SELECT COUNT(DISTINCT user_id) 
                FROM deployments 
                WHERE server_id = ?
            ''', (server_id,), fetch_one=True)[0] or 0
            
            appli_count = db_manager.execute_query('''
                SELECT COUNT(DISTINCT application_name) 
                FROM deployments 
                WHERE server_id = ?
            ''', (server_id,), fetch_one=True)[0] or 0
            
            # Check if server has capacity
            if user_count < user_max and appli_count < appli_max:
                # Update server status to ACTIVE only if currently STAND_BY
                db_manager.execute_query('''
                    UPDATE servers SET SERVER_STATUS = 'ACTIVE' 
                    WHERE id = ? AND SERVER_STATUS = 'STAND_BY'
                ''', (server_id,))
                
                return jsonify({'server_id': server_id})
        
        return jsonify({'error': 'All servers at capacity'}), 503
        
    except Exception as e:
        return jsonify({'error': f'Server allocation failed: {str(e)}'}), 500

@api_bp.route('/database/tables/<table_name>/<record_id>', methods=['PUT', 'DELETE'])
def api_database_record(table_name, record_id):
    """Database record management endpoint"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    # Check if user is admin
    user = db_manager.execute_query(
        'SELECT username FROM users WHERE id = ?', 
        (session['user_id'],), fetch_one=True
    )
    
    if not user or user[0] != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    # Validate table name
    allowed_tables = [
        'users', 'applications', 'auth_tokens', 'user_applications', 
        'deployments', 'servers', 'application_costs', 'billing_activities', 'users_logs'
    ]
    
    if table_name not in allowed_tables:
        return jsonify({'error': 'Invalid table name'}), 400
    
    if request.method == 'PUT':
        try:
            data = request.get_json()
            
            # Build UPDATE query dynamically
            set_clauses = []
            values = []
            
            for column, value in data.items():
                if column.lower() != 'id':  # Don't update ID
                    set_clauses.append(f'{column} = ?')
                    values.append(value)
            
            if not set_clauses:
                return jsonify({'error': 'No fields to update'}), 400
            
            values.append(record_id)  # Add ID for WHERE clause
            set_clause = ', '.join(set_clauses)
            query = f'UPDATE {table_name} SET {set_clause} WHERE id = ?'
            
            db_manager.execute_query(query, values)
            
            return jsonify({'message': 'Record updated successfully'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'DELETE':
        try:
            db_manager.execute_query(f'DELETE FROM {table_name} WHERE id = ?', (record_id,))
            return jsonify({'message': 'Record deleted successfully'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500