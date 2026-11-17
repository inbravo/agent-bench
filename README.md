# agent-bench

> **A pattern-first benchmark for agentic AI — measure every design decision by its cost and quality**

[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Patterns](https://img.shields.io/badge/patterns-32-brightgreen)](#categories)
[![Examples](https://img.shields.io/badge/examples-10%20done-blue)](#completed-examples)

---

## Why Design Patterns for Agentic AI?

Agentic systems fail in predictable ways — and almost never because of the
underlying model. They fail because of **architectural choices**: the wrong
reasoning loop, a topology that creates bottlenecks, tools that are called
when they shouldn't be, or an optimisation that costs more than it saves.
Design patterns give those choices names, structure, and a repeatable shape.
Once a pattern is named it can be measured, compared, and improved.

That is what this repo does. Each folder is one pattern, implemented once per
framework so the *same architectural decision* can be compared across different
tech stacks on a single axis:

```
CPCD = token_cost_usd / quality_score   ← Cost-Per-Correct-Decision
```

**Lower CPCD is better.** It answers: *Is the smarter (more expensive) agent
actually worth it for this specific task?*

For patterns that optimise themselves, a second axis is tracked:

```
CPCD_delta = CPCD_before − CPCD_after   ← Self-Improvement ROI
```

It answers: *Does the cost of optimisation produce a measurable quality gain?*

The frameworks — LangGraph, CrewAI, AG2, DSPy, and others planned — are
**interchangeable implementations** of the patterns, not the subject of study.
The patterns are.

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

| Folder | Pattern | Scenario | Framework |
|---|---|---|---|
| [reasoning/`[tool-use]-[langgraph]-[ollama]`](reasoning/[tool-use]-[langgraph]-[ollama]/README.md) | Tool Use | Weather assistant | LangGraph |
| [reasoning/`[tool-use]-[crewai]-[ollama]`](reasoning/[tool-use]-[crewai]-[ollama]/README.md) | Tool Use | Weather assistant | CrewAI |
| [reasoning/`[tool-use]-[ag2]-[ollama]`](reasoning/[tool-use]-[ag2]-[ollama]/README.md) | Tool Use | Weather assistant | AG2 |
| [reasoning/`[react]-[langgraph]-[ollama]`](reasoning/[react]-[langgraph]-[ollama]/README.md) | ReAct | Book finder | LangGraph |
| [reasoning/`[react]-[crewai]-[ollama]`](reasoning/[react]-[crewai]-[ollama]/README.md) | ReAct | Book finder | CrewAI |
| [reasoning/`[react]-[ag2]-[ollama]`](reasoning/[react]-[ag2]-[ollama]/README.md) | ReAct | Book finder | AG2 |
| [topology/`[fw-swap]-[crewai]-[ollama]`](topology/[fw-swap]-[crewai]-[ollama]/README.md) | Framework Swap | Blog post crew (Researcher → Writer → Editor) | CrewAI |
| [decision-econ/`[cpcd]-[multi]-[ollama]`](decision-econ/[cpcd]-[multi]-[ollama]/README.md) | CPCD | Multi-framework CPCD comparison dashboard | Multi |
| [self-improvement/`[prompt-opt]-[dspy]-[ollama]`](self-improvement/[prompt-opt]-[dspy]-[ollama]/README.md) | Prompt Optimisation | BootstrapFewShot optimiser on weather task | DSPy |
| [self-improvement/`[research-swarm]-[ollama-harness]-[ollama]`](self-improvement/[research-swarm]-[ollama-harness]-[ollama]/README.md) | Self-Critique | Producer-critique revision loop | ollama-harness |

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

## Implementations

The same patterns are implemented across multiple frameworks. The framework is
a variable — swap it via `config.yaml` without changing pattern logic.

| Framework | Install | Notes |
|---|---|---|
| [LangGraph](https://github.com/langchain-ai/langgraph) [![](https://img.shields.io/badge/LangGraph-0.2%2B-orange)](https://github.com/langchain-ai/langgraph) | `pip install langgraph` | Graph-based; explicit state and edges |
| [CrewAI](https://github.com/joaomdmoura/crewAI) [![](https://img.shields.io/badge/CrewAI-0.28%2B-purple)](https://github.com/joaomdmoura/crewAI) | `pip install crewai` | Role-based crews; task hierarchy |
| [AG2](https://github.com/ag2ai/ag2) [![](https://img.shields.io/badge/AG2-0.3%2B-teal)](https://github.com/ag2ai/ag2) | `pip install ag2` | Community AutoGen fork; native Ollama support |
| [DSPy](https://github.com/stanfordnlp/dspy) [![](https://img.shields.io/badge/DSPy-2.5%2B-blueviolet)](https://github.com/stanfordnlp/dspy) | `pip install dspy-ai` | Prompts as learnable parameters |
| Databricks Mosaic AI | — | Planned |
| OpenAI Agents SDK | — | Planned |
| Claude SDK | — | Planned |

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
