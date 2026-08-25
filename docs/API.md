# API Reference

## NvidiaSwarmDAG

```python
from src.nvidia_swarm.core import NvidiaSwarmDAG, DAGNode

async with NvidiaSwarmDAG(max_concurrent=16, timeout=30) as dag:
    dag.register_agent("researcher", NvidiaAgent(...))
    nodes = [
        DAGNode(agent_name="researcher", dependencies=[], inputs={"task": "..."}),
        DAGNode(agent_name="analyst", dependencies=["researcher"], inputs={"task": "..."}),
    ]
    results = await dag.run_dag(nodes, context)
```

## NvidiaAgent

```python
from src.nvidia_swarm.agent import NvidiaAgent

agent = NvidiaAgent(
    name="researcher",
    system_prompt="You are a research agent.",
    model="meta/llama-3.1-405b-instruct",
    temperature=0.3,
    max_tokens=4096,
    tools=[{"name": "web_search", ...}],
    grammar=r'...',
)
```

## LensProfile

```python
from src.nvidia_swarm.lens import get_lens

lens = get_lens("researcher")
agent = NvidiaAgent(**lens.to_agent_config())
```

## Environment Variables

| Var | Required | Description |
|-----|----------|-------------|
| `NVIDIA_API_KEY` | Yes | NVIDIA NIM API key |
| `NVIDIA_BASE_URL` | No | Default: `https://integrate.api.nvidia.com/v1` |
| `GITHUB_TOKEN` | No | For push operations |
| `SWARM_MAX_CONCURRENT` | No | Default: 16 |
| `SWARM_TIMEOUT` | No | Default: 30 |
