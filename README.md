<div align="center">

# Additional Lens Profiles
### Autonomous Intelligence Discovery Platform

[![Swarm](https://img.shields.io/badge/NVIDIA--Swarm-v2.0-76c893?style=for-the-badge&logo=nvidia)](https://docs.api.nvidia.com/)
[![Python](https://img.shields.io/badge/Python-3.12-3776ab?style=for-the-badge&logo=python)](https://python.org)
[![License](https://img.shields.io/badge/license-OSINT-555555?style=for-the-badge)](LICENSE)

**Multi-agent swarm for autonomous discovery, analysis, and synthesis of open-source intelligence**

</div>

---

## What is This?

This repository hosts **lens profiles** — autonomous discovery campaigns executed by multi-agent NVIDIA NIM swarms. Each folder represents a completed campaign with full datasets, agent outputs, and generated tooling.

## How It Works

```
User Task -> Swarm Orchestrator -> Parallel Agents (70B/8B) -> Synthesis -> Push to GitHub
```

**Swarm Architecture:**
- **Architect** (70B) — Designs system topology, APIs, schemas
- **Complex Coder** (70B) — Generates production Python with tests
- **Proof Writer** (70B) — Formal correctness proofs
- **Analyst** (70B) — Threat/intelligence analysis
- **Reporter** (70B) — Synthesizes aesthetic markdown reports

**Infrastructure:**
- Async DAG execution with HTTP/2 persistent connections
- Grammar-constrained JSON decoding
- Llama 3.1 native prompt format
- KV-cache-aware context packing
- Streaming with incremental save
- Tunnel daemon (:80/:443 forwarding)
- MITM proxy with request logging

---

## Campaigns

| Campaign | Repos | Agents | Date | Folder |
|----------|-------|--------|------|--------|
| **Streaming Ecosystem Aug 2026** | 324 | 5 | 2026-08-25 | [`streaming-aug2026/`](streaming-aug2026/) |

---

## Swarm Core Modules

| Module | Purpose |
|--------|---------|
| [`swarm_maximal.py`](swarm_maximal.py) | Maximal orchestrator with 90B/70B/8B tiers |
| [`nvidia_swarm_core.py`](nvidia_swarm_core.py) | Async DAG execution engine |
| [`nvidia_swarm_agent.py`](nvidia_swarm_agent.py) | Llama 3.1 native agent |
| [`nvidia_swarm_transport.py`](nvidia_swarm_transport.py) | HTTP/2 + gRPC transport |
| [`lens_profile.py`](lens_profile.py) | Agent lens profile registry |
| [`swarm_tunnel_daemon.py`](swarm_tunnel_daemon.py) | Port forwarding daemon |
| [`swarm_mitm_proxy.py`](swarm_mitm_proxy.py) | Traffic analysis proxy |
| [`benchmark_references.py`](benchmark_references.py) | Baseline benchmarks |

---

## Usage

```bash
# Run a new discovery campaign
python3 swarm_maximal.py --task "Find Kubernetes security tools" --agents architect,coder,analyst

# Start tunnel daemon
python3 swarm_tunnel_daemon.py start

# Start MITM proxy
python3 swarm_mitm_proxy.py --port 8080
```

---

## Benchmarks

| Source | Metric | Our Delta |
|--------|--------|-----------|
| [llm-serving-benchmark](https://github.com/deepaksatna/llm-serving-benchmark) | 31.70 tok/s (NIM 8B) | +agent orchestration overhead |
| [NIMStats](https://github.com/MauroDruwel/NIMStats) | 163.3 TPS avg | +DAG handoff latency |
| [exemplar-performance](https://github.com/NVIDIA/exemplar-performance) | 405B @ 512 GPUs | +context packing |
| [triton-perf_analyzer](https://github.com/triton-inference-server/perf_analyzer) | 407 infer/sec | +tool-call parsing |

---

## Proof Summary

The async DAG engine satisfies:
1. **Termination** — O(|V| + |E|) steps
2. **Safety** — Circular deps detected by topological sort
3. **Liveness** — Ready agents execute in O(1) rounds
4. **Bounded Concurrency** — 0 <= active <= max_concurrent
5. **Compositionality** — Local properties imply global

See [`streaming-aug2026/MAXIMAL_proof_writer_141751.md`](streaming-aug2026/MAXIMAL_proof_writer_141751.md)

---

<div align="center">

**Last updated**: 2026-08-25 15:29 UTC  
**PAT**: Rotated per campaign (never committed)  
**Model**: meta/llama-3.1-70b-instruct via integrate.api.nvidia.com

[![ARC-AGI](https://img.shields.io/badge/ARC--AGI-experiment-9b5de5?style=flat-square)](https://arcprize.org)
[![NVIDIA](https://img.shields.io/badge/NVIDIA-NIM-76b900?style=flat-square&logo=nvidia)](https://www.nvidia.com/en-us/ai/)

</div>
