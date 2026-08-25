# Merge Document: Live Repo vs Case Study One Restructure

## What Was Preserved from Live Repo

| Live File | Live Content | Preserved In |
|---|---|---|
| `src/nvidia_swarm/swarm_main.py` | `run_swarm_task()`, `main()`, agent registration from lens | `src/nvidia_swarm/swarm_main.py` — exact signature preserved |
| `src/nvidia_swarm/core.py` | `NvidiaSwarmDAG`, `DAGNode`, `get_throughput_stats()` | `src/nvidia_swarm/core.py` — `DAGNode` dataclass + `run_dag()` logic preserved |
| `src/nvidia_swarm/agent.py` | `NvidiaAgent`, tool schemas, prompt templates | `src/nvidia_swarm/agent.py` — `NvidiaAgent` class + `_tool_schemas_openai()` preserved |
| `src/nvidia_swarm/transport.py` | `NvidiaSwarmTransport` | `src/transport/nim_transport.py` — renamed for clarity |
| `src/nvidia_swarm/lens.py` | `LENS_REGISTRY`, `get_lens()`, `LensProfile` | `src/lens/profile.py` — exact API preserved |
| `lens-profiles/*.yaml` | Researcher, analyst, coder profiles | `lens-profiles/swarm/*.yaml` — content preserved, structure enhanced |
| `case-study-01-groq-deprecation/` | Folder structure | `case-study-01-groq-deprecation/` — expanded with tasks, output, README |

## What Was Added / Changed

### Architecture Changes

| Change | Live | New | Reason |
|---|---|---|---|
| **Async DAG** | Serial execution | Parallel `asyncio.gather()` + semaphore | Saturation of NVIDIA NIM throughput |
| **Grammar Constraints** | Retry-based JSON parsing | Regex/BNF `GrammarConstraint` class | Deterministic tool calls, no retries |
| **Batch Inference** | Single requests | `submit_batch()` with chunking | Throughput gains on H100 |
| **CDP Tunnel** | None | `CDPTunnel` class with real browser | Real OSINT, not simulation |
| **KV-Cache Tracking** | None | `SwarmState.pack()` with sliding window | NVIDIA KV-cache efficiency |
| **Handoff Protocol** | Implicit | Explicit `HANDOFF: agent_name` + grammar validation | Reliable agent transfers |

### New Modules

| Module | File | Purpose |
|---|---|---|
| `src/transport/cdp_tunnel.py` | NEW | Chrome DevTools Protocol reverse proxy |
| `src/lens/nv_metrics.py` | NEW | Prometheus metrics for NVIDIA NIM |
| `src/benchmarks/swarm_bench.py` | NEW | Throughput + latency benchmark harness |
| `case-study-01-groq-deprecation/tasks/groq_osint.py` | NEW | Full OSINT task with 5-agent DAG |
| `lens-profiles/osint/` | NEW | OSINT-specific agent profiles |
| `lens-profiles/benchmark/` | NEW | Benchmark runner profiles |

### File Moves (for hyper-modularity)

| Live Path | New Path | Reason |
|---|---|---|
| `src/nvidia_swarm/transport.py` | `src/transport/nim_transport.py` | Transport is cross-cutting, not swarm-specific |
| `src/nvidia_swarm/lens.py` | `src/lens/profile.py` | Lens is its own domain |
| `lens-profiles/researcher.yaml` | `lens-profiles/swarm/researcher.yaml` | Namespacing by use case |

### Secret Hygiene (CRITICAL)

| Live Issue | Fix |
|---|---|
| `models.json` hardcoded `nvapi-...` key | `.env.example` + `os.getenv()` |
| No `.gitignore` for secrets | Added comprehensive `.gitignore` |
| No `.env.example` | Created with all required keys |
| GitHub PAT in clipboard dumps | **NEVER** in repo — `.env` only |

## Staging Diff

To see exact diffs:

```bash
# Compare live repo to restructure
cd ~/additional-lens-profiles
git diff --stat main..case-study-one-restructure

# Or file-by-file
git diff main..case-study-one-restructure -- src/nvidia_swarm/core.py
```

## Branch Strategy

- `main` — Live repo (preserved)
- `case-study-one-restructure` — This restructure (merged live + new)
- `case-study/01-groq-deprecation` — CI runs case study on push

## Integration Checklist

- [ ] Copy `.env.example` to `.env` and fill keys
- [ ] Verify `src/nvidia_swarm/swarm_main.py` runs: `python -m src.nvidia_swarm.swarm_main --task "test"`
- [ ] Run benchmarks: `bash scripts/benchmark.sh`
- [ ] Run case study: `python -m case-study-01-groq-deprecation.tasks.groq_osint`
- [ ] Check Prometheus metrics: `curl http://127.0.0.1:25105/metrics`
- [ ] Verify CDP tunnel: set `CDP_TUNNEL_ENDPOINT` and run agent with `cdp_navigate`
