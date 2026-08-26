#!/usr/bin/env bash
# Restart socat tunnels for CDP/VNC reverse proxy
# Run as root or via unshare

set -euo pipefail

echo "=== Tunnel Restart ==="

# Kill existing socat processes
pkill -f "socat TCP-LISTEN:80" 2>/dev/null || true
pkill -f "socat TCP-LISTEN:443" 2>/dev/null || true
pkill -f "socat TCP-LISTEN:5900" 2>/dev/null || true

# Start tunnels
# :80 -> VNC RFB (5901)
socat TCP-LISTEN:80,fork,reuseaddr TCP:127.0.0.1:5901 &
echo "[OK] :80 -> 127.0.0.1:5901 (VNC RFB)"

# :443 -> VNC WebSocket (6080)
socat TCP-LISTEN:443,fork,reuseaddr TCP:127.0.0.1:6080 &
echo "[OK] :443 -> 127.0.0.1:6080 (VNC WebSocket)"

# :5900 -> VNC RFB (5901) — duplicate for compatibility
socat TCP-LISTEN:5900,fork,reuseaddr TCP:127.0.0.1:5901 &
echo "[OK] :5900 -> 127.0.0.1:5901 (VNC RFB)"

echo ""
echo "=== Verify ==="
ss -tlnp | grep -E ":80|:443|:5900|:5901" || echo "No listeners found"

echo ""
echo "Tunnels restarted. PID $$"
