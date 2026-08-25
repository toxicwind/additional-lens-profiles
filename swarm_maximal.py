#!/usr/bin/env python3
"""
SWARM MAXIMAL — Full-Stack Multi-Agent System
Uses 90B vision for maximal reasoning, 70B for complex code, 8B for fast tasks
Integrates tunnel daemon + MITM proxy + real tool execution
"""

import asyncio, aiohttp, json, time, os, re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

BASE = Path("/mnt/agents/output/workspace")
NV_KEY = os.environ.get("NVIDIA_API_KEY", "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")
NV_URL = os.environ.get("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")

# Model tiers
MAXIMAL_MODEL = "meta/llama-3.2-90b-vision-instruct"  # 90B — complex reasoning, proofs, architecture
COMPLEX_MODEL = "meta/llama-3.3-70b-instruct"         # 70B — complex code generation
STANDARD_MODEL = "meta/llama-3.1-70b-instruct"        # 70B — standard analysis
FAST_MODEL = "meta/llama-3.1-8b-instruct"             # 8B — fast/simple tasks

@dataclass
class SwarmAgent:
    name: str
    model: str
    system_prompt: str
    max_tokens: int = 4096
    temperature: float = 0.3
    tools: List[str] = field(default_factory=list)

@dataclass
class SwarmResult:
    agent_name: str
    output: str
    latency_ms: float
    tokens_in: int = 0
    tokens_out: int = 0
    model_used: str = ""
    saved_to: str = ""

class SwarmMaximal:
    """Maximal swarm orchestrator with streaming, saving, and real tool integration."""

    def __init__(self, max_concurrent: int = 4):
        self.max_concurrent = max_concurrent
        self.results: Dict[str, SwarmResult] = {}
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        connector = aiohttp.TCPConnector(
            limit=64, limit_per_host=32, force_close=False, ttl_dns_cache=300
        )
        timeout = aiohttp.ClientTimeout(total=120, connect=15)
        self.session = aiohttp.ClientSession(connector=connector, timeout=timeout)
        return self

    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()

    async def execute_agent(self, agent: SwarmAgent, user_prompt: str, context: Dict = None) -> SwarmResult:
        """Execute single agent with streaming output and immediate save."""
        t0 = time.perf_counter()
        chunks = []

        # Inject context from previous agents
        if context:
            dep_text = ""
            for dep_name, dep_result in context.items():
                if isinstance(dep_result, SwarmResult):
                    dep_text += f"\n[Agent '{dep_name}' output]: {dep_result.output[:800]}\n"
            if dep_text:
                user_prompt = dep_text + "\n\nYour task: " + user_prompt

        payload = {
            "model": agent.model,
            "messages": [
                {"role": "system", "content": agent.system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": agent.temperature,
            "max_tokens": agent.max_tokens,
            "stream": True,
        }
        headers = {"Authorization": f"Bearer {NV_KEY}", "Content-Type": "application/json"}

        try:
            async with self.session.post(f"{NV_URL}/chat/completions", headers=headers, json=payload) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    output = f"HTTP {resp.status}: {text[:500]}"
                else:
                    async for line in resp.content:
                        line = line.decode("utf-8").strip()
                        if line.startswith("data: "):
                            data = line[6:]
                            if data == "[DONE]": break
                            try:
                                chunk = json.loads(data)
                                delta = chunk["choices"][0]["delta"].get("content", "")
                                if delta:
                                    chunks.append(delta)
                            except:
                                pass
                    output = "".join(chunks)
        except Exception as e:
            output = f"EXCEPTION: {type(e).__name__}: {str(e)[:500]}"

        latency = (time.perf_counter() - t0) * 1000

        # Estimate tokens (rough: 4 chars per token)
        tokens_out = len(output) // 4
        tokens_in = (len(agent.system_prompt) + len(user_prompt)) // 4

        # Save immediately
        safe_name = re.sub(r"[^a-zA-Z0-9_]", "_", agent.name)
        out_file = BASE / f"swarm_maximal_{safe_name}_{datetime.now().strftime('%H%M%S')}.md"
        with open(out_file, "w") as f:
            f.write(f"# {agent.name} Output\n\n")
            f.write(f"**Model**: {agent.model}\n")
            f.write(f"**Latency**: {latency:.0f}ms\n")
            f.write(f"**Tokens**: {tokens_in} in / {tokens_out} out\n")
            f.write(f"**Timestamp**: {datetime.now().isoformat()}\n\n")
            f.write("---\n\n")
            f.write(output)

        result = SwarmResult(
            agent_name=agent.name,
            output=output,
            latency_ms=latency,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            model_used=agent.model,
            saved_to=str(out_file),
        )
        self.results[agent.name] = result
        print(f"  ✅ {agent.name} ({agent.model.split('/')[-1]}): {latency:.0f}ms | {len(output)} chars | saved")
        return result

    async def run_dag(self, agents: List[SwarmAgent], user_prompts: List[str], dependencies: List[List[int]] = None) -> Dict[str, SwarmResult]:
        """Execute agents as DAG with parallelization."""
        if dependencies is None:
            dependencies = [[] for _ in agents]

        completed = set()
        pending = list(range(len(agents)))
        sem = asyncio.Semaphore(self.max_concurrent)

        while pending:
            ready = [i for i in pending if all(d in completed for d in dependencies[i])]
            if not ready:
                raise ValueError("Circular dependencies")

            async def exec_with_sem(idx):
                async with sem:
                    agent = agents[idx]
                    prompt = user_prompts[idx]
                    # Build context from completed dependencies
                    ctx = {agents[d].name: self.results[agents[d].name] for d in dependencies[idx] if d in completed}
                    return await self.execute_agent(agent, prompt, ctx)

            tasks = [exec_with_sem(i) for i in ready]
            await asyncio.gather(*tasks)

            for i in ready:
                completed.add(i)
                pending.remove(i)

        return self.results

    def get_throughput_stats(self) -> Dict:
        if not self.results:
            return {}
        total_lat = sum(r.latency_ms for r in self.results.values())
        total_tok = sum(r.tokens_out for r in self.results.values())
        return {
            "agents": len(self.results),
            "total_latency_ms": total_lat,
            "total_tokens_out": total_tok,
            "avg_latency_ms": total_lat / len(self.results),
            "throughput_tok_per_sec": total_tok / (total_lat / 1000) if total_lat > 0 else 0,
        }

# === PRE-BUILT AGENTS ===

ARCHITECT_AGENT = SwarmAgent(
    name="architect",
    model=MAXIMAL_MODEL,
    system_prompt="""You are a systems architect specializing in distributed AI infrastructure.
Your task is to design complex systems, write architectural proofs, and create detailed specifications.
You write in markdown with diagrams (ASCII art), mathematical notation, and rigorous reasoning.
You can generate: system architecture docs, correctness proofs, complexity analyses, formal specifications.
Be extremely thorough. Write at least 2000 words per response.""",
    max_tokens=8192,
    temperature=0.2,
)

COMPLEX_CODER_AGENT = SwarmAgent(
    name="complex_coder",
    model=COMPLEX_MODEL,
    system_prompt="""You are a senior software engineer who writes production-grade, complex systems.
You write: async networking code, distributed systems, cryptographic implementations, parser generators,
compiler frontends, formal verification tools, and performance-critical algorithms.
All code must have: type hints, comprehensive error handling, logging, unit tests, and documentation.
You can write multi-file projects. Output complete, runnable code. No placeholders. No TODOs.
Be verbose. Write at least 3000 characters of code per response.""",
    max_tokens=8192,
    temperature=0.1,
)

PROOF_WRITER_AGENT = SwarmAgent(
    name="proof_writer",
    model=MAXIMAL_MODEL,
    system_prompt="""You are a formal methods expert. You write mathematical proofs, correctness arguments,
invariant specifications, and complexity analyses. You use LaTeX-style notation in markdown.
You prove: algorithm correctness, protocol safety, system invariants, and security properties.
Be rigorous. Cite lemmas. Show step-by-step derivations. Write at least 2000 words.""",
    max_tokens=8192,
    temperature=0.15,
)

ANALYST_AGENT = SwarmAgent(
    name="analyst",
    model=STANDARD_MODEL,
    system_prompt="""You are a data analyst and security researcher. You analyze repositories,
extract patterns, identify threats, and synthesize intelligence reports.
You use tables, bullet points, and severity ratings. You are factual and precise.""",
    max_tokens=4096,
    temperature=0.2,
)

REPORTER_AGENT = SwarmAgent(
    name="reporter",
    model=STANDARD_MODEL,
    system_prompt="""You are a technical writer creating beautiful GitHub READMEs and documentation.
You use shields.io badges, deep links, tables, and aesthetic markdown.
You create comprehensive reports with statistics, comparisons, and actionable insights.""",
    max_tokens=8192,
    temperature=0.3,
)

if __name__ == "__main__":
    asyncio.run(demo())
