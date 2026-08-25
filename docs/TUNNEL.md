# Tunnel & Infrastructure

## Active Tunnels

| Port | Forward | Purpose |
|------|---------|---------|
| 80 | → 5901 | VNC RFB (HTTP access) |
| 443 | → 6080 | VNC WebSocket |
| 5900 | → 5901 | VNC RFB (duplicate) |

## Services

| Service | Address | Status |
|---------|---------|--------|
| Portal API | `[::1]:8080` | Proxies to `kimi-api-sandbox.msh.team/apiv2` |
| gRPC Envd | `[::1]:32001` | IPv6 only |
| Chrome CDP | `127.0.0.1:9222` | Browser automation |
| KasmVNC | `127.0.0.1:6080` | Web VNC |
| HTTP Server | `127.0.0.1:18080` | Local file serving |

## CDP Proxy

The CDP proxy at `127.0.0.1:9223` bridges Chrome DevTools Protocol for remote access.

## Usage

```bash
# Access VNC via tunnel
curl http://localhost:80  # → VNC RFB on 5901

# Access portal API
curl http://[::1]:8080/health

# Access gRPC
python -c "import grpc; channel = grpc.insecure_channel('[::1]:32001')"
```
