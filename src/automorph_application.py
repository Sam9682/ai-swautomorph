import subprocess
import datetime
import time
import re

# 📁 Chemin du repo qui sert à docker-compose up
REPO_DIR = "/home/ubuntu/deployments/"

# 🌐 URL du remote Gitea local
GITEA_REMOTE_URL = "git@gitea.local:monorg/myapp.git"

def process_qchat_request(user_request: str, auto_approve: bool = True, app_name: str = '', app_folder: str = '', git_url: str = ''):
    """
    Process Q Chat request using automorph application logic
    Returns dict with response, execution details, and timing
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    branch_name = f"auto-update-{timestamp}"
    start_time = time.time()
    
    # Use provided app folder or default REPO_DIR
    repo_dir = app_folder if app_folder else REPO_DIR
    repo_git_url = git_url if git_url else GITEA_REMOTE_URL
    
    print(f"[AUTOMORPH] Processing request: {user_request[:100]}{'...' if len(user_request) > 100 else ''}")
    print(f"[AUTOMORPH] App: {app_name}, Folder: {repo_dir}, Git: {repo_git_url}")
    
    # 🧠 Prompt complet envoyé à Q Chat
    prompt = f"""
You are an autonomous DevOps/code agent running on a Linux server
with access to the local filesystem and shell commands.

The application source code is located in the following git repository:
  REPO_DIR = "{repo_dir}"

This repository is the one used by docker-compose to run the application.
The deployment command is executed from the repo root:
  docker-compose up -d --build

There is (or must be) a local Gitea instance reachable with the Git URL:
  GITEA_REMOTE_URL = "{repo_git_url}"

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
     {repo_git_url}
   - If 'gitea' does not exist, add it:
       git remote add gitea {repo_git_url}
   - If 'gitea' exists but with a different URL, update it:
       git remote set-url gitea {repo_git_url}

4. Fetch from 'gitea':
     git fetch gitea

5. Determine the default branch (prefer 'main', otherwise 'master', otherwise stay on current).
   Then create and checkout a new branch named:
     {branch_name}
   starting from the default branch, for example:
     git checkout main
     git pull --ff-only
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
     git push gitea {branch_name}

10. Rebuild and redeploy the running application by executing:
      docker-compose up -d --build
    from the repository root ({repo_dir}).

11. At the end, print a short summary including:
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
        
        print(f"[AUTOMORPH] Executing qchat command with auto_approve={auto_approve} using: {qchat_cmd}")
        
        # Execute Q Chat command
        result = subprocess.run(cmd_args, capture_output=True, text=True, timeout=600)
        execution_time = time.time() - start_time
        
        print(f"[AUTOMORPH] Command completed in {execution_time:.2f}s, Return code: {result.returncode}")
        
        # Handle response from both stdout and stderr
        response_text = ''
        if result.stdout and result.stdout.strip():
            response_text = result.stdout.strip()
        elif result.stderr and result.stderr.strip():
            response_text = result.stderr.strip()
        else:
            response_text = 'Automorph Q Chat completed but returned no output'
        
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
        print(f"[AUTOMORPH] Request timed out after 600s")
        return {
            'error': 'Automorph request timed out',
            'execution_time': round(time.time() - start_time, 2)
        }
    except Exception as e:
        print(f"[AUTOMORPH] Error: {str(e)}")
        return {
            'error': f'Automorph error: {str(e)}',
            'execution_time': round(time.time() - start_time, 2)
        }

def process_qchat_question(user_question: str):
    """
    Process Virtual Advisor question using Q Chat for simple Q&A
    Returns dict with response and timing
    """
    start_time = time.time()
    
    print(f"[VIRTUAL ADVISOR] Processing question: {user_question[:100]}{'...' if len(user_question) > 100 else ''}")
    
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
        
        cmd_args = [qchat_cmd, 'chat', prompt]
        
        print(f"[VIRTUAL ADVISOR] Executing qchat command for question using: {qchat_cmd}")
        
        # Execute Q Chat command
        result = subprocess.run(cmd_args, capture_output=True, text=True, timeout=300)
        execution_time = time.time() - start_time
        
        print(f"[VIRTUAL ADVISOR] Command completed in {execution_time:.2f}s, Return code: {result.returncode}")
        
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
        print(f"[VIRTUAL ADVISOR] Question timed out after 300s")
        return {
            'error': 'Virtual Advisor question timed out',
            'execution_time': round(time.time() - start_time, 2)
        }
    except Exception as e:
        print(f"[VIRTUAL ADVISOR] Error: {str(e)}")
        return {
            'error': f'Virtual Advisor error: {str(e)}',
            'execution_time': round(time.time() - start_time, 2)
        }

def send_update_request_to_qchat(user_request: str):
    """
    Legacy function for backward compatibility
    """
    result = process_qchat_request(user_request)
    if 'error' in result:
        raise Exception(result['error'])
    return result

if __name__ == "__main__":
    # Exemple d'appel
    demande = "Ajoute un endpoint /healthcheck sur /health en GET qui retourne un JSON {{'status': 'ok'}}."
    result = process_qchat_request(demande)
    print(f"Result: {result}")