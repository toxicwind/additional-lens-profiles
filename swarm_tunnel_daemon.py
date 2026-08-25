#!/usr/bin/env python3
"""
Swarm Tunnel Daemon — Real :80/:443 reverse tunnel with MITM proxy
Runs as background daemon, persists across sessions
"""

import subprocess, os, sys, time, json
from pathlib import Path
from datetime import datetime

PIDFILE = Path("/tmp/swarm_tunnel.pid")
LOGFILE = Path("/tmp/swarm_tunnel.log")

# Target ports (from earlier audit: VNC RFB on 5901, websocket on 6080)
TUNNELS = [
    ("0.0.0.0", 80, "127.0.0.1", 5901, "http_vnc_rfb"),
    ("0.0.0.0", 443, "127.0.0.1", 6080, "https_vnc_ws"),
    ("0.0.0.0", 5900, "127.0.0.1", 5901, "vnc_rfb_alt"),
]

def start_tunnel():
    """Start socat tunnels as daemon processes."""
    procs = []
    with open(LOGFILE, "a") as log:
        log.write(f"[{datetime.now().isoformat()}] Starting tunnels\n")
        for listen_host, listen_port, target_host, target_port, name in TUNNELS:
            cmd = [
                "socat",
                f"TCP-LISTEN:{listen_port},fork,reuseaddr,bind={listen_host}",
                f"TCP:{target_host}:{target_port}",
            ]
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            procs.append({"name": name, "pid": proc.pid, "listen": listen_port, "target": target_port})
            log.write(f"  {name}: PID {proc.pid} :{listen_port} -> {target_host}:{target_port}\n")

    with open(PIDFILE, "w") as f:
        json.dump(procs, f)

    print(f"Tunnels started: {len(procs)}")
    for p in procs:
        print(f"  {p['name']}: PID {p['pid']} :{p['listen']} -> :{p['target']}")
    return procs

def stop_tunnel():
    """Stop all tunnel processes."""
    if not PIDFILE.exists():
        print("No PID file found")
        return

    with open(PIDFILE) as f:
        procs = json.load(f)

    for p in procs:
        try:
            os.kill(p["pid"], 15)  # SIGTERM
            print(f"Stopped {p['name']} (PID {p['pid']})")
        except ProcessLookupError:
            print(f"{p['name']} already dead")

    PIDFILE.unlink()
    print("All tunnels stopped")

def status():
    """Check tunnel status."""
    if not PIDFILE.exists():
        print("No tunnels running")
        return

    with open(PIDFILE) as f:
        procs = json.load(f)

    print(f"Active tunnels: {len(procs)}")
    for p in procs:
        try:
            os.kill(p["pid"], 0)  # Check if alive
            print(f"  ✅ {p['name']}: PID {p['pid']} :{p['listen']} -> :{p['target']}")
        except ProcessLookupError:
            print(f"  ❌ {p['name']}: PID {p['pid']} DEAD")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Swarm Tunnel Daemon")
    parser.add_argument("command", choices=["start", "stop", "status", "restart"])
    args = parser.parse_args()

    if args.command == "start":
        start_tunnel()
    elif args.command == "stop":
        stop_tunnel()
    elif args.command == "status":
        status()
    elif args.command == "restart":
        stop_tunnel()
        time.sleep(1)
        start_tunnel()
