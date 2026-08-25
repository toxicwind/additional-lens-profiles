# Credits & Prior Art

This project builds on patterns, tools, and research from the following sources.

## Skill Patterns

| Source | What We Borrowed | License |
|--------|-----------------|---------|
| [am-will/swarms](https://github.com/am-will/swarms) | Wave-based execution, swarm-planner + parallel-task skills, dependency-aware planning | MIT |
| [ruvnet/agentic-flow](https://github.com/ruvnet/agentic-flow) | Swarm orchestration topologies (mesh, hierarchical, adaptive), agent spawning | MIT |
| [shinpr/sub-agents-skills](https://github.com/shinpr/sub-agents-skills) | Cross-LLM agent routing, `.agents/` folder pattern, frontmatter-based agent definitions | MIT |
| [qodex-ai/ai-agent-skills](https://github.com/qodex-ai/ai-agent-skills) | Multi-agent orchestration metrics, self-organizing teams, adaptive workflows | MIT |
| [vectara/agent-skills](https://github.com/vectara/agent-skills) | Deterministic step-gated agents, state machine workflows, structured output gating | MIT |
| [Dimillian/Skills/review-swarm](https://github.com/Dimillian/Skills/tree/main/review-swarm) | Parallel read-only multi-agent review pattern, diff-based regression detection | MIT |
| [desplega-ai/agent-swarm](https://github.com/desplega-ai/agent-swarm) | Agentic operating system patterns, lead/worker swarm topology | MIT |

## Research Papers

| Paper | Authors | What We Used |
|-------|---------|-------------|
| [Autogrammar: Learning Context-Free Grammars for Grammar-Constrained Decoding](https://arxiv.org/abs/2608.05493) | Amazon Science, 2026 | Grammar-constrained decoding approach, 3.8x speedup via LTL constraints |
| [Generative Agents](https://arxiv.org/abs/2304.03442) | Park et al., Stanford | Agent memory and simulation patterns |
| [Self-Organizing Multi-Agent Systems](https://arxiv.org/search/?query=multi-agent+orchestration) | Various | Adaptive workflow and cross-agent learning patterns |

## Benchmark Baselines

| Source | What We Measured Against |
|--------|------------------------|
| [deepaksatna/llm-serving-benchmark](https://github.com/deepaksatna/llm-serving-benchmark) | NIM vs vLLM/SGLang/TGI throughput (31.70 tok/s baseline) |
| [MauroDruwel/NIMStats](https://github.com/MauroDruwel/NIMStats) | Live NIM endpoint uptime and TPS (163.3 avg) |
| [NVIDIA/exemplar-performance](https://github.com/NVIDIA/exemplar-performance) | 405B scale targets (256-512 GPU clusters) |
| [triton-inference-server/perf_analyzer](https://github.com/triton-inference-server/perf_analyzer) | gRPC async latency p99 (4172 usec) |

## Frameworks Referenced

- [OpenAI Swarm](https://github.com/openai/swarm) — Baseline synchronous loop we replaced
- [CrewAI](https://crewai.com/) — Role-based agent teams
- [AutoGen](https://microsoft.github.io/autogen/) — Conversational agent orchestration
- [LangGraph](https://langchain-ai.github.io/langgraph/) — Graph-based agent workflows

## Model Providers

- [NVIDIA NIM](https://docs.api.nvidia.com/) — Primary inference backend
- [Groq](https://groq.com/) — Case study subject (Compound Mini deprecation)
- [Together AI](https://www.together.ai/) — Alternative inference provider

---

All borrowed patterns are credited above. Original contributions in this repo:
- Async DAG execution engine with semaphore-based concurrency control
- Grammar-constrained JSON decoding layer (regex-based, no retry loops)
- Llama 3.1 native prompt format conversion
- Lens profile system with NVIDIA metrics integration
- KV-cache-aware context window packing strategies
- CDP tunnel reverse proxy for real browser OSINT

MIT License — See [LICENSE](LICENSE)
