"""API routes"""
from flask import Blueprint, request, jsonify, session, Response, stream_with_context
from werkzeug.security import generate_password_hash
import sqlite3
import os
import requests
import json
import subprocess
from datetime import datetime
from ..config import DB_PATH, TRANSLATIONS, OUTPUT_PRINT_LOGS_FILENAME, \
    TIMEOUT_GITEA_HTTP_POST, TIMEOUT_SUBPROCESS_RUN, TIMEOUT_QCHAT_DEVELOPER_RUN, \
    TIMEOUT_CLEAN_SHUTDOWN, TIMEOUT_QCHAT_OPERATOR_RUN
from ..database import db_manager
from ..db_health import check_database_health, get_database_stats

def get_language():
    return session.get('language', 'en')

def get_text(key):
    try:
        lang = get_language()
        return TRANSLATIONS.get(lang, {}).get(key, TRANSLATIONS['en'].get(key, key))
    except (KeyError, AttributeError, TypeError):
        return key

def log_with_timestamp(message):
    """Log message with datetime timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] {message}"
    print(log_message)
    try:
        with open(OUTPUT_PRINT_LOGS_FILENAME, 'a') as f:
            f.write(log_message + '\n')
    except (IOError, OSError) as e:
        print(f"Warning: Failed to write to log file: {e}")

api_bp = Blueprint('api', __name__, url_prefix='/api')

def return_prompt_for_developer(detected_action, application_name, application_folder, user_name, user_email, version = 'default'):

    l_prompt = ''

    # 🧠 Prompt complet envoyé à Q Chat
    if (version == 'default'):
        # Sanitize detected_action to prevent path traversal
        if not detected_action or not isinstance(detected_action, str):
            log_with_timestamp(f'AI Chat Developer - Security: Invalid detected_action input rejected: {repr(detected_action)}')
            return ''
        
        # Remove any path traversal characters and limit to alphanumeric + underscore
        original_action = detected_action
        safe_action = ''.join(c for c in detected_action.upper() if c.isalnum() or c == '_')[:50]
        if not safe_action or safe_action != original_action.upper():
            log_with_timestamp(f'AI Chat Developer - Security: Potentially malicious detected_action sanitized from "{original_action}" to "{safe_action}"')
            if not safe_action:
                return ''
        
        context_file = f"/home/ubuntu/ai-swautomorph/shared/{safe_action}_context.md"
        
        if os.path.exists(context_file):
            log_with_timestamp(f'AI Chat Developer - Loading context from {detected_action.upper()}_context.md')

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
                    log_with_timestamp( f"data: {json.dumps({'chunk': f'Found application ID: {application_id} for {application_name}'})}\n\n")
                else:
                    log_with_timestamp( f"data: {json.dumps({'chunk': f'Warning: Application {application_name} not found in database, using ID 0'})}\n\n")
            
            # Load configuration values from database.py (unused but required for context)
            from ..database import load_deploy_config
            _ = load_deploy_config()  # Load but don't unpack unused variables
            
            # Replace placeholders
            try:
                l_prompt = context_template.replace('{USER_ID}', str(session.get('user_id', 0)))
                l_prompt = l_prompt.replace('{USER_NAME}', user_name or '')
                l_prompt = l_prompt.replace('{USER_EMAIL}', user_email or '')
                l_prompt = l_prompt.replace('{TAIL_LINES}', '100')
                l_prompt = l_prompt.replace('{APPLICATION_FOLDER}', application_folder)
            except KeyError as e:
                log_with_timestamp(f'AI Chat Developer - Session key error: {str(e)}')
                l_prompt = ''

    return l_prompt

def _create_fallback_prompt(message):
    """Create fallback Q&A prompt for invalid actions"""
    return f"""You are a helpful Virtual Advisor assistant. Answer the user's question clearly and concisely.
Do not execute any commands or modify any files. Just provide helpful information and guidance.
User Question: {message}
Provide a helpful and informative response.
"""

def return_prompt_for_operator(detected_action, application_name, application_folder, user_name, user_email, message, version = 'default'):

    l_prompt = ''

    # 🧠 Prompt sent to Q Chat
    if (version == 'default'):
        # Sanitize detected_action to prevent path traversal
        if not detected_action or not isinstance(detected_action, str):
            log_with_timestamp(f'AI Chat Operator - Context file not found: invalid action, using default Q&A mode')
            return _create_fallback_prompt(message)
        
        # Remove any path traversal characters and limit to alphanumeric + underscore
        safe_action = ''.join(c for c in detected_action.upper() if c.isalnum() or c == '_')[:50]
        if not safe_action:
            log_with_timestamp(f'AI Chat Operator - Context file not found: invalid action, using default Q&A mode')
            return _create_fallback_prompt(message)
        
        context_file = f"/home/ubuntu/ai-swautomorph/shared/{safe_action}_context.md"
                
        if os.path.exists(context_file):
            log_with_timestamp(f'AI Chat Operator - Loading context from {detected_action.upper()}_context.md')
            
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
                    log_with_timestamp( f"data: {json.dumps({'chunk': f'Found application ID: {application_id} for {application_name}'})}\n\n")
                else:
                    log_with_timestamp( f"data: {json.dumps({'chunk': f'Warning: Application {application_name} not found in database, using ID 0'})}\n\n")

            # Load configuration values from database.py (unused but required for context)
            from ..database import load_deploy_config
            _ = load_deploy_config()  # Load but don't unpack unused variables
            
            # Replace placeholders
            try:
                l_prompt = context_template.replace('{USER_ID}', str(session.get('user_id', 0)))
                l_prompt = l_prompt.replace('{USER_NAME}', user_name or '')
                l_prompt = l_prompt.replace('{USER_EMAIL}', user_email or '')
                l_prompt = l_prompt.replace('{TAIL_LINES}', '100')
                l_prompt = l_prompt.replace('{APPLICATION_FOLDER}', application_folder)
            except KeyError as e:
                log_with_timestamp(f'AI Chat Operator - Session key error: {str(e)}')
                l_prompt = ''
        else:
            log_with_timestamp(f'AI Chat Operator - Context file not found: {context_file}, using default Q&A mode')
            l_prompt = _create_fallback_prompt(message)
            log_with_timestamp(f'AI Chat Operator - (Context {context_file} not found) Prompt : {l_prompt[:120]}')

    return l_prompt

def create_gitea_user(username, email, password, first_name='', last_name=''):
    """Create user in Gitea server"""
    try:
        # Gitea API endpoint
        gitea_url = 'http://localhost:3000/api/v1/admin/users'
        
        # Get admin token for Gitea API
        admin_token = get_gitea_admin_token()
        
        if not admin_token:
            log_with_timestamp(f"[GITEA] Failed to get admin token for user creation: {username}")
            return False
        
        # User data for Gitea
        full_name = ''
        if first_name or last_name:
            full_name = f"{first_name} {last_name}".strip()
        
        user_data = {
            'username': username,
            'email': email,
            'password': password,
            'full_name': full_name,
            'must_change_password': False,
            'send_notify': False
        }
        
        headers = {
            'Authorization': f'token {admin_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(gitea_url, json=user_data, headers=headers, timeout=TIMEOUT_GITEA_HTTP_POST)
        
        if response.status_code == 201:
            log_with_timestamp(f"[GITEA] User {username} created successfully")
            return True
        else:
            log_with_timestamp(f"[GITEA] Failed to create user {username}: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        log_with_timestamp(f"[GITEA] Error creating user {username}: {str(e)}")
        return False

def get_gitea_admin_token():
    """Get or create admin token for Gitea API access"""
    try:
        # Try to get existing token from file
        token_file = '/tmp/gitea_admin_token'
        if os.path.exists(token_file):
            try:
                with open(token_file, 'r') as f:
                    return f.read().strip()
            except (IOError, OSError) as e:
                log_with_timestamp(f"[GITEA] Error reading token file: {str(e)}")
                return None
        
        # If no token file, return None (manual setup required)
        log_with_timestamp("[GITEA] No admin token found. Manual Gitea setup required.")
        return None
        
    except Exception as e:
        log_with_timestamp(f"[GITEA] Error getting admin token: {str(e)}")
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
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT username FROM users WHERE id = ?', (session['user_id'],))
        user = cursor.fetchone()
        
        if not user or user[0] != 'admin':
            conn.close()
            return jsonify({'error': 'Admin access required'}), 403
        
        if request.method == 'PUT':
            data = request.get_json()
            name = data.get('name')
            description = data.get('description', '')
            
            if not name:
                conn.close()
                return jsonify({'error': 'Name required'}), 400
            
            git_url = data.get('git_url', '')
            git_repo_size = data.get('git_repo_size', 50)
            docker_build_duration = data.get('docker_build_duration')
            docker_start_duration = data.get('docker_start_duration')
            docker_stop_duration = data.get('docker_stop_duration')
            docker_ps_duration = data.get('docker_ps_duration')
            
            cursor.execute('''
                UPDATE applications SET name = ?, description = ?, git_url = ?, git_repo_size = ?,
                       docker_build_duration = ?, docker_start_duration = ?, docker_stop_duration = ?, docker_ps_duration = ?
                WHERE id = ?
            ''', (name, description, git_url, git_repo_size, docker_build_duration, docker_start_duration, docker_stop_duration, docker_ps_duration, app_id))
            conn.commit()
            conn.close()
            return jsonify({'message': 'Application updated successfully'})
        
        elif request.method == 'DELETE':
            cursor.execute('DELETE FROM applications WHERE id = ?', (app_id,))
            conn.commit()
            conn.close()
            return jsonify({'message': 'Application deleted successfully'})
            
    except sqlite3.Error as e:
        if 'conn' in locals():
            conn.close()
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        if 'conn' in locals():
            conn.close()
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@api_bp.route('/users', methods=['GET', 'POST'])
def api_users():
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    # Check if user is admin
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT username FROM users WHERE id = ?', (session['user_id'],))
        user = cursor.fetchone()
        
        if not user or user[0] != 'admin':
            conn.close()
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
                conn.close()
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
                try:
                    from ..database import assign_default_apps_to_user
                    assign_default_apps_to_user(user_id)
                except Exception as e:
                    log_with_timestamp(f"Warning: Failed to assign default apps to user {user_id}: {str(e)}")
                
                # Create user in Gitea
                create_gitea_user(username, email, password, first_name, last_name)
                
                return jsonify({'message': 'User created successfully'}), 201
            except sqlite3.IntegrityError:
                conn.close()
                return jsonify({'error': 'Username or email already exists'}), 409
            except Exception as e:
                conn.close()
                return jsonify({'error': f'Database error: {str(e)}'}), 500
                
    except sqlite3.Error as e:
        if 'conn' in locals():
            conn.close()
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        if 'conn' in locals():
            conn.close()
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@api_bp.route('/users/<int:user_id>', methods=['PUT', 'DELETE'])
def api_user_actions(user_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    # Check if user is admin
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT username FROM users WHERE id = ?', (session['user_id'],))
        user = cursor.fetchone()
        
        if not user or user[0] != 'admin':
            conn.close()
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
                    conn.close()
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
            
    except sqlite3.Error as e:
        if 'conn' in locals():
            conn.close()
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        if 'conn' in locals():
            conn.close()
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@api_bp.route('/users/<int:user_id>/applications', methods=['GET', 'POST', 'DELETE'])
def api_user_applications(user_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    # Check if user is admin
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT username FROM users WHERE id = ?', (session['user_id'],))
        user = cursor.fetchone()
        
        if not user or user[0] != 'admin':
            conn.close()
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
                conn.close()
                return jsonify({'error': 'Application ID required'}), 400
            
            try:
                # Calculate ports for the user and application
                from ..database import calculate_app_ports
                HTTP_PORT, HTTPS_PORT, HTTP_PORT2, HTTPS_PORT2 = calculate_app_ports(user_id, app_id)
                
                # Get application name for URL generation
                cursor.execute('SELECT name FROM applications WHERE id = ?', (app_id,))
                app_result = cursor.fetchone()
                if not app_result:
                    conn.close()
                    return jsonify({'error': 'Application not found'}), 404
                
                app_name = app_result[0]
                url = f'https://www.swautomorph.com:{HTTPS_PORT}'
                
                cursor.execute('INSERT INTO user_applications (user_id, application_id, url, http_port, https_port, http_port2, https_port2) VALUES (?, ?, ?, ?, ?, ?, ?)',
                              (user_id, app_id, url, HTTP_PORT, HTTPS_PORT, HTTP_PORT2, HTTPS_PORT2))
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
                conn.close()
                return jsonify({'error': 'Application ID required'}), 400
            
            cursor.execute('DELETE FROM user_applications WHERE user_id = ? AND application_id = ?',
                          (user_id, app_id))
            conn.commit()
            conn.close()
            return jsonify({'message': 'Application unassigned successfully'})
            
    except sqlite3.Error as e:
        if 'conn' in locals():
            conn.close()
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        if 'conn' in locals():
            conn.close()
        return jsonify({'error': f'Server error: {str(e)}'}), 500

def _handle_clone_action(user_id, app_name, git_url, server_id, deployment_path, data):
    """Handle clone deployment action"""
    import subprocess
    import os
    import shutil
    import socket
    from flask import Response, stream_with_context
    import json
    
    if not git_url:
        log_with_timestamp(f"[DEPLOYMENT API] CLONE - FAILED - No git_url provided for user {user_id}")
        return jsonify({'error': 'Git URL required for clone action'}), 400
    
    if not server_id:
        log_with_timestamp(f"[DEPLOYMENT API] CLONE - FAILED - No server_id provided for user {user_id}")
        return jsonify({'error': 'Server ID required for clone action'}), 400
    
    log_with_timestamp(f"[DEPLOYMENT API] CLONE - Starting clone from {git_url} to {deployment_path}")
    
    # Get current and target server IPs
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        current_server_ip = s.getsockname()[0]
        s.close()
    except (OSError, socket.error) as e:
        log_with_timestamp(f"[DEPLOYMENT API] CLONE - Warning: Failed to get current server IP: {str(e)}")
        current_server_ip = "127.0.0.1"
    
    target_server = db_manager.execute_query(
        'SELECT SERVER_IP FROM servers WHERE id = ?', 
        (server_id,), fetch_one=True
    )
    
    if not target_server:
        log_with_timestamp(f"[DEPLOYMENT API] CLONE - FAILED - Server {server_id} not found")
        return jsonify({'error': f'Server {server_id} not found'}), 400
    
    target_server_ip = target_server[0]
    is_local_server = (target_server_ip == current_server_ip or target_server_ip == "127.0.0.1" or target_server_ip == "localhost")
    
    # Execute clone operation
    if is_local_server:
        if os.path.exists(deployment_path):
            shutil.rmtree(deployment_path)
        os.makedirs(deployment_path, exist_ok=True)
        
        git_env = os.environ.copy()
        git_env.update({'GIT_CONFIG_NOSYSTEM': '1', 'HOME': '/home/ubuntu', 'USER': 'ubuntu'})
        result = subprocess.run(['git', 'clone', '--recurse-submodules', git_url, deployment_path], 
                              capture_output=True, text=True, timeout=TIMEOUT_SUBPROCESS_RUN, env=git_env)
    else:
        ssh_commands = [
            f"rm -rf {deployment_path}",
            f"mkdir -p {deployment_path}",
            f"cd {os.path.dirname(deployment_path)} && git clone --recurse-submodules {git_url} {os.path.basename(deployment_path)}"
        ]
        ssh_command = f"ssh -o StrictHostKeyChecking=no ubuntu@{target_server_ip} '{'; '.join(ssh_commands)}'"
        result = subprocess.run(ssh_command, shell=True, capture_output=True, text=True, timeout=TIMEOUT_SUBPROCESS_RUN)
    
    # Handle result
    output_parts = []
    if result.stdout and result.stdout.strip():
        output_parts.append(f"STDOUT:\n{result.stdout}")
    if result.stderr and result.stderr.strip():
        output_parts.append(f"STDERR:\n{result.stderr}")
    command_output = "\n\n".join(output_parts) if output_parts else "No output"
    
    if result.returncode == 0:
        status = 'cloned'
        # Record deployment
        existing_record = db_manager.execute_query(
            'SELECT id FROM deployments WHERE user_id = ? AND application_name = ? AND server_id = ?',
            (user_id, app_name, server_id), fetch_one=True
        )
        
        if existing_record:
            db_manager.execute_query(
                'UPDATE deployments SET status = ?, deployment_path = ?, git_url = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ? AND application_name = ? AND server_id = ?',
                (status, deployment_path, git_url, session['user_id'], app_name, server_id)
            )
        else:
            db_manager.execute_query(
                'INSERT INTO deployments (user_id, application_name, status, deployment_path, git_url, server_id) VALUES (?, ?, ?, ?, ?, ?)',
                (session['user_id'], app_name, status, deployment_path, git_url, server_id)
            )
        
        if data.get('stream', False):
            def generate_clone_response():
                yield f"data: {json.dumps({'chunk': f'Clone completed successfully for {app_name}'})}\n\n"
                yield f"data: {json.dumps({'chunk': f'Repository cloned to: {deployment_path}'})}\n\n"
                yield f"data: {json.dumps({'chunk': command_output})}\n\n"
                yield f"data: {json.dumps({'done': True, 'success': True})}\n\n"
            return Response(stream_with_context(generate_clone_response()), mimetype='text/event-stream',
                           headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})
    else:
        status = 'failed'
        error_msg = f'Git clone failed: {result.stderr}'
        log_with_timestamp(f"[DEPLOYMENT API] CLONE - FAILED - {error_msg}")
        return jsonify({'error': error_msg, 'logs': command_output}), 400
    
    return jsonify({'message': f'Clone completed for {app_name}', 'status': status, 'logs': command_output}), 202

def _handle_app_action(user_id, app_name, action, data):
    """Handle application lifecycle actions (start, stop, restart, ps, logs)"""
    import subprocess
    import os
    from flask import Response, stream_with_context
    import json
    
    # Check if deployment exists
    deployment = db_manager.execute_query(
        'SELECT deployment_path FROM deployments WHERE user_id = ? AND application_name = ? AND status != "failed" ORDER BY updated_at DESC LIMIT 1',
        (user_id, app_name), fetch_one=True
    )
    
    if not deployment:
        log_with_timestamp(f"[DEPLOYMENT API] {action.upper()} - FAILED - No deployment found for app '{app_name}'")
        return jsonify({'error': 'Application not deployed. Clone first.'}), 202
    
    deploy_path = str(deployment[0]) if isinstance(deployment, (list, tuple)) else str(deployment)
    deploy_script = os.path.join(deploy_path, 'deployApp.sh')
    
    if not os.path.exists(deploy_script):
        log_with_timestamp(f"[DEPLOYMENT API] {action.upper()} - FAILED - deployApp.sh not found at {deploy_script}")
        return jsonify({'error': f'deployApp.sh not found in {deploy_script}'}), 202
    
    # Get user details
    user_details = db_manager.execute_query(
        'SELECT username, email, first_name, last_name FROM users WHERE id = ?', 
        (user_id,), fetch_one=True
    )
    user_name = f"{user_details[2] or ''} {user_details[3] or ''}" if user_details else 'User'
    user_email = user_details[1] if user_details else 'user@example.com'
    
    # Execute action
    if data.get('stream', False):
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
                status = 'running' if action.upper() == 'START' else 'STOPPED' if action.upper() == 'STOP' else 'COMPLETED'
                db_manager.execute_query(
                    'UPDATE deployments SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ? AND application_name = ?',
                    (status, user_id, app_name)
                )
                if action.upper() in ['START', 'STOP'] and process.returncode == 0:
                    from .billing_routes import record_billing_activity
                    record_billing_activity(user_id, app_name, action)
                yield f"data: {json.dumps({'done': True, 'success': process.returncode == 0})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        return Response(stream_with_context(generate()), mimetype='text/event-stream',
                       headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})
    else:
        result = subprocess.run([deploy_script, action, str(session['user_id']), user_name, user_email], 
                              cwd=deploy_path, capture_output=True, text=True, timeout=TIMEOUT_SUBPROCESS_RUN)
        
        output_parts = []
        if result.stdout and result.stdout.strip():
            output_parts.append(f"STDOUT:\n{result.stdout}")
        if result.stderr and result.stderr.strip():
            output_parts.append(f"STDERR:\n{result.stderr}")
        command_output = "\n\n".join(output_parts) if output_parts else "No output"
        
        status = 'RUNNING' if action.upper() == 'START' else 'STOPPED' if action.upper() == 'STOP' else 'COMPLETED'
        db_manager.execute_query(
            'UPDATE deployments SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ? AND application_name = ?',
            (status, session['user_id'], app_name)
        )
        
        if action.upper() in ['start', 'stop'] and result.returncode == 0:
            from .billing_routes import record_billing_activity
            record_billing_activity(session['user_id'], app_name, action)
        
        return jsonify({
            'message': f'{action.capitalize()} completed for {app_name}',
            'status': status,
            'logs': command_output
        }), 200

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
    
    log_with_timestamp(f"[DEPLOYMENT API] {method} /api/deployments - User: {user_id}, IP: {remote_ip}, UA: {user_agent[:50]}")
    
    if 'user_id' not in session:
        log_with_timestamp(f"[DEPLOYMENT API] FAILED - Authentication required from {remote_ip}")
        return jsonify({'error': 'Authentication required'}), 401
    
    if request.method == 'GET':
        log_with_timestamp(f"[DEPLOYMENT API] GET - Fetching deployments for user {user_id}")
        deployments_data = db_manager.execute_query('''
            SELECT id, application_name, status, deployment_path, git_url, created_at, updated_at, server_id
            FROM deployments WHERE user_id = ? ORDER BY updated_at DESC
        ''', (session['user_id'],), fetch_all=True)
        
        deployments = [{
            'id': row[0], 'application_name': row[1], 'status': row[2], 'deployment_path': row[3],
            'git_url': row[4], 'created_at': row[5], 'updated_at': row[6], 'server_id': row[7]
        } for row in deployments_data]
        
        log_with_timestamp(f"[DEPLOYMENT API] GET - Returning {len(deployments)} deployments for user {user_id}")
        return jsonify(deployments)
    
    elif request.method == 'POST':
        data = request.get_json()
        action = data.get('action')
        app_name = data.get('application_name')
        git_url = data.get('git_url')
        server_id = data.get('server_id')
        
        log_with_timestamp(f"[DEPLOYMENT API] POST - User {user_id} requesting action '{action}' for app '{app_name}'")
        
        if not all([action, app_name]):
            log_with_timestamp(f"[DEPLOYMENT API] POST - FAILED - Missing action or app_name for user {user_id}")
            return jsonify({'error': 'Action and application name required'}), 400
        
        # Get username for deployment path
        user = db_manager.execute_query(
            'SELECT username FROM users WHERE id = ?', 
            (session['user_id'],), fetch_one=True
        )
        username = user[0] if user else f'user_{session["user_id"]}'
        deployment_path = f'/home/ubuntu/deployments/{username}/{app_name.lower().replace(" ", "-")}'
        
        try:
            if action == 'clone':
                return _handle_clone_action(user_id, app_name, git_url, server_id, deployment_path, data)
            elif action.upper() in ['START', 'STOP', 'RESTART', 'PS', 'LOGS']:
                return _handle_app_action(user_id, app_name, action, data)
            else:
                return jsonify({'error': f'Unknown action: {action}'}), 400
                
        except subprocess.TimeoutExpired:
            log_with_timestamp(f"[DEPLOYMENT API] POST - TIMEOUT - Action '{action}' timed out for app '{app_name}' by user {user_id}")
            return jsonify({'error': 'Operation timed out'}), 408
        except Exception as e:
            log_with_timestamp(f"[DEPLOYMENT API] POST - ERROR - Action '{action}' failed for app '{app_name}' by user {user_id}: {str(e)}")
            return jsonify({'error': str(e)}), 500

@api_bp.route('/deployments/<int:deployment_id>/logs')
def api_deployment_logs(deployment_id):
    # Log API call
    user_id = session.get('user_id', 'anonymous')
    remote_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    
    log_with_timestamp(f"[DEPLOYMENT LOGS] GET /api/deployments/{deployment_id}/logs - User: {user_id}, IP: {remote_ip}")
    
    if 'user_id' not in session:
        log_with_timestamp(f"[DEPLOYMENT LOGS] FAILED - Authentication required from {remote_ip}")
        return jsonify({'error': 'Authentication required'}), 401
    
    deployment = db_manager.execute_query('''
        SELECT deployment_path FROM deployments 
        WHERE id = ? AND user_id = ?
    ''', (deployment_id, session['user_id']), fetch_one=True)
    
    if not deployment:
        log_with_timestamp(f"[DEPLOYMENT LOGS] FAILED - Deployment {deployment_id} not found for user {user_id}")
        return jsonify({'error': 'Deployment not found'}), 404
    
    # Extract deployment path safely
    deploy_path = str(deployment[0] if isinstance(deployment, (list, tuple)) else deployment)
    
    # Validate deployment path to prevent path traversal
    if not deploy_path or '..' in deploy_path or not deploy_path.startswith('/home/ubuntu/deployments/'):
        log_with_timestamp(f"[DEPLOYMENT LOGS] SECURITY - Invalid deployment path: {deploy_path} for user {user_id}")
        return jsonify({'error': 'Invalid deployment path'}), 400
    
    log_file = os.path.join(deploy_path, 'deployment.log')
    
    # Additional security check for log file path
    if not log_file.startswith('/home/ubuntu/deployments/') or '..' in log_file:
        log_with_timestamp(f"[DEPLOYMENT LOGS] SECURITY - Invalid log file path: {log_file} for user {user_id}")
        return jsonify({'error': 'Invalid log file path'}), 400
    
    try:
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                logs = f.read()
        else:
            logs = 'No logs available'
        
        log_with_timestamp(f"[DEPLOYMENT LOGS] SUCCESS - Returned logs for deployment {deployment_id} to user {user_id}")
        return jsonify({'logs': logs})
    except Exception as e:
        log_with_timestamp(f"[DEPLOYMENT LOGS] ERROR - Failed to read logs for deployment {deployment_id} by user {user_id}: {str(e)}")
        return jsonify({'error': f'Failed to read logs: {str(e)}'}), 500

@api_bp.route('/qchat_developer', methods=['POST'])
def api_qchat_developer():
    from flask import Response, stream_with_context
    import subprocess
    import re
    
    user_id = session.get('user_id', '0')
    
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    data = request.get_json()
    message = data.get('message', '').strip()
    application_name = data.get('application_name', '')
    application_folder = data.get('application_folder', '')
    detected_action = data.get('action_operation', '')

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

    log_with_timestamp(f"AI Chat Developer - User: {username}, Email: {user_email}, App: {application_name}, Folder: {application_folder}")
    log_with_timestamp(f"AI Chat Developer - Message: {message[:120]}")

    def generate():
        try:
            yield f"data: {json.dumps({'chunk': 'Starting Q Chat Developer session...'})}\n\n"
            
            # Build prompt directly here
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            branch_name = f"{session['user_id']}-automorph-{application_name}-{timestamp}"

            log_with_timestamp(f'AI Chat Developer - Detected action: {detected_action}')
            yield f"data: {json.dumps({'chunk': f'AI Chat Developer - Detected action: {detected_action}'})}\n\n"

            # Use provided app folder or default REPO_DIR
            repo_dir = application_folder if application_folder else "/home/ubuntu/deployments/"
            repo_github_url = f"git@github.com:Sam9682/{application_name}" if application_name else "git@github.com:Sam9682/"
            repo_gitea_url = f"http://gitadmin:password@localhost:3000/gitadmin/{branch_name}"
            
            yield f"data: {json.dumps({'chunk': f'App: {application_name}, Folder: {repo_dir}'})}\n\n"
            
            # 🧠 Prompt complet envoyé à Q Chat
            l_prompt = return_prompt_for_developer(detected_action, application_name, application_folder, user_name, user_email)

            # dump the value of l_prompt to a file. Be aware that l_prompt is a variable composed of multiple lines
            from ..config import get_logs_dir
            prompt_file_path = os.path.join(get_logs_dir(), 'dev_prompt_generated.txt')
            try:
                with open(prompt_file_path, 'w') as f:
                    f.write(l_prompt+"\n")
            except (IOError, OSError) as e:
                yield f"data: {json.dumps({'chunk': f'Warning: Failed to write prompt to file: {str(e)}'})}"

            # Find qchat command
            from ..config import get_qchat_paths
            qchat_paths = get_qchat_paths()
            qchat_cmd = None
            for path in qchat_paths:
                try:
                    result = subprocess.run([path, '--version'], capture_output=True, timeout=TIMEOUT_SUBPROCESS_RUN)
                    if result.returncode == 0:
                        qchat_cmd = path
                        break
                except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError, FileNotFoundError) as e:
                    log_with_timestamp(f'AI Chat Developer - Failed to check qchat at {path}: {str(e)}')
                    continue
                except Exception as e:
                    log_with_timestamp(f'AI Chat Developer - Unexpected error checking qchat at {path}: {str(e)}')
                    continue
            
            if not qchat_cmd:
                yield f"data: {json.dumps({'error': 'Q Chat not found in paths: ' + str(qchat_paths)})}\n\n"
                return
            
            yield f"data: {json.dumps({'chunk': f'Found Q Chat at: {qchat_cmd}'})}\n\n"
            
            cmd_args = [qchat_cmd, 'chat', '--trust-all-tools', l_prompt]
            qchat_env = os.environ.copy()
            qchat_env.update({'HOME': '/home/ubuntu', 'USER': 'ubuntu', 'PATH': '/home/ubuntu/.local/bin:' + qchat_env.get('PATH', '')})
            
            yield f"data: {json.dumps({'chunk': 'Executing Q Chat command...'})}\n\n"
            
            # Start process with longer timeout and better error handling
            process = subprocess.Popen(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                      text=True, bufsize=1, env=qchat_env, preexec_fn=os.setsid)
            
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            
            import signal
            import time
            
            # Set a longer timeout for Q Chat operations (30 minutes)
            timeout_seconds = TIMEOUT_QCHAT_DEVELOPER_RUN
            start_time = time.time()
            
            try:
                for line in iter(process.stdout.readline, ''):
                    if line:
                        clean_line = ansi_escape.sub('', line.rstrip())
                        if clean_line and 'Thinking...' not in clean_line:
                            yield f"data: {json.dumps({'chunk': clean_line})}\n\n"
                    
                    # Check timeout
                    if time.time() - start_time > timeout_seconds:
                        yield f"data: {json.dumps({'chunk': 'WARNING: Q Chat operation timeout reached (30 minutes), terminating...'})}\n\n"
                        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                        time.sleep(5)
                        if process.poll() is None:
                            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                        break
                
                process.wait(timeout=TIMEOUT_CLEAN_SHUTDOWN)  # Wait up to 1 minute for clean shutdown
                
            except subprocess.TimeoutExpired:
                yield f"data: {json.dumps({'chunk': 'Q Chat process cleanup timeout, forcing termination...'})}\n\n"
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                process.returncode = -1
            
            yield f"data: {json.dumps({'done': True, 'success': process.returncode == 0, 'returncode': process.returncode})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'error': f'Exception in generate(): {str(e)}'})}\n\n"
    
    return Response(stream_with_context(generate()), mimetype='text/event-stream',
                   headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})

@api_bp.route('/qchat_operations', methods=['POST'])
def api_qchat_operations():
    from flask import Response, stream_with_context
    import subprocess
    import re
    
    user_id = session.get('user_id', 'anonymous')
    
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    data = request.get_json()
    message = data.get('message', '').strip()
    application_name = data.get('application_name', '')
    application_folder = data.get('application_folder', '')
    action_operation = data.get('action_operation', '')
    
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

    log_with_timestamp(f"AI Chat Operator - User: {username}, Email: {user_email}, App: {application_name}, Folder: {application_folder}")
    log_with_timestamp(f"AI Chat Operator - Message: {message[:120]}")

    def generate():
        import os
        
        try:
            yield f"data: {json.dumps({'chunk': 'Starting Q Chat DevOps session...'})}\n\n"
            
            # Build prompt directly here instead of calling process_qchat_devops
            # Detect application management actions
            
            if action_operation:
                # Map complete sentences to actions
                if 'MODIFY_CODE' in action_operation:
                    l_msg = f"[VIRTUAL OPERATIONS] ERROR : asking to modify the code, should be sent to Developer agent"
                    yield f"data: {json.dumps({'error': l_msg})}\n\n"
                    return
                else:
                    detected_action = action_operation

                log_with_timestamp(f'AI Chat Operator - Detected action: {detected_action}')
                yield f"data: {json.dumps({'chunk': f'Detected complete sentence action: {detected_action}'})}\n\n"

                # 🧠 Prompt complet envoyé à Q Chat
                try:
                    l_prompt = return_prompt_for_operator(detected_action, application_name, application_folder, user_name, user_email, message)
                    log_with_timestamp(f'AI Chat Operator - Prompt : {l_prompt[:120]}')
                except Exception as e:
                    log_with_timestamp(f'AI Chat Operator - Error generating prompt: {str(e)}')
                    yield f"data: {json.dumps({'error': f'Failed to generate prompt: {str(e)}'})}\n\n"
                    return

            else:
                # Simple prompt for Q&A without code execution
                l_prompt = f"""You are a helpful Virtual Advisor assistant. Answer the user's question clearly and concisely.
Do not execute any commands or modify any files. Just provide helpful information and guidance.
User Question: {message}. Provide a helpful and informative response."""
                log_with_timestamp(f'AI Chat Operator - (Simple Q&A) Prompt : {l_prompt[:120]}')

            # dump the value of l_prompt to a file. Be aware that l_prompt is a variable composed of multiple lines
            from ..config import get_logs_dir
            prompt_file_path = os.path.join(get_logs_dir(), 'ope_prompts_generated.log')
            try:
                with open(prompt_file_path, 'w') as f:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    f.write(f"----------------- Generated Prompt for Virtual Operator at {timestamp}: \n")
                    f.write(l_prompt+"\n")
                    f.write(f"----------------- END OF Generated Prompt for Virtual Operator at {timestamp}: \n")
            except (IOError, OSError) as e:
                log_with_timestamp(f'AI Chat Operator - Warning: Failed to write prompt to file: {str(e)}')
                yield f"data: {json.dumps({'chunk': f'Warning: Failed to write prompt to file: {str(e)}'})}\n\n"

            # Find qchat command
            from ..config import get_qchat_paths
            qchat_paths = get_qchat_paths()
            qchat_cmd = None
            for path in qchat_paths:
                try:
                    result = subprocess.run([path, '--version'], capture_output=True, timeout=TIMEOUT_SUBPROCESS_RUN)
                    if result.returncode == 0:
                        qchat_cmd = path
                        break
                except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError, FileNotFoundError) as e:
                    log_with_timestamp(f'AI Chat Operator - Failed to check qchat at {path}: {str(e)}')
                    continue
                except Exception as e:
                    log_with_timestamp(f'AI Chat Operator - Unexpected error checking qchat at {path}: {str(e)}')
                    continue
            
            if not qchat_cmd:
                yield f"data: {json.dumps({'error': 'Q Chat not found in paths: ' + str(qchat_paths)})}\n\n"
                return
            
            yield f"data: {json.dumps({'chunk': f'Found Q Chat at: {qchat_cmd}'})}\n\n"
            
            # Use --trust-all-tools if action detected (needs command execution)
            cmd_args = [qchat_cmd, 'chat']
            try:
                if 'detected_action' in locals() and detected_action:
                    cmd_args.extend(['--trust-all-tools'])
                cmd_args.append(l_prompt)
            except NameError:
                cmd_args.append(l_prompt)
            
            qchat_env = os.environ.copy()
            qchat_env.update({'HOME': '/home/ubuntu', 'USER': 'ubuntu', 'PATH': '/home/ubuntu/.local/bin:' + qchat_env.get('PATH', '')})
            
            # Start process with longer timeout and better error handling
            try:
                process = subprocess.Popen(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                          text=True, bufsize=1, env=qchat_env, preexec_fn=os.setsid)
            except (OSError, subprocess.SubprocessError) as e:
                log_with_timestamp(f'AI Chat Operator - Failed to start process: {str(e)}')
                yield f"data: {json.dumps({'error': f'Failed to start Q Chat process: {str(e)}'})}\n\n"
                return
            
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            
            import signal
            import time
            
            # Set a longer timeout for Q Chat operations (30 minutes)
            timeout_seconds = TIMEOUT_QCHAT_OPERATOR_RUN
            start_time = time.time()
            
            try:
                for line in iter(process.stdout.readline, ''):
                    if line:
                        clean_line = ansi_escape.sub('', line.rstrip())
                        if clean_line and 'Thinking...' not in clean_line:
                            yield f"data: {json.dumps({'chunk': clean_line})}\n\n"
                    
                    # Check timeout
                    if time.time() - start_time > timeout_seconds:
                        yield f"data: {json.dumps({'chunk': 'WARNING: Q Chat operation timeout reached (30 minutes), terminating...'})}\n\n"
                        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                        time.sleep(5)
                        if process.poll() is None:
                            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                        break
                
                process.wait(timeout=TIMEOUT_CLEAN_SHUTDOWN)  # Wait up to 1 minute for clean shutdown
                
            except subprocess.TimeoutExpired:
                yield f"data: {json.dumps({'chunk': 'Q Chat process cleanup timeout, forcing termination...'})}\n\n"
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                process.returncode = -1
            
            # Record billing activity for START and STOP actions if successful
            if (detected_action.upper() == 'START' or detected_action.upper() == 'STOP') and process.returncode == 0 and application_name:
                try:
                    from .billing_routes import record_billing_activity
                    record_billing_activity(session['user_id'], application_name, detected_action)
                    log_with_timestamp(f'AI Chat Operator - Billing activity recorded for {detected_action} action on {application_name}')
                    yield f"data: {json.dumps({'chunk': f'Billing activity recorded for {detected_action} action on {application_name}'})}\n\n"
                except Exception as billing_error:
                    yield f"data: {json.dumps({'chunk': f'Warning: Failed to record billing activity: {str(billing_error)}'})}\n\n"
            
            yield f"data: {json.dumps({'chunk': f'=== Q Chat Session Completed ==='})}\n\n"
            yield f"data: {json.dumps({'done': True, 'success': process.returncode == 0, 'returncode': process.returncode})}\n\n"
            log_with_timestamp(f'AI Chat Operator - done ! rc = {process.returncode}')
        except Exception as e:
            log_with_timestamp(f'AI Chat Operator - Exception in generate(): {str(e)}')
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
            if not data or not isinstance(data, dict):
                return jsonify({'error': 'Invalid JSON data'}), 400
            
            if not data.keys():
                return jsonify({'error': 'No data provided'}), 400
            
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
        
        if not data or not isinstance(data, dict):
            return jsonify({'error': 'Invalid JSON data'}), 400
        
        required_fields = ['SERVER_IP', 'SERVER_NAME', 'SERVER_CAPACITY_USER_MAX', 
                          'SERVER_CAPACITY_APPLI_MAX', 'SERVER_STATUS', 'SERVER_TYPE']
        
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
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
        try:
            data = request.get_json()
            if not data or not isinstance(data, dict):
                return jsonify({'error': 'Invalid JSON data'}), 400
            
            required_fields = ['SERVER_IP', 'SERVER_NAME', 'SERVER_CAPACITY_USER_MAX', 
                             'SERVER_CAPACITY_APPLI_MAX', 'SERVER_STATUS', 'SERVER_TYPE']
            if not all(field in data for field in required_fields):
                return jsonify({'error': 'Missing required fields'}), 400
            
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
        try:
            # Check if server is ACTIVE
            server = db_manager.execute_query(
                'SELECT SERVER_STATUS FROM servers WHERE id = ?', 
                (server_id,), fetch_one=True
            )
            
            if not server:
                return jsonify({'error': 'Server not found'}), 404
            
            if server[0] == 'ACTIVE':
                return jsonify({'error': 'Cannot delete ACTIVE server'}), 400
            
            db_manager.execute_query('DELETE FROM servers WHERE id = ?', (server_id,))
            return jsonify({'message': 'Server deleted successfully'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@api_bp.route('/server/allocate', methods=['POST'])
def api_server_allocate():
    """Allocate server for deployment based on capacity constraints"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        data = request.get_json()
        application_name = data.get('application_name')
        
        if not application_name:
            return jsonify({'error': 'Application name required'}), 400
        
        # Find available server based on capacity constraints with usage counts
        servers = db_manager.execute_query('''
            SELECT s.id, s.SERVER_CAPACITY_USER_MAX, s.SERVER_CAPACITY_APPLI_MAX,
                   COALESCE(user_counts.user_count, 0) as current_users,
                   COALESCE(app_counts.app_count, 0) as current_apps
            FROM servers s
            LEFT JOIN (
                SELECT server_id, COUNT(DISTINCT user_id) as user_count
                FROM deployments
                GROUP BY server_id
            ) user_counts ON s.id = user_counts.server_id
            LEFT JOIN (
                SELECT server_id, COUNT(DISTINCT application_name) as app_count
                FROM deployments
                GROUP BY server_id
            ) app_counts ON s.id = app_counts.server_id
            WHERE s.SERVER_STATUS = 'STAND_BY' OR s.SERVER_STATUS = 'ACTIVE'
            ORDER BY s.SERVER_STATUS ASC
        ''', fetch_all=True)
        
        if not servers:
            return jsonify({'error': 'No standby servers available'}), 503
        
        for server in servers:
            server_id, user_max, appli_max, user_count, appli_count = server
            
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
            if not data or not isinstance(data, dict):
                return jsonify({'error': 'Invalid JSON data'}), 400
            
            # Build UPDATE query dynamically
            set_clauses = []
            values = []
            
            try:
                for column, value in data.items():
                    if column.lower() != 'id':  # Don't update ID
                        set_clauses.append(f'{column} = ?')
                        values.append(value)
            except (AttributeError, TypeError) as e:
                return jsonify({'error': 'Invalid data format'}), 400
            
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