import subprocess
import datetime

# 📁 Chemin du repo qui sert à docker-compose up
REPO_DIR = "/srv/app/myapp"

# 🌐 URL du remote Gitea local
GITEA_REMOTE_URL = "git@gitea.local:monorg/myapp.git"

def send_update_request_to_qchat(user_request: str):
    """
    user_request = description de la modif demandée, ex:
    "Ajoute une route /healthcheck en GET qui retourne {status: 'ok'}"
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    branch_name = f"auto-update-{timestamp}"

    # 🧠 Prompt complet envoyé à Q Chat
    prompt = f"""
You are an autonomous DevOps/code agent running on a Linux server
with access to the local filesystem and shell commands.

The application source code is located in the following git repository:
  REPO_DIR = "{REPO_DIR}"

This repository is the one used by docker-compose to run the application.
The deployment command is executed from the repo root:
  docker-compose up -d --build

There is (or must be) a local Gitea instance reachable with the Git URL:
  GITEA_REMOTE_URL = "{GITEA_REMOTE_URL}"

Your goal is to:
  - modify the source code according to the user request,
  - commit the changes on a new branch,
  - push this branch to the local Gitea remote,
  - rebuild and redeploy the running application with docker-compose.

USER REQUEST (what must be changed in the app):
\"\"\"{user_request}\"\"\"

Follow these steps EXACTLY:

1. Change directory to the repository:
   cd {REPO_DIR}

2. Check that the working tree is clean (no uncommitted changes).
   If there are local changes, STOP and print a clear error message,
   do NOT try to auto-commit existing local changes.

3. Ensure that a git remote named 'gitea' exists and points to:
     {GITEA_REMOTE_URL}
   - If 'gitea' does not exist, add it:
       git remote add gitea {GITEA_REMOTE_URL}
   - If 'gitea' exists but with a different URL, update it:
       git remote set-url gitea {GITEA_REMOTE_URL}

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
    from the repository root ({REPO_DIR}).

11. At the end, print a short summary including:
    - the branch name,
    - the git commit hash,
    - the result of the docker-compose command (success or failure),
    - and any warnings (e.g. tests were not found, tests were skipped, etc.).

If ANY step fails, explain clearly which step failed and why.
"""

    # 🚀 Appel de Q Chat via subprocess
    cmd = ["q", "chat", prompt]
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    # Exemple d’appel
    demande = "Ajoute un endpoint /healthcheck sur /health en GET qui retourne un JSON {{'status': 'ok'}}."
    send_update_request_to_qchat(demande)