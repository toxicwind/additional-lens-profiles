#!/usr/bin/env python3
"""
MCP Tool Implementations — Real executors for the swarm.
Each tool is a pure function that returns a string result.
"""

import requests, json, re
from datetime import datetime
from typing import Dict

def web_search(query: str) -> str:
    """Search the web. Returns top results as formatted text."""
    # Note: This is a stub that documents the interface.
    # In production, this connects to a search API or uses mshtools-web_search.
    return f"[web_search] Query: '{query}'\nStatus: Tool interface ready. Connect to search provider."

def web_open_url(url: str) -> str:
    """Fetch a URL and return content preview."""
    try:
        r = requests.get(url, timeout=15, headers={
            "User-Agent": "ARC-AGI-Swarm/1.0 (MCP; research)"
        })
        text = r.text[:3000]
        # Extract title
        title_match = re.search(r"<title>(.*?)</title>", text, re.IGNORECASE | re.DOTALL)
        title = title_match.group(1).strip() if title_match else "No title"
        # Extract meta description
        desc_match = re.search(r'<meta[^>]*name=["']description["'][^>]*content=["']([^"']+)', text, re.IGNORECASE)
        desc = desc_match.group(1) if desc_match else "No description"
        return f"[web_open_url] {url}\nStatus: {r.status_code}\nTitle: {title}\nDescription: {desc}\nPreview: {text[:800]}..."
    except Exception as e:
        return f"[web_open_url] {url}\nERROR: {type(e).__name__}: {e}"

def github_search_repos(query: str, per_page: int = 5) -> str:
    """Search GitHub repositories."""
    try:
        r = requests.get("https://api.github.com/search/repositories",
            params={"q": query, "per_page": per_page, "sort": "updated", "order": "desc"},
            headers={"Accept": "application/vnd.github+json"},
            timeout=15)
        data = r.json()
        items = data.get("items", [])
        lines = [f"[github_search] Query: '{query}' | Found {data.get('total_count', 0)} repos"]
        for item in items[:per_page]:
            lines.append(f"  • {item.get('full_name','?')} | ⭐{item.get('stargazers_count',0)} | Updated: {item.get('pushed_at','?')} | {item.get('description','')[:80]}")
        return "\n".join(lines)
    except Exception as e:
        return f"[github_search] ERROR: {type(e).__name__}: {e}"

def github_get_file(owner: str, repo: str, path: str, branch: str = "main") -> str:
    """Fetch a file from GitHub raw."""
    url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
    return web_open_url(url)

def extract_m3u_urls(text: str) -> str:
    """Extract M3U/M3U8 URLs from text."""
    import re
    urls = re.findall(r'https?://[^\s"<>]+\.(m3u|m3u8)(\?[^\s"<>]*)?', text, re.IGNORECASE)
    if not urls:
        return "[extract_m3u_urls] No M3U URLs found"
    return "[extract_m3u_urls] Found URLs:\n" + "\n".join([f"  • {u[0]}" for u in urls[:20]])

def extract_manifest_urls(text: str) -> str:
    """Extract manifest.json URLs from text."""
    import re
    urls = re.findall(r'https?://[^\s"<>]+/manifest\.json', text, re.IGNORECASE)
    if not urls:
        return "[extract_manifest_urls] No manifest URLs found"
    return "[extract_manifest_urls] Found URLs:\n" + "\n".join([f"  • {u}" for u in urls[:20]])

def get_current_time() -> str:
    """Return current UTC time."""
    return datetime.now().isoformat() + "Z"

# Tool schemas for registration
TOOL_SCHEMAS = {
    "web_search": {
        "description": "Search the web for information",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query string"},
            },
            "required": ["query"],
        },
        "executor": web_search,
    },
    "web_open_url": {
        "description": "Open a URL and read its content",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to fetch"},
            },
            "required": ["url"],
        },
        "executor": web_open_url,
    },
    "github_search": {
        "description": "Search GitHub repositories",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "GitHub search query"},
                "per_page": {"type": "integer", "description": "Results per page (max 100)"},
            },
            "required": ["query"],
        },
        "executor": github_search_repos,
    },
    "github_get_file": {
        "description": "Fetch a file from a GitHub repository",
        "parameters": {
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner"},
                "repo": {"type": "string", "description": "Repository name"},
                "path": {"type": "string", "description": "File path in repo"},
                "branch": {"type": "string", "description": "Git branch (default: main)"},
            },
            "required": ["owner", "repo", "path"],
        },
        "executor": github_get_file,
    },
    "extract_m3u_urls": {
        "description": "Extract M3U/M3U8 stream URLs from text",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to scan for M3U URLs"},
            },
            "required": ["text"],
        },
        "executor": extract_m3u_urls,
    },
    "extract_manifest_urls": {
        "description": "Extract Stremio manifest.json URLs from text",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to scan for manifest URLs"},
            },
            "required": ["text"],
        },
        "executor": extract_manifest_urls,
    },
    "get_current_time": {
        "description": "Get current UTC timestamp",
        "parameters": {
            "type": "object",
            "properties": {},
        },
        "executor": get_current_time,
    },
}
