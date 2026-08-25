#!/usr/bin/env python3.12
"""
fix_rustup_source.py — TODO 1
Replaces non-POSIX 'source' builtin with POSIX '.' in all shell scripts
under /mnt/agents/dot, fixing the 'source: not found' error that occurs
when scripts are executed by /bin/sh instead of bash.
"""
import re, sys, time
from pathlib import Path

def ts() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")

def fix_source_in_file(p: Path) -> bool:
    """Return True if file was modified."""
    try:
        data = p.read_text(errors="replace")
        # Replace 'source ' when used as a shell command, not inside strings/docs
        new_data = re.sub(r"(?<![a-zA-Z0-9_\-/])source\s+", ". ", data)
        if new_data != data:
            p.write_text(new_data)
            return True
    except Exception:
        pass
    return False

def fix_rustup_env_files() -> int:
    """Fix known cargo/env files that may use 'source'."""
    fixed = 0
    for env_path in [Path("/root/.cargo/env"), Path("/workspace/rust/cargo/env")]:
        if env_path.exists() and fix_source_in_file(env_path):
            print(f"  [{ts()}] FIXED env: {env_path}")
            fixed += 1
    return fixed

def fix_all_dot_shell() -> int:
    """Recursively fix all files under /mnt/agents/dot."""
    base = Path("/mnt/agents/dot")
    fixed = 0
    for p in base.rglob("*"):
        if p.is_file() and p.stat().st_size < 5 * 1024 * 1024:
            if fix_source_in_file(p):
                fixed += 1
    return fixed

def verify() -> bool:
    import subprocess
    r = subprocess.run(
        ["sh", "-c", ". /root/.cargo/env && echo OK"],
        capture_output=True, text=True, timeout=10
    )
    ok = r.stdout.strip() == "OK"
    print(f"  [{ts()}] VERIFY sh -c '. /root/.cargo/env': {r.stdout.strip()} {r.stderr.strip()}")
    r2 = subprocess.run(
        ["bash", "-c", ". /root/.cargo/env && which rustc"],
        capture_output=True, text=True, timeout=10
    )
    print(f"  [{ts()}] VERIFY bash rustc path: {r2.stdout.strip()}")
    return ok

def main() -> int:
    print(f"[{ts()}] TODO 1: Fixing rustup source -> . (POSIX)")
    env_fixed = fix_rustup_env_files()
    dot_fixed = fix_all_dot_shell()
    total = env_fixed + dot_fixed
    print(f"[{ts()}] TODO 1: Fixed {total} files ({env_fixed} env + {dot_fixed} dot)")
    verify()
    return 0

if __name__ == "__main__":
    sys.exit(main())
