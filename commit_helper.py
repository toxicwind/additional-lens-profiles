#!/usr/bin/env python3.12
"""
Git Commit Helper - One File At A Time
Usage: python3.12 commit_helper.py <repo_path> <file_path> [commit_message]
"""
import sys, subprocess, os

def commit_one_file(repo_path, file_path, message="auto: update"):
    """Stage and commit exactly one file, setting identity locally."""
    os.chdir(repo_path)
    subprocess.run(["git", "config", "user.email", "audit@local"], check=False)
    subprocess.run(["git", "config", "user.name", "System Audit"], check=False)
    result = subprocess.run(["git", "add", file_path], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[ERR] git add: {result.stderr}")
        return False
    result = subprocess.run(["git", "commit", "-m", message], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[ERR] git commit: {result.stderr}")
        return False
    print(f"[OK] Committed: {file_path} | {message}")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3.12 commit_helper.py <repo> <file> [msg]")
        sys.exit(1)
    ok = commit_one_file(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else f"update: {os.path.basename(sys.argv[2])}")
    sys.exit(0 if ok else 1)
