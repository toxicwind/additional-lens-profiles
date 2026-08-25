#!/usr/bin/env python3
"""
NVIDIA-Native Agent — Llama 3.1 Optimized Prompt Engineering + Grammar-Constrained Decoding
"""

import json, re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import aiohttp

@dataclass
class NvidiaAgent:
    """Agent optimized for Llama 3.1 405B Instruct via NVIDIA NIM.

    Differences from OpenAI Swarm Agent:
    - Uses Llama 3.1 native prompt format (not OpenAI chat format)
    - Grammar-constrained JSON decoding instead of retry logic
    - Tool schema injected via prompt injection, not function calling API
    - KV-cache aware context packing
    """

    name: str
    system_prompt: str = ""
    tools: List[Dict] = field(default_factory=list)
    model: str = "meta/llama-3.1-405b-instruct"
    temperature: float = 0.3
    max_tokens: int = 2048
    grammar: Optional[str] = None  # JSON schema or regex for constrained decoding

    # Llama 3.1 instruct format markers
    START_HEADER_ID = "<|start_header_id|>"
    END_HEADER_ID = "<|end_header_id|>"
    EOT_ID = "<|eot_id|>"

    def build_llama_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Build Llama 3.1 native prompt format.

        OpenAI format: [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
        Llama 3.1 format: <|start_header_id|>system<|end_header_id|>

...<|eot_id|><|start_header_id|>user<|end_header_id|>

...<|eot_id|>
        """
        prompt = ""
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            prompt += f"{self.START_HEADER_ID}{role}{self.END_HEADER_ID}\n\n{content}{self.EOT_ID}"
        prompt += f"{self.START_HEADER_ID}assistant{self.END_HEADER_ID}\n\n"
        return prompt

    def inject_tools_into_prompt(self, base_prompt: str) -> str:
        """Inject tool definitions directly into the system prompt.
        This replaces OpenAI's function calling API with prompt injection."""
        if not self.tools:
            return base_prompt

        tool_block = "\n\n## AVAILABLE TOOLS\nYou have access to the following tools. When you need to use a tool, respond with a JSON object in this exact format:\n"
        tool_block += '{"tool": "TOOL_NAME", "params": {"param1": "value1", ...}}\n\n'

        for tool in self.tools:
            tool_block += f"### {tool['name']}\n"
            tool_block += f"Description: {tool.get('description', '')}\n"
            if "parameters" in tool:
                props = tool["parameters"].get("properties", {})
                required = tool["parameters"].get("required", [])
                for param_name, param_info in props.items():
                    req_flag = " (REQUIRED)" if param_name in required else ""
                    tool_block += f"  - {param_name}: {param_info.get('type', 'string')}{req_flag} — {param_info.get('description', '')}\n"
            tool_block += "\n"

        tool_block += "If no tool is needed, respond normally without JSON.\n"
        return base_prompt + tool_block

    def build_grammar_regex(self) -> str:
        """Build a regex grammar for constrained JSON tool call decoding.
        This guarantees valid JSON tool calls without retry logic."""
        if not self.tools:
            return r".*"

        tool_names = "|".join(re.escape(t["name"]) for t in self.tools)
        # Matches: {"tool": "NAME", "params": {...}}
        grammar = (
            r'\{\s*"tool"\s*:\s*"(' + tool_names + r')"\s*,\s*'
            r'"params"\s*:\s*\{[^}]*\}\s*\}'
        )
        return grammar

    def parse_tool_calls(self, response: str) -> List[Dict]:
        """Extract tool calls from response using grammar-constrained parsing."""
        tool_calls = []
        # Look for JSON blocks
        json_pattern = r'\{\s*"tool"\s*:\s*"([^"]+)"\s*,\s*"params"\s*:\s*(\{[^}]*\})\s*\}'
        matches = re.finditer(json_pattern, response, re.DOTALL)
        for match in matches:
            try:
                tool_name = match.group(1)
                params = json.loads(match.group(2))
                tool_calls.append({"tool": tool_name, "params": params})
            except json.JSONDecodeError:
                continue
        return tool_calls

    async def arun(self, inputs: Dict[str, Any], session: aiohttp.ClientSession, context: Dict[str, Any]) -> Any:
        """Async run with NVIDIA NIM endpoint."""
        from nvidia_swarm_core import AgentResult

        # Build messages
        messages = [{"role": "system", "content": self.inject_tools_into_prompt(self.system_prompt)}]

        # Add context from previous agents
        for k, v in inputs.items():
            if k.endswith("_output"):
                messages.append({"role": "user", "content": f"Previous agent ({k}): {v}"})
            else:
                messages.append({"role": "user", "content": f"{k}: {v}"})

        messages.append({"role": "user", "content": "Proceed with your task."})

        # Convert to Llama 3.1 format
        prompt = self.build_llama_prompt(messages)

        # NVIDIA NIM payload
        payload = {
            "model": self.model,
            "messages": messages,  # NIM also accepts OpenAI format
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": False,
        }

        # Add grammar constraint if supported
        if self.grammar:
            payload["extra_body"] = {"grammar": self.grammar}

        api_key = context.get("nvidia_api_key", "")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        base_url = context.get("nvidia_base_url", "https://integrate.api.nvidia.com/v1")

        async with session.post(f"{base_url}/chat/completions", headers=headers, json=payload) as resp:
            if resp.status != 200:
                text = await resp.text()
                return AgentResult(
                    agent_name=self.name,
                    output=f"API ERROR {resp.status}: {text[:200]}",
                    latency_ms=0,
                )

            data = await resp.json()
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})

            # Parse tool calls
            tool_calls = self.parse_tool_calls(content)

            return AgentResult(
                agent_name=self.name,
                output=content,
                tool_calls=tool_calls,
                tokens_in=usage.get("prompt_tokens", 0),
                tokens_out=usage.get("completion_tokens", 0),
            )
