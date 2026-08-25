#!/usr/bin/env python3.12
"""
auto_hooks_loader.py — TODO 8
Loads shell auto-hooks from /mnt/agents/dot/hooks/ and /mnt/agents/dot/.bashrc
into the current environment. Sources .bashrc with POSIX `.` instead of `source`.
"""
import os, subprocess, sys

def ts() -> str:
    import time
    return time.strftime("%Y-%m-%dT%H:%M:%S")

def load_hooks() -> int:
    print(f"[{ts()}] TODO 8: Loading auto-hooks...")
    bashrc = "/mnt/agents/dot/.bashrc"
    if os.path.exists(bashrc):
        r = subprocess.run(["bash", "-c", f". {bashrc} && env"],
                           capture_output=True, text=True, timeout=10)
        for line in r.stdout.split("\n"):
            if "=" in line and not line.startswith("_"):
                k, v = line.split("=", 1)
                os.environ[k] = v
        print(f"  Loaded {bashrc}")
    for hook in ["post-checkout", "post-merge"]:
        hp = f"/mnt/agents/dot/hooks/{hook}"
        if os.path.exists(hp):
            subprocess.run(["bash", hp], capture_output=True, timeout=10)
            print(f"  Ran {hook}")
    print(f"[{ts()}] Auto-hooks loaded")
    return 0

if __name__ == "__main__":
    sys.exit(load_hooks())
