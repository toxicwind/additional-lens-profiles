#!/usr/bin/env python3.12
"""
git_push_helper.py — TODO 5
Pushes a single file to a GitHub repo without git init.
Clones repo to workspace, sets per-repo identity (no --global),
stages, commits, and pushes one file at a time.
"""
import os, sys, subprocess, shutil
from pathlib import Path
from datetime import datetime

def ts() -> str:
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]

def push_one(repo: str, filepath: str, message: str | None, pat: str) -> int:
    pat = pat or os.environ.get("GITHUB_TOKEN", "")
    if not pat:
        print(f"[{ts()}] ERROR: No PAT"); return 1
    fp = Path(filepath)
    if not fp.exists():
        print(f"[{ts()}] ERROR: {fp} not found"); return 1

    workspace = Path("/mnt/agents/output/repos")
    workspace.mkdir(parents=True, exist_ok=True)
    repo_dir = workspace / repo

    if not (repo_dir / ".git").exists():
        url = f"https://toxicwind:{pat}@github.com/toxicwind/{repo}.git"
        r = subprocess.run(["git", "clone", "--depth", "1", url, str(repo_dir)],
                           capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            print(f"[{ts()}] Clone failed: {r.stderr[:200]}"); return 1

    # Per-repo identity — NO --global
    subprocess.run(["git", "config", "user.email", "toxicwind@users.noreply.github.com"],
                   cwd=str(repo_dir), capture_output=True)
    subprocess.run(["git", "config", "user.name", "toxicwind"],
                   cwd=str(repo_dir), capture_output=True)

    target = repo_dir / fp.name
    shutil.copy2(fp, target)
    subprocess.run(["git", "add", str(target)], cwd=str(repo_dir), capture_output=True)
    msg = message or f"feat: add {fp.name} — {ts()}"
    subprocess.run(["git", "commit", "-m", msg], cwd=str(repo_dir), capture_output=True, text=True)
    r = subprocess.run(["git", "push", "origin", "main"], cwd=str(repo_dir),
                       capture_output=True, text=True, timeout=20)
    if r.returncode == 0:
        print(f"[{ts()}] PUSHED {fp.name} -> toxicwind/{repo}")
    else:
        print(f"[{ts()}] Push note: {r.stderr[:100]}")
    return r.returncode

def main() -> int:
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("repo")
    p.add_argument("file")
    p.add_argument("-m", "--message", default=None)
    p.add_argument("--pat", default=os.environ.get("GITHUB_TOKEN", ""))
    args = p.parse_args()
    return push_one(args.repo, args.file, args.message, args.pat)

if __name__ == "__main__":
    sys.exit(main())
