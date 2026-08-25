#!/usr/bin/env python3
"""
Case Study 01 Runner: Groq Compound Mini Deprecation OSINT
Uses: SwarmPlanner + SwarmRunner + NvidiaSwarmDAG
"""

import asyncio, json, os
from pathlib import Path
from datetime import datetime

# Load .env
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        if line.strip() and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k, v)

from nvidia_swarm_runner import SwarmRunner

async def main():
    runner = SwarmRunner(max_concurrent=16, timeout=30)

    task = """Investigate Groq Compound Mini deprecation:
    1. What is Compound Mini? Find architecture, history, public references
    2. Why is Groq deprecating it now? Analyze competitive landscape
    3. Build migration script from Groq API to NVIDIA NIM
    4. Synthesize findings into OSINT report with sources"""

    context = {
        "nvidia_api_key": os.environ.get("NVIDIA_API_KEY", ""),
        "nvidia_base_url": os.environ.get("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1"),
        "focus": "groq",
        "model": "compound-mini",
        "deadline": "2026-09-21",
        "company": "Groq, Inc.",
        "address": "2700 Zanker Road, Suite 150, San Jose, CA 95134",
    }

    print("=" * 60)
    print("CASE STUDY 01: Groq Compound Mini Deprecation OSINT")
    print("=" * 60)

    result = await runner.run(task, context)

    # Save results
    out_dir = Path(__file__).parent
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(out_dir / "execution_result.json", "w") as f:
        json.dump(result, f, indent=2, default=str)

    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    print(f"Total tasks: {result['summary']['total_tasks']}")
    print(f"Total waves: {result['summary']['total_waves']}")
    print(f"Total latency: {result['summary']['total_latency_ms']:.1f}ms")
    print(f"Total tokens: {result['summary']['total_tokens']}")
    print(f"\nSaved to: {out_dir / 'execution_result.json'}")

    return result

if __name__ == "__main__":
    asyncio.run(main())
