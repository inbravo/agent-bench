# `[fw-swap]-[crewai]-[ollama]` — Framework Swap Pattern

> **Category**: Agent Topology | **Pattern**: Framework Swap | **Framework**: CrewAI | **Backend**: Ollama


## Pattern Diagram

```mermaid
flowchart LR
    A([Blog Topic]) --> B[Researcher]
    B --> C[Writer]
    C --> D[Editor]
    D --> E([Published Post])

    style A fill:#666666,stroke:#fff,color:#fff
    style B fill:#4a7ab5,stroke:#fff,color:#fff
    style C fill:#4a7ab5,stroke:#fff,color:#fff
    style D fill:#4a7ab5,stroke:#fff,color:#fff
    style E fill:#666666,stroke:#fff,color:#fff
```

## What This Example Demonstrates

The same multi-step task (blog post generation) solved with CrewAI instead of LangGraph, enabling a direct framework comparison on CPCD.

**Scenario**: Three-role blog post crew — Researcher → Writer → Editor

## LangGraph vs CrewAI

| Dimension | LangGraph (ReAct) | CrewAI (this example) |
|---|---|---|
| Abstraction | Graph nodes + edges | Agents + Tasks + Crew |
| Roles | Single agent, multiple tools | Multiple specialised agents |
| Flow control | Explicit edge conditions | Sequential or hierarchical process |

## Crew Architecture

```
Task Input
     │
     ▼
Research Analyst  → fetch_facts("walking") → bullet list of facts
     │
     ▼
Content Writer    → draft 3-4 paragraph blog post from facts
     │
     ▼
Senior Editor     → tighten prose, improve opening + conclusion
     │
     ▼
Final blog post
```

## Quick Start

```bash
cd topology/[fw-swap]-[crewai]-[ollama]
pip install crewai
python agent.py
python agent.py "Write a blog post about the benefits of drinking water."
```

## When NOT to Use Framework Swap

- When you are not benchmarking — just choose the right framework
- When role boundaries are unclear — agents will overlap
- When a single ReAct agent can do the job
