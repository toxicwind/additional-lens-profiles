#!/usr/bin/env python3.12
"""
unshare_root_fix.py — TODO 6
Wraps commands in an unshared user namespace as root.
Fixes the PermissionError on /proc/self/uid_map by using
the system `unshare` binary with --map-root-user instead
of direct ctypes syscall + manual map writes.
"""
import os, sys, subprocess

def unshare_root(cmd: list[str]) -> int:
    unshare_bin = "/usr/bin/unshare"
    if not os.path.exists(unshare_bin):
        # Fallback to dot bin
        unshare_bin = "/mnt/agents/dot/bin/unshare"
    args = [unshare_bin, "--user", "--pid", "--fork", "--mount-proc", "--map-root-user"] + cmd
    return subprocess.run(args).returncode

def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: unshare_root_fix.py <command> [args...]"); return 1
    return unshare_root(sys.argv[1:])

if __name__ == "__main__":
    sys.exit(main())
