#!/usr/bin/env python3.12
"""
fix_vnc_rfb.py — TODO 2
Diagnoses and repairs VNC RFB port 5901 forwarding.
Xvnc runs on display :99 with -rfbport 5901 but 5901 appears closed
because socat tunnels (80->5901, 443->6080, 5900->5901) were not running.
This module starts the missing socat relays.
"""
import os, subprocess, socket, time, sys
from pathlib import Path

def ts() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")

def port_open(port: int, host="127.0.0.1", timeout=1) -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((host, port))
        s.close()
        return True
    except Exception:
        return False

def get_xvnc_pid() -> int | None:
    for pid_dir in sorted(Path("/proc").glob("[0-9]*")):
        try:
            cmd = (pid_dir / "cmdline").read_text().replace("\x00", " ")
            if "Xvnc" in cmd and "-rfbport" in cmd:
                return int(pid_dir.name)
        except Exception:
            pass
    return None

def get_xvnc_rfb_port(pid: int) -> int:
    """Parse /proc/PID/cmdline for -rfbport value."""
    try:
        cmd = (Path(f"/proc/{pid}/cmdline")).read_text().replace("\x00", " ")
        parts = cmd.split()
        for i, p in enumerate(parts):
            if p == "-rfbport" and i + 1 < len(parts):
                return int(parts[i + 1])
    except Exception:
        pass
    return 5901

def kill_existing_socat():
    subprocess.run(["pkill", "-f", "socat"], capture_output=True)
    time.sleep(0.3)

def start_socat(src: int, dst: int) -> int:
    cmd = ["socat", f"TCP-LISTEN:{src},fork,reuseaddr", f"TCP:127.0.0.1:{dst}"]
    p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return p.pid

def main() -> int:
    print(f"[{ts()}] TODO 2: VNC RFB fix")
    pid = get_xvnc_pid()
    if pid is None:
        print(f"  ERROR: Xvnc not found")
        return 1
    rfb_port = get_xvnc_rfb_port(pid)
    print(f"  Xvnc PID {pid}, RFB port {rfb_port}")

    before = {
        80: port_open(80), 443: port_open(443),
        5900: port_open(5900), 5901: port_open(5901), 6080: port_open(6080)
    }
    print(f"  Before: {before}")

    kill_existing_socat()
    relays = [(80, rfb_port), (443, 6080), (5900, rfb_port)]
    for src, dst in relays:
        pid = start_socat(src, dst)
        print(f"  Started socat {src}->{dst} (PID {pid})")

    time.sleep(1)
    after = {
        80: port_open(80), 443: port_open(443),
        5900: port_open(5900), 5901: port_open(5901), 6080: port_open(6080)
    }
    print(f"  After:  {after}")

    ok = all(after[p] for p in [80, 443, 5900, 6080])
    print(f"[{ts()}] VNC RFB fix: {'OK' if ok else 'PARTIAL'}")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
