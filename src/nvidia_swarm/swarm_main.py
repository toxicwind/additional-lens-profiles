#!/usr/bin/env python3
"""
NVIDIA Swarm Main Orchestrator
Ties together: Core (DAG) + Agent (Llama-native) + Transport (HTTP/2) + Lens (Profiles)
"""

import asyncio, json, os
from pathlib import Path
from dotenv import load_dotenv

from nvidia_swarm_core import NvidiaSwarmDAG, DAGNode
from nvidia_swarm_agent import NvidiaAgent
from nvidia_swarm_transport import NvidiaSwarmTransport
from lens_profile import LENS_REGISTRY, get_lens

# Load .env (never committed)
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

NV_KEY = os.getenv("NVIDIA_API_KEY", "")
NV_URL = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")

async def run_swarm_task(task: str, lens_names: List[str], context: dict = None):
    """Run a complete swarm task with NVIDIA NIM optimization.

    Args:
        task: The user task description
        lens_names: List of lens profile names to use (e.g., ["researcher", "analyst"])
        context: Additional context dict

    Returns:
        Dict of agent results + throughput stats
    """
    context = context or {}
    context.setdefault("nvidia_api_key", NV_KEY)
    context.setdefault("nvidia_base_url", NV_URL)

    async with NvidiaSwarmDAG(max_concurrent=16, timeout=30) as dag:
        # Register agents from lens profiles
        for lens_name in lens_names:
            lens = get_lens(lens_name)
            agent = NvidiaAgent(**lens.to_agent_config())
            dag.register_agent(lens.name, agent)

        # Build DAG nodes
        nodes = []
        for i, lens_name in enumerate(lens_names):
            lens = get_lens(lens_name)
            deps = [get_lens(lens_names[j]).name for j in range(i)] if i > 0 else []
            nodes.append(DAGNode(
                agent_name=lens.name,
                dependencies=deps,
                inputs={"task": task, "step": i + 1},
                output_key=f"{lens_name}_result",
            ))

        # Execute DAG
        results = await dag.run_dag(nodes, context)
        stats = dag.get_throughput_stats()

        return {
            "results": {k: {
                "output": v.output,
                "tool_calls": v.tool_calls,
                "latency_ms": v.latency_ms,
                "tokens_in": v.tokens_in,
                "tokens_out": v.tokens_out,
            } for k, v in results.items()},
            "throughput": stats,
            "task": task,
        }

async def main():
    """Example: Run an IPTV research swarm."""
    task = "Find all GitHub repos related to IPTV, Stremio, or Nuvio updated in August 2026"

    # Define the swarm: researcher finds repos, analyst categorizes, coder builds tools
    lens_names = ["researcher", "analyst", "coder"]

    print(f"Running NVIDIA Swarm task: {task}")
    print(f"Agents: {lens_names}")

    result = await run_swarm_task(task, lens_names)

    print(f"\n=== RESULTS ===")
    for agent_name, data in result["results"].items():
        print(f"\n{agent_name}:")
        print(f"  Output: {data['output'][:200]}...")
        print(f"  Latency: {data['latency_ms']:.1f}ms")
        print(f"  Tokens: {data['tokens_in']} in / {data['tokens_out']} out")

    print(f"\n=== THROUGHPUT ===")
    for k, v in result["throughput"].items():
        print(f"  {k}: {v}")

    return result

if __name__ == "__main__":
    asyncio.run(main())
