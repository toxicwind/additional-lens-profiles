#!/usr/bin/env python3
"""
NVIDIA Swarm Main Orchestrator — PROVEN LIVE 2026-08-25
Uses meta/llama-3.1-70b-instruct as default (405B unavailable on integrate tier).
"""

import os, json
from pathlib import Path
from dotenv import load_dotenv

# Load .env
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

NV_KEY = os.getenv("NVIDIA_API_KEY", "")
NV_URL = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
DEFAULT_MODEL = "meta/llama-3.1-70b-instruct"  # Proven working, best accuracy/speed tradeoff

def run_swarm_sync(task: str, agents: list, context: dict = None):
    """Synchronous swarm execution — proven live."""
    import requests, time
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from dataclasses import dataclass

    @dataclass
    class Result:
        name: str; output: str; latency_ms: float = 0; tokens_in: int = 0; tokens_out: int = 0

    registry = {
        "researcher": {"system": "Precise research agent. Facts only. 2-3 sentences.", "model": DEFAULT_MODEL},
        "analyst": {"system": "Business analyst. Synthesize into conclusion. 1-2 sentences.", "model": DEFAULT_MODEL},
        "coder": {"system": "Python coder. Short script, max 5 lines. Standard lib only.", "model": DEFAULT_MODEL},
    }

    results = {}
    pending = {a["name"]: a for a in agents}
    completed = set()

    while pending:
        ready = [a for a in pending.values() if all(d in completed for d in a.get("deps", []))]
        if not ready: raise ValueError("Circular dependency")

        with ThreadPoolExecutor(max_workers=2) as ex:
            futures = {}
            for ag in ready:
                cfg = registry.get(ag["name"], registry["researcher"])
                msgs = [{"role": "system", "content": cfg["system"]}]
                for d in ag.get("deps", []):
                    if d in results: msgs.append({"role": "user", "content": f"From {d}: {results[d].output}"})
                msgs.append({"role": "user", "content": ag.get("task", "")})

                def call(name, messages, model):
                    t0 = time.perf_counter()
                    r = requests.post(f"{NV_URL}/chat/completions", headers={"Authorization": f"Bearer {NV_KEY}", "Content-Type": "application/json"},
                        json={"model": model, "messages": messages, "temperature": 0.2, "max_tokens": 256}, timeout=30)
                    if r.status_code != 200: return Result(name, f"ERR {r.status_code}")
                    d = r.json()
                    return Result(name, d["choices"][0]["message"]["content"], (time.perf_counter()-t0)*1000,
                        d.get("usage", {}).get("prompt_tokens", 0), d.get("usage", {}).get("completion_tokens", 0))

                futures[ex.submit(call, ag["name"], msgs, cfg["model"])] = ag["name"]

            for fut in as_completed(futures):
                n = futures[fut]
                results[n] = fut.result()
                completed.add(n); del pending[n]

    return results

if __name__ == "__main__":
    agents = [
        {"name": "researcher", "task": "What is quantum computing?"},
        {"name": "analyst", "deps": ["researcher"], "task": "Business implications?"},
    ]
    res = run_swarm_sync("test", agents)
    for k, v in res.items(): print(f"{k}: {v.output[:100]}...")
