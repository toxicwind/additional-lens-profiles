#!/usr/bin/env python3
"""MCP Helper — fetch and install MCP servers from GitHub."""
import json, os, sys, subprocess, argparse
from pathlib import Path
from urllib.request import urlopen, Request

MCP_REGISTRY = {
    "filesystem": "modelcontextprotocol/server-filesystem",
    "github": "modelcontextprotocol/server-github",
    "postgres": "modelcontextprotocol/server-postgres",
    "sqlite": "modelcontextprotocol/server-sqlite",
    "git": "modelcontextprotocol/server-git",
    "fetch": "modelcontextprotocol/server-fetch",
    "puppeteer": "modelcontextprotocol/server-puppeteer",
}

def github_latest(repo):
    """Fetch latest release info from GitHub API."""
    token = os.environ.get("GITHUB_TOKEN", "")
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = Request(f"https://api.github.com/repos/{repo}/releases/latest", headers=headers)
    try:
        with urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {"error": str(e)}

def list_mcp():
    print("Available MCP servers:")
    for name, repo in MCP_REGISTRY.items():
        info = github_latest(repo)
        tag = info.get("tag_name", "unknown") if "error" not in info else f"ERR: {info['error']}"
        print(f"  {name:<15} {repo:<45} {tag}")

def install_mcp(name, target_dir="/mnt/agents/output/workspace/mcp"):
    """Install MCP server by cloning or downloading release."""
    if name not in MCP_REGISTRY:
        print(f"Unknown MCP: {name}")
        return 1
    repo = MCP_REGISTRY[name]
    target = Path(target_dir) / name
    target.mkdir(parents=True, exist_ok=True)
    
    # Try git clone first
    result = subprocess.run(
        ["git", "clone", f"https://github.com/{repo}.git", str(target)],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode == 0:
        print(f"Installed {name} to {target}")
        return 0
    else:
        print(f"Git clone failed: {result.stderr[:200]}")
        return 1

def main():
    parser = argparse.ArgumentParser(description="MCP Helper")
    parser.add_argument("command", choices=["list", "install", "info"])
    parser.add_argument("--name", "-n", help="MCP server name")
    parser.add_argument("--target", "-t", default="/mnt/agents/output/workspace/mcp")
    args = parser.parse_args()

    if args.command == "list":
        list_mcp()
    elif args.command == "install":
        if not args.name:
            print("--name required")
            return 1
        return install_mcp(args.name, args.target)
    elif args.command == "info":
        if not args.name or args.name not in MCP_REGISTRY:
            print("Valid names:", ", ".join(MCP_REGISTRY.keys()))
            return 1
        info = github_latest(MCP_REGISTRY[args.name])
        print(json.dumps(info, indent=2, default=str)[:2000])

if __name__ == "__main__":
    sys.exit(main() or 0)
