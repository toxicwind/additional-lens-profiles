#!/usr/bin/env python3
"""
Swarm MITM Proxy — Intercepts HTTP/HTTPS traffic for analysis
Integrates with tunnel daemon, logs all requests/responses
"""

import asyncio, json, time, re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import aiohttp
from aiohttp import web

LOG_DIR = Path("/mnt/agents/output/workspace/mitm_logs")
LOG_DIR.mkdir(exist_ok=True)

class SwarmMITMProxy:
    """MITM proxy that intercepts, logs, and optionally modifies HTTP traffic.

    Usage:
        proxy = SwarmMITMProxy(listen_port=8080, target_url="https://integrate.api.nvidia.com")
        asyncio.run(proxy.start())
    """

    def __init__(self, listen_port: int = 8080, target_host: str = "integrate.api.nvidia.com", target_port: int = 443):
        self.listen_port = listen_port
        self.target_host = target_host
        self.target_port = target_port
        self.request_log: List[Dict] = []
        self.session: Optional[aiohttp.ClientSession] = None

    async def start(self):
        """Start the MITM proxy server."""
        connector = aiohttp.TCPConnector(limit=100, force_close=False)
        timeout = aiohttp.ClientTimeout(total=60)
        self.session = aiohttp.ClientSession(connector=connector, timeout=timeout)

        app = web.Application()
        app.router.add_route("*", "/{path:.*}", self.handle_request)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", self.listen_port)
        await site.start()

        print(f"MITM proxy listening on :{self.listen_port} -> {self.target_host}:{self.target_port}")

        # Keep running
        while True:
            await asyncio.sleep(1)

    async def handle_request(self, request: web.Request) -> web.Response:
        """Handle incoming request, forward to target, log everything."""
        t0 = time.perf_counter()

        # Build target URL
        path = request.path
        query = request.query_string
        target_url = f"https://{self.target_host}{path}"
        if query:
            target_url += f"?{query}"

        # Read request body
        body = await request.read()

        # Copy headers (filter out host)
        headers = dict(request.headers)
        headers.pop("Host", None)

        # Log request
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "method": request.method,
            "path": path,
            "target_url": target_url,
            "headers": dict(headers),
            "body_size": len(body),
        }

        # Forward to target
        try:
            async with self.session.request(
                method=request.method,
                url=target_url,
                headers=headers,
                data=body,
            ) as resp:
                response_body = await resp.read()

                log_entry["status"] = resp.status
                log_entry["response_size"] = len(response_body)
                log_entry["latency_ms"] = (time.perf_counter() - t0) * 1000

                # Check for API keys in response (for security audit)
                text = response_body.decode("utf-8", errors="replace")
                keys_found = re.findall(r'(api[_-]?key|token|pat|secret)["'\s:=]+([a-zA-Z0-9_\-]{20,})', text, re.IGNORECASE)
                if keys_found:
                    log_entry["keys_exposed"] = len(keys_found)

                self.request_log.append(log_entry)

                # Save incremental log
                log_file = LOG_DIR / f"mitm_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
                with open(log_file, "a") as f:
                    f.write(json.dumps(log_entry) + "\n")

                # Return response to client
                response_headers = dict(resp.headers)
                response_headers.pop("Transfer-Encoding", None)

                return web.Response(
                    body=response_body,
                    status=resp.status,
                    headers=response_headers,
                )
        except Exception as e:
            log_entry["error"] = str(e)
            self.request_log.append(log_entry)
            return web.Response(status=502, text=f"Proxy error: {e}")

    def get_stats(self) -> Dict:
        """Get proxy statistics."""
        if not self.request_log:
            return {}
        total = len(self.request_log)
        errors = sum(1 for r in self.request_log if "error" in r)
        avg_latency = sum(r.get("latency_ms", 0) for r in self.request_log) / total
        return {
            "total_requests": total,
            "errors": errors,
            "avg_latency_ms": avg_latency,
            "keys_exposed": sum(r.get("keys_exposed", 0) for r in self.request_log),
        }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Swarm MITM Proxy")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--target", default="integrate.api.nvidia.com")
    args = parser.parse_args()

    proxy = SwarmMITMProxy(listen_port=args.port, target_host=args.target)
    asyncio.run(proxy.start())
