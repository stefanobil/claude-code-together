import subprocess
import datetime
import os
import sys

# Configuration
REPO_PATH = r"c:\Users\merzi\Desktop\VIBE CODE\claude code together"
LOG_FILE = os.path.join(REPO_PATH, "backup_log.txt")

def log_message(msg):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {msg}\n")
    print(f"[{timestamp}] {msg}")

def run_git_cmd(cmd):
    try:
        result = subprocess.run(
            cmd, 
            cwd=REPO_PATH, 
            capture_output=True, 
            text=True, 
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        log_message(f"ERROR executing {' '.join(cmd)}: {e.stderr}")
        return None

def auto_backup():
    log_message("Starting automated backup...")
    
    # Check for changes
    status = run_git_cmd(["git", "status", "--porcelain"])
    if status is None:
        return
    
    if not status:
        log_message("No changes detected. Skipping backup.")
        return
    
    # Add files
    run_git_cmd(["git", "add", "."])
    
    # Commit
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_msg = f"Auto-save: trading bot update - {timestamp}"
    res = run_git_cmd(["git", "commit", "-m", commit_msg])
    
    if res:
        log_message(f"Committed changes: {commit_msg}")
        
        # Push
        push_res = run_git_cmd(["git", "push", "origin", "master"])
        if push_res is not None:
            log_message("Successfully pushed to GitHub.")
        else:
            log_message("Failed to push to GitHub. Check your authentication/connection.")
    else:
        log_message("Commit failed or nothing to commit.")

if __name__ == "__main__":
    auto_backup()
