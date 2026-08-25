#!/usr/bin/env python3.12
"""
batch_pusher.py — TODO 13
Pushes all workspace .py files to the GitHub repo one at a time.
"""
import os, sys, subprocess
from pathlib import Path

def ts() -> str:
    import time
    return time.strftime("%Y-%m-%dT%H:%M:%S")

def push_all(repo: str, pat: str) -> int:
    workspace = Path("/mnt/agents/output/workspace")
    files = sorted(workspace.glob("*.py"))
    print(f"[{ts()}] TODO 13: Pushing {len(files)} files to {repo}...")
    for fp in files:
        r = subprocess.run([
            "python3.12", "/mnt/agents/dot/bin/git-push-one.py",
            repo, str(fp), "-m", f"feat: add {fp.name}", "--pat", pat
        ], capture_output=True, text=True, timeout=60)
        print(f"  {fp.name}: {'OK' if r.returncode == 0 else 'ERR'}")
    print(f"[{ts()}] Batch push complete")
    return 0

def main() -> int:
    pat = os.environ.get("GITHUB_TOKEN", "")
    return push_all("token-recovery-20260824", pat)

if __name__ == "__main__":
    sys.exit(main())
