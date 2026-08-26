"""
MCP bridge — connects VOLUME to sovereign mesh MCP servers.
"""
from __future__ import annotations

import json
import os
from typing import Any

import httpx


class MCPBridge:
    """Bridge to MCP servers (ghas-mcp, byte-vision, etc.)."""

    def __init__(self, base_url: str = "http://127.0.0.1:25127"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=httpx.Timeout(30.0))

    async def list_tools(self) -> list[dict[str, Any]]:
        """List available MCP tools."""
        try:
            r = await self.client.get(f"{self.base_url}/mcp")
            return r.json().get("tools", [])
        except Exception as e:
            return [{"error": str(e)}]

    async def call_tool(self, tool_name: str, params: dict[str, Any]) -> dict[str, Any]:
        """Call an MCP tool."""
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": params},
            "id": 1,
        }
        try:
            r = await self.client.post(f"{self.base_url}/mcp", json=payload)
            return r.json()
        except Exception as e:
            return {"error": str(e)}

    async def health(self) -> dict[str, Any]:
        """Check MCP bridge health."""
        try:
            r = await self.client.get(f"{self.base_url}/health")
            return r.json()
        except Exception as e:
            return {"status": "error", "detail": str(e)}

    async def close(self):
        await self.client.aclose()
