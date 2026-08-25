#!/usr/bin/env python3.12
"""
fix_symlinks.py — TODO 7
Finds all symlinks under /mnt/agents and replaces them with
copies of their targets. Never creates new symlinks.
"""
import os, subprocess, sys
from pathlib import Path

def ts() -> str:
    import time
    return time.strftime("%Y-%m-%dT%H:%M:%S")

def fix_symlink(link_path: Path) -> bool:
    if not link_path.is_symlink():
        return False
    target = os.readlink(link_path)
    link_path.unlink()
    if os.path.isdir(target):
        os.makedirs(str(link_path), exist_ok=True)
        for item in os.listdir(target):
            s = os.path.join(target, item)
            d = os.path.join(str(link_path), item)
            subprocess.run(["cp", "-r" if os.path.isdir(s) else "", s, d],
                           capture_output=True, timeout=5)
    else:
        subprocess.run(["cp", target, str(link_path)], capture_output=True, timeout=5)
        os.chmod(str(link_path), 0o755)
    return True

def main() -> int:
    print(f"[{ts()}] TODO 7: Fixing symlinks...")
    fixed = 0
    for root, dirs, files in os.walk("/mnt/agents"):
        for name in dirs + files:
            p = Path(root) / name
            if p.is_symlink():
                if fix_symlink(p):
                    fixed += 1
    print(f"[{ts()}] Fixed {fixed} symlinks")
    return 0

if __name__ == "__main__":
    sys.exit(main())
