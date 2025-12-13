import subprocess
import datetime
import time
import re

# 📁 Chemin du repo qui sert à docker-compose up
REPO_DIR = "/home/ubuntu/deployments/"

# 🌐 URL du remote Gitea local
GITHUB_REMOTE_URL = "git@github.com:Sam9682/"
GITEA_REMOTE_URL = "http://gitadmin:password@localhost:3000/gitadmin/"

def process_qchat_developer(user_request: str, auto_approve: bool = True, app_name: str = '', app_folder: str = '', git_url: str = '', user_id: str = '0', user_name: str = 'anonymous'):
    """
    Process Q Chat request using automorph application logic
    Returns dict with response, execution details, and timing
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    branch_name = f"{user_id}-automorph-{app_name}-{timestamp}"
    start_time = time.time()
    
    # Use provided app folder or default REPO_DIR
    repo_dir = app_folder if app_folder else REPO_DIR
    repo_github_url = git_url if git_url else GITHUB_REMOTE_URL + app_name
    repo_gitea_url = GITEA_REMOTE_URL + branch_name

    print(f"[VIRTUAL DEVELOPER] Processing request: {user_request[:100]}{'...' if len(user_request) > 100 else ''}")
    print(f"[VIRTUAL DEVELOPER] App: {app_name}, Folder: {repo_dir}")
    print(f"[VIRTUAL DEVELOPER] Github: {repo_github_url}")
    print(f"[VIRTUAL DEVELOPER] Gitea: {repo_gitea_url}")
    
    # 🧠 Prompt complet envoyé à Q Chat
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
\"\"\"{user_request}\"\"\"

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
     git commit -m "Auto-update: {user_request}"

9. Push the new branch to the 'gitea' remote:
     git push gitea --all

10. Update table Application from swautomorph.db localted in ~/swautomorph/softfluid/db/ folder, 
    set the field 'gitea_url' of Deployments table to the value '{repo_gitea_url}' where application_name = '{app_name}'

11. Rebuild and redeploy the running application by executing:
      deployApp.sh stop
      deployApp.sh start {user_id} {user_name}
    from the repository root ({repo_dir}).

12. At the end, print a short summary including:
    - the branch name,
    - the git commit hash,
    - the result of the docker-compose command (success or failure),
    - and any warnings (e.g. tests were not found, tests were skipped, etc.).

If ANY step fails, explain clearly which step failed and why.
"""

    try:
        # Try different possible paths for qchat
        qchat_paths = ['/usr/local/bin/qchat', '/usr/bin/qchat', 'qchat']
        qchat_cmd = None
        
        for path in qchat_paths:
            try:
                subprocess.run([path, '--version'], capture_output=True, timeout=5)
                qchat_cmd = path
                break
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                continue
        
        if not qchat_cmd:
            return {
                'error': 'Q Chat command not found. Please install qchat or check PATH.',
                'execution_time': round(time.time() - start_time, 2)
            }
        
        # Prepare Q Chat command with --trust-all-tools option if auto_approve
        cmd_args = [qchat_cmd, 'chat']
        if auto_approve:
            cmd_args.append('--trust-all-tools')
        cmd_args.append(prompt)
        
        print(f"[VIRTUAL DEVELOPER] Executing qchat command with auto_approve={auto_approve} using: {qchat_cmd}")
        
        # Set up proper environment to avoid permission issues
        import os
        qchat_env = os.environ.copy()
        qchat_env.update({
            'HOME': '/home/ubuntu',
            'USER': 'ubuntu',
            'PATH': '/usr/local/bin:/usr/bin:/bin:' + qchat_env.get('PATH', '')
        })
        
        # Execute Q Chat command with proper environment
        result = subprocess.run(cmd_args, capture_output=True, text=True, timeout=1500, env=qchat_env)
        execution_time = time.time() - start_time
        
        print(f"[VIRTUAL DEVELOPER] Command completed in {execution_time:.2f}s, Return code: {result.returncode}")
        
        # Handle response from both stdout and stderr
        response_text = ''
        if result.stdout and result.stdout.strip():
            response_text = result.stdout.strip()
        elif result.stderr and result.stderr.strip():
            response_text = result.stderr.strip()
        else:
            response_text = 'VIRTUAL DEVELOPER Q Chat completed but returned no output'
        
        # Strip ANSI color codes from response
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        response_text = ansi_escape.sub('', response_text)
        
        # Check if command was executed
        command_executed = 'git commit' in response_text.lower() or 'docker-compose' in response_text.lower()
        
        return {
            'response': response_text,
            'command_executed': command_executed,
            'branch_name': branch_name,
            'execution_time': round(execution_time, 2),
            'success': result.returncode == 0
        }
        
    except subprocess.TimeoutExpired:
        print(f"[VIRTUAL DEVELOPER] Request timed out after 1500s")
        return {
            'error': 'Automorph request timed out after 25 minutes',
            'execution_time': round(time.time() - start_time, 2)
        }
    except Exception as e:
        print(f"[VIRTUAL DEVELOPER] Error: {str(e)}")
        return {
            'error': f'VIRTUAL DEVELOPER error: {str(e)}',
            'execution_time': round(time.time() - start_time, 2)
        }



def process_qchat_operations(user_question: str, user_id: str = '0', user_name: str = 'User', user_email: str = 'user@example.com', description: str = ''):
    """
    Process Virtual Advisor question using Q Chat for simple Q&A or app management
    Returns dict with response and timing
    """
    start_time = time.time()
    
    print(f"[VIRTUAL OPERATIONS] Processing question: {user_question[:100]}{'...' if len(user_question) > 100 else ''}")
    
    # Detect application management actions
    # First check for bracketed actions like [START], [STOP], etc.
    import re
    bracket_match = re.search(r'\[(START|STOP|RESTART|PS|LOGS)\]', user_question.upper())
    
    detected_action = None
    
    if bracket_match:
        # Use bracketed action with priority
        detected_action = bracket_match.group(1).lower()
        print(f"[VIRTUAL OPERATIONS] Detected bracketed action: {detected_action.upper()}")
    else:
        # Fallback to keyword detection
        action_keywords = {
            'start': ['start', 'deploy', 'launch', 'run'],
            'stop': ['stop', 'shutdown', 'halt', 'terminate'],
            'restart': ['restart', 'reboot', 'reload'],
            'ps': ['status', 'ps', 'check', 'running'],
            'logs': ['logs', 'log', 'output', 'console']
        }
        
        question_lower = user_question.lower()
        
        for action, keywords in action_keywords.items():
            if any(keyword in question_lower for keyword in keywords):
                detected_action = action
                break
    
    # Load context from shared folder if action detected
    if detected_action:
        import os
        context_file = f"/home/ubuntu/ai-swautomorph/shared/{detected_action.upper()}_context.md"
        
        if os.path.exists(context_file):
            print(f"[VIRTUAL OPERATIONS] Detected action: {detected_action.upper()}, loading context from {context_file}")
            
            with open(context_file, 'r') as f:
                context_template = f.read()
            
            # Replace placeholders
            context = context_template.replace('{USER_ID}', user_id)
            context = context.replace('{USER_NAME}', user_name)
            context = context.replace('{USER_EMAIL}', user_email)
            context = context.replace('{DESCRIPTION}', description)
            context = context.replace('{TAIL_LINES}', '100')  # Default tail lines
            
            # Extract application folder from description if present
            app_folder = ''
            if 'Path:' in description:
                parts = description.split('Path:')
                if len(parts) > 1:
                    app_folder = parts[1].strip()
            
            prompt = f"""
You are an autonomous Operations agent with access to execute shell commands on a Linux server.

The user has requested an application management action.

User Request: {user_question}

{'Application Folder: ' + app_folder if app_folder else ''}

Follow the instructions below to execute the {detected_action.upper()} action:

{context}

IMPORTANT: Execute all commands in the application folder: {app_folder if app_folder else '/home/ubuntu/deployments/[username]/[appname]'}

Execute all required steps and provide a clear summary of the results.
"""
        else:
            print(f"[VIRTUAL OPERATIONS] Context file not found: {context_file}, using default Q&A mode")
            prompt = f"""
You are a helpful Virtual Advisor assistant. Answer the user's question clearly and concisely.
Do not execute any commands or modify any files. Just provide helpful information and guidance.

User Question: {user_question}

Provide a helpful and informative response.
"""
    else:
        # Simple prompt for Q&A without code execution
        prompt = f"""
You are a helpful Virtual Advisor assistant. Answer the user's question clearly and concisely.
Do not execute any commands or modify any files. Just provide helpful information and guidance.

User Question: {user_question}

Provide a helpful and informative response.
"""

    try:
        # Execute Q Chat command without --trust-all-tools (no code execution)
        # Try different possible paths for qchat
        qchat_paths = ['/usr/local/bin/qchat', '/usr/bin/qchat', 'qchat']
        qchat_cmd = None
        
        for path in qchat_paths:
            try:
                subprocess.run([path, '--version'], capture_output=True, timeout=5)
                qchat_cmd = path
                break
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                continue
        
        if not qchat_cmd:
            return {
                'error': 'Q Chat command not found. Please install qchat or check PATH.',
                'execution_time': round(time.time() - start_time, 2)
            }
        
        # Use --trust-all-tools if action detected (needs command execution)
        cmd_args = [qchat_cmd, 'chat']
        if detected_action:
            cmd_args.append('--trust-all-tools')
        cmd_args.append(prompt)
        
        print(f"[VIRTUAL OPERATIONS] Executing qchat command for question using: {qchat_cmd}")
        
        # Set up proper environment to avoid permission issues
        import os
        qchat_env = os.environ.copy()
        qchat_env.update({
            'HOME': '/home/ubuntu',
            'USER': 'ubuntu',
            'PATH': '/usr/local/bin:/usr/bin:/bin:' + qchat_env.get('PATH', '')
        })
        
        # Execute Q Chat command with proper environment
        result = subprocess.run(cmd_args, capture_output=True, text=True, timeout=300, env=qchat_env)
        execution_time = time.time() - start_time
        
        print(f"[VIRTUAL OPERATIONS] Command completed in {execution_time:.2f}s, Return code: {result.returncode}")
        
        # Handle response from both stdout and stderr
        response_text = ''
        if result.stdout and result.stdout.strip():
            response_text = result.stdout.strip()
        elif result.stderr and result.stderr.strip():
            response_text = result.stderr.strip()
        else:
            response_text = 'Virtual Advisor completed but returned no output'
        
        # Strip ANSI color codes from response
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        response_text = ansi_escape.sub('', response_text)
        
        return {
            'response': response_text,
            'execution_time': round(execution_time, 2),
            'success': result.returncode == 0
        }
        
    except subprocess.TimeoutExpired:
        print(f"[VIRTUAL OPERATIONS] Question timed out after 300s")
        return {
            'error': 'Virtual Operations question timed out',
            'execution_time': round(time.time() - start_time, 2)
        }
    except Exception as e:
        print(f"[VIRTUAL OPERATIONS] Error: {str(e)}")
        return {
            'error': f'Virtual Operations error: {str(e)}',
            'execution_time': round(time.time() - start_time, 2)
        }

def send_update_request_to_qchat(user_request: str):
    """
    Legacy function for backward compatibility
    """
    result = process_qchat_developer(user_request)
    if 'error' in result:
        raise Exception(result['error'])
    return result

if __name__ == "__main__":
    # Exemple d'appel
    demande = "Ajoute un endpoint /healthcheck sur /health en GET qui retourne un JSON {{'status': 'ok'}}."
    result = process_qchat_developer(demande)
    print(f"Result: {result}")