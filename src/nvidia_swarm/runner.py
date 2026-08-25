#!/usr/bin/env python3
"""
NVIDIA Swarm Runner — Wave-based execution with context handoff
Inspired by: am-will/swarms (parallel-task skill)
Credit: https://github.com/am-will/swarms
"""

import asyncio, json, time
from typing import Dict, List, Any
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from nvidia_swarm_core import NvidiaSwarmDAG, DAGNode
from nvidia_swarm_agent import NvidiaAgent
from nvidia_swarm_planner import SwarmPlanner, PlanTask
from lens_profile import LENS_REGISTRY, get_lens

@dataclass
class WaveResult:
    wave_number: int
    task_results: Dict[str, Any]
    latency_ms: float
    tokens_total: int

class SwarmRunner:
    """Executes a swarm plan wave by wave, with parallel execution within waves.

    Borrowed patterns:
    - Wave execution from am-will/swarms
    - Context handoff between agents
    - Work verification after each wave
    """

    def __init__(self, max_concurrent: int = 16, timeout: float = 30.0):
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.planner = SwarmPlanner(LENS_REGISTRY)
        self.results: Dict[str, Any] = {}
        self.wave_results: List[WaveResult] = []

    async def run(self, task_description: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a complete swarm task: plan -> execute waves -> verify -> return."""
        context = context or {}

        # Phase 1: Plan
        print(f"[PLANNER] Analyzing task: {task_description[:60]}...")
        plan = self.planner.plan(task_description, context)
        print(f"[PLANNER] Generated {len(plan.tasks)} tasks in {len(plan.waves)} waves")
        for i, wave in enumerate(plan.waves):
            print(f"  Wave {i+1}: {wave}")

        # Phase 2: Execute waves
        async with NvidiaSwarmDAG(max_concurrent=self.max_concurrent, timeout=self.timeout) as dag:
            # Register agents from lens profiles
            for task in plan.tasks:
                lens = get_lens(task.agent_type)
                if lens.name not in dag.agents:
                    agent = NvidiaAgent(**lens.to_agent_config())
                    dag.register_agent(lens.name, agent)

            for wave_idx, wave_tasks in enumerate(plan.waves):
                print(f"\n[WAVE {wave_idx+1}/{len(plan.waves)}] Executing {len(wave_tasks)} tasks in parallel...")
                t0 = time.perf_counter()

                # Build DAG nodes for this wave
                nodes = []
                for task_id in wave_tasks:
                    task = next(t for t in plan.tasks if t.id == task_id)
                    # Merge inputs from completed dependencies
                    inputs = {"task": task.description, "plan_id": plan.task_id}
                    for dep in task.dependencies:
                        if dep in self.results:
                            inputs[f"{dep}_output"] = self.results[dep].get("output", "")

                    nodes.append(DAGNode(
                        agent_name=get_lens(task.agent_type).name,
                        dependencies=[],  # Dependencies already satisfied by wave ordering
                        inputs=inputs,
                        output_key=task_id,
                    ))

                # Execute wave
                wave_results = await dag.run_dag(nodes, context)

                # Store results
                for task_id, result in wave_results.items():
                    self.results[task_id] = {
                        "output": result.output,
                        "tool_calls": result.tool_calls,
                        "latency_ms": result.latency_ms,
                        "tokens_in": result.tokens_in,
                        "tokens_out": result.tokens_out,
                    }

                latency = (time.perf_counter() - t0) * 1000
                tokens = sum(r.tokens_out for r in wave_results.values())
                self.wave_results.append(WaveResult(
                    wave_number=wave_idx + 1,
                    task_results={k: v["output"][:200] for k, v in self.results.items() if k in wave_tasks},
                    latency_ms=latency,
                    tokens_total=tokens,
                ))

                print(f"[WAVE {wave_idx+1}] Complete: {latency:.1f}ms, {tokens} tokens")

                # Phase 3: Verify wave
                if not self._verify_wave(wave_tasks, plan.tasks):
                    print(f"[WARN] Wave {wave_idx+1} verification failed — continuing")

        # Phase 4: Final summary
        total_latency = sum(w.latency_ms for w in self.wave_results)
        total_tokens = sum(w.tokens_total for w in self.wave_results)

        return {
            "plan": plan.to_json(),
            "results": self.results,
            "waves": [{"wave": w.wave_number, "latency_ms": w.latency_ms, "tokens": w.tokens_total} 
                      for w in self.wave_results],
            "summary": {
                "total_tasks": len(plan.tasks),
                "total_waves": len(plan.waves),
                "total_latency_ms": total_latency,
                "total_tokens": total_tokens,
                "avg_wave_latency_ms": total_latency / len(self.wave_results) if self.wave_results else 0,
            },
        }

    def _verify_wave(self, wave_task_ids: List[str], all_tasks: List[PlanTask]) -> bool:
        """Verify that wave tasks produced valid outputs."""
        for tid in wave_task_ids:
            task = next(t for t in all_tasks if t.id == tid)
            result = self.results.get(tid, {})
            output = result.get("output", "")

            # Check validation criteria
            for criterion in task.validation_criteria:
                if criterion == "At least 3 sources found" and len(output) < 100:
                    return False
                if criterion == "Report is structured" and "#" not in output:
                    return False

        return True
