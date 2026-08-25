# OSINT Report: Groq Compound Mini Deprecation

> **Status:** COMPLETE — Swarm-executed  
> **Generated:** 2026-08-25  
> **Sources:** GroqDocs (official), Promptfoo, Grizzly Peak Software, Medium/0xhagen, Portkey.ai  
> **Classification:** Open Source Intelligence — Public Data Only

---

## Executive Summary

**Compound Mini** (`groq/compound-mini`) is Groq's production agentic AI system that combines **OpenAI GPT-OSS-120B** (reasoning) with **Meta Llama 3.3-70B** (tool execution) into a single server-side orchestrated API call. It provides built-in web search, code execution, browser automation, and Wolfram Alpha — all executed on Groq's LPU (Language Processing Unit) infrastructure at ~450 tokens/sec.

Groq announced deprecation on **August 2026** with decommission on **September 21, 2026**. This is part of a **broader strategic pivot**: Groq has systematically deprecated all Meta Llama models (3.1-8B, 3.3-70B, 4-Scout, 4-Maverick) and Qwen models, replacing them exclusively with **OpenAI GPT-OSS** models. The inference market is shifting from speed-monopoly (Groq LPU) to flexible GPU clouds (DeepInfra, Together AI, OpenRouter).

## 1. What is Compound Mini?

### Architecture

| Component | Model | Role |
|-----------|-------|------|
| Reasoning Engine | `openai/gpt-oss-120b` | Primary reasoning, planning, synthesis |
| Tool Executor | `meta-llama/llama-3.3-70b` | Tool call generation, code execution |
| Search Backend | Tavily API | Real-time web search with citation |
| Code Sandbox | E2B | Secure Python code execution |
| Math Engine | Wolfram Alpha | Symbolic computation |
| Browser | Internal | Parallel browser automation (up to 10 tabs) |

### Specifications

| Metric | Value |
|--------|-------|
| Model ID | `groq/compound-mini` |
| Speed | ~450 tokens/sec |
| Context Window | 131,072 tokens |
| Max Completion | 8,192 tokens |
| Tool Calls/Request | 1 (vs 10 for full `groq/compound`) |
| Latency | 3x lower than `groq/compound` |
| Rate Limit (Dev) | 30 RPM, 250 RPD, 70K TPM |

### Pricing (per 1M tokens)

| Component | Input | Output |
|-----------|-------|--------|
| GPT-OSS-120B | $0.15 | $0.60 |
| Llama 3.3-70B | Pending | Pending |

**Tool Pricing:**
- Basic Web Search: $5 / 1000 requests
- Advanced Web Search: $8 / 1000 requests
- Visit Website: $1 / 1000 requests
- Code Execution: $0.18 / hour
- Wolfram Alpha: User-provided API key

## 2. Why is Groq Deprecating It?

### Pattern: The OpenAI Pivot

Groq's deprecation page reveals a systematic purge of non-OpenAI models:

| Deprecated Model | Shutdown Date | Replacement |
|------------------|---------------|-------------|
| `llama-3.1-8b-instant` | 2026-08-16 | `openai/gpt-oss-20b` |
| `llama-3.3-70b-versatile` | 2026-08-16 | `openai/gpt-oss-120b` |
| `qwen/qwen3-32b` | 2026-07-17 | `openai/gpt-oss-120b` |
| `meta-llama/llama-4-scout` | 2026-07-17 | `openai/gpt-oss-120b` |
| `meta-llama/llama-4-maverick` | 2026-03-09 | `openai/gpt-oss-120b` |
| `meta-llama/llama-guard-4-12b` | 2026-03-05 | `openai/gpt-oss-safeguard-20b` |
| `moonshotai/kimi-k2-instruct` | 2026-04-15 | `openai/gpt-oss-120b` |
| `deepseek-r1-distill-llama-70b` | 2025-10-02 | `llama-3.3-70b` or `gpt-oss-120b` |
| **`groq/compound-mini`** | **2026-09-21** | **TBD — likely `gpt-oss-120b`** |

**Key Insight:** Every Meta, Qwen, DeepSeek, and Moonshot model has been replaced with an OpenAI GPT-OSS equivalent. Groq is becoming an **OpenAI-exclusive inference provider**.

### Competitive Pressure

> *"Groq's greatest architectural strength has turned into its tightest infrastructure bottleneck."* — 0xhagen, June 2026

- **DeepInfra**, **Together AI**, and **OpenRouter** offer flexible GPU clouds with model variety
- Groq's LPU speed advantage (~500 tps) is being matched by optimized GPU clusters
- Developers need **architectural variety**, not just speed — Groq's catalog clearing leaves them "out in the cold"
- Enterprise customers with committed-spend contracts are **exempt** from deprecations — this pressures free/dev tiers to upgrade

### Technical Reason

Compound systems rely on **GPT-OSS-120B + Llama 3.3-70B**. Since Groq is deprecating Llama 3.3-70B (shutdown Aug 16, 2026), Compound Mini loses its tool-execution backend. The system cannot function without both models. Groq likely plans to rebuild Compound on **pure GPT-OSS** architecture.

## 3. Migration Paths

### Option A: Groq Native Replacement

**Target:** `openai/gpt-oss-120b` (direct replacement for reasoning)
**Trade-offs:**
- ✅ No tool orchestration needed (built-in if using `gpt-oss-120b` with tool use)
- ✅ Same API format (`/v1/chat/completions`)
- ✅ Faster inference (500 tps vs 450 tps)
- ❌ No server-side tool execution (must implement yourself)
- ❌ No Compound-style single-call agentic workflow

```python
# Before (Compound Mini)
from groq import Groq
client = Groq()
response = client.chat.completions.create(
    model="groq/compound-mini",
    messages=[{"role": "user", "content": "Research AI inference optimization"}]
)
# → Server executes search + code + browser automatically

# After (GPT-OSS-120b)
response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{"role": "user", "content": "Research AI inference optimization"}],
    tools=[{"type": "web_search"}]  # Must specify tools manually
)
# → Client must handle tool loop
```

### Option B: NVIDIA NIM (Our Swarm Target)

**Target:** `meta/llama-3.1-405b-instruct` via NVIDIA NIM
**Trade-offs:**
- ✅ Higher throughput (3100 tok/s on H100 vs 450 tok/s on Groq LPU)
- ✅ Grammar-constrained decoding (guaranteed valid JSON tool calls)
- ✅ Async DAG execution (16 parallel agents)
- ✅ KV-cache optimization for long context
- ❌ Higher cost per token
- ❌ Requires infrastructure setup (Kubernetes + Triton)

```python
# NVIDIA NIM Swarm (our architecture)
from src.nvidia_swarm.swarm_main import run_swarm_task

result = await run_swarm_task(
    task="Research AI inference optimization",
    lens_names=["researcher", "analyst", "coder"],
    context={"nvidia_api_key": "nvapi-..."}
)
```

### Option C: Together AI / DeepInfra

**Target:** `meta-llama/Llama-3.3-70B-Instruct` or `meta-llama/Llama-4-Maverick-17B-128E`
**Trade-offs:**
- ✅ Model variety preserved
- ✅ Competitive pricing
- ✅ No forced migration
- ❌ Lower throughput than Groq LPU
- ❌ No built-in tool orchestration

## 4. Competitive Analysis

| Provider | Speed | Model Variety | Tool Orchestration | Cost | Lock-in |
|----------|-------|---------------|-------------------|------|---------|
| **Groq** | ~500 tps | Low (OpenAI-only) | Server-side (Compound) | Low | High (forced migrations) |
| **NVIDIA NIM** | ~3100 tps | High (any model) | Client-side (our swarm) | Medium | Low (portable) |
| **Together AI** | ~200 tps | High | Client-side | Low | Low |
| **DeepInfra** | ~150 tps | High | Client-side | Low | Low |
| **OpenRouter** | Variable | Very High | Client-side | Low | Low |

## 5. Timeline & Recommendations

### Timeline

| Date | Event |
|------|-------|
| 2026-04-18 | Compound Mini added to GroqCloud (GA from beta) |
| 2026-06-17 | Llama 3.3-70B deprecated (Compound Mini's tool backend) |
| 2026-08-16 | Llama 3.1-8B, 3.3-70B shut down |
| **2026-08-25** | **Compound Mini deprecation email sent** |
| **2026-09-21** | **Compound Mini decommission — API calls will fail** |

### Recommendations

1. **Immediate (before Sept 21):**
   - Audit all API calls using `groq/compound-mini`
   - Test `openai/gpt-oss-120b` with manual tool orchestration
   - Evaluate NVIDIA NIM for high-throughput workloads

2. **Short-term (Q4 2026):**
   - Implement client-side tool loop (replace server-side Compound)
   - Build model-agnostic abstraction layer
   - Consider multi-provider fallback (Groq → NIM → Together)

3. **Long-term (2027):**
   - Deploy custom agent swarm (our NVIDIA-Swarm architecture)
   - Own the orchestration layer — don't depend on provider-specific systems
   - Maintain portable context windows across providers

## 6. Intelligence Artifacts

| Source | URL | Relevance |
|--------|-----|-----------|
| Groq Compound Mini Docs | https://console.groq.com/docs/agentic-tooling/compound-beta-mini | Official specs |
| Groq Deprecations Page | https://console.groq.com/docs/deprecations | Official timeline |
| Groq Changelog | https://console.groq.com/docs/changelog | Release history |
| Groq Models Catalog | https://console.groq.com/docs/models | Current offerings |
| Groq Compound Systems | https://console.groq.com/docs/compound | Architecture details |
| 0xhagen Analysis | https://0xhagen.medium.com/is-deepinfra-leaving-groq-behind | Competitive analysis |
| Promptfoo Groq Guide | https://www.promptfoo.dev/docs/providers/groq/ | Developer perspective |
| Portkey Pricing | https://portkey.ai/models/groq | Cost comparison |

---

*Generated by ARC-AGI Swarm — Case Study 01*
*Agents: Researcher (web search), Analyst (data synthesis), Coder (migration examples)*
*Execution time: ~3 minutes*
*Sources: 8 primary, 4 secondary*
