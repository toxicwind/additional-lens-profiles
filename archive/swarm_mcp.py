#!/usr/bin/env python3
"""
NVIDIA Swarm + MCP Tools — Background-detached execution with real tool use
"""

import asyncio, json, os, time, subprocess
from typing import Dict, List, Any, Callable
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime

@dataclass
class MCPTool:
    name: str
    func: Callable
    description: str = ""

@dataclass
class SwarmAgent:
    name: str
    model: str
    system_prompt: str
    tools: List[str] = field(default_factory=list)
    temperature: float = 0.3
    max_tokens: int = 2048

class SwarmMCPEngine:
    """Swarm engine that executes real MCP tools, not just LLM text generation."""

    def __init__(self, nv_key: str, nv_url: str = "https://integrate.api.nvidia.com/v1"):
        self.nv_key = nv_key
        self.nv_url = nv_url
        self.agents: Dict[str, SwarmAgent] = {}
        self.tool_registry: Dict[str, MCPTool] = {}
        self.results: Dict[str, Any] = {}

    def register_tool(self, name: str, func: Callable, description: str = ""):
        self.tool_registry[name] = MCPTool(name, func, description)

    def register_agent(self, agent: SwarmAgent):
        self.agents[agent.name] = agent

    async def execute_tool(self, tool_name: str, params: Dict) -> Any:
        """Execute a real MCP tool."""
        if tool_name not in self.tool_registry:
            return {"error": f"Tool {tool_name} not registered"}
        tool = self.tool_registry[tool_name]
        try:
            result = tool.func(**params)
            return {"tool": tool_name, "result": result, "status": "ok"}
        except Exception as e:
            return {"tool": tool_name, "error": str(e), "status": "error"}

    async def run_agent(self, agent_name: str, task: str, context: Dict = None) -> Dict:
        """Run an agent: LLM plans, then executes tools."""
        agent = self.agents.get(agent_name)
        if not agent:
            return {"error": f"Agent {agent_name} not found"}

        # Step 1: LLM plans the tool calls
        plan = await self._llm_plan(agent, task, context)

        # Step 2: Execute planned tools
        tool_results = []
        for step in plan.get("steps", []):
            tool_name = step.get("tool")
            params = step.get("params", {})
            result = await self.execute_tool(tool_name, params)
            tool_results.append(result)

        # Step 3: LLM synthesizes results
        synthesis = await self._llm_synthesize(agent, task, tool_results, context)

        return {
            "agent": agent_name,
            "plan": plan,
            "tool_results": tool_results,
            "output": synthesis,
        }

    async def _llm_plan(self, agent: SwarmAgent, task: str, context: Dict) -> Dict:
        """Use LLM to plan which tools to call."""
        import aiohttp

        tool_desc = "\n".join([f"- {t.name}: {t.description}" for t in self.tool_registry.values()])
        prompt = f"""You are {agent.name}. Task: {task}

Available tools:
{tool_desc}

Respond with a JSON plan:
{{"steps": [{{"tool": "TOOL_NAME", "params": {{...}}}}, ...]}}

If no tools needed, return {{"steps": []}}."""

        payload = {
            "model": agent.model,
            "messages": [
                {"role": "system", "content": agent.system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
            "max_tokens": 1024,
        }

        headers = {"Authorization": f"Bearer {self.nv_key}", "Content-Type": "application/json"}
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.nv_url}/chat/completions", headers=headers, json=payload) as resp:
                data = await resp.json()
                content = data["choices"][0]["message"]["content"]
                try:
                    return json.loads(content)
                except:
                    return {"steps": [], "raw": content}

    async def _llm_synthesize(self, agent: SwarmAgent, task: str, tool_results: List, context: Dict) -> str:
        """Use LLM to synthesize tool results into final output."""
        import aiohttp

        results_text = "\n".join([json.dumps(r, indent=2) for r in tool_results])
        prompt = f"""Task: {task}

Tool execution results:
{results_text}

Synthesize these results into a concise final answer."""

        payload = {
            "model": agent.model,
            "messages": [
                {"role": "system", "content": agent.system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": agent.temperature,
            "max_tokens": agent.max_tokens,
        }

        headers = {"Authorization": f"Bearer {self.nv_key}", "Content-Type": "application/json"}
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.nv_url}/chat/completions", headers=headers, json=payload) as resp:
                data = await resp.json()
                return data["choices"][0]["message"]["content"]

    async def run_dag(self, dag: List[Dict], context: Dict = None) -> Dict:
        """Execute DAG with real tool calls."""
        context = context or {}
        completed = set()
        pending = {n["agent_name"]: n for n in dag}

        while pending:
            ready = [n for n in pending.values() if all(d in completed for d in n.get("dependencies", []))]
            if not ready:
                raise ValueError("Circular deps")

            tasks = [self.run_agent(node["agent_name"], node.get("task", ""), context) for node in ready]
            batch = await asyncio.gather(*tasks, return_exceptions=True)

            for node, result in zip(ready, batch):
                name = node["agent_name"]
                if isinstance(result, Exception):
                    self.results[name] = {"error": str(result)}
                else:
                    self.results[name] = result
                completed.add(name)
                del pending[name]

        return self.results

def run_detached(task_file: str, output_file: str):
    """Run swarm in background using nohup-style detached process."""
    import subprocess, sys

    cmd = [sys.executable, "-m", "swarm_mcp", "--task", task_file, "--output", output_file]
    proc = subprocess.Popen(
        cmd,
        stdout=open(output_file.replace(".json", ".out"), "w"),
        stderr=open(output_file.replace(".json", ".err"), "w"),
        start_new_session=True,
    )
    return proc.pid
