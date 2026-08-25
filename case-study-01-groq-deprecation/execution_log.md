# Swarm Execution Log — Case Study 01

> **Status:** LIVE EXECUTION COMPLETE  
> **Date:** 2026-08-25  
> **Endpoint:** https://integrate.api.nvidia.com/v1/chat/completions  
> **Model:** meta/llama-3.1-8b-instruct  
> **API Key:** nvapi-***[REDACTED]***  

---

## DAG Configuration

```
researcher (8B) ──► analyst (8B) ──► coder (8B)
     │                  │                │
   896ms             4261ms           1060ms
   45 tok out        42 tok out       48 tok out
```

## Agent Outputs

### researcher
> The Groq Compound Mini is a compact, high-performance AI accelerator chip developed by Groq, but it appears to be deprecated as the company has shifted its focus to the more advanced Groq Accelerator 1000.

**Note:** 8B model hallucinated "Groq Accelerator 1000" — does not exist. Need 405B for factual accuracy.

### analyst
> The Groq Compound Mini AI accelerator chip appears to be a legacy product with limited future prospects, as the company has prioritized the development and marketing of its more advanced Groq Accelerator 1000.

**Note:** Propagated hallucination from researcher. Chain-of-thought dependency working correctly.

### coder
```python
print("The Groq Compound Mini AI accelerator chip appears to be a legacy product with limited future prospects, as the company has prioritized the development and marketing of its more advanced Groq Accelerator 1000.")
```

## Throughput Metrics

| Metric | Value |
|--------|-------|
| Total latency | 6218 ms |
| Total tokens out | 135 |
| Effective throughput | 21.7 tok/s |
| Parallel efficiency | 1.0 (serial DAG — researcher blocked analyst) |

## Issues Identified

1. **Model too small:** 8B hallucinated facts. Need 405B for research tasks.
2. **Serial bottleneck:** analyst waited for researcher. Could parallelize with split tasks.
3. **No grammar constraint:** Tool calls not tested. Need regex-constrained decode.
4. **No KV-cache optimization:** Context not packed. Full history sent each time.

## Next Run Targets

- Use `meta/llama-3.1-405b-instruct` for researcher
- Use `meta/llama-3.1-70b-instruct` for analyst (speed/cost balance)
- Parallelize researcher into 4 sub-agents (web search, docs, community, competitive)
- Add grammar constraint for tool-call JSON
- Implement KV-cache sliding window

---

*Proof of live execution. Not simulation.*
