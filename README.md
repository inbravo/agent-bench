# agent-bench

> **Agentic AI framework benchmarking — decision economics at the core**

[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2%2B-orange)](https://github.com/langchain-ai/langgraph)
[![CrewAI](https://img.shields.io/badge/CrewAI-0.28%2B-purple)](https://github.com/joaomdmoura/crewAI)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## What Is This Repo?

A structured collection of **agentic design pattern examples** across multiple
frameworks (LangGraph, CrewAI, Databricks Mosaic AI, OpenAI SDK, Claude SDK),
all benchmarked on a single axis:

```
CPCD = token_cost_usd / quality_score
```

**Cost-Per-Correct-Decision (CPCD)** is the primary metric. Lower is better.
It answers: *Is the smarter (more expensive) agent actually worth it?*

---

## Folder Convention

```
[pattern]-[framework]-[backend]/          ← generic examples
[pattern]-[task]-[framework]-[backend]/   ← domain-specific examples
```

Brackets `[]` are visual separators — no dates, no version numbers.

---

## Categories

| # | Folder | Description |
|---|---|---|
| 1 | [reasoning/](reasoning/README.md) | Tool Use, ReAct, Reflection, Plan-and-Execute |
| 2 | [topology/](topology/README.md) | Framework Swap, Role Crew, Orchestrator-Worker, Fan-out |
| 3 | [context-integration/](context-integration/) | MCP Tools, RAG-as-Tool, Memory |
| 4 | [evaluation/](evaluation/) | LLM-as-Judge, Trace-and-Score |
| 5 | [decision-econ/](decision-econ/README.md) | CPCD, Pareto Frontier, Budget, Tier Routing ← *signature* |
| 6 | [governance/](governance/) | HITL, Guardrails, Adversarial Stress |
| 7 | [portability/](portability/) | Backend Swap, Framework Compare, Model Fallback |

Full catalogue with status and "When NOT to use" notes → [`PATTERNS.md`](PATTERNS.md)

---

## Completed Examples

| Folder | Pattern | Scenario |
|---|---|---|
| [reasoning/`[tool-use]-[langgraph]-[ollama]`](reasoning/[tool-use]-[langgraph]-[ollama]/README.md) | Tool Use | Weather assistant |
| [reasoning/`[react]-[langgraph]-[ollama]`](reasoning/[react]-[langgraph]-[ollama]/README.md) | ReAct | Book finder with availability check |
| [topology/`[fw-swap]-[crewai]-[ollama]`](topology/[fw-swap]-[crewai]-[ollama]/README.md) | Framework Swap | Blog post crew (Researcher → Writer → Editor) |
| [decision-econ/`[cpcd]-[multi]-[ollama]`](decision-econ/[cpcd]-[multi]-[ollama]/README.md) | CPCD | Multi-framework CPCD comparison dashboard |

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/inbravo/agent-bench.git
cd agent-bench

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# 3. Install core dependencies
pip install -r requirements.txt

# 4. Start Ollama (must be running locally)
ollama pull llama3.1:8b

# 5. Run your first example
python reasoning/\[tool-use\]-\[langgraph\]-\[ollama\]/agent.py

# 6. Run the CPCD comparison
python decision-econ/\[cpcd\]-\[multi\]-\[ollama\]/agent.py
```

---

## Shared Utilities (`_shared/`)

| Module | Purpose |
|---|---|
| `logging_config.py` | Structured JSON logging, one-line setup |
| `backend.py` | `get_llm(config)` — backend-agnostic LLM factory |
| `scorer.py` | `score_run(...)` → `{ quality_score, token_cost_usd, cpcd }` |

The dual `sys.path` pattern in every `agent.py`:

```python
sys.path.insert(0, str(Path(__file__).parents[2]))               # repo root
sys.path.insert(0, str(Path(__file__).parents[2] / "_shared"))   # shared utils
```

---

## See Also

- [`PATTERNS.md`](PATTERNS.md) — full catalogue: 25 patterns, status tracker, "When NOT to use it"
- [`context-lab`](https://github.com/inbravo/context-lab) — companion repo for context engineering and RAG

---

## Author

**Amit Dixit** · Lead Presales Architect  
[GitHub](https://github.com/inbravo) · [LinkedIn](https://www.linkedin.com/in/inbravo/) · [Web](https://inbravo.github.io)
