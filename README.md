# VOLUME Master 2.0

> **One Master. LMS-Ready Volumes.**  
> Modular EPUB3 splitter with async musepool processing, MCP skill integration, and agentic optimization.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        VOLUME MASTER 2.0                             │
├──────────────┬──────────────┬──────────────┬────────────────────────┤
│   Parsers    │  Splitters   │  Optimizers  │      Exporters         │
│  (EPUB3/2)   │ (size/chunk) │ (font/img)   │  (EPUB/PDF/zip)        │
├──────────────┴──────────────┴──────────────┴────────────────────────┤
│                     MUSEPOOL Async Engine                            │
│         (CDN-aware · Mutative scheduling · Process pool)            │
├─────────────────────────────────────────────────────────────────────┤
│                        MCP SKILLS LAYER                              │
│   byte-vision · agentgateway · shallow · lens · local-llm           │
├─────────────────────────────────────────────────────────────────────┤
│                      AGENTIC ORCHESTRATOR                            │
│      Researcher → Optimizer → Validator → Publisher (DAG)           │
└─────────────────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
pip install -e ".[all]"

# CLI
volume split --input textbook.epub --max-mb 45 --output ./volumes/

# Web UI
volume-web

# Agentic (auto-optimize based on content analysis)
volume-agent --input textbook.epub --mode auto
```

## Musepool Integration

VOLUME uses **musepool** for async chapter processing:

```python
from musepool import ProcessPool
from volume.splitters import SizeSplitter

async with ProcessPool(max_workers=8) as pool:
    volumes = await pool.map(
        SizeSplitter.split_chapter,
        chapters,
        scheduler="mutative",  # CDN-aware, cache-optimized
    )
```

## MCP Skills

| Skill | Source | Purpose |
|---|---|---|
| `shallow` | Local | Fast content analysis (TOC extraction, heading hierarchy) |
| `byte-vision` | byte-vision-mcp | Local LLM chapter summarization |
| `lens` | additional-lens-profiles | Observability & metrics |
| `agentgateway` | agentgateway | Distributed splitting across nodes |

## Agents

```
Researcher  → Analyzes EPUB structure, identifies MathML, images, fonts
Optimizer   → Decides compression strategy (WebP, font subsetting, SVG)
Validator   → Checks output against LMS requirements (size, accessibility)
Publisher   → Packages final ZIP, generates manifest, uploads
```

## License

MIT
