# ARC-AGI Swarm — Additional Lens Profiles

> **Hyper-modular NVIDIA-NIM Swarm framework** for async agent orchestration, IPTV/Stremio discovery, and LLM inference benchmarking.
> 
> **Status:** Private case study repository. Public release TBD.

---

## Quick Start

```bash
git clone https://github.com/toxicwind/additional-lens-profiles.git
cd additional-lens-profiles
pip install -r requirements.txt
python src/nvidia_swarm/swarm_main.py
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SWARM ORCHESTRATOR                        │
│              (async DAG + lens profiles)                     │
├─────────────┬─────────────┬─────────────┬─────────────────┤
│  Researcher │   Analyst   │    Coder    │  Orchestrator   │
│   (405B)    │   (70B)     │   (405B)    │    (405B)       │
├─────────────┴─────────────┴─────────────┴─────────────────┤
│              NVIDIA NIM Transport Layer                     │
│         (HTTP/2 persistent + gRPC fallback)               │
├─────────────────────────────────────────────────────────────┤
│              Triton Inference Server                        │
│         (dynamic batching + KV-cache opt)                 │
└─────────────────────────────────────────────────────────────┘
```

## Case Studies

| # | Title | Status | Link |
|---|-------|--------|------|
| 01 | Groq Compound Mini Deprecation OSINT | In Progress | [`case-study-01-groq-deprecation/`](case-study-01-groq-deprecation/) |
| 02 | IPTV/Stremio/Nuvio Repo Discovery (Aug 2026) | Complete | [`data/aug2026/`](data/aug2026/) |

## Modules

| Module | Purpose | File |
|--------|---------|------|
| `nvidia_swarm_core` | Async DAG execution engine | [`src/nvidia_swarm/core.py`](src/nvidia_swarm/core.py) |
| `nvidia_swarm_agent` | Llama 3.1 native prompt + grammar-constrained decoding | [`src/nvidia_swarm/agent.py`](src/nvidia_swarm/agent.py) |
| `nvidia_swarm_transport` | HTTP/2 persistent connections + Triton gRPC | [`src/nvidia_swarm/transport.py`](src/nvidia_swarm/transport.py) |
| `lens_profile` | Agent configuration registry (researcher/coder/analyst/orchestrator) | [`src/nvidia_swarm/lens.py`](src/nvidia_swarm/lens.py) |
| `iptv_discovery` | GitHub API parallel search + deep M3U/manifest extraction | [`src/iptv_discovery/discovery.py`](src/iptv_discovery/discovery.py) |
| `benchmark_references` | Prior art baselines (4 sources) | [`src/benchmarks/references.py`](src/benchmarks/references.py) |

## Benchmarks

See [`docs/BENCHMARK_BASELINES.md`](docs/BENCHMARK_BASELINES.md) for prior art.

Our targets:
- **Agent handoff latency:** < 100ms (DAG node-to-node)
- **Throughput:** Saturate NIM's 3100 tok/s (405B on H100)
- **Concurrent efficiency:** 16 agents parallel with semaphore control

## Data

| Dataset | Records | Size | Link |
|---------|---------|------|------|
| IPTV/Stremio Aug 2026 repos | 324 | 216 KB | [`data/aug2026/iptv_stremio_repos.jsonl`](data/aug2026/iptv_stremio_repos.jsonl) |
| Nuvio-specific repos | 33 | 25 KB | [`data/aug2026/nuvio_repos.json`](data/aug2026/nuvio_repos.json) |
| Live manifest hits | 4 | 20 KB | [`data/aug2026/deep_scan.json`](data/aug2026/deep_scan.json) |
| Benchmark references | 4 sources | 7 KB | [`data/benchmarks/references.json`](data/benchmarks/references.json) |

## Live Manifests Discovered

| Repo | Manifest | Type |
|------|----------|------|
| [yowmamasita/usa-tv-next](https://github.com/yowmamasita/usa-tv-next) | [manifest.json](https://raw.githubusercontent.com/yowmamasita/usa-tv-next/main/manifest.json) | TV |
| [esp4ce/stremio-letterboxd-addon](https://github.com/esp4ce/stremio-letterboxd-addon) | [manifest.json](https://raw.githubusercontent.com/esp4ce/stremio-letterboxd-addon/main/manifest.json) | Movie |
| [Gowaru/gowaru-nuvio-providers](https://github.com/Gowaru/gowaru-nuvio-providers) | [manifest.json](https://raw.githubusercontent.com/Gowaru/gowaru-nuvio-providers/main/manifest.json) | Repo |
| [victorgveloso/animes-season-addon](https://github.com/victorgveloso/animes-season-addon) | [manifest.json](https://raw.githubusercontent.com/victorgveloso/animes-season-addon/main/manifest.json) | Movie/Series |

## Live M3U Playlists

| Repo | Playlist | Size |
|------|----------|------|
| [Ace550-Ramon/IPTV](https://github.com/Ace550-Ramon/IPTV) | [tv.m3u](https://raw.githubusercontent.com/Ace550-Ramon/IPTV/main/tv.m3u) | 1.3 MB |
| [ikku47/iptv-ld](https://github.com/ikku47/iptv-ld) | [index.m3u](https://raw.githubusercontent.com/ikku47/iptv-ld/main/index.m3u) | 2.6 MB |
| [time2shine/Rokon-IPTV](https://github.com/time2shine/Rokon-IPTV) | [playlist.m3u](https://raw.githubusercontent.com/time2shine/Rokon-IPTV/main/playlist.m3u) | 168 KB |

## License

MIT — See [`LICENSE`](LICENSE)

## Contact

ARC-AGI Experiment — `toxicwind` on GitHub
