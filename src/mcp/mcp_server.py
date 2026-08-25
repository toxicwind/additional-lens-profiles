#!/usr/bin/env python3
"""
MCP Server — SSE Transport with Tool Registry
Model Context Protocol implementation for NVIDIA Swarm.
"""

import json, asyncio, re, requests
from typing import Dict, List, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Tool:
    name: str
    description: str
    parameters: Dict[str, Any]
    executor: Callable

class MCPServer:
    """MCP Server with in-process tool execution (no HTTP server needed for single-process swarm)."""

    def __init__(self, name: str = "nvidia-swarm-mcp"):
        self.name = name
        self.tools: Dict[str, Tool] = {}
        self.sessions: Dict[str, Dict] = {}
        self.message_counter = 0

    def register_tool(self, name: str, description: str, parameters: Dict, executor: Callable):
        """Register a tool with JSON schema parameters."""
        self.tools[name] = Tool(name, description, parameters, executor)

    def list_tools(self) -> List[Dict]:
        """Return tool definitions for LLM system prompt injection."""
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                }
            }
            for t in self.tools.values()
        ]

    def get_system_prompt_block(self) -> str:
        """Generate the tool block for system prompt."""
        lines = [
            "## AVAILABLE TOOLS",
            "You have access to the following tools. When you need to use a tool,",
            "respond with a JSON object in this EXACT format (no markdown, no code blocks):",
            '',
            '{"tool": "TOOL_NAME", "params": {"param1": "value1", "param2": "value2"}}',
            '',
            "Available tools:",
        ]
        for t in self.tools.values():
            lines.append(f"\n### {t.name}")
            lines.append(f"{t.description}")
            props = t.parameters.get("properties", {})
            required = t.parameters.get("required", [])
            for pname, pschema in props.items():
                req = " (REQUIRED)" if pname in required else ""
                desc = pschema.get("description", "")
                ptype = pschema.get("type", "string")
                lines.append(f"  - {pname}: {ptype}{req} — {desc}")
        lines.append("\nIf no tool is needed, respond normally without JSON.")
        return "\n".join(lines)

    def parse_tool_calls(self, text: str) -> List[Dict]:
        """Grammar-constrained JSON extraction. No retry."""
        pattern = r'\{\s*"tool"\s*:\s*"([^"]+)"\s*,\s*"params"\s*:\s*(\{[^}]*\})\s*\}'
        calls = []
        for match in re.finditer(pattern, text, re.DOTALL):
            try:
                calls.append({"tool": match.group(1), "params": json.loads(match.group(2))})
            except json.JSONDecodeError:
                continue
        return calls

    def execute_tool(self, name: str, params: Dict) -> str:
        """Execute a tool and return string result."""
        if name not in self.tools:
            return f"[ERROR] Tool '{name}' not found in registry"
        tool = self.tools[name]
        # Validate required params
        required = tool.parameters.get("required", [])
        missing = [p for p in required if p not in params]
        if missing:
            return f"[ERROR] Missing required parameters: {missing}"
        try:
            result = tool.executor(**params)
            return f"[TOOL RESULT: {name}]\n{str(result)[:2000]}"
        except Exception as e:
            return f"[ERROR executing {name}] {type(e).__name__}: {e}"

    def run_agent_loop(self, agent_name: str, system_prompt: str, task: str, 
                       model: str, api_key: str, api_url: str,
                       max_iterations: int = 5, max_tokens: int = 512) -> Dict:
        """Full agent loop: think → tool call → execute → synthesize."""
        from datetime import datetime

        full_system = system_prompt + "\n\n" + self.get_system_prompt_block()
        messages = [
            {"role": "system", "content": full_system},
            {"role": "user", "content": task},
        ]

        tool_calls_made = []
        tool_results = []
        total_tokens_in = 0
        total_tokens_out = 0

        for iteration in range(max_iterations):
            # Call LLM
            payload = {
                "model": model,
                "messages": messages,
                "temperature": 0.2,
                "max_tokens": max_tokens,
                "stream": False,
            }
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

            try:
                resp = requests.post(f"{api_url}/chat/completions", headers=headers, json=payload, timeout=30)
                resp.raise_for_status()
            except Exception as e:
                return {
                    "agent": agent_name,
                    "error": f"API call failed: {e}",
                    "iterations": iteration,
                    "tool_calls": tool_calls_made,
                    "tool_results": tool_results,
                }

            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            total_tokens_in += usage.get("prompt_tokens", 0)
            total_tokens_out += usage.get("completion_tokens", 0)

            # Parse tool calls
            calls = self.parse_tool_calls(content)

            if not calls:
                # No tool calls — agent is done
                return {
                    "agent": agent_name,
                    "output": content,
                    "iterations": iteration + 1,
                    "tool_calls": tool_calls_made,
                    "tool_results": tool_results,
                    "tokens_in": total_tokens_in,
                    "tokens_out": total_tokens_out,
                    "messages": messages,
                }

            # Execute tools
            for call in calls:
                tool_calls_made.append(call)
                result = self.execute_tool(call["tool"], call["params"])
                tool_results.append(result)

            # Feed results back
            messages.append({"role": "assistant", "content": content})
            feedback = "\n\n".join([f"Tool result {i+1}:\n{r}" for i, r in enumerate(tool_results[-len(calls):])])
            messages.append({"role": "user", "content": f"Here are the tool results:\n{feedback}\n\nSynthesize these into your final answer. If you need more tools, use JSON format. Otherwise respond normally."})

        # Max iterations reached
        return {
            "agent": agent_name,
            "output": "[MAX ITERATIONS REACHED] " + content,
            "iterations": max_iterations,
            "tool_calls": tool_calls_made,
            "tool_results": tool_results,
            "tokens_in": total_tokens_in,
            "tokens_out": total_tokens_out,
            "messages": messages,
        }
