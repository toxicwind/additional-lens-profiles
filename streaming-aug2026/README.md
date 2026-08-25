<div align="center">

# Streaming Ecosystem Discovery — August 2026

[![Repos](https://img.shields.io/badge/repos-324-blue?style=for-the-badge&logo=github)](https://github.com/toxicwind/additional-lens-profiles/tree/main/streaming-aug2026)
[![Nuvio](https://img.shields.io/badge/nuvio-33-ff6b6b?style=for-the-badge)](https://nuvio.tv)
[![Stremio](https://img.shields.io/badge/stremio-106-4ecdc4?style=for-the-badge)](https://stremio.com)
[![IPTV](https://img.shields.io/badge/iptv-209-ffe66d?style=for-the-badge)](https://github.com/iptv-org/iptv)
[![Swarm](https://img.shields.io/badge/NVIDIA--Swarm-active-76c893?style=for-the-badge&logo=nvidia)](https://docs.api.nvidia.com/)

**Autonomous multi-agent discovery of IPTV, Stremio, and Nuvio repositories**  
*Discovered via 5-agent NVIDIA NIM Swarm | Pushed August 1-31, 2026*

</div>

---

## Dataset

| File | Records | Size | Description |
|------|---------|------|-------------|
| [`iptv_stremio_aug2026.jsonl`](iptv_stremio_aug2026.jsonl) | 324 | 211 KB | Full repo dataset with metadata |
| [`nuvio_aug2026.json`](nuvio_aug2026.json) | 33 | 25 KB | Nuvio-specific extract |
| [`deep_scan_aug2026.json`](deep_scan_aug2026.json) | 11 | 20 KB | Live manifest + M3U endpoints |
| [`aug2026_summary.json`](aug2026_summary.json) | — | 1.3 KB | Statistics + top 10 |
| [`aug2026_lens.py`](aug2026_lens.py) | — | 115 KB | Python query module |

---

## Top 10 Repositories

| Rank | Repository | Stars | Platform | Description |
|------|-----------|-------|----------|-------------|
| 1 | [Guovin/iptv-api](https://github.com/Guovin/iptv-api) | 24974 | ![IPTV](https://img.shields.io/badge/IPTV-ffe66d) | ⚡️ IPTV直播源自动更新工具：自动采集、校验、测速并生成可播放结果，支持 M3U/TX |
| 2 | [4gray/iptvnator](https://github.com/4gray/iptvnator) | 6900 | ![IPTV](https://img.shields.io/badge/IPTV-ffe66d) | :tv: Cross-platform IPTV player application w |
| 3 | [dongyubin/IPTV](https://github.com/dongyubin/IPTV) | 4345 | ![IPTV](https://img.shields.io/badge/IPTV-ffe66d) | 2026年8月更新直播源，体育直播源、F1直播源，IPTV电视直播源、APTV电视直播源、 |
| 4 | [Viren070/AIOStreams](https://github.com/Viren070/AIOStreams) | 2571 | ![Stremio](https://img.shields.io/badge/Stremio-4ecdc4) | AIOStreams consolidates multiple Stremio addo |
| 5 | [Stremio/stremio-core](https://github.com/Stremio/stremio-core) | 2285 | ![Stremio](https://img.shields.io/badge/Stremio-4ecdc4) | ⚛️ The Stremio Core: types, addon system, UI  |
| 6 | [taksssss/iptv-tool](https://github.com/taksssss/iptv-tool) | 1107 | ![IPTV](https://img.shields.io/badge/IPTV-ffe66d) | IPTV工具箱， Docker🐳部署，支持EPG管理、直播源管理、台标管理，兼容DIYP/ |
| 7 | [LITUATUI/M3UPT](https://github.com/LITUATUI/M3UPT) | 625 | ![IPTV](https://img.shields.io/badge/IPTV-ffe66d) | IPTV playlist in M3U format with TV and radio |
| 8 | [EdenwareApps/Megacubo](https://github.com/EdenwareApps/Megacubo) | 597 | ![IPTV](https://img.shields.io/badge/IPTV-ffe66d) | 🎬 A powerful, intuitive IPTV streaming app su |
| 9 | [euzu/tuliprox](https://github.com/euzu/tuliprox) | 539 | ![IPTV](https://img.shields.io/badge/IPTV-ffe66d) | Flexible IPTV playlist processor & proxy in R |
| 10 | [akiralereal/iptv](https://github.com/akiralereal/iptv) | 436 | ![IPTV](https://img.shields.io/badge/IPTV-ffe66d) | 自托管的模块化 IPTV 直播源管理与分发系统——把平台抓取源（咪咕 / B 站直播）、精 |


---

## Live Manifest.json Endpoints

| Repository | Manifest | Name | Version | Types |
|------------|----------|------|---------|-------|
| yowmamasita/usa-tv-next | [USA TV Next](https://raw.githubusercontent.com/yowmamasita/usa-tv-next/main/manifest.json) | 2.1.0 | tv |
| esp4ce/stremio-letterboxd-addon | [Stremboxd](https://raw.githubusercontent.com/esp4ce/stremio-letterboxd-addon/main/manifest.json) | 1.0.0 | movie |
| Gowaru/gowaru-nuvio-providers | [Gowaru's Repo](https://raw.githubusercontent.com/Gowaru/gowaru-nuvio-providers/main/manifest.json) | 1.2.0 |  |
| victorgveloso/animes-season-addon | [Animes' season](https://raw.githubusercontent.com/victorgveloso/animes-season-addon/main/manifest.json) | 1.19.1 | movie, series |


---

## Live M3U Playlists

| Repository | Playlist | Size |
|------------|----------|------|
| kl0wn/iptv | [playlist](https://raw.githubusercontent.com/kl0wn/iptv/main/index.m3u) | 8.9 KB |
| shidul100/Iptv | [playlist](https://raw.githubusercontent.com/shidul100/Iptv/main/playlist.m3u) | 30.8 KB |
| time2shine/Rokon-IPTV | [playlist](https://raw.githubusercontent.com/time2shine/Rokon-IPTV/main/playlist.m3u) | 164.6 KB |
| Ace550-Ramon/IPTV | [playlist](https://raw.githubusercontent.com/Ace550-Ramon/IPTV/main/tv.m3u) | 1272.6 KB |
| ikku47/iptv-ld | [playlist](https://raw.githubusercontent.com/ikku47/iptv-ld/main/index.m3u) | 2539.4 KB |
| Adam-ZS/iptv-ru-ua | [playlist](https://raw.githubusercontent.com/Adam-ZS/iptv-ru-ua/main/playlist.m3u) | 5.8 KB |
| Babuperumana/movies_m3u | [playlist](https://raw.githubusercontent.com/Babuperumana/movies_m3u/main/playlist.m3u) | 250.4 KB |


---

## Swarm Agent Outputs

| Agent | Model | Output | Size |
|-------|-------|--------|------|
| Architect | llama-3.1-70b | [`MAXIMAL_architect_141705.md`](MAXIMAL_architect_141705.md) | 7.2 KB |
| Complex Coder | llama-3.1-70b | [`MAXIMAL_complex_coder_141718.md`](MAXIMAL_complex_coder_141718.md) | 6.1 KB |
| Proof Writer | llama-3.1-70b | [`MAXIMAL_proof_writer_141751.md`](MAXIMAL_proof_writer_141751.md) | 5.2 KB |
| Analyst | llama-3.1-70b | [`MAXIMAL_analyst_141708.md`](MAXIMAL_analyst_141708.md) | 3.3 KB |
| Reporter | llama-3.1-70b | [`MAXIMAL_reporter_141941.md`](MAXIMAL_reporter_141941.md) | 3.7 KB |

**Total swarm latency:** ~280s (4 parallel + 1 sequential)

---

## Code

| File | Purpose |
|------|---------|
| [`streaming_discovery.py`](streaming_discovery.py) | Async discovery module with argparse CLI |

---

## Nuvio Ecosystem Intelligence

| Resource | URL | Purpose |
|----------|-----|---------|
| Nuvio Cloud API | `https://api.nuvio.tv` | Official Supabase endpoint |
| Nuvio Docs | `https://nuvioapp.space/docs` | Public API docs |
| Trakt-Nuvio Bridge | `trakt-nuvio.duckdns.org` | Trakt history sync |
| Nuvio Account Manager | [GitHub](https://github.com/techuhak/Nuvio-Account-Manager) | Account clone/migrate |
| Scrob | [GitHub](https://github.com/ellite/scrob) | Cross-platform tracker |

---

<div align="center">

**Generated**: 2026-08-25 15:29 UTC  
**Method**: 5-agent NVIDIA NIM Swarm + GitHub Search API + Deep Endpoint Scan  
**Model**: meta/llama-3.1-70b-instruct

</div>
