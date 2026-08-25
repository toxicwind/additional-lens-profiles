#!/usr/bin/env python3
"""
Case Study 01: Groq Compound Mini Deprecation — REAL MCP SWARM
Uses mcp_server.py + mcp_tools.py with live tool execution.
"""

import os, json, time
from pathlib import Path
from datetime import datetime

# Import MCP layer
from mcp_server import MCPServer
from mcp_tools import TOOL_SCHEMAS

# Config
NV_KEY = os.getenv("NVIDIA_API_KEY", "")
NV_URL = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
MODEL = "meta/llama-3.1-70b-instruct"

def ts():
    return datetime.now().strftime("%H:%M:%S.%f")[:12]

def run_case_study_01():
    """Execute Case Study 01 with real MCP tool loop."""

    print(f"[{ts()}] === CASE STUDY 01: GROQ COMPOUND MINI DEPRECATION ===")
    print(f"[{ts()}] Model: {MODEL}")
    print(f"[{ts()}] Endpoint: {NV_URL}")
    print(f"[{ts()}] MCP Tools: {list(TOOL_SCHEMAS.keys())}\n")

    # Build MCP server
    mcp = MCPServer(name="groq-osint-mcp")
    for name, schema in TOOL_SCHEMAS.items():
        mcp.register_tool(name, schema["description"], schema["parameters"], schema["executor"])

    # === AGENT 1: RESEARCHER ===
    print(f"[{ts()}] --- AGENT 1: RESEARCHER ---")
    researcher_prompt = (
        "You are an OSINT research agent. Your job is to investigate the Groq Compound Mini deprecation. "
        "Use web_open_url to check https://console.groq.com/docs/deprecations and https://console.groq.com/docs/models. "
        "Use github_search to find any public repos or issues mentioning 'groq compound mini'. "
        "Use web_open_url on https://console.groq.com/docs/changelog to find when Compound Mini was added. "
        "Be precise. If information is not found, say so explicitly."
    )

    researcher_task = (
        "Investigate Groq Compound Mini. What is it (model, chip, or service)? "
        "Is it officially deprecated? When? What replaces it? "
        "Use the available tools to gather evidence."
    )

    t0 = time.perf_counter()
    res1 = mcp.run_agent_loop(
        agent_name="researcher",
        system_prompt=researcher_prompt,
        task=researcher_task,
        model=MODEL,
        api_key=NV_KEY,
        api_url=NV_URL,
        max_iterations=5,
        max_tokens=512,
    )
    t1 = time.perf_counter()

    print(f"[{ts()}] Researcher done in {(t1-t0)*1000:.0f}ms")
    print(f"[{ts()}] Iterations: {res1.get('iterations', 0)}")
    print(f"[{ts()}] Tool calls: {len(res1.get('tool_calls', []))}")
    for tc in res1.get("tool_calls", []):
        print(f"  → {tc['tool']}({tc['params']})")
    print(f"[{ts()}] Output:
{res1.get('output', 'NO OUTPUT')[:800]}\n")

    # === AGENT 2: ANALYST ===
    print(f"[{ts()}] --- AGENT 2: ANALYST ---")
    analyst_prompt = (
        "You are a business analyst. You receive research findings and synthesize strategic conclusions. "
        "You have access to web_search for competitive analysis. "
        "Do not invent facts. Use ONLY what the researcher provided."
    )

    context = f"RESEARCHER FINDINGS:\n{res1.get('output', '')}\n\nTOOL RESULTS:\n"
    for i, tr in enumerate(res1.get("tool_results", [])):
        context += f"\n--- Result {i+1} ---\n{tr[:500]}\n"

    analyst_task = (
        "Based on the researcher findings, what is the strategic business implication "
        "of Groq potentially deprecating Compound Mini? Consider: customer impact, "
        "competitive landscape, migration costs, and Groq's market position."
    )

    t2 = time.perf_counter()
    res2 = mcp.run_agent_loop(
        agent_name="analyst",
        system_prompt=analyst_prompt,
        task=analyst_task,
        model=MODEL,
        api_key=NV_KEY,
        api_url=NV_URL,
        max_iterations=3,
        max_tokens=512,
    )
    t3 = time.perf_counter()

    print(f"[{ts()}] Analyst done in {(t3-t2)*1000:.0f}ms")
    print(f"[{ts()}] Output:
{res2.get('output', 'NO OUTPUT')[:800]}\n")

    # === AGENT 3: CODER ===
    print(f"[{ts()}] --- AGENT 3: CODER ---")
    coder_prompt = (
        "You are a Python migration engineer. You write clean, working scripts. "
        "You have access to github_search to find example implementations. "
        "Write scripts with no external dependencies. Include comments."
    )

    coder_context = (
        f"ANALYST CONCLUSION:\n{res2.get('output', '')}\n\n"
        f"RESEARCHER FINDINGS:\n{res1.get('output', '')[:500]}"
    )

    coder_task = (
        "Write a Python script that checks if a Groq API response is using Compound Mini "
        "and prints a migration warning with the September 21, 2026 deadline. "
        "The script should be defensive and handle missing fields."
    )

    t4 = time.perf_counter()
    res3 = mcp.run_agent_loop(
        agent_name="coder",
        system_prompt=coder_prompt,
        task=coder_task,
        model=MODEL,
        api_key=NV_KEY,
        api_url=NV_URL,
        max_iterations=2,
        max_tokens=512,
    )
    t5 = time.perf_counter()

    print(f"[{ts()}] Coder done in {(t5-t4)*1000:.0f}ms")
    print(f"[{ts()}] Output:
{res3.get('output', 'NO OUTPUT')[:1200]}\n")

    # === SUMMARY ===
    total_time = (t5 - t0) * 1000
    total_tokens = (
        res1.get("tokens_out", 0) + res2.get("tokens_out", 0) + res3.get("tokens_out", 0)
    )

    print(f"[{ts()}] === CASE STUDY 01 COMPLETE ===")
    print(f"[{ts()}] Total time: {total_time:.0f}ms")
    print(f"[{ts()}] Total tokens out: {total_tokens}")
    print(f"[{ts()}] Throughput: {total_tokens / (total_time/1000):.1f} tok/s")
    print(f"[{ts()}] Total tool calls: {len(res1.get('tool_calls',[])) + len(res2.get('tool_calls',[])) + len(res3.get('tool_calls',[]))}")

    # Save results
    result = {
        "case_study": "01",
        "title": "Groq Compound Mini Deprecation OSINT",
        "timestamp": datetime.now().isoformat(),
        "model": MODEL,
        "endpoint": NV_URL,
        "agents": {
            "researcher": {
                "output": res1.get("output", ""),
                "iterations": res1.get("iterations", 0),
                "tool_calls": res1.get("tool_calls", []),
                "tool_results": res1.get("tool_results", []),
                "tokens_in": res1.get("tokens_in", 0),
                "tokens_out": res1.get("tokens_out", 0),
            },
            "analyst": {
                "output": res2.get("output", ""),
                "iterations": res2.get("iterations", 0),
                "tool_calls": res2.get("tool_calls", []),
                "tokens_in": res2.get("tokens_in", 0),
                "tokens_out": res2.get("tokens_out", 0),
            },
            "coder": {
                "output": res3.get("output", ""),
                "iterations": res3.get("iterations", 0),
                "tool_calls": res3.get("tool_calls", []),
                "tokens_in": res3.get("tokens_in", 0),
                "tokens_out": res3.get("tokens_out", 0),
            },
        },
        "metrics": {
            "total_time_ms": total_time,
            "total_tokens_out": total_tokens,
            "throughput_tok_per_sec": total_tokens / (total_time/1000) if total_time > 0 else 0,
        },
    }

    out_path = Path("case_study_01_results.json")
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"[{ts()}] Results saved: {out_path}")

    return result

if __name__ == "__main__":
    run_case_study_01()
