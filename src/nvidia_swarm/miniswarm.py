#!/usr/bin/env python3
"""
MiniSwarm — Minimal working NVIDIA NIM swarm.
Proven live 2026-08-25. Copy this to test immediately.
"""
import requests, json, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

NV_KEY = ""  # Fill from .env
NV_URL = "https://integrate.api.nvidia.com/v1/chat/completions"

@dataclass
class AgentResult:
    agent_name: str
    output: str
    latency_ms: float = 0
    tokens_in: int = 0
    tokens_out: int = 0

class MiniSwarm:
    def __init__(self, max_concurrent=3, timeout=15):
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.agents = {}
        self.results = {}

    def register(self, name, system, model="meta/llama-3.1-8b-instruct"):
        self.agents[name] = {"system": system, "model": model}

    def _call(self, name, messages, model):
        t0 = time.perf_counter()
        r = requests.post(NV_URL, headers={"Authorization": f"Bearer {NV_KEY}", "Content-Type": "application/json"},
            json={"model": model, "messages": messages, "temperature": 0.3, "max_tokens": 128}, timeout=self.timeout)
        if r.status_code != 200:
            return AgentResult(name, f"ERR {r.status_code}: {r.text[:100]}", 0, 0, 0)
        d = r.json()
        lat = (time.perf_counter() - t0) * 1000
        return AgentResult(name, d["choices"][0]["message"]["content"], lat,
            d.get("usage", {}).get("prompt_tokens", 0), d.get("usage", {}).get("completion_tokens", 0))

    def run(self, dag):
        pending = {n["agent_name"]: n for n in dag}
        completed = set()
        while pending:
            ready = [n for n in pending.values() if all(d in completed for d in n.get("dependencies", []))]
            if not ready: raise ValueError("Circular dep")
            with ThreadPoolExecutor(max_workers=self.max_concurrent) as ex:
                futures = {}
                for node in ready:
                    ag = self.agents[node["agent_name"]]
                    msgs = [{"role": "system", "content": ag["system"]}]
                    for d in node.get("dependencies", []):
                        if d in self.results: msgs.append({"role": "user", "content": f"From {d}: {self.results[d].output}"})
                    for k, v in node.get("inputs", {}).items(): msgs.append({"role": "user", "content": f"{k}: {v}"})
                    futures[ex.submit(self._call, node["agent_name"], msgs, ag["model"])] = node["agent_name"]
                for fut in as_completed(futures):
                    n = futures[fut]
                    self.results[n] = fut.result()
                    completed.add(n); del pending[n]
                    print(f"{n}: {self.results[n].latency_ms:.0f}ms")
        return self.results

if __name__ == "__main__":
    import os
    NV_KEY = os.getenv("NVIDIA_API_KEY", "")
    s = MiniSwarm()
    s.register("r", "Research agent. One sentence.")
    s.register("a", "Analyst. One sentence.")
    results = s.run([
        {"agent_name": "r", "inputs": {"task": "What is quantum computing?"}},
        {"agent_name": "a", "dependencies": ["r"], "inputs": {"task": "Implications?"}},
    ])
    for k, v in results.items(): print(f"{k}: {v.output.strip()}")
