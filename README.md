# agent-bench

> **Agentic AI framework benchmarking — decision economics at the core**

[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2%2B-orange)](https://github.com/langchain-ai/langgraph)
[![CrewAI](https://img.shields.io/badge/CrewAI-0.28%2B-purple)](https://github.com/joaomdmoura/crewAI)
[![AG2](https://img.shields.io/badge/AG2-0.3%2B-teal)](https://github.com/ag2ai/ag2)
[![DSPy](https://img.shields.io/badge/DSPy-2.5%2B-blueviolet)](https://github.com/stanfordnlp/dspy)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## What Is This Repo?

A structured collection of **agentic design pattern examples** across multiple
frameworks (LangGraph, CrewAI, AG2, DSPy — Databricks, OpenAI SDK, and Claude SDK planned),
all benchmarked on a single axis:

```
CPCD = token_cost_usd / quality_score
```

**Cost-Per-Correct-Decision (CPCD)** is the primary metric. Lower is better.
It answers: *Is the smarter (more expensive) agent actually worth it?*

For the **self-improvement** category a second axis is tracked:

```
CPCD_delta = CPCD_before − CPCD_after
```

It answers: *Does the cost of optimisation produce a measurable quality gain?*

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
| 8 | [self-improvement/](self-improvement/README.md) | Prompt Optimisation (DSPy), Self-Critique (ollama-harness), Recursive Harness (harness²) |

Full catalogue with status and "When NOT to use" notes → [`PATTERNS.md`](PATTERNS.md)

---

## Completed Examples

| Folder | Pattern | Framework | Scenario |
|---|---|---|---|
| [reasoning/`[tool-use]-[langgraph]-[ollama]`](reasoning/[tool-use]-[langgraph]-[ollama]/README.md) | Tool Use | LangGraph | Weather assistant |
| [reasoning/`[tool-use]-[crewai]-[ollama]`](reasoning/[tool-use]-[crewai]-[ollama]/README.md) | Tool Use | CrewAI | Weather assistant |
| [reasoning/`[tool-use]-[ag2]-[ollama]`](reasoning/[tool-use]-[ag2]-[ollama]/README.md) | Tool Use | AG2 | Weather assistant |
| [reasoning/`[react]-[langgraph]-[ollama]`](reasoning/[react]-[langgraph]-[ollama]/README.md) | ReAct | LangGraph | Book finder |
| [reasoning/`[react]-[crewai]-[ollama]`](reasoning/[react]-[crewai]-[ollama]/README.md) | ReAct | CrewAI | Book finder |
| [reasoning/`[react]-[ag2]-[ollama]`](reasoning/[react]-[ag2]-[ollama]/README.md) | ReAct | AG2 | Book finder |
| [topology/`[fw-swap]-[crewai]-[ollama]`](topology/[fw-swap]-[crewai]-[ollama]/README.md) | Framework Swap | CrewAI | Blog post crew (Researcher → Writer → Editor) |
| [decision-econ/`[cpcd]-[multi]-[ollama]`](decision-econ/[cpcd]-[multi]-[ollama]/README.md) | CPCD | Multi | Multi-framework CPCD comparison dashboard |
| [self-improvement/`[prompt-opt]-[dspy]-[ollama]`](self-improvement/[prompt-opt]-[dspy]-[ollama]/README.md) | Prompt Optimisation | DSPy | BootstrapFewShot optimiser on weather task |
| [self-improvement/`[research-swarm]-[ollama-harness]-[ollama]`](self-improvement/[research-swarm]-[ollama-harness]-[ollama]/README.md) | Self-Critique | ollama-harness | Producer-critique revision loop |

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/inbravo/agent-bench.git
cd agent-bench

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# 3. Install core dependencies (includes langgraph, crewai, ag2, dspy-ai, ollama)
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

- [`PATTERNS.md`](PATTERNS.md) — full catalogue: 32 patterns, status tracker, "When NOT to use it"
- [`context-lab`](https://github.com/inbravo/context-lab) — companion repo for context engineering and RAG

---

## Author

**Amit Dixit** · Lead Presales Architect  
[GitHub](https://github.com/inbravo) · [LinkedIn](https://www.linkedin.com/in/inbravo/) · [Web](https://inbravo.github.io)
