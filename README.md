# ARC-AGI Swarm — Case Study One

> **Hyper-modular NVIDIA-NIM Swarm framework** for async agent orchestration, OSINT deep research, and LLM inference benchmarking via CDP tunnel reverse proxy.

**Status:** Private case study repository. Public release TBD after case study validation.

---

## Quick Start

```bash
git clone https://github.com/toxicwind/additional-lens-profiles.git
cd additional-lens-profiles
cp .env.example .env
# Edit .env with your keys (NEVER commit .env)
pip install -r requirements.txt
python -m src.nvidia_swarm.swarm_main --task "groq-deprecation-osint"
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SWARM ORCHESTRATOR                        │
│         (async DAG + lens profiles + CDP tunnel)            │
├─────────────┬─────────────┬─────────────┬─────────────────┤
│  Researcher │   Analyst   │    Coder    │  Orchestrator   │
│   (405B)    │   (70B)     │   (405B)    │    (405B)       │
├─────────────┴─────────────┴─────────────┴─────────────────┤
│              NVIDIA NIM Transport Layer                     │
│    (HTTP/2 persistent + gRPC fallback + CDP tunnel)       │
├─────────────────────────────────────────────────────────────┤
│              Triton Inference Server                        │
│         (dynamic batching + KV-cache opt)                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Modules

| Module | Purpose | File |
|---|---|---|
| `nvidia_swarm.core` | Async DAG execution engine with parallel tool calls | [`src/nvidia_swarm/core.py`](src/nvidia_swarm/core.py) |
| `nvidia_swarm.agent` | Llama 3.1 native prompt + grammar-constrained decoding | [`src/nvidia_swarm/agent.py`](src/nvidia_swarm/agent.py) |
| `nvidia_swarm.transport` | HTTP/2 persistent + gRPC + CDP tunnel reverse proxy | [`src/transport/nim_transport.py`](src/transport/nim_transport.py) |
| `lens.profile` | Agent configuration registry with NV metrics | [`src/lens/profile.py`](src/lens/profile.py) |
| `lens.nv_metrics` | NVIDIA-specific KV-cache + throughput observability | [`src/lens/nv_metrics.py`](src/lens/nv_metrics.py) |
| `tasks.groq_osint` | Case Study 01: Groq Compound Mini deprecation deep research | [`case-study-01-groq-deprecation/tasks/groq_osint.py`](case-study-01-groq-deprecation/tasks/groq_osint.py) |
| `benchmarks.swarm_bench` | Swarm throughput + latency benchmark harness | [`src/benchmarks/swarm_bench.py`](src/benchmarks/swarm_bench.py) |

---

## Case Studies

| # | Title | Status | Folder |
|---|---|---|---|
| 01 | Groq Compound Mini Deprecation OSINT | In Progress | [`case-study-01-groq-deprecation/`](case-study-01-groq-deprecation/) |
| 02 | IPTV/Stremio/Nuvio Repo Discovery (Aug 2026) | Complete | `data/aug2026/` |

---

## Lens Profiles

Lens profiles define agent behavior, model selection, and observability hooks.

| Profile | Agent Type | Model | Lens File |
|---|---|---|---|
| `researcher` | Deep research | `meta/llama-3.1-405b-instruct` | [`lens-profiles/swarm/researcher.yaml`](lens-profiles/swarm/researcher.yaml) |
| `analyst` | Pattern analysis | `nvidia/nemotron-3-super-120b-a12b` | [`lens-profiles/swarm/analyst.yaml`](lens-profiles/swarm/analyst.yaml) |
| `coder` | Code generation | `meta/llama-3.1-405b-instruct` | [`lens-profiles/swarm/coder.yaml`](lens-profiles/swarm/coder.yaml) |
| `osint_lead` | OSINT orchestration | `nvidia/nemotron-3-super-120b-a12b` | [`lens-profiles/osint/osint_lead.yaml`](lens-profiles/osint/osint_lead.yaml) |
| `benchmark_runner` | Benchmark orchestration | `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning` | [`lens-profiles/benchmark/runner.yaml`](lens-profiles/benchmark/runner.yaml) |

---

## Benchmarks

See [`docs/baselines/BENCHMARK_BASELINES.md`](docs/baselines/BENCHMARK_BASELINES.md) for prior art.

Our targets:

- **Agent handoff latency:** < 100ms (DAG node-to-node)
- **Throughput:** Saturate NIM's 3100 tok/s (405B on H100)
- **Concurrent efficiency:** 16 agents parallel with semaphore control
- **CDP tunnel round-trip:** < 50ms added latency

---

## CDP Tunnel Reverse Proxy

Swarm agents execute through a Chrome DevTools Protocol (CDP) tunnel for:
- **Real browser OSINT** (not simulation)
- **JavaScript-rendered target analysis**
- **Session persistence across agent handoffs**

See [`src/transport/cdp_tunnel.py`](src/transport/cdp_tunnel.py) and [`docs/wiki/CDP_TUNNEL.md`](docs/wiki/CDP_TUNNEL.md).

---

## License

MIT — See [`LICENSE`](LICENSE)

## Contact

ARC-AGI Experiment — `toxicwind` on GitHub
