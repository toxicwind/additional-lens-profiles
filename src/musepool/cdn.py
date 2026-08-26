"""
CDN-aware package resolution for musepool.
Selects fastest mirror based on latency probes.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Optional

import httpx


@dataclass
class CDNEndpoint:
    name: str
    url: str
    latency_ms: float = float("inf")
    healthy: bool = False


class CDNResolver:
    """Resolves the fastest CDN endpoint for package/asset downloads."""

    ENDPOINTS = {
        "alibaba": "https://mirrors.aliyun.com/pypi/simple/",
        "tsinghua": "https://pypi.tuna.tsinghua.edu.cn/simple/",
        "pypi": "https://pypi.org/simple/",
    }

    def __init__(self, preference: Optional[str] = None):
        self.preference = preference
        self._cache: dict[str, CDNEndpoint] = {}

    async def probe(self, timeout: float = 3.0) -> CDNEndpoint:
        """Probe all endpoints and return the fastest."""
        if self.preference and self.preference in self.ENDPOINTS:
            return CDNEndpoint(self.preference, self.ENDPOINTS[self.preference], 0, True)

        async with httpx.AsyncClient(timeout=httpx.Timeout(timeout)) as client:
            tasks = [
                self._probe_one(client, name, url)
                for name, url in self.ENDPOINTS.items()
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        endpoints = [r for r in results if isinstance(r, CDNEndpoint) and r.healthy]
        if not endpoints:
            # Fallback to PyPI
            return CDNEndpoint("pypi", self.ENDPOINTS["pypi"], 0, True)

        return min(endpoints, key=lambda e: e.latency_ms)

    async def _probe_one(self, client: httpx.AsyncClient, name: str, url: str) -> CDNEndpoint:
        import time
        start = time.time()
        try:
            resp = await client.head(url)
            latency = (time.time() - start) * 1000
            return CDNEndpoint(name, url, latency, resp.status_code < 400)
        except Exception:
            return CDNEndpoint(name, url, float("inf"), False)
